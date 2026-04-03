"""
VidSnap Backend — Production Ready v2.1
Optimized for Render.com
"""

import os
import uuid
import threading
import time
import shutil
from pathlib import Path

from flask import Flask, request, jsonify, send_file, after_this_request
from flask_cors import CORS
import yt_dlp

# ========================= APP SETUP =========================
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)

# FFmpeg check (important for Render)
FFMPEG_PATH = shutil.which('ffmpeg')

# Auto cleanup thread
def cleanup_old_files():
    while True:
        time.sleep(300)  # every 5 minutes
        now = time.time()
        for file in DOWNLOAD_DIR.iterdir():
            if file.is_file() and now - file.stat().st_mtime > 600:  # older than 10 minutes
                try:
                    file.unlink(missing_ok=True)
                except:
                    pass

threading.Thread(target=cleanup_old_files, daemon=True).start()


# ========================= FORMAT & OPTIONS =========================
QUALITY_MAP = {
    "best": "",
    "1080p": "[height<=1080]",
    "720p": "[height<=720]",
    "480p": "[height<=480]",
    "360p": "[height<=360]",
}

def build_format_string(fmt: str, quality: str) -> str:
    q = QUALITY_MAP.get(quality, "")

    if fmt == "mp3":
        return "bestaudio/best"

    # Prioritize MP4, then WebM, then best available
    return (
        f"bestvideo[ext=mp4]{q}+bestaudio[ext=m4a]/"
        f"bestvideo[ext=webm]{q}+bestaudio[ext=webm]/"
        f"bestvideo{q}+bestaudio/best{q}"
    )


def make_ydl_opts(output_path: str, fmt: str, quality: str) -> dict:
    opts = {
        "outtmpl": output_path,
        "format": build_format_string(fmt, quality),
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "merge_output_format": "mp4" if fmt != "mp3" else None,
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        },
        "socket_timeout": 60,
        "retries": 5,
        "fragment_retries": 5,
        "continuedl": True,
    }

    if FFMPEG_PATH:
        opts["ffmpeg_location"] = FFMPEG_PATH

    if fmt == "mp3":
        opts["postprocessors"] = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }]

    return opts


# ========================= ROUTES =========================
@app.route("/")
def index():
    return jsonify({
        "status": "VidSnap API is running",
        "version": "2.1",
        "ffmpeg_available": bool(FFMPEG_PATH)
    })


@app.route("/info", methods=["POST"])
def get_info():
    data = request.get_json(silent=True) or {}
    url = data.get("url", "").strip()

    if not url:
        return jsonify({"error": "URL is required"}), 400

    try:
        with yt_dlp.YoutubeDL({
            "quiet": True,
            "skip_download": True,
            "noplaylist": True,
        }) as ydl:
            info = ydl.extract_info(url, download=False)

        return jsonify({
            "title": info.get("title", "Unknown Title"),
            "thumbnail": info.get("thumbnail"),
            "duration": info.get("duration"),
            "uploader": info.get("uploader"),
            "webpage_url": info.get("webpage_url", url),
        })

    except yt_dlp.utils.DownloadError as e:
        return jsonify({"error": str(e)}), 422
    except Exception as e:
        return jsonify({"error": "Failed to fetch video information"}), 500


@app.route("/download", methods=["POST"])
def download_video():
    data = request.get_json(silent=True) or {}
    url = data.get("url", "").strip()
    fmt = data.get("format", "mp4").lower()
    quality = data.get("quality", "best").lower()

    if not url:
        return jsonify({"error": "URL is required"}), 400
    if fmt not in ("mp4", "mp3", "webm"):
        return jsonify({"error": "Invalid format. Use mp4, mp3 or webm"}), 400

    uid = uuid.uuid4().hex[:12]
    output_template = str(DOWNLOAD_DIR / f"{uid}_%(title)s.%(ext)s")

    try:
        ydl_opts = make_ydl_opts(output_template, fmt, quality)

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            downloaded_path = ydl.prepare_filename(info)

        # Handle MP3 file extension
        if fmt == "mp3":
            mp3_path = Path(downloaded_path).with_suffix(".mp3")
            if mp3_path.exists():
                downloaded_path = str(mp3_path)

        # Failsafe: Find file if naming changed
        file_path = Path(downloaded_path)
        if not file_path.exists():
            candidates = list(DOWNLOAD_DIR.glob(f"{uid}*"))
            if candidates:
                file_path = candidates[0]
            else:
                return jsonify({"error": "Downloaded file not found"}), 500

        # Auto-delete after sending response
        @after_this_request
        def remove_file(response):
            try:
                if file_path.exists():
                    file_path.unlink()
            except:
                pass
            return response

        # Safe filename for download
        title = info.get("title", "video")[:60]
        safe_title = "".join(c if c.isalnum() or c in " -_()" else "_" for c in title)
        filename = f"{safe_title}.{fmt}"

        mimetype = {
            "mp4": "video/mp4",
            "webm": "video/webm",
            "mp3": "audio/mpeg"
        }.get(fmt, "application/octet-stream")

        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename,
            mimetype=mimetype
        )

    except yt_dlp.utils.DownloadError as e:
        return jsonify({"error": f"Download failed: {str(e)}"}), 422
    except Exception as e:
        return jsonify({"error": "Unexpected server error"}), 500


# ========================= RUN SERVER =========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 VidSnap API running on port {port}")
    print(f"📍 FFmpeg available: {bool(FFMPEG_PATH)}")
    app.run(host="0.0.0.0", port=port)