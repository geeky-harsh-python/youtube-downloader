import os
import yt_dlp
import subprocess
import re
from pathlib import Path
from flask import Flask, request, jsonify, render_template, send_from_directory, after_this_request

app = Flask(__name__)

# Output directory for downloads
OUTPUT_DIR = Path("downloads")
OUTPUT_DIR.mkdir(exist_ok=True)

def sanitize_filename(filename):
    return re.sub(r'[<>:"/\\|?*]', "", filename).replace(" ", "_")

def get_video_title(video_url):
    ydl_opts = {"quiet": True, "noplaylist": True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(video_url, download=False)
        return sanitize_filename(info_dict.get("title", "video"))

def get_best_webm_formats(video_url, resolution):
    ydl_opts = {"quiet": True, "noplaylist": True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(video_url, download=False)
        formats = info_dict.get("formats", [])
        video_format = None
        audio_format = None
        for fmt in formats:
            if (fmt.get("height") == int(resolution) and fmt.get("ext") == "webm" and fmt.get("vcodec") != "none"):
                video_format = fmt
            if (fmt.get("acodec") == "opus" and fmt.get("ext") == "webm" and 
                (audio_format is None or fmt.get("abr", 0) > audio_format.get("abr", 0))):
                audio_format = fmt
        return video_format, audio_format

def download_webm(video_url, resolution):
    video_title = get_video_title(video_url)
    video_file = OUTPUT_DIR / f"{video_title}_{resolution}p_video.webm"
    audio_file = OUTPUT_DIR / f"{video_title}_{resolution}p_audio.webm"
    final_file = OUTPUT_DIR / f"{video_title}_{resolution}p_final.webm"

    video_format, audio_format = get_best_webm_formats(video_url, resolution)
    if not video_format or not audio_format:
        ydl_opts = {
            "format": "bestvideo[ext=webm]+bestaudio[ext=webm]/best[ext=webm]",
            "outtmpl": str(final_file),
            "noplaylist": True,
            "merge_output_format": "webm",
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
        return final_file.name

    ydl_opts_video = {"format": video_format["format_id"], "outtmpl": str(video_file), "noplaylist": True}
    ydl_opts_audio = {"format": audio_format["format_id"], "outtmpl": str(audio_file), "noplaylist": True}

    with yt_dlp.YoutubeDL(ydl_opts_video) as ydl:
        ydl.download([video_url])
    with yt_dlp.YoutubeDL(ydl_opts_audio) as ydl:
        ydl.download([video_url])

    return merge_webm_files(video_file, audio_file, final_file)

def download_best_audio(video_url):
    video_title = get_video_title(video_url)
    audio_file_webm = OUTPUT_DIR / f"{video_title}_best_audio.webm"
    audio_file_mp3 = OUTPUT_DIR / f"{video_title}_best_audio.mp3"

    ydl_opts_audio = {
        "format": "bestaudio[ext=webm]/bestaudio",
        "outtmpl": str(audio_file_webm),
        "noplaylist": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts_audio) as ydl:
        ydl.download([video_url])

    convert_audio_to_mp3(audio_file_webm, audio_file_mp3)
    return audio_file_mp3.name

def convert_audio_to_mp3(input_file, output_file):
    command = ["ffmpeg", "-i", str(input_file), "-vn", "-ab", "192k", "-ar", "44100", "-y", str(output_file)]
    subprocess.run(command, check=True, capture_output=True, text=True)
    input_file.unlink(missing_ok=True)

def merge_webm_files(video_file, audio_file, output_file):
    command = ["ffmpeg", "-i", str(video_file), "-i", str(audio_file), "-c:v", "copy", "-c:a", "copy", "-y", str(output_file)]
    subprocess.run(command, check=True, capture_output=True, text=True)
    video_file.unlink(missing_ok=True)
    audio_file.unlink(missing_ok=True)
    return output_file.name

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    data = request.json
    video_url = data.get('url')
    choice = data.get('choice')
    resolution = data.get('resolution')

    try:
        if not video_url:
            return jsonify({'error': 'URL is required'}), 400

        if choice == '1' and resolution in ['360', '480', '720', '1080']:
            filename = download_webm(video_url, resolution)
        elif choice == '2':
            filename = download_best_audio(video_url)
        else:
            return jsonify({'error': 'Invalid choice or resolution'}), 400
        
        return jsonify({'filename': filename})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/downloads/<filename>')
def serve_file(filename):
    file_path = OUTPUT_DIR / filename
    if not file_path.exists():
        return jsonify({'error': 'File not found'}), 404
    
    @after_this_request
    def cleanup(response):
        try:
            file_path.unlink(missing_ok=True)
            print(f"Deleted {filename} from server")
        except Exception as e:
            print(f"Error deleting {filename}: {e}")
        return response

    return send_from_directory(OUTPUT_DIR, filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)