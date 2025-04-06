# Use official Python image
FROM python:3.10-slim

# Install ffmpeg and other necessary packages
RUN apt-get update && apt-get install -y ffmpeg gcc && apt-get clean

# Set working directory
WORKDIR /app

# Copy project files
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port
EXPOSE 5000

# Start the app with gunicorn
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:5000"]
