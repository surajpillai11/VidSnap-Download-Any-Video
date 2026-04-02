// ── CONFIG: change this to your deployed backend URL ──
const API_BASE = 'http://localhost:5000';

let selectedFormat = 'mp4';
let selectedQuality = 'best';

function setFmt(btn) {
  document.querySelectorAll('.fmt-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  selectedFormat = btn.dataset.fmt;

  const qualityRow = document.getElementById('quality-row');
  if (selectedFormat === 'mp3') {
    qualityRow.classList.add('hidden');
  } else {
    qualityRow.classList.remove('hidden');
  }
}

function setQuality(btn) {
  document.querySelectorAll('.quality-pill').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  selectedQuality = btn.dataset.quality;
}

function showToast(msg, type = 'success') {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.className = 'show ' + type;
  setTimeout(() => t.className = '', 3000);
}

function setStatus(msg, type = '') {
  const el = document.getElementById('status-text');
  el.textContent = msg;
  el.className = 'status-text ' + type;
}

function setProgress(pct) {
  document.getElementById('progress-bar').style.width = pct + '%';
}

function detectSite(url) {
  if (url.includes('youtube') || url.includes('youtu.be')) return 'YouTube';
  if (url.includes('instagram')) return 'Instagram';
  if (url.includes('twitter') || url.includes('x.com')) return 'Twitter / X';
  if (url.includes('reddit')) return 'Reddit';
  if (url.includes('tiktok')) return 'TikTok';
  if (url.includes('vimeo')) return 'Vimeo';
  if (url.includes('facebook') || url.includes('fb.watch')) return 'Facebook';
  if (url.includes('apnacollege')) return 'Apna College';
  return 'Video site';
}

async function fetchInfo(url) {
  try {
    const res = await fetch(`${API_BASE}/info`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url })
    });
    if (!res.ok) return null;
    return await res.json();
  } catch { return null; }
}

async function startDownload() {
  const url = document.getElementById('url-input').value.trim();
  if (!url) { showToast('Please paste a video URL first', 'error'); return; }
  if (!url.startsWith('http')) { showToast('Please enter a valid URL starting with http', 'error'); return; }

  const btn = document.getElementById('download-btn');
  const statusArea = document.getElementById('status-area');
  const videoInfo = document.getElementById('video-info');

  btn.disabled = true;
  document.getElementById('btn-icon').innerHTML = '<span class="spinner"></span>';
  document.getElementById('btn-text').textContent = 'Processing...';
  statusArea.style.display = 'block';
  videoInfo.classList.remove('show');
  setProgress(10);
  setStatus('Fetching video information...');

  // Fetch video info first
  const info = await fetchInfo(url);
  if (info && info.title) {
    document.getElementById('video-title').textContent = info.title;
    document.getElementById('video-site-name').textContent = detectSite(url);
    if (info.thumbnail) {
      document.getElementById('thumb-img').src = info.thumbnail;
      videoInfo.classList.add('show');
    }
  }

  setProgress(30);
  setStatus('Downloading video...');

  try {
    const res = await fetch(`${API_BASE}/download`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url, format: selectedFormat, quality: selectedQuality })
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ error: 'Server error' }));
      throw new Error(err.error || 'Download failed');
    }

    setProgress(80);
    setStatus('Preparing your file...');

    const blob = await res.blob();
    setProgress(100);

    // Trigger browser download
    const ext = selectedFormat === 'mp3' ? 'mp3' : selectedFormat === 'webm' ? 'webm' : 'mp4';
    const filename = (info?.title || 'video').replace(/[^a-z0-9]/gi, '_') + '.' + ext;
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();

    setStatus('✓ Download complete!', 'success');
    showToast('Downloaded successfully!', 'success');

  } catch (e) {
    setStatus('✗ ' + e.message, 'error');
    showToast(e.message, 'error');
  } finally {
    btn.disabled = false;
    document.getElementById('btn-icon').textContent = '↓';
    document.getElementById('btn-text').textContent = 'Download Now';
  }
}

// Allow pressing Enter to download
document.getElementById('url-input').addEventListener('keydown', e => {
  if (e.key === 'Enter') startDownload();
});

// Auto-paste on focus if clipboard has a URL
document.getElementById('url-input').addEventListener('focus', async () => {
  if (document.getElementById('url-input').value) return;
  try {
    const text = await navigator.clipboard.readText();
    if (text.startsWith('http')) {
      document.getElementById('url-input').value = text;
    }
  } catch {}
});
