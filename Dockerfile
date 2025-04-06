# Use a lightweight official Python image
FROM python:3.10-slim

# Set working directory inside the container
WORKDIR /app

# Copy all contents of yt_downloader folder into /app
COPY yt_downloader/ /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port used by Flask
EXPOSE 8000

# Run the Flask app
CMD ["python", "app.py"]
