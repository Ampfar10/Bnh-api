import os
import shutil
from flask import Flask, request, send_file, jsonify
from yt_dlp import YoutubeDL
from threading import Thread
import tempfile

app = Flask(__name__)

# Config: max file size ~100MB to avoid overload
MAX_FILE_SIZE_MB = 1000

def download_youtube_audio(url: str, outdir: str):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(outdir, '%(title)s.%(ext)s'),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True,
        'no_warnings': True,
    }
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        mp3_filename = os.path.splitext(filename)[0] + '.mp3'
        return mp3_filename

def download_youtube_video(url: str, outdir: str):
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': os.path.join(outdir, '%(title)s.%(ext)s'),
        'quiet': True,
        'no_warnings': True,
        'merge_output_format': 'mp4',
    }
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        # yt-dlp merges video+audio to mp4
        mp4_filename = os.path.splitext(filename)[0] + '.mp4'
        return mp4_filename

def remove_file_later(filepath: str):
    # Remove after 30 seconds (adjust as needed)
    import time
    time.sleep(30)
    try:
        os.remove(filepath)
    except Exception:
        pass

@app.route('/download/song', methods=['GET'])
def download_song():
    url = request.args.get('url')
    if not url:
        return jsonify({'error': 'Missing "url" parameter'}), 400

    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            filepath = download_youtube_audio(url, tmpdir)
            filesize_mb = os.path.getsize(filepath) / (1024 * 1024)
            if filesize_mb > MAX_FILE_SIZE_MB:
                return jsonify({'error': f'File too large ({filesize_mb:.2f}MB), max is {MAX_FILE_SIZE_MB}MB'}), 400

            # Send file and auto delete after sending
            response = send_file(filepath, as_attachment=True)
            
            # Background delete
            Thread(target=remove_file_later, args=(filepath,)).start()

            return response
        except Exception as e:
            return jsonify({'error': f'Failed to download audio: {str(e)}'}), 500

@app.route('/download/video', methods=['GET'])
def download_video():
    url = request.args.get('url')
    if not url:
        return jsonify({'error': 'Missing "url" parameter'}), 400

    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            filepath = download_youtube_video(url, tmpdir)
            filesize_mb = os.path.getsize(filepath) / (1024 * 1024)
            if filesize_mb > MAX_FILE_SIZE_MB:
                return jsonify({'error': f'File too large ({filesize_mb:.2f}MB), max is {MAX_FILE_SIZE_MB}MB'}), 400

            response = send_file(filepath, as_attachment=True)
            Thread(target=remove_file_later, args=(filepath,)).start()
            return response
        except Exception as e:
            return jsonify({'error': f'Failed to download video: {str(e)}'}), 500

@app.route('/')
def index():
    return """
    <h2>YouTube Downloader API</h2>
    <p>Use <code>/download/song?url=VIDEO_URL</code> to download audio (MP3)</p>
    <p>Use <code>/download/video?url=VIDEO_URL</code> to download video (MP4)</p>
    """

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=1000)
                  
