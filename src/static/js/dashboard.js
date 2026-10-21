/* =============================================================================
   dashboard.js – CrimeVision AI frontend logic
   All API calls use the Flask REST endpoints.
   No framework dependencies – vanilla JS only.
   ============================================================================= */

'use strict';

// ── State ────────────────────────────────────────────────────────────────────
const state = {
  caseId: '',
  imageFile: null,
  audioFile: null,
  videoFile: null,
  stats: { images: 0, audio: 0, videos: 0, observations: 0 },
};

// ── DOM helpers ──────────────────────────────────────────────────────────────
const $ = (id) => document.getElementById(id);
const showEl = (id) => $(id).classList.remove('hidden');
const hideEl = (id) => $(id).classList.add('hidden');

// ── Toast ────────────────────────────────────────────────────────────────────
function toast(msg, duration = 3200) {
  const el = $('toast');
  el.textContent = msg;
  el.classList.add('show');
  setTimeout(() => el.classList.remove('show'), duration);
}

// ── Case ID management ────────────────────────────────────────────────────────
function generateCaseId() {
  const ts = Date.now().toString(36).toUpperCase();
  const rand = Math.random().toString(36).slice(2, 6).toUpperCase();
  return `CASE-${ts}-${rand}`;
}

function getCaseId() {
  return $('caseIdInput').value.trim();
}

$('caseIdInput').addEventListener('input', () => {
  state.caseId = getCaseId();
  updateCasePill();
});

$('newCaseBtn').addEventListener('click', () => {
  const id = generateCaseId();
  $('caseIdInput').value = id;
  state.caseId = id;
  updateCasePill();
  toast(`New case created: ${id}`);
});

function updateCasePill() {
  const pill = $('casePill');
  pill.textContent = state.caseId || 'No case selected';
}

// ── Section navigation ────────────────────────────────────────────────────────
const SECTIONS = ['dashboard', 'image', 'audio', 'video', 'timeline', 'chat', 'report'];
const TITLES = {
  dashboard: 'Dashboard',
  image: 'Image Analysis',
  audio: 'Audio Analysis',
  video: 'Video Analysis',
  timeline: 'Evidence Timeline',
  chat: 'AI Evidence Chat',
  report: 'Generate Report',
};

function showSection(name) {
  SECTIONS.forEach((s) => {
    document.getElementById(`section${cap(s)}`).classList.remove('active');
    document.getElementById(`nav${cap(s)}`).classList.remove('active');
  });
  document.getElementById(`section${cap(name)}`).classList.add('active');
  document.getElementById(`nav${cap(name)}`).classList.add('active');
  $('pageTitle').textContent = TITLES[name] || name;

  if (name === 'dashboard') loadDashboard();
  if (name === 'timeline') loadTimeline();
}

function cap(str) {
  return str.charAt(0).toUpperCase() + str.slice(1);
}

// ── Health check ──────────────────────────────────────────────────────────────
async function loadHealth() {
  try {
    const [resp, mResp] = await Promise.all([
      fetch('/api/health'),
      fetch('/api/models/status').catch(() => null),
    ]);
    const data = await resp.json();
    const modelData = mResp && mResp.ok ? await mResp.json() : null;
    const dot = document.querySelector('.status-dot');
    const txt = $('healthText');
    if (data.status === 'ok') {
      dot.className = 'status-dot ok';
      txt.textContent = 'System OK';
    } else {
      dot.className = 'status-dot error';
      txt.textContent = 'System Error';
    }
    renderSystemStatus(data, modelData);
    return data;
  } catch (e) {
    document.querySelector('.status-dot').className = 'status-dot error';
    $('healthText').textContent = 'Offline';
    return null;
  }
}

function renderSystemStatus(data, modelData) {
  const cfg = data.config || {};
  const img = modelData ? modelData.image_models : null;
  const aud = modelData ? modelData.audio_models : null;
  const llm = modelData ? modelData.llm : null;

  const rows = [
    ['Application', data.application || 'CrimeVision AI'],
    ['Version', data.version || '–'],
    ['Cases on disk', data.cases_on_disk ?? '–'],
    ['Max Upload', `${cfg.max_upload_mb} MB`],
    ['Video frame rate', `1 frame / ${cfg.video_frame_interval_sec}s`],
    // Model rows
    ['RT-DETR (vision)', img ? (img.rtdetr ? '✓ Loaded' : '⟳ Heuristic fallback') : cfg.rtdetr_model || '–', img ? (img.rtdetr ? 'ok' : 'pending') : null],
    ['BLIP (captions)',  img ? (img.blip  ? '✓ Loaded' : '⟳ Heuristic fallback') : (cfg.enable_blip ? 'Enabled' : 'Disabled'), img ? (img.blip ? 'ok' : 'pending') : (cfg.enable_blip ? 'ok' : null)],
    ['CLIP (tags)',      img ? (img.clip  ? '✓ Loaded' : '⟳ Heuristic fallback') : (cfg.enable_clip ? 'Enabled' : 'Disabled'), img ? (img.clip ? 'ok' : 'pending') : (cfg.enable_clip ? 'ok' : null)],
    ['Whisper (audio)',  aud ? (aud.whisper ? '✓ Loaded' : '⟳ Heuristic fallback') : cfg.whisper_model || '–', aud ? (aud.whisper ? 'ok' : 'pending') : null],
    ['Groq LLM', llm ? (llm.groq_available ? `✓ ${llm.groq_model}` : (llm.groq_configured ? '⚠ Key set but client failed' : '✗ Not configured')) : (cfg.groq_configured ? `✓ ${cfg.groq_model}` : '✗ Not configured'), llm ? (llm.groq_available ? 'ok' : 'warn') : (cfg.groq_configured ? 'ok' : 'warn')],
  ];

  const html = `<div class="status-list">${rows.map(([k, v, tag]) => `
    <div class="status-row">
      <span class="status-key">${k}</span>
      <span class="status-val">
        ${tag ? `<span class="tag tag--${tag}">${v}</span>` : v}
      </span>
    </div>`).join('')}</div>
    ${ (!llm || !llm.groq_available) ? `
    <div class="callout callout--warning" style="margin-top:12px;font-size:12px">
      <strong>AI Chat running in offline mode.</strong><br/>
      To enable LLM-powered evidence chat, add your free Groq API key:<br/>
      1. Get a key at <strong>console.groq.com/keys</strong><br/>
      2. Open <code>.env</code> in the project folder<br/>
      3. Set <code>GROQ_API_KEY=your_actual_key</code><br/>
      4. Restart the server
    </div>` : '' }`;
  $('systemStatus').innerHTML = html;
}

// ── Dashboard ─────────────────────────────────────────────────────────────────
async function loadDashboard() {
  await loadHealth();
  await loadRecentCases();
  // Update stat cards from timeline if case is selected
  if (state.caseId) {
    try {
      const r = await fetch(`/api/evidence/timeline/${encodeURIComponent(state.caseId)}`);
      const d = await r.json();
      const obs = d.observations || [];
      $('statImages').textContent = obs.filter(o => o.modality === 'image').length;
      $('statAudio').textContent  = obs.filter(o => o.modality === 'audio').length;
      $('statVideos').textContent = obs.filter(o => o.modality === 'video').length;
      $('statObs').textContent    = obs.length;
    } catch (_) { /* ignore */ }
  } else {
    ['statImages','statAudio','statVideos','statObs'].forEach(id => $(id).textContent = '–');
  }
}

async function loadRecentCases() {
  try {
    const r = await fetch('/api/cases');
    const d = await r.json();
    const cases = d.cases || [];
    if (!cases.length) {
      $('recentCases').innerHTML = '<p class="muted-text">No cases found.</p>';
      return;
    }
    $('recentCases').innerHTML = cases.map(c => `
      <div class="status-row" style="cursor:pointer" onclick="selectCase('${c}')">
        <span class="status-key" style="font-family:'JetBrains Mono',monospace;font-size:11px">${c}</span>
        <span class="tag tag--ok">open</span>
      </div>`).join('');
  } catch (_) {
    $('recentCases').innerHTML = '<p class="muted-text">Could not load cases.</p>';
  }
}

function selectCase(caseId) {
  $('caseIdInput').value = caseId;
  state.caseId = caseId;
  updateCasePill();
  toast(`Switched to case: ${caseId}`);
}

// ── Image Upload & Analysis ───────────────────────────────────────────────────
setupDropArea('imageDropArea', 'imageFileInput', handleImageFile);

$('imageFileInput').addEventListener('change', (e) => {
  if (e.target.files[0]) handleImageFile(e.target.files[0]);
});

function handleImageFile(file) {
  state.imageFile = file;
  const reader = new FileReader();
  reader.onload = (e) => {
    $('imagePreview').src = e.target.result;
    showEl('imagePreviewWrap');
  };
  reader.readAsDataURL(file);
  hideEl('imageResult');
}

async function analyseImage() {
  if (!requireCase()) return;
  if (!state.imageFile) { toast('Please select an image first.'); return; }

  const btn = $('imageAnalyseBtn');
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span> Analysing…';

  const form = new FormData();
  form.append('file', state.imageFile);
  form.append('case_id', state.caseId);

  try {
    const r = await fetch('/api/image/analyse', { method: 'POST', body: form });
    const d = await r.json();
    renderResult('imageResult', d, r.ok);
    const oldHypothesisButton = $('imageHypothesesBtn');
    if (oldHypothesisButton) oldHypothesisButton.remove();
    if (r.ok && d.status === 'ok' && d.evidence_id) {
      const hypothesesButton = document.createElement('button');
      hypothesesButton.id = 'imageHypothesesBtn';
      hypothesesButton.className = 'btn btn-secondary mt-2';
      hypothesesButton.textContent = 'Generate tentative hypotheses (optional Groq)';
      hypothesesButton.addEventListener('click', () => generateImageHypotheses(d.evidence_id, hypothesesButton));
      $('imageResult').appendChild(hypothesesButton);
    }
    if (r.ok && d.annotated_image_url) {
      const preview = document.createElement('img');
      preview.src = d.annotated_image_url;
      preview.alt = 'Image with model-produced bounding boxes';
      preview.loading = 'lazy';
      preview.style.cssText = 'display:block;max-width:100%;max-height:520px;object-fit:contain;margin-top:12px;border-radius:8px;';
      $('imageResult').appendChild(preview);
    } else if (r.ok && d.models_used && !d.models_used.rtdetr) {
      const note = document.createElement('p');
      note.className = 'timeline-sub';
      note.textContent = 'Annotated detections are unavailable because RT-DETR did not run. Heuristic candidate regions are not drawn as identified objects.';
      $('imageResult').appendChild(note);
    }
    if (r.ok) state.stats.images++;
  } catch (e) {
    renderResult('imageResult', { error: e.message }, false);
  } finally {
    btn.disabled = false;
    btn.textContent = 'Analyse Image';
  }
}

async function generateImageHypotheses(evidenceId, button) {
  if (!requireCase()) return;
  const confirmed = window.confirm(
    'This optional action sends stored image observation descriptions to your configured Groq service. It does not send the image file or pixels. Results are tentative. Continue?'
  );
  if (!confirmed) return;
  button.disabled = true;
  button.textContent = 'Generating tentative hypotheses…';
  try {
    const response = await fetch('/api/image/hypotheses', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ case_id: state.caseId, source_evidence_id: evidenceId, allow_external: true }),
    });
    const result = await response.json();
    const output = document.createElement('pre');
    output.textContent = JSON.stringify(result, null, 2);
    output.setAttribute('aria-label', 'Tentative image hypotheses');
    button.insertAdjacentElement('afterend', output);
    button.textContent = response.ok ? 'Tentative hypotheses returned' : 'Hypotheses unavailable';
  } catch (error) {
    button.textContent = 'Hypothesis request failed';
    toast(`Image hypothesis request failed: ${error.message}`);
  } finally {
    button.disabled = false;
  }
}

// ── Audio Upload & Transcription ──────────────────────────────────────────────
setupDropArea('audioDropArea', 'audioFileInput', handleAudioFile);

$('audioFileInput').addEventListener('change', (e) => {
  if (e.target.files[0]) handleAudioFile(e.target.files[0]);
});

function handleAudioFile(file) {
  state.audioFile = file;
  $('audioFileInfo').className = 'file-info-bar';
  $('audioFileInfo').innerHTML = `🎙️ <strong>${file.name}</strong> &nbsp;·&nbsp; ${humanSize(file.size)}`;
  $('audioTranscribeBtn').style.display = 'inline-flex';
  hideEl('audioResult');
}

async function transcribeAudio() {
  if (!requireCase()) return;
  if (!state.audioFile) { toast('Please select an audio file.'); return; }

  const btn = $('audioTranscribeBtn');
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span> Transcribing…';

  const form = new FormData();
  form.append('file', state.audioFile);
  form.append('case_id', state.caseId);

  try {
    const r = await fetch('/api/audio/transcribe', { method: 'POST', body: form });
    const d = await r.json();
    renderResult('audioResult', d, r.ok);
    const previousButton = $('audioEventsBtn');
    if (previousButton) previousButton.remove();
    if (r.ok && d.transcription_status === 'available' && d.segments && d.segments.length && d.evidence_id) {
      const eventsButton = document.createElement('button');
      eventsButton.id = 'audioEventsBtn';
      eventsButton.className = 'btn btn-secondary mt-2';
      eventsButton.textContent = 'Extract candidate events (optional Groq)';
      eventsButton.addEventListener('click', () => extractAudioEvents(d.evidence_id, eventsButton));
      $('audioResult').appendChild(eventsButton);
    }
  } catch (e) {
    renderResult('audioResult', { error: e.message }, false);
  } finally {
    btn.disabled = false;
    btn.textContent = 'Transcribe Audio';
  }
}

async function extractAudioEvents(evidenceId, button) {
  if (!requireCase()) return;
  const confirmed = window.confirm(
    'This optional action sends the timestamped transcript text for this audio evidence to your configured Groq service. It does not send the audio file. Continue?'
  );
  if (!confirmed) return;
  button.disabled = true;
  button.textContent = 'Extracting candidate events…';
  try {
    const response = await fetch('/api/audio/events', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ case_id: state.caseId, source_evidence_id: evidenceId, allow_external: true }),
    });
    const result = await response.json();
    const output = document.createElement('pre');
    output.textContent = JSON.stringify(result, null, 2);
    output.setAttribute('aria-label', 'Candidate audio event results');
    button.insertAdjacentElement('afterend', output);
    button.textContent = 'Candidate events requested';
  } catch (error) {
    button.textContent = 'Event extraction failed';
    toast(`Event extraction failed: ${error.message}`);
  } finally {
    button.disabled = false;
  }
}

// ── Video Upload & Analysis ───────────────────────────────────────────────────
setupDropArea('videoDropArea', 'videoFileInput', handleVideoFile);

$('videoFileInput').addEventListener('change', (e) => {
  if (e.target.files[0]) handleVideoFile(e.target.files[0]);
});

function handleVideoFile(file) {
  state.videoFile = file;
  $('videoFileInfo').className = 'file-info-bar';
  $('videoFileInfo').innerHTML = `🎬 <strong>${file.name}</strong> &nbsp;·&nbsp; ${humanSize(file.size)}`;
  $('videoAnalyseBtn').style.display = 'inline-flex';
  hideEl('videoResult');
}

async function analyseVideo() {
  if (!requireCase()) return;
  if (!state.videoFile) { toast('Please select a video file.'); return; }

  const btn = $('videoAnalyseBtn');
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span> Processing…';

  const form = new FormData();
  form.append('file', state.videoFile);
  form.append('case_id', state.caseId);

  try {
    const r = await fetch('/api/video/analyse', { method: 'POST', body: form });
    const d = await r.json();
    renderResult('videoResult', d, r.ok);
    const oldClassifyButton = $('videoClassifyBtn');
    if (oldClassifyButton) oldClassifyButton.remove();
    if (r.ok && d.status === 'ok' && d.evidence_id) {
      const classifyButton = document.createElement('button');
      classifyButton.id = 'videoClassifyBtn';
      classifyButton.className = 'btn btn-secondary mt-2';
      classifyButton.textContent = 'Classify candidate events (optional Groq)';
      classifyButton.addEventListener('click', () => classifyVideoEvents(d.evidence_id, classifyButton));
      $('videoResult').appendChild(classifyButton);
    }
    if (r.ok && Array.isArray(d.keyframes) && d.keyframes.length) {
      const gallery = document.createElement('div');
      gallery.style.cssText = 'display:flex;gap:12px;overflow-x:auto;margin-top:16px;padding:8px 0;';
      for (const frame of d.keyframes) {
        const card = document.createElement('figure');
        card.style.cssText = 'margin:0;min-width:190px;max-width:260px;';
        const preview = document.createElement('img');
        preview.src = `/api/video/keyframes/${encodeURIComponent(d.evidence_id)}/${encodeURIComponent(frame.keyframe_file)}`;
        preview.alt = `Sampled keyframe at ${frame.timestamp_hms || 'unknown time'}`;
        preview.loading = 'lazy';
        preview.style.cssText = 'display:block;width:100%;height:auto;border-radius:8px;';
        const caption = document.createElement('figcaption');
        caption.className = 'timeline-sub';
        caption.textContent = `${frame.timestamp_hms || 'Unknown time'} · ${frame.detections_count || 0} semantic detections`;
        card.append(preview, caption);
        gallery.appendChild(card);
      }
      $('videoResult').appendChild(gallery);
    }
  } catch (e) {
    renderResult('videoResult', { error: e.message }, false);
  } finally {
    btn.disabled = false;
    btn.textContent = 'Analyse Video';
  }
}

async function classifyVideoEvents(evidenceId, button) {
  if (!requireCase()) return;
  const confirmed = window.confirm(
    'This optional action sends analyzed video observation descriptions and frame references to your configured Groq service. It does not send the video file. Results are tentative. Continue?'
  );
  if (!confirmed) return;
  button.disabled = true;
  button.textContent = 'Classifying candidate events…';
  try {
    const response = await fetch('/api/video/classify', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ case_id: state.caseId, source_evidence_id: evidenceId, allow_external: true }),
    });
    const result = await response.json();
    const output = document.createElement('pre');
    output.textContent = JSON.stringify(result, null, 2);
    output.setAttribute('aria-label', 'Tentative video event classifications');
    button.insertAdjacentElement('afterend', output);
    button.textContent = response.ok ? 'Tentative classifications returned' : 'Classification unavailable';
  } catch (error) {
    button.textContent = 'Classification failed';
    toast(`Video classification failed: ${error.message}`);
  } finally {
    button.disabled = false;
  }
}

// ── Timeline ──────────────────────────────────────────────────────────────────
async function loadTimeline() {
  if (!state.caseId) {
    $('timelineContainer').innerHTML = '<p class="muted-text">Enter a Case ID in the sidebar first.</p>';
    return;
  }
  $('timelineContainer').innerHTML = '<div class="skeleton-line"></div><div class="skeleton-line short"></div><div class="skeleton-line"></div>';
  try {
    const r = await fetch(`/api/evidence/timeline/${encodeURIComponent(state.caseId)}`);
    const d = await r.json();
    renderTimelineView(d);
  } catch (e) {
    $('timelineContainer').innerHTML = `<div class="callout callout--error">Failed to load timeline: ${escHtml(e.message)}</div>`;
  }
}

function renderTimelineView(data) {
  const container = $('timelineContainer');
  const obs = data.observations || [];
  if (!obs.length) {
    container.innerHTML = '<p class="muted-text">No observations found for this case. Analyse some evidence first.</p>';
    return;
  }

  // 1. Render interactive multi-track SVG timeline if timeline.js is loaded
  if (typeof window.renderInteractiveTimeline === 'function') {
    window.renderInteractiveTimeline(data);
  } else {
    container.innerHTML = '';
  }

  // 2. Render detailed chronological observation cards below
  const listWrap = document.createElement('div');
  listWrap.id = 'timelineCardsSection';
  listWrap.style.cssText = 'margin-top:24px;border-top:1px solid var(--border);padding-top:18px;';

  const items = obs.map((o) => {
    const mod = o.modality || 'fusion';
    const ts = o.timestamp_start !== null && o.timestamp_start !== undefined
      ? secsToHms(o.timestamp_start)
      : 'unknown';
    const objList = (o.detected_objects || []).map(obj => `<span class="tag tag--ok">${escHtml(obj.label || '')}</span>`).join(' ');
    const shaTag = o.metadata && o.metadata.sha256 ? `<span class="timeline-sub" style="font-family:'JetBrains Mono',monospace;font-size:10px;margin-top:4px;display:block;color:var(--text-muted)">SHA-256: ${escHtml(o.metadata.sha256.slice(0, 16))}…</span>` : '';
    return `
    <div class="timeline-item">
      <div class="timeline-dot timeline-dot--${mod}"></div>
      <div class="timeline-card">
        <div class="timeline-card-header">
          <span class="timeline-modality modality--${mod}">${mod}</span>
          <span class="timeline-ts">@ ${ts}</span>
        </div>
        <div class="timeline-desc">${escHtml(o.description || '')}</div>
        ${objList ? `<div class="timeline-sub" style="margin-top:6px">${objList}</div>` : ''}
        ${o.uncertainty ? `<div class="timeline-sub">⚠ ${escHtml(o.uncertainty)}</div>` : ''}
        ${shaTag}
      </div>
    </div>`;
  }).join('');

  listWrap.innerHTML = `
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;">
      <h3 style="font-size:13px;font-weight:600;color:var(--text-secondary);text-transform:uppercase;letter-spacing:0.05em">Chronological Event Log</h3>
      <span style="font-size:12px;color:var(--text-muted)">${obs.length} event${obs.length !== 1 ? 's' : ''}</span>
    </div>
    <div class="timeline-list">${items}</div>`;
  container.appendChild(listWrap);
}


// ── AI Chat ───────────────────────────────────────────────────────────────────
$('chatInput').addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendChat(); }
});

async function sendChat() {
  if (!requireCase()) return;
  const input = $('chatInput');
  const question = input.value.trim();
  if (!question) return;

  const allowExternal = window.confirm(
    'For this message, allow the configured Groq service to receive your question and a small set of matching case observations? The audio/video files themselves are not sent. Choose Cancel to keep the lookup local.'
  );

  appendChatBubble(question, 'user');
  input.value = '';

  const btn = $('chatSendBtn');
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span>';

  try {
    const r = await fetch('/api/chat/ask', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ case_id: state.caseId, question, allow_external: allowExternal }),
    });
    const d = await r.json();
    if (d.warning) {
      const offlineMsg = d.warning.includes('offline')
        ? `⚠ ${d.warning} — To enable LLM chat, add GROQ_API_KEY to .env and restart.`
        : `⚠ ${d.warning}`;
      appendChatBubble(offlineMsg, 'system');
    }
    appendChatBubble(d.answer || 'No response.', 'ai');
    if (d.citations && d.citations.length) {
      const citedEvents = d.citations.map(item => item.event_id).filter(Boolean).join(', ');
      if (citedEvents) appendChatBubble(`Source event IDs: ${citedEvents}`, 'system');
    }
    for (const hypothesis of (d.alternative_hypotheses || [])) {
      appendChatBubble(`Tentative alternative: ${hypothesis.text}\nUncertainty: ${hypothesis.uncertainty}`, 'system');
    }
  } catch (e) {
    appendChatBubble(`Error: ${e.message}`, 'system');
  } finally {
    btn.disabled = false;
    btn.textContent = 'Send';
  }
}

function appendChatBubble(text, type) {
  const msgs = $('chatMessages');
  const div = document.createElement('div');
  div.className = `chat-bubble chat-bubble--${type}`;
  div.textContent = text;
  msgs.appendChild(div);
  msgs.scrollTop = msgs.scrollHeight;
}

// ── Report ─────────────────────────────────────────────────────────────────────
async function generateReport() {
  if (!requireCase()) return;

  const btn = $('generateReportBtn');
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span> Generating…';
  $('reportResult').innerHTML = '';

  try {
    const r = await fetch('/api/report/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ case_id: state.caseId }),
    });
    const d = await r.json();

    if (d.status === 'ok' || d.output_path) {
      $('reportResult').innerHTML = `
        <div class="callout callout--success">
          Report generated!
          <a class="btn-download" href="/api/report/download/${encodeURIComponent(state.caseId)}" style="margin-top:8px;display:inline-block">⬇ Download PDF</a>
        </div>`;
    } else {
      $('reportResult').innerHTML = `<div class="callout callout--warning">${escHtml(d.message || 'Report generation pending Phase 7 implementation.')}</div>`;
    }
  } catch (e) {
    $('reportResult').innerHTML = `<div class="callout callout--error">Error: ${escHtml(e.message)}</div>`;
  } finally {
    btn.disabled = false;
    btn.textContent = 'Generate Report';
  }
}

// ── Helpers ───────────────────────────────────────────────────────────────────
function requireCase() {
  const id = getCaseId();
  if (!id) {
    toast('⚠ Please enter a Case ID in the sidebar first.');
    $('caseIdInput').focus();
    return false;
  }
  state.caseId = id;
  updateCasePill();
  return true;
}

function renderResult(containerId, data, isOk) {
  const el = $(containerId);
  el.classList.remove('hidden');
  const transcriptionUnavailable = data.transcription_status === 'unavailable';
  const statusClass = transcriptionUnavailable ? 'callout--warning' : (isOk ? 'callout--success' : 'callout--error');
  const statusText = transcriptionUnavailable
    ? 'Audio decoded; speech transcription is unavailable.'
    : (isOk ? '✓ Request completed' : '✗ ' + escHtml(data.error || 'Error'));
  const preview = JSON.stringify(data, null, 2);
  el.innerHTML = `
    <div class="callout ${statusClass}" style="margin-bottom:12px">
      ${statusText}
    </div>
    <h3>Raw Response</h3>
    <pre>${escHtml(preview)}</pre>`;
}

function setupDropArea(areaId, inputId, handler) {
  const area = $(areaId);
  area.addEventListener('click', () => $(inputId).click());
  area.addEventListener('dragover', (e) => { e.preventDefault(); area.classList.add('drag-over'); });
  area.addEventListener('dragleave', () => area.classList.remove('drag-over'));
  area.addEventListener('drop', (e) => {
    e.preventDefault();
    area.classList.remove('drag-over');
    if (e.dataTransfer.files[0]) handler(e.dataTransfer.files[0]);
  });
}

function humanSize(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1048576).toFixed(1)} MB`;
}

function secsToHms(s) {
  if (s == null) return 'unknown';
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const sec = (s % 60).toFixed(1);
  return `${String(h).padStart(2,'0')}:${String(m).padStart(2,'0')}:${String(sec).padStart(4,'0')}`;
}

function escHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

// ── Init ──────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  loadHealth();
});
