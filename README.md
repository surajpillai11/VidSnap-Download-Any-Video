# VidSnap — Video Downloader

A professional self-hosted video downloader built with **Python + Flask + yt-dlp**.
Supports 1000+ sites: YouTube, Instagram, Twitter, TikTok, Apna College, and more.

---

## Project Structure

```
vidsnap/
├── app.py              ← Flask backend (API server)
├── index.html          ← Frontend (the website)
├── requirements.txt    ← Python dependencies
└── downloads/          ← Temp folder (auto-created, auto-cleaned)
```

---

## Run Locally (your computer)

### Step 1 — Install Python 3.10+
Download from https://python.org if not installed.

### Step 2 — Install dependencies
```bash
pip install -r requirements.txt
```

### Step 3 — Install ffmpeg (required for merging video+audio)
- **Windows**: Download from https://ffmpeg.org/download.html → add to PATH
- **Mac**: `brew install ffmpeg`
- **Linux / Replit / Render**: `apt-get install ffmpeg` (usually pre-installed)

### Step 4 — Start the backend
```bash
python app.py
```
Backend runs at http://localhost:5000

### Step 5 — Open the frontend
Open `index.html` in your browser directly, OR serve it:
```bash
python -m http.server 8080
```
Then go to http://localhost:8080

---

## Deploy on Render (free, recommended)

1. Push all files to a **GitHub repo**
2. Go to https://render.com → New → Web Service
3. Connect your GitHub repo
4. Settings:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python app.py`
   - **Environment**: Python 3
5. Click **Deploy**
6. Copy your Render URL (e.g. `https://vidsnap.onrender.com`)
7. Open `index.html`, find `const API_BASE = 'http://localhost:5000'`
   and replace it with your Render URL
8. Host `index.html` on Render Static Site, GitHub Pages, or Netlify

---

## Deploy on Replit

1. Go to https://replit.com → Create Repl → Python
2. Upload `app.py`, `index.html`, `requirements.txt`
3. In the Shell tab run: `pip install -r requirements.txt`
4. Click **Run** — Replit gives you a public URL automatically
5. Update `API_BASE` in `index.html` to your Replit URL
6. For the frontend: create a new Repl → HTML/CSS/JS → paste `index.html`

---

## API Endpoints

### GET /
Health check — returns `{"status": "VidSnap API running"}`

### POST /info
Get video metadata without downloading.
```json
Request:  { "url": "https://youtube.com/watch?v=..." }
Response: { "title": "...", "thumbnail": "...", "duration": 120, "uploader": "..." }
```

### POST /download
Download and stream the video file.
```json
Request: {
  "url": "https://youtube.com/watch?v=...",
  "format": "mp4",       // mp4 | mp3 | webm
  "quality": "720p"      // best | 1080p | 720p | 480p | 360p
}
Response: Binary file stream (video/mp4, audio/mpeg, etc.)
```

---

## Notes

- Files are automatically deleted from the server after download
- The `downloads/` folder is auto-cleaned every 5 minutes
- For personal use only — respect copyright and site terms of service
- Some sites (e.g. Instagram) may require cookies for private content
