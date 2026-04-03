// ── UPDATE THIS TO YOUR RENDER URL ──
const API_BASE = 'https://vidsnap-download-any-video.onrender.com';   // ← Change this!

let selectedFormat = 'mp4';
let selectedQuality = 'best';

function setFmt(btn) {
  document.querySelectorAll('.fmt-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  selectedFormat = btn.dataset.fmt;
  document.getElementById('quality-row').classList.toggle('hidden', selectedFormat === 'mp3');
}

function setQuality(btn) {
  document.querySelectorAll('.quality-pill').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  selectedQuality = btn.dataset.quality;
}

function showToast(msg, type = 'success') {
  const toast = document.getElementById('toast');
  toast.textContent = msg;
  toast.className = `toast show ${type}`;
  setTimeout(() => toast.className = 'toast', 4000);
}

function setStatus(msg, type = '') {
  const el = document.getElementById('status-text');
  el.textContent = msg;
  el.className = `status-text ${type}`;
}

function setProgress(pct) {
  document.getElementById('progress-bar').style.width = pct + '%';
}

function detectSite(url) {
  const host = url.toLowerCase();
  if (host.includes('youtube') || host.includes('youtu.be')) return 'YouTube';
  if (host.includes('instagram')) return 'Instagram';
  if (host.includes('twitter') || host.includes('x.com')) return 'X / Twitter';
  if (host.includes('tiktok')) return 'TikTok';
  if (host.includes('reddit')) return 'Reddit';
  if (host.includes('vimeo')) return 'Vimeo';
  if (host.includes('facebook')) return 'Facebook';
  return 'Video Platform';
}

async function fetchInfo(url) {
  try {
    const res = await fetch(`${API_BASE}/info`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url })
    });
    return res.ok ? await res.json() : null;
  } catch {
    return null;
  }
}

async function startDownload() {
  const url = document.getElementById('url-input').value.trim();
  if (!url || !url.startsWith('http')) {
    showToast('Please enter a valid video URL', 'error');
    return;
  }

  const btn = document.getElementById('download-btn');
  btn.disabled = true;
  document.getElementById('btn-icon').innerHTML = '⟳';
  document.getElementById('btn-text').textContent = 'Processing...';

  const statusArea = document.getElementById('status-area');
  const videoInfo = document.getElementById('video-info');
  statusArea.style.display = 'block';
  videoInfo.classList.remove('show');
  setProgress(10);
  setStatus('Fetching video info...');

  const info = await fetchInfo(url);
  if (info?.title) {
    document.getElementById('video-title').textContent = info.title;
    document.getElementById('video-site-name').textContent = detectSite(url);
    if (info.thumbnail) {
      document.getElementById('thumb-img').src = info.thumbnail;
      videoInfo.classList.add('show');
    }
  }

  setProgress(40);
  setStatus('Downloading...');

  try {
    const res = await fetch(`${API_BASE}/download`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url, format: selectedFormat, quality: selectedQuality })
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.error || 'Download failed');
    }

    setProgress(75);
    setStatus('Finalizing file...');

    const blob = await res.blob();
    const ext = selectedFormat;
    let filename = (info?.title || 'video')
      .replace(/[^a-z0-9\s-]/gi, '_')
      .replace(/\s+/g, '_')
      .slice(0, 60);

    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `${filename}.${ext}`;
    link.click();
    URL.revokeObjectURL(link.href);

    setProgress(100);
    setStatus('✓ Download started!', 'success');
    showToast('Download started successfully!', 'success');

  } catch (e) {
    setStatus('✗ ' + e.message, 'error');
    showToast(e.message, 'error');
  } finally {
    btn.disabled = false;
    document.getElementById('btn-icon').textContent = '↓';
    document.getElementById('btn-text').textContent = 'Download Now';
  }
}

// Keyboard & Clipboard support
document.getElementById('url-input').addEventListener('keydown', e => {
  if (e.key === 'Enter') startDownload();
});

document.getElementById('url-input').addEventListener('focus', async () => {
  const input = document.getElementById('url-input');
  if (input.value) return;
  try {
    const text = await navigator.clipboard.readText();
    if (text.startsWith('http')) input.value = text.trim();
  } catch {}
});