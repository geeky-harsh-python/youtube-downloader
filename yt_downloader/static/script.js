document.getElementById('downloadForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const url = document.getElementById('url').value;
    const choice = document.getElementById('choice').value;
    const resolution = document.getElementById('resolution').value;
    const status = document.getElementById('status');
    const downloadLink = document.getElementById('downloadLink');

    status.textContent = 'Downloading...';
    downloadLink.style.display = 'none';

    try {
        const response = await fetch('/download', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url, choice, resolution })
        });
        const data = await response.json();

        if (response.ok) {
            status.textContent = 'Download starting...';
            downloadLink.href = `/downloads/${data.filename}`;
            downloadLink.style.display = 'none';
            setTimeout(() => {
                downloadLink.click();
                status.textContent = 'Download complete!';
            }, 500);
        } else {
            status.textContent = `Error: ${data.error}`;
        }
    } catch (error) {
        status.textContent = `Error: ${error.message}`;
    }
});

document.getElementById('choice').addEventListener('change', (e) => {
    document.getElementById('resolutionDiv').style.display = e.target.value === '1' ? 'block' : 'none';
});