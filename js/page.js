/* Do by-elections make Parliament listen? UK by-elections since 1909 on a plain MapLibre base map (OpenFreeMap Positron).
 * Towns named in the seat are coloured by the change in Commons "in <town>" mentions in the year after polling against the
 * reference year (24 to 13 months before), relative to five matched towns; or by whether the seat changed hands, or the cause.
 * Dr Tristan Hotham, Independent researcher, 2026. MIT licence. */
(function () {
  'use strict';
  const qs = new URLSearchParams(location.search);
  const STYLE = 'https://tiles.openfreemap.org/styles/positron';
  const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const norm = s => String(s).normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
  const small = matchMedia('(max-width:800px)').matches;
  const fmt = n => n == null ? 'n/a' : Number(n).toLocaleString('en-GB');
  const DIV = ['#2F6A9E', '#8FB0CF', '#C9C2B4', '#E3A58F', '#B4442E'];
  const CAUSE = { death: '#6E4E8E', resignation: '#C98A2B', scandal: '#B4442E', 'same MP': '#7A8A6A' };
  const CAUSE_LAB = { death: 'death', resignation: 'resignation or appointment', scandal: 'scandal or void election', 'same MP': 'same member re-elected' };
  const MON = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
  let map = null, D = null, mode = qs.get('mode') || 'x', yMax = 2026, timer = null;
  document.getElementById('theme').addEventListener('click', () => { const r = document.documentElement, d = r.dataset.theme ? r.dataset.theme === 'dark' : matchMedia('(prefers-color-scheme: dark)').matches; r.dataset.theme = d ? 'light' : 'dark'; });
  const ct = document.getElementById('cartouche'); const fold = f => ct.classList.toggle('folded', f);
  if (small) fold(true);
  document.getElementById('ctToggle').addEventListener('click', () => fold(!ct.classList.contains('folded')));
  document.getElementById('ctFold').addEventListener('click', () => fold(true));

  function colorExpr() {
    if (mode === 'ch') return ['case', ['==', ['get', 'ch'], 1], '#B4442E', '#8E8576'];
    if (mode === 'cg') return ['match', ['get', 'cg'], 'death', CAUSE.death, 'resignation', CAUSE.resignation, 'scandal', CAUSE.scandal, CAUSE['same MP']];
    return ['interpolate', ['linear'], ['get', 'lx'], -3, DIV[0], -1.5, DIV[1], 0, DIV[2], 1.5, DIV[3], 3, DIV[4]];
  }
  function key() {
    const t = document.getElementById('keyTitle'), b = document.getElementById('keyBar'), e = document.getElementById('keyEnds');
    if (mode === 'ch') { t.textContent = 'Did the seat change hands?'; b.style.background = 'linear-gradient(90deg,#8E8576 50%,#B4442E 50%)'; e.innerHTML = '<span>held</span><span>changed hands</span>'; }
    else if (mode === 'cg') { t.textContent = 'Cause of the by-election'; b.style.background = `linear-gradient(90deg,${CAUSE.death} 25%,${CAUSE.resignation} 25% 50%,${CAUSE.scandal} 50% 75%,${CAUSE['same MP']} 75%)`; e.innerHTML = '<span>death</span><span>resignation</span><span>scandal</span><span>same MP</span>'; }
    else { t.textContent = 'Mentions, year after vs reference year'; b.style.background = `linear-gradient(90deg,${DIV.join(',')})`; e.innerHTML = '<span>1/8</span><span>no change</span><span>8x</span>'; }
    document.getElementById('keyX').style.display = mode === 'x' ? '' : 'none';
    document.querySelectorAll('.chip[data-m]').forEach(x => x.setAttribute('aria-pressed', x.dataset.m === mode));
  }
  function refresh() {
    map.setPaintProperty('pts', 'circle-color', colorExpr());
    map.setPaintProperty('xpts', 'circle-color', mode === 'x' ? '#B9B4AA' : colorExpr());
    map.setPaintProperty('xpts', 'circle-opacity', mode === 'x' ? 0.85 : 0.55);
    key();
  }
  function setYear(y) {
    yMax = y; const f = ['<=', ['get', 'y'], y];
    map.setFilter('pts', ['all', ['==', ['get', 'k'], 1], f]); map.setFilter('xpts', ['all', ['==', ['get', 'k'], 0], f]); map.setFilter('upts', ['all', ['==', ['get', 'k'], 2], f]);
    map.setFilter('lbl', ['all', ['<', ['get', 'k'], 2], f]);
    document.getElementById('yr').value = y; document.getElementById('yrLab').textContent = `1909 to ${y}`;
  }
  function spark(p) {
    if (!p.sp) return '';
    const w = 270, h = 54, n = p.sp.length, mx = Math.max(1, ...p.sp), bw = w / n;
    let s = `<svg class="spark" width="${w}" height="${h + 14}" viewBox="0 0 ${w} ${h + 14}" role="img" aria-label="Quarterly Commons mentions of ${esc(p.n)}, two years before to three years after polling">`;
    p.sp.forEach((v, i) => { const k = p.s0 + 3 * i; const bh = Math.max(v ? 2 : 0, h * v / mx);
      s += `<rect x="${(i * bw + 1).toFixed(1)}" y="${(h - bh).toFixed(1)}" width="${(bw - 2).toFixed(1)}" height="${bh.toFixed(1)}" fill="${k >= 0 && k <= 12 ? '#B4442E' : k > 12 ? '#D8B9A8' : '#9C9384'}"><title>${v}</title></rect>`; });
    const x0 = (-p.s0 / 3) * bw;
    s += `<line x1="${x0}" x2="${x0}" y1="0" y2="${h}" stroke="#2B2119" stroke-dasharray="3 2"/><text x="${x0 + 3}" y="${h + 12}" font-size="10" fill="#6E604E">poll</text><text x="1" y="${h + 12}" font-size="10" fill="#6E604E">${p.s0 / 12 | 0} yr</text><text x="${w}" y="${h + 12}" font-size="10" text-anchor="end" fill="#6E604E">+3 yr</text></svg>`;
    return s;
  }
  function popup(b, ll) {
    const [yy, mm] = b.d.split('-');
    let h = `<b class="t">${esc(b.s)}</b><div class="nt">by-election, ${MON[+mm - 1]} ${yy}</div><table>`;
    h += `<tr><td>Before</td><td>${esc(b.ipn)}</td></tr><tr><td>Won by</td><td><b>${esc(b.wpn)}</b>${b.ch ? ' (changed hands)' : ''}</td></tr>`;
    h += `<tr><td>Cause</td><td>${esc(b.c)}</td></tr></table>`;
    (b.p || []).forEach(p => {
      h += `<div class="pl"><b>"in ${esc(p.n)}"</b> in Commons speeches`;
      if (p.r12 != null) h += `<table><tr><td>Reference year</td><td>${fmt(p.r12)} (24 to 13 months before)</td></tr><tr><td>Year after</td><td><b>${fmt(p.p12)}</b> (polling month and 12 after)</td></tr>`;
      if (p.x != null) h += `<tr><td>Matched towns</td><td>${fmt(p.c12[0])} then ${fmt(p.c12[1])} (five together)</td></tr><tr><td>Change vs matched</td><td><b>${p.x >= 1 ? p.x.toFixed(1) + ' times' : 'down to ' + p.x.toFixed(2)}</b></td></tr>`;
      if (p.r12 != null) h += '</table>';
      h += spark(p);
      if (p.why) h += `<p class="nt">Not in the analysis: ${esc(p.why)}.</p>`;
      h += '</div>';
    });
    if (b.why) h += `<p class="nt">Not in the analysis: ${esc(b.why)}. Shown at the seat's point.</p>`;
    h += `<p class="nt">Sources: Hansard (Open Parliament Licence v3.0); <a href="https://en.wikipedia.org/wiki/${encodeURIComponent(yy + ' ' + b.s + ' by-election')}" target="_blank" rel="noopener">Wikipedia</a> by-election lists (CC BY-SA 4.0). Single by-elections are noisy.</p>`;
    new maplibregl.Popup({ maxWidth: '330px', anchor: small ? 'bottom' : undefined }).setLngLat(ll).setHTML(h).addTo(map);
  }
  function setup() {
    const feats = [];
    D.b.forEach((b, i) => {
      if (b.p) b.p.forEach(p => feats.push({ type: 'Feature', properties: { i, n: p.n, y: b.y, ch: b.ch, cg: b.cg, k: p.x != null ? 1 : 0, lx: p.x != null ? Math.log2(p.x) : 0, sz: Math.sqrt(p.p12 || 0) }, geometry: { type: 'Point', coordinates: [p.lo, p.la] } }));
      else if (b.la != null) feats.push({ type: 'Feature', properties: { i, n: b.s, y: b.y, ch: b.ch, cg: b.cg, k: 2, lx: 0, sz: 0 }, geometry: { type: 'Point', coordinates: [b.lo, b.la] } });
    });
    feats.sort((a, b) => b.properties.sz - a.properties.sz);
    map.addSource('b', { type: 'geojson', data: { type: 'FeatureCollection', features: feats }, attribution: 'Hansard: Open Parliament Licence v3.0; by-election lists: Wikipedia (CC BY-SA 4.0)' });
    const k0 = small ? 0.9 : 1.3;
    const rad = ['interpolate', ['linear'], ['zoom'], 4, ['+', 3, ['*', k0, ['get', 'sz']]], 8, ['+', 5, ['*', 1.8, ['get', 'sz']]], 13, ['+', 8, ['*', 2.4, ['get', 'sz']]]];
    map.addLayer({ id: 'upts', type: 'circle', source: 'b', filter: ['==', ['get', 'k'], 2], paint: { 'circle-radius': ['interpolate', ['linear'], ['zoom'], 4, 2.6, 9, 4.5, 13, 7], 'circle-color': 'rgba(0,0,0,0)', 'circle-stroke-color': '#8E8576', 'circle-stroke-width': 1.2 } });
    map.addLayer({ id: 'xpts', type: 'circle', source: 'b', filter: ['==', ['get', 'k'], 0], paint: { 'circle-radius': ['interpolate', ['linear'], ['zoom'], 4, 3, 9, 5, 13, 7.5], 'circle-color': '#B9B4AA', 'circle-stroke-color': '#fff', 'circle-stroke-width': 1 } });
    map.addLayer({ id: 'pts', type: 'circle', source: 'b', filter: ['==', ['get', 'k'], 1], paint: { 'circle-radius': rad, 'circle-color': colorExpr(), 'circle-stroke-color': '#fff', 'circle-stroke-width': 1.2, 'circle-opacity': 0.95 } });
    map.addLayer({ id: 'lbl', type: 'symbol', source: 'b', minzoom: 8, filter: ['<', ['get', 'k'], 2], layout: { 'text-field': ['get', 'n'], 'text-size': 11.5, 'text-font': ['Noto Sans Regular'], 'text-offset': [0, 1.1], 'text-anchor': 'top', 'text-optional': true }, paint: { 'text-color': '#2B2119', 'text-halo-color': '#fff', 'text-halo-width': 1.5 } });
    ['pts', 'xpts', 'upts'].forEach(l => { map.on('click', l, e => { const f = e.features[0]; popup(D.b[f.properties.i], f.geometry.coordinates); }); map.on('mouseenter', l, () => map.getCanvas().style.cursor = 'pointer'); map.on('mouseleave', l, () => map.getCanvas().style.cursor = ''); });
    const lp = document.getElementById('lp'), btn = document.getElementById('lyrBtn');
    btn.addEventListener('click', e => { e.stopPropagation(); const o = lp.classList.toggle('open'); btn.setAttribute('aria-expanded', o); });
    document.addEventListener('click', e => { if (!lp.contains(e.target) && e.target !== btn) { lp.classList.remove('open'); btn.setAttribute('aria-expanded', false); } });
    const vis = (ids, v) => ids.forEach(id => map.setLayoutProperty(id, 'visibility', v ? 'visible' : 'none'));
    document.getElementById('lyP').addEventListener('change', e => vis(['pts'], e.target.checked));
    document.getElementById('lyX').addEventListener('change', e => vis(['xpts'], e.target.checked));
    document.getElementById('lyU').addEventListener('change', e => vis(['upts'], e.target.checked));
    document.getElementById('lyL').addEventListener('change', e => vis(['lbl'], e.target.checked));
    const baseSym = map.getStyle().layers.filter(l => l.type === 'symbol' && l.id !== 'lbl').map(l => l.id);
    document.getElementById('lyB').addEventListener('change', e => vis(baseSym, e.target.checked));
    document.querySelectorAll('.chip[data-m]').forEach(b => b.addEventListener('click', () => { mode = b.dataset.m; refresh(); }));
    const yr = document.getElementById('yr'), play = document.getElementById('play');
    yr.addEventListener('input', () => { if (timer) { clearInterval(timer); timer = null; play.textContent = 'Play'; } setYear(+yr.value); });
    play.addEventListener('click', () => {
      if (timer) { clearInterval(timer); timer = null; play.textContent = 'Play'; return; }
      let y = yMax >= 2026 ? 1909 : yMax; setYear(y); play.textContent = 'Pause';
      timer = setInterval(() => { y += 1; setYear(y); if (y >= 2026) { clearInterval(timer); timer = null; play.textContent = 'Play'; } }, 160);
    });
    refresh(); setYear(2026);
  }
  function go(i) {
    const b = D.b[i]; fold(true);
    const ll = b.p ? [b.p[0].lo, b.p[0].la] : [b.lo, b.la];
    if (ll[0] == null) return;
    if (b.y > yMax) setYear(2026);
    map.flyTo({ center: ll, zoom: small ? 9 : 9.5, duration: 1200, offset: [0, Math.round(map.getContainer().clientHeight * (small ? 0.3 : 0.22))] });
    map.once('moveend', () => popup(b, ll));
  }
  function setupSearch() {
    const q = document.getElementById('q'), sug = document.getElementById('sug'); let items = [], k = -1;
    const idx = [];
    D.b.forEach((b, i) => { if (!b.p && b.la == null) return; idx.push({ t: b.s, nn: norm(b.s), i, s: b.y }); (b.p || []).forEach(p => { if (norm(p.n) !== norm(b.s)) idx.push({ t: `${p.n} (${b.s})`, nn: norm(p.n), i, s: b.y }); }); });
    const show = () => { const v = norm(q.value.trim()); sug.innerHTML = ''; k = -1; if (v.length < 2) { sug.style.display = 'none'; return; }
      items = idx.filter(x => x.nn.startsWith(v)).concat(idx.filter(x => !x.nn.startsWith(v) && v.length > 3 && x.nn.includes(v))).slice(0, 14);
      items.forEach((it, j) => { const li = document.createElement('li'); li.setAttribute('role', 'option'); li.innerHTML = `${esc(it.t)} <span>${it.s}</span>`; li.addEventListener('mousedown', e => { e.preventDefault(); pick(j); }); sug.appendChild(li); });
      sug.style.display = items.length ? 'block' : 'none'; };
    const pick = j => { const it = items[j]; if (!it) return; q.value = it.t; sug.style.display = 'none'; go(it.i); };
    q.addEventListener('input', show);
    q.addEventListener('keydown', e => { const lis = [...sug.children];
      if (e.key === 'ArrowDown' || e.key === 'ArrowUp') { e.preventDefault(); k = Math.max(0, Math.min(lis.length - 1, k + (e.key === 'ArrowDown' ? 1 : -1))); lis.forEach((l, i) => l.setAttribute('aria-selected', i === k)); }
      else if (e.key === 'Enter') { e.preventDefault(); if (!items.length) show(); pick(k < 0 ? 0 : k); } else if (e.key === 'Escape') sug.style.display = 'none'; });
    q.addEventListener('blur', () => setTimeout(() => sug.style.display = 'none', 150));
    document.querySelectorAll('[data-go]').forEach(a => a.addEventListener('click', e => { e.preventDefault(); const [s, y] = a.dataset.go.split('|'); const i = D.b.findIndex(b => b.s === s && b.y === +y); if (i < 0) return;
      document.getElementById('mapWrap').scrollIntoView({ behavior: 'smooth' }); go(i); }));
  }
  fetch('data/site.json').then(r => r.json()).then(d => {
    D = d;
    const at = (qs.get('at') || '').split(',').map(Number);
    const mo = at.length === 3 && at.every(isFinite) ? { center: [at[1], at[0]], zoom: at[2] } : { bounds: [[-8.3, 49.9], [1.9, 58.8]], fitBoundsOptions: { padding: small ? { top: 10, bottom: 60, left: 10, right: 10 } : { top: 40, bottom: 70, left: 360, right: 60 } } };
    const m0 = new maplibregl.Map(Object.assign({ container: 'map', style: STYLE, attributionControl: { compact: true }, maxZoom: 15 }, mo));
    return new Promise((res, rej) => { m0.once('load', () => res(m0)); m0.once('error', e => { if (!m0.loaded()) rej(e.error || e); }); });
  }).then(mm => {
    map = mm; window.__map = mm;
    mm.on('error', e => { const er = e && e.error; if (er && (er.name === 'AbortError' || /abort/i.test(er.message || ''))) return; console.error(er || e); });
    const n = document.getElementById('nojs'); if (n) n.remove();
    mm.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'bottom-right');
    const foldAt = () => document.querySelectorAll('.maplibregl-ctrl-attrib.maplibregl-compact').forEach(at => { at.classList.remove('maplibregl-compact-show'); at.removeAttribute('open'); });
    mm.once('idle', foldAt); setTimeout(foldAt, 1500);
    setup(); setupSearch();
    if (qs.get('seat')) { const i = D.b.findIndex(b => norm(b.s) === norm(qs.get('seat'))); if (i >= 0) go(i); }
    document.getElementById('mapWrap').addEventListener('pointerdown', e => { if (e.target.closest && e.target.closest('.cartouche,.ov-top,.lp,.keys,.tl,.mfs-btn,.maplibregl-ctrl,.maplibregl-popup')) return; fold(true); }, { capture: true, passive: true, once: true });
  }).catch(e => { console.error(e); const n = document.getElementById('nojs'); if (n) n.textContent = 'The map could not load: ' + e.message; });
})();
