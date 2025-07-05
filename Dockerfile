# Use official Python slim image
FROM python:3.11-slim

# Install ffmpeg (required for audio conversion)
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy project files
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port 10000 (Render default)
EXPOSE 10000

# Run the app with Gunicorn (better production server)
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:10000", "--workers", "2"]
