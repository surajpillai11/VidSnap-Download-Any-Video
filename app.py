"""
VidSnap Backend — Final Stable Version
Flask + yt-dlp video downloader API
"""

import os
import uuid
import threading
import time
from pathlib import Path

from flask import Flask, request, jsonify, send_file, after_this_request
from flask_cors import CORS
import yt_dlp

# ──────────────────────────────────────────────
# App Setup
# ──────────────────────────────────────────────

app = Flask(__name__)
CORS(app)

DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)

# Auto cleanup older than 10 minutes
def cleanup_old_files():
    while True:
        time.sleep(300)
        now = time.time()
        for f in DOWNLOAD_DIR.iterdir():
            if f.is_file() and now - f.stat().st_mtime > 600:
                f.unlink(missing_ok=True)

threading.Thread(target=cleanup_old_files, daemon=True).start()


# ──────────────────────────────────────────────
# Format Builders
# ──────────────────────────────────────────────

QUALITY_MAP = {
    "best": "",
    "1080p": "[height<=1080]",
    "720p": "[height<=720]",
    "480p": "[height<=480]",
    "360p": "[height<=360]",
}

def build_format_string(fmt: str, quality: str) -> str:
    """
    Stable yt-dlp format selector:
    Guarantees fallback formats so download never breaks.
    """
    q = QUALITY_MAP.get(quality, "")

    # AUDIO ONLY
    if fmt == "mp3":
        return "bestaudio/best"

    # MP4 preferred
    mp4_fmt = f"bestvideo[ext=mp4]{q}+bestaudio[ext=m4a]/best[ext=mp4]{q}"

    # WebM backup
    webm_fmt = f"bestvideo[ext=webm]{q}+bestaudio[ext=webm]/best[ext=webm]{q}"

    # Final fallback (any format)
    fallback = f"bestvideo{q}+bestaudio/best{q}"

    return f"{mp4_fmt}/{webm_fmt}/{fallback}"


def make_ydl_opts(output_path: str, fmt: str, quality: str) -> dict:
    opts = {
        "outtmpl": output_path,
        "format": build_format_string(fmt, quality),
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "merge_output_format": fmt if fmt != "mp3" else None,
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        },
        "socket_timeout": 30,
        "retries": 3,
    }

    if fmt == "mp3":
        opts["postprocessors"] = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }]

    return opts


# ──────────────────────────────────────────────
# Routes
# ──────────────────────────────────────────────

@app.route("/", methods=["GET"])
def index():
    return jsonify({"status": "VidSnap API running", "version": "1.1.0"})


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
            "noplaylist": True
        }) as ydl:
            info = ydl.extract_info(url, download=False)

        return jsonify({
            "title": info.get("title", "Unknown"),
            "thumbnail": info.get("thumbnail"),
            "duration": info.get("duration"),
            "uploader": info.get("uploader"),
            "webpage_url": info.get("webpage_url", url),
        })

    except yt_dlp.utils.DownloadError as e:
        return jsonify({"error": str(e)}), 422

    except Exception:
        return jsonify({"error": "Could not fetch video info"}), 500


@app.route("/download", methods=["POST"])
def download_video():
    data = request.get_json(silent=True) or {}
    url = data.get("url", "").strip()
    fmt = data.get("format", "mp4").lower()
    quality = data.get("quality", "best").lower()

    if not url:
        return jsonify({"error": "URL is required"}), 400

    if fmt not in ("mp4", "mp3", "webm"):
        return jsonify({"error": "Invalid format"}), 400

    uid = uuid.uuid4().hex[:8]
    output_template = str(DOWNLOAD_DIR / f"{uid}_%(title)s.%(ext)s")

    try:
        ydl_opts = make_ydl_opts(output_template, fmt, quality)

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            downloaded_path = ydl.prepare_filename(info)

        # MP3 renaming fix
        if fmt == "mp3":
            mp3_path = Path(downloaded_path).with_suffix(".mp3")
            if mp3_path.exists():
                downloaded_path = str(mp3_path)

        # FAILSAFE: find file if name changed
        if not Path(downloaded_path).exists():
            candidates = list(DOWNLOAD_DIR.glob(f"{uid}*"))
            if not candidates:
                return jsonify({"error": "File missing"}), 500
            downloaded_path = str(candidates[0])

        # Delete file after sending
        @after_this_request
        def remove_file(response):
            try:
                os.unlink(downloaded_path)
            except:
                pass
            return response

        # Download file to user
        title = info.get("title", "video")
        safe_title = "".join(c if c.isalnum() or c in " -_" else "_" for c in title)[:60]
        filename = f"{safe_title}.{fmt}"

        mimetype = {
            "mp4": "video/mp4",
            "webm": "video/webm",
            "mp3": "audio/mpeg"
        }.get(fmt, "application/octet-stream")

        return send_file(
            downloaded_path,
            as_attachment=True,
            download_name=filename,
            mimetype=mimetype
        )

    except yt_dlp.utils.DownloadError as e:
        return jsonify({"error": "Download failed: " + str(e)}), 422

    except Exception:
        return jsonify({"error": "Unexpected server error"}), 500


# ──────────────────────────────────────────────
# Run Server
# ──────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 VidSnap API running on http://127.0.0.1:{port}")
    app.run(host="0.0.0.0", port=port)