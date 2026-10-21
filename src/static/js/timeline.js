/* =============================================================================
   timeline.js – CrimeVision AI Interactive Evidence Timeline
   Renders an SVG-based chronological forensic timeline with modality tracks,
   hover cards, and zoom support. No third-party dependencies.
   ============================================================================= */

'use strict';

/* ── Constants ─────────────────────────────────────────────────────────────── */
const TL = {
  MODALITIES:   ['image', 'audio', 'video', 'fusion'],
  COLORS: {
    image:   { dot: '#6ee7f7', track: 'rgba(110,231,247,0.15)', label: '#6ee7f7' },
    audio:   { dot: '#a78bfa', track: 'rgba(167,139,250,0.15)', label: '#a78bfa' },
    video:   { dot: '#34d399', track: 'rgba(52,211,153,0.15)',  label: '#34d399' },
    fusion:  { dot: '#f59e0b', track: 'rgba(245,158,11,0.15)', label: '#f59e0b' },
    unknown: { dot: '#94a3b8', track: 'rgba(148,163,184,0.15)', label: '#94a3b8' },
  },
  TRACK_H:  64,   // height per modality row  (px)
  PAD_TOP:  48,   // header height
  PAD_SIDE: 80,   // left label column width
  PAD_RIGHT:24,
  DOT_R:    7,    // dot radius
  HOVER_W:  260,  // tooltip card width
  ANIM_MS:  320,
};

/* ── State ─────────────────────────────────────────────────────────────────── */
let _obs       = [];   // current observations
let _zoom      = 1.0;  // horizontal zoom multiplier
let _panOffset = 0;    // horizontal pan offset in virtual-seconds
let _svgEl     = null;
let _tooltip   = null;

/* ── Main entry – called from dashboard.js ─────────────────────────────────── */
function renderTimeline(data) {
  const container = document.getElementById('timelineContainer');
  if (!container) return;

  _obs = (data.observations || []).slice().sort(
    (a, b) => (a.timestamp_start ?? 0) - (b.timestamp_start ?? 0)
  );

  if (!_obs.length) {
    container.innerHTML = '<p class="muted-text">No observations found for this case. Analyse some evidence first.</p>';
    return;
  }

  /* Header info bar */
  container.innerHTML = '';
  _buildInfoBar(container, data);

  /* Controls */
  _buildControls(container);

  /* SVG canvas */
  const svgWrap = document.createElement('div');
  svgWrap.id = 'tlSvgWrap';
  svgWrap.style.cssText = 'position:relative;overflow:hidden;border-radius:10px;background:var(--bg-card,#0f172a);margin-top:12px;';
  container.appendChild(svgWrap);

  /* Tooltip overlay */
  _tooltip = document.createElement('div');
  _tooltip.id = 'tlTooltip';
  _tooltip.style.cssText = `
    position:absolute;z-index:99;width:${TL.HOVER_W}px;
    background:var(--bg-elevated,#1e293b);
    border:1px solid rgba(255,255,255,.1);
    border-radius:10px;padding:14px;
    pointer-events:none;opacity:0;
    transition:opacity .18s ease;
    box-shadow:0 8px 32px rgba(0,0,0,.5);
    font-size:12px;color:var(--text-primary,#e2e8f0);
    max-height:220px;overflow:hidden;
  `;
  svgWrap.appendChild(_tooltip);

  _svgEl = null;
  _zoom  = 1.0;
  _panOffset = 0;

  _drawTimeline(svgWrap);

  /* Zoom shortcuts */
  svgWrap.addEventListener('wheel', (e) => {
    e.preventDefault();
    const delta = e.deltaY < 0 ? 0.15 : -0.15;
    _zoom = Math.max(0.5, Math.min(8, _zoom + delta));
    _drawTimeline(svgWrap);
  }, { passive: false });
}

/* ── Info bar ─────────────────────────────────────────────────────────────── */
function _buildInfoBar(container, data) {
  const counts = {};
  _obs.forEach(o => { const m = o.modality || 'unknown'; counts[m] = (counts[m] || 0) + 1; });
  const chips = Object.entries(counts).map(([m, n]) => {
    const c = TL.COLORS[m] || TL.COLORS.unknown;
    return `<span style="display:inline-flex;align-items:center;gap:5px;
      background:${c.track};border:1px solid ${c.dot};
      border-radius:20px;padding:3px 10px;font-size:11px;color:${c.label};font-weight:600">
      <span style="width:7px;height:7px;border-radius:50%;background:${c.dot}"></span>
      ${n} ${m}
    </span>`;
  }).join('');

  const bar = document.createElement('div');
  bar.style.cssText = 'display:flex;align-items:center;flex-wrap:wrap;gap:8px;margin-bottom:4px;';
  bar.innerHTML = `
    <span style="color:var(--text-muted,#94a3b8);font-size:12px">
      📋 Case&nbsp;<strong style="color:var(--text-primary,#e2e8f0)">${_escHtml(data.case_id || '–')}</strong>
      &nbsp;·&nbsp;${_obs.length} observation${_obs.length !== 1 ? 's' : ''}
      <br><span style="display:inline-block;margin-top:5px;color:var(--text-muted,#94a3b8)">${_escHtml(data.time_axis_note || 'Timestamps are relative to their source media unless marked otherwise.')}</span>
    </span>
    <span style="flex:1"></span>
    ${chips}
  `;
  container.appendChild(bar);
}

/* ── Controls row ─────────────────────────────────────────────────────────── */
function _buildControls(container) {
  const row = document.createElement('div');
  row.style.cssText = 'display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-top:6px;';

  const zoomIn  = _ctrlBtn('＋ Zoom In',  () => { _zoom = Math.min(8,   _zoom + 0.4); _drawTimeline(document.getElementById('tlSvgWrap')); });
  const zoomOut = _ctrlBtn('－ Zoom Out', () => { _zoom = Math.max(0.5, _zoom - 0.4); _drawTimeline(document.getElementById('tlSvgWrap')); });
  const reset   = _ctrlBtn('↺ Reset',    () => { _zoom = 1; _panOffset = 0; _drawTimeline(document.getElementById('tlSvgWrap')); });

  const panL = _ctrlBtn('◀ Pan',  () => { _panOffset = Math.max(0, _panOffset - _virtualDuration() * 0.1); _drawTimeline(document.getElementById('tlSvgWrap')); });
  const panR = _ctrlBtn('Pan ▶',  () => { _panOffset += _virtualDuration() * 0.1; _drawTimeline(document.getElementById('tlSvgWrap')); });

  const label = document.createElement('span');
  label.id = 'tlZoomLabel';
  label.style.cssText = 'font-size:11px;color:var(--text-muted,#94a3b8);margin-left:4px;';
  label.textContent = 'Scroll to zoom · Drag to pan';

  row.append(zoomIn, zoomOut, reset, panL, panR, label);
  container.appendChild(row);
}

function _ctrlBtn(text, onClick) {
  const b = document.createElement('button');
  b.textContent = text;
  b.style.cssText = `
    background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.1);
    color:var(--text-secondary,#94a3b8);border-radius:6px;
    padding:4px 12px;font-size:11px;cursor:pointer;
    transition:background .15s,color .15s;
  `;
  b.onmouseenter = () => { b.style.background = 'rgba(255,255,255,.12)'; b.style.color = '#fff'; };
  b.onmouseleave = () => { b.style.background = 'rgba(255,255,255,.06)'; b.style.color = 'var(--text-secondary,#94a3b8)'; };
  b.addEventListener('click', onClick);
  return b;
}

/* ── Core SVG draw ─────────────────────────────────────────────────────────── */
function _drawTimeline(wrap) {
  /* Remove old SVG */
  if (_svgEl && _svgEl.parentNode === wrap) wrap.removeChild(_svgEl);

  const containerW = wrap.clientWidth || 760;
  const drawW      = containerW;
  const modalities = _activeMods();
  const svgH       = TL.PAD_TOP + modalities.length * TL.TRACK_H + 24;

  const ns = 'http://www.w3.org/2000/svg';
  const svg = document.createElementNS(ns, 'svg');
  svg.setAttribute('width',  drawW);
  svg.setAttribute('height', svgH);
  svg.style.cssText = 'display:block;cursor:default;';

  /* Time range */
  const { minT, maxT } = _timeRange();
  const duration = Math.max(maxT - minT, 1);
  const innerW   = drawW - TL.PAD_SIDE - TL.PAD_RIGHT;

  /* Helper: seconds → x */
  function secToX(s) {
    const frac  = ((s - minT) - _panOffset) / (duration / _zoom);
    return TL.PAD_SIDE + frac * innerW;
  }

  /* ── Background tracks ── */
  modalities.forEach((mod, i) => {
    const y = TL.PAD_TOP + i * TL.TRACK_H;
    const c = TL.COLORS[mod] || TL.COLORS.unknown;
    const rect = document.createElementNS(ns, 'rect');
    rect.setAttribute('x', TL.PAD_SIDE);
    rect.setAttribute('y', y);
    rect.setAttribute('width', innerW);
    rect.setAttribute('height', TL.TRACK_H);
    rect.setAttribute('fill', c.track);
    svg.appendChild(rect);

    /* Row separator */
    const line = document.createElementNS(ns, 'line');
    line.setAttribute('x1', 0); line.setAttribute('x2', drawW);
    line.setAttribute('y1', y + TL.TRACK_H); line.setAttribute('y2', y + TL.TRACK_H);
    line.setAttribute('stroke', 'rgba(255,255,255,.05)');
    svg.appendChild(line);

    /* Label */
    const txt = document.createElementNS(ns, 'text');
    txt.setAttribute('x', TL.PAD_SIDE - 8);
    txt.setAttribute('y', y + TL.TRACK_H / 2 + 5);
    txt.setAttribute('text-anchor', 'end');
    txt.setAttribute('font-size', '11');
    txt.setAttribute('font-family', 'Inter,system-ui,sans-serif');
    txt.setAttribute('fill', c.label);
    txt.setAttribute('font-weight', '600');
    txt.textContent = mod;
    svg.appendChild(txt);
  });

  /* ── Time axis (ruler) ── */
  _drawRuler(svg, ns, minT, duration, innerW, svgH);

  /* ── Observation dots ── */
  _obs.forEach((o, idx) => {
    const mod  = o.modality || 'unknown';
    const row  = modalities.indexOf(mod);
    if (row < 0) return;

    const ts   = o.timestamp_start ?? 0;
    const x    = secToX(ts);
    if (x < TL.PAD_SIDE - TL.DOT_R || x > drawW + TL.DOT_R) return; // clipped

    const y    = TL.PAD_TOP + row * TL.TRACK_H + TL.TRACK_H / 2;
    const c    = TL.COLORS[mod] || TL.COLORS.unknown;

    /* Glow ring */
    const ring = document.createElementNS(ns, 'circle');
    ring.setAttribute('cx', x); ring.setAttribute('cy', y);
    ring.setAttribute('r', TL.DOT_R + 4);
    ring.setAttribute('fill', 'none');
    ring.setAttribute('stroke', c.dot);
    ring.setAttribute('stroke-opacity', '0.25');
    ring.setAttribute('stroke-width', '2');
    svg.appendChild(ring);

    /* Main dot */
    const dot = document.createElementNS(ns, 'circle');
    dot.setAttribute('cx', x); dot.setAttribute('cy', y);
    dot.setAttribute('r', TL.DOT_R);
    dot.setAttribute('fill', c.dot);
    dot.setAttribute('style', 'cursor:pointer;transition:r .15s');
    dot.dataset.idx = idx;

    /* Hover */
    dot.addEventListener('mouseenter', (e) => {
      dot.setAttribute('r', TL.DOT_R + 3);
      ring.setAttribute('stroke-opacity', '0.6');
      _showTooltip(e, o, x, y, wrap);
    });
    dot.addEventListener('mousemove', (e) => _moveTooltip(e, wrap));
    dot.addEventListener('mouseleave', () => {
      dot.setAttribute('r', TL.DOT_R);
      ring.setAttribute('stroke-opacity', '0.25');
      _hideTooltip();
    });

    svg.appendChild(dot);

    /* Duration bar (if timestamp_end available) */
    if (o.timestamp_end != null && o.timestamp_end > ts) {
      const x2   = secToX(o.timestamp_end);
      const barW = Math.max(4, x2 - x);
      const bar  = document.createElementNS(ns, 'rect');
      bar.setAttribute('x', x);
      bar.setAttribute('y', y - 3);
      bar.setAttribute('width', barW);
      bar.setAttribute('height', 6);
      bar.setAttribute('rx', 3);
      bar.setAttribute('fill', c.dot);
      bar.setAttribute('fill-opacity', '0.35');
      svg.insertBefore(bar, dot); // behind dot
    }
  });

  wrap.insertBefore(svg, wrap.firstChild);
  _svgEl = svg;
}

/* ── Ruler ─────────────────────────────────────────────────────────────────── */
function _drawRuler(svg, ns, minT, duration, innerW, svgH) {
  const modalities = _activeMods();
  /* Axis line */
  const axLine = document.createElementNS(ns, 'line');
  axLine.setAttribute('x1', TL.PAD_SIDE); axLine.setAttribute('x2', TL.PAD_SIDE + innerW);
  axLine.setAttribute('y1', TL.PAD_TOP - 4); axLine.setAttribute('y2', TL.PAD_TOP - 4);
  axLine.setAttribute('stroke', 'rgba(255,255,255,.15)');
  svg.appendChild(axLine);

  /* Ticks */
  const tickCount = Math.min(10, Math.max(4, Math.floor(innerW / 80)));
  const step      = (duration / _zoom) / tickCount;

  for (let i = 0; i <= tickCount; i++) {
    const t  = minT + _panOffset + step * i;
    const x  = TL.PAD_SIDE + (i / tickCount) * innerW;
    const label = _formatTime(t);

    const tick = document.createElementNS(ns, 'line');
    tick.setAttribute('x1', x); tick.setAttribute('x2', x);
    tick.setAttribute('y1', TL.PAD_TOP - 10); tick.setAttribute('y2', TL.PAD_TOP - 4);
    tick.setAttribute('stroke', 'rgba(255,255,255,.2)');
    svg.appendChild(tick);

    const gridLine = document.createElementNS(ns, 'line');
    gridLine.setAttribute('x1', x); gridLine.setAttribute('x2', x);
    gridLine.setAttribute('y1', TL.PAD_TOP);
    gridLine.setAttribute('y2', TL.PAD_TOP + modalities.length * TL.TRACK_H);
    gridLine.setAttribute('stroke', 'rgba(255,255,255,.04)');
    svg.appendChild(gridLine);

    const txt = document.createElementNS(ns, 'text');
    txt.setAttribute('x', x);
    txt.setAttribute('y', TL.PAD_TOP - 14);
    txt.setAttribute('text-anchor', 'middle');
    txt.setAttribute('font-size', '10');
    txt.setAttribute('font-family', 'JetBrains Mono,monospace');
    txt.setAttribute('fill', 'rgba(255,255,255,.4)');
    txt.textContent = label;
    svg.appendChild(txt);
  }
}

/* ── Tooltip ─────────────────────────────────────────────────────────────── */
function _showTooltip(e, obs, dotX, dotY, wrap) {
  if (!_tooltip) return;
  const c    = TL.COLORS[obs.modality] || TL.COLORS.unknown;
  const ts   = obs.timestamp_start != null ? _formatTime(obs.timestamp_start) : 'unknown';
  const objs = (obs.detected_objects || []).slice(0, 4).map(o => o.label).join(', ') || '–';
  const prov = obs.inference_engine ? `<div style="margin-top:6px;color:#64748b;font-size:10px">Engine: ${_escHtml(obs.inference_engine)}</div>` : '';
  const hash = obs.sha256 ? `<div style="color:#64748b;font-size:10px;word-break:break-all;margin-top:4px" title="SHA-256">🔒 ${obs.sha256.slice(0,16)}…</div>` : '';

  _tooltip.innerHTML = `
    <div style="display:flex;align-items:center;gap:7px;margin-bottom:8px">
      <span style="width:9px;height:9px;border-radius:50%;background:${c.dot};flex-shrink:0"></span>
      <strong style="color:${c.label};font-size:12px;text-transform:uppercase;letter-spacing:.04em">${_escHtml(obs.modality || 'unknown')}</strong>
      <span style="margin-left:auto;color:rgba(255,255,255,.4);font-size:10px;font-family:monospace">@ ${ts}</span>
    </div>
    <div style="color:rgba(255,255,255,.8);line-height:1.5;font-size:11px;margin-bottom:6px">
      ${_escHtml((obs.description || '').slice(0, 140))}</div>
    <div style="color:rgba(255,255,255,.4);font-size:10px">Objects: ${_escHtml(objs)}</div>
    ${obs.uncertainty ? `<div style="color:#f59e0b;font-size:10px;margin-top:4px">⚠ ${_escHtml(obs.uncertainty)}</div>` : ''}
    ${prov}${hash}
  `;
  _tooltip.style.opacity = '1';
  _moveTooltip(e, wrap);
}

function _moveTooltip(e, wrap) {
  if (!_tooltip) return;
  const rect  = wrap.getBoundingClientRect();
  let lx      = e.clientX - rect.left + 16;
  let ly      = e.clientY - rect.top  - 20;
  if (lx + TL.HOVER_W > wrap.clientWidth)  lx -= TL.HOVER_W + 32;
  if (ly < 0) ly = 4;
  _tooltip.style.left = `${lx}px`;
  _tooltip.style.top  = `${ly}px`;
}

function _hideTooltip() {
  if (_tooltip) _tooltip.style.opacity = '0';
}

/* ── Helpers ──────────────────────────────────────────────────────────────── */
function _activeMods() {
  const seen = new Set(_obs.map(o => o.modality || 'unknown'));
  return TL.MODALITIES.concat(['unknown']).filter(m => seen.has(m));
}

function _timeRange() {
  const times = _obs.map(o => o.timestamp_start ?? 0);
  const ends  = _obs.map(o => o.timestamp_end  ?? o.timestamp_start ?? 0);
  return { minT: Math.min(...times, 0), maxT: Math.max(...times, ...ends, 1) };
}

function _virtualDuration() {
  const { minT, maxT } = _timeRange();
  return Math.max(maxT - minT, 1);
}

function _formatTime(s) {
  if (s == null) return '?';
  if (s < 60)   return `${s.toFixed(1)}s`;
  if (s < 3600) return `${Math.floor(s/60)}m${String(Math.floor(s%60)).padStart(2,'0')}s`;
  return `${Math.floor(s/3600)}h${String(Math.floor((s%3600)/60)).padStart(2,'0')}m`;
}

function _escHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;')
    .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

window.renderInteractiveTimeline = renderTimeline;
