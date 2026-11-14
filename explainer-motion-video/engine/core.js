// ===== core: palette, primitives, registry & layout verification =====
const W = 1920, H = 1080;
const C = {
  bg: '#0F1522', panel: '#151D2C', panel2: '#1A2436', line: '#2B3954', grid: 'rgba(138,184,255,0.045)',
  text: '#E8EEF7', muted: '#8D9AB2', dim: '#5B6880',
  blue: '#8AB8FF', blue2: '#5B9BFF', sky: '#9FD6F2', mint: '#93D9C3', lav: '#B9AEF2',
  peach: '#F4BE9C', butter: '#EED68E', rose: '#EFA3B0', gray: '#6E7A90'
};
const FONT = 'Pretendard';
const SUB_ZONE = { x: 0, y: 930, w: W, h: 150 };   // subtitle area: no diagram nodes allowed

// ---- math / easing
const clamp = (v, a = 0, b = 1) => Math.max(a, Math.min(b, v));
const ease = x => { x = clamp(x); return x < .5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2; };
const eo = x => 1 - Math.pow(1 - clamp(x), 3);
const ap = (t, t0, d = .6) => eo((t - t0) / d);           // appear progress
const lerp = (a, b, k) => a + (b - a) * k;
function rgba(hex, a) { const n = parseInt(hex.slice(1), 16); return `rgba(${n >> 16 & 255},${n >> 8 & 255},${n & 255},${a})`; }

// ---- registry
function newReg() { return { boxes: [], links: [], lines: [], texts: [], polys: [] }; }

function font(sz, wt = 500) { return `${wt} ${sz}px ${FONT}`; }
function txt(x, y, s, o = {}) {
  const sz = o.size || 24;
  ctx.font = font(sz, o.weight || 500); ctx.fillStyle = o.color || C.text;
  ctx.textAlign = o.align || 'left'; ctx.textBaseline = o.base || 'middle';
  ctx.globalAlpha = (o.a ?? 1) * (o.alpha ?? 1);
  // inline highlight: *word*
  if (s.includes('*')) {
    const parts = s.split('*'); let total = 0; parts.forEach((p, i) => { ctx.font = font(sz, i % 2 ? 700 : (o.weight || 500)); total += ctx.measureText(p).width; });
    let cx = o.align === 'center' ? x - total / 2 : o.align === 'right' ? x - total : x; ctx.textAlign = 'left';
    parts.forEach((p, i) => { ctx.font = font(sz, i % 2 ? 700 : (o.weight || 500)); ctx.fillStyle = i % 2 ? (o.hl || C.blue) : (o.color || C.text); ctx.fillText(p, cx, y); cx += ctx.measureText(p).width; });
  } else ctx.fillText(s, x, y);
  ctx.globalAlpha = 1;
  ctx.font = font(sz, o.weight || 500);
  return ctx.measureText(s.replace(/\*/g, '')).width;
}
function measure(s, sz, wt = 500) { ctx.font = font(sz, wt); return ctx.measureText(s).width; }

function rrect(x, y, w, h, r) { ctx.beginPath(); ctx.roundRect(x, y, w, h, r); }

// box: kind 'node' (obstacle) | 'group' (container, not obstacle; its title is a text obstacle)
function box(R, id, x, y, w, h, o = {}) {
  const a = o.a ?? 1; if (a <= 0.001) return null;
  const col = o.col || C.blue, kind = o.kind || 'node', r = o.r ?? 12;
  const dy = (1 - a) * 10;
  ctx.save(); ctx.globalAlpha = a; ctx.translate(0, dy);
  rrect(x, y, w, h, r);
  ctx.fillStyle = o.fill ?? (kind === 'group' ? rgba(col, .04) : rgba(col, o.fillA ?? .12)); ctx.fill();
  ctx.lineWidth = o.lw ?? (kind === 'group' ? 1.2 : 1.6);
  ctx.strokeStyle = o.stroke ?? rgba(col, kind === 'group' ? .35 : .85);
  if (o.dash) ctx.setLineDash(o.dash); ctx.stroke(); ctx.setLineDash([]);
  ctx.restore();
  const b = { id, x, y, w, h, kind, parent: o.parent || null };
  R.boxes.push(b);
  // labels
  ctx.save(); ctx.globalAlpha = a; ctx.translate(0, dy);
  if (kind === 'group' && o.label) {
    const tw = txt(x + 18, y + 26, o.label, { size: o.lsize || 19, weight: 600, color: o.lcol || rgba(col, .95) });
    R.texts.push({ id: id + ':title', x: x + 18, y: y + 14, w: tw, h: 24, owner: id });
  } else if (o.label) {
    const ic = o.icon ? 34 : 0;
    const lines = o.label.split('\n'); const sz = o.lsize || 22; const subSz = o.ssize || 16;
    const lh = sz * 1.25; const tot = lines.length * lh + (o.sub ? subSz * 1.5 : 0);
    let ty = y + h / 2 - tot / 2 + lh / 2;
    const al = o.align || 'center';
    const tx = al === 'left' ? x + 18 + ic : x + w / 2 + ic / 2;
    let maxw = 0;
    lines.forEach(L => { const tw = txt(tx, ty, L, { size: sz, weight: o.weight || 600, color: o.lcol || C.text, align: al }); maxw = Math.max(maxw, tw); ty += lh; });
    if (o.sub) { const tw = txt(tx, ty - lh / 2 + subSz * .95, o.sub, { size: subSz, weight: 400, color: o.scol || C.muted, align: al }); maxw = Math.max(maxw, tw); }
    b.textW = maxw + ic; b.pad = al === 'left' ? 18 : 12;
    if (o.icon) { const ix = al === 'left' ? x + 18 + 14 : x + w / 2 - maxw / 2 - 6; drawIcon(o.icon, ix, y + h / 2, o.icol || col); }
  }
  ctx.restore();
  return b;
}

function getBox(R, id) { const b = R.boxes.find(b => b.id === id); if (!b) throw new Error('no box ' + id); return b; }
function sidePt(b, side, f = .5) {
  if (side === 'r') return [b.x + b.w, b.y + b.h * f];
  if (side === 'l') return [b.x, b.y + b.h * f];
  if (side === 't') return [b.x + b.w * f, b.y];
  return [b.x + b.w * f, b.y + b.h];
}
// link: orthogonal connector with arrowhead; o: {fs,ts,ff,tf,mx,my,pts,col,p,dash,label}
function link(R, from, to, o = {}) {
  const p = o.p ?? 1; if (p <= 0.001) return;
  const A = R.boxes.find(b => b.id === from), B = R.boxes.find(b => b.id === to);
  if (!A || !B) return;
  const fs = o.fs || 'r', ts = o.ts || 'l';
  const p0 = o.p0 || sidePt(A, fs, o.ff ?? .5), p1 = o.p1 || sidePt(B, ts, o.tf ?? .5);
  let pts;
  if (o.pts) pts = [p0, ...o.pts, p1];
  else if ((fs === 'r' || fs === 'l') && (ts === 'l' || ts === 'r')) {
    const mx = o.mx ?? (p0[0] + p1[0]) / 2;
    pts = Math.abs(p0[1] - p1[1]) < .5 ? [p0, p1] : [p0, [mx, p0[1]], [mx, p1[1]], p1];
  } else if ((fs === 'b' || fs === 't') && (ts === 't' || ts === 'b')) {
    const my = o.my ?? (p0[1] + p1[1]) / 2;
    pts = Math.abs(p0[0] - p1[0]) < .5 ? [p0, p1] : [p0, [p0[0], my], [p1[0], my], p1];
  } else if (fs === 'r' || fs === 'l') pts = [p0, [p1[0], p0[1]], p1];
  else pts = [p0, [p0[0], p1[1]], p1];
  R.links.push({ from, to, pts, ts });
  drawPath(pts, p, o);
  if (o.label && p > .6) {
    const m = o.lpos || midOf(pts);
    const a = clamp((p - .6) / .4);
    const tw = measure(o.label, o.lsize || 15, 500) + 16;
    ctx.globalAlpha = a; rrect(m[0] - tw / 2, m[1] - 13 + (o.ldy || 0), tw, 26, 13); ctx.fillStyle = C.bg; ctx.fill(); ctx.globalAlpha = 1;
    txt(m[0], m[1] + (o.ldy || 0), o.label, { size: o.lsize || 15, color: o.lcol || C.muted, align: 'center', a });
    R.texts.push({ id: from + '>' + to + ':label', x: m[0] - tw / 2, y: m[1] - 13 + (o.ldy || 0), w: tw, h: 26, owner: 'link:' + from + '>' + to });
  }
}
function midOf(pts) {
  let L = 0; const seg = []; for (let i = 1; i < pts.length; i++) { const l = Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]); seg.push(l); L += l; }
  let h = L / 2; for (let i = 0; i < seg.length; i++) { if (h <= seg[i]) { const k = h / seg[i]; return [lerp(pts[i][0], pts[i + 1][0], k), lerp(pts[i][1], pts[i + 1][1], k)]; } h -= seg[i]; }
  return pts[0];
}
function drawPath(pts, p, o) {
  const col = o.col || C.blue;
  let L = 0; for (let i = 1; i < pts.length; i++) L += Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]);
  let rem = L * p;
  ctx.save(); ctx.strokeStyle = rgba(col, o.alpha ?? .9); ctx.lineWidth = o.lw || 2; ctx.lineJoin = 'round'; ctx.lineCap = 'round';
  if (o.dash) ctx.setLineDash(o.dash);
  ctx.beginPath(); ctx.moveTo(pts[0][0], pts[0][1]);
  let end = pts[0], dir = [1, 0];
  for (let i = 1; i < pts.length && rem > 0; i++) {
    const dx = pts[i][0] - pts[i - 1][0], dy = pts[i][1] - pts[i - 1][1], l = Math.hypot(dx, dy);
    const k = Math.min(1, rem / l); end = [pts[i - 1][0] + dx * k, pts[i - 1][1] + dy * k]; dir = [dx / l, dy / l];
    ctx.lineTo(end[0], end[1]); rem -= l;
  }
  ctx.stroke(); ctx.setLineDash([]);
  if (o.arrow !== false && p > .02) {
    const s = 9; ctx.fillStyle = rgba(col, o.alpha ?? .9); ctx.beginPath();
    ctx.moveTo(end[0], end[1]);
    ctx.lineTo(end[0] - dir[0] * s * 1.4 - dir[1] * s * .75, end[1] - dir[1] * s * 1.4 + dir[0] * s * .75);
    ctx.lineTo(end[0] - dir[0] * s * 1.4 + dir[1] * s * .75, end[1] - dir[1] * s * 1.4 - dir[0] * s * .75);
    ctx.closePath(); ctx.fill();
  }
  ctx.restore();
}
// plain line (divider etc.) — still checked against nodes
function line(R, x1, y1, x2, y2, o = {}) {
  const a = o.a ?? 1; if (a <= 0) return;
  ctx.save(); ctx.globalAlpha = a; ctx.strokeStyle = o.col || C.line; ctx.lineWidth = o.lw || 1.5; if (o.dash) ctx.setLineDash(o.dash);
  ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); ctx.stroke(); ctx.restore();
  if (!o.free) R.lines.push({ id: o.id || 'line', pts: [[x1, y1], [x2, y2]] });
}
function textObs(R, id, x, y, s, o = {}) {   // standalone text that diagram lines must not cross
  const w = txt(x, y, s, o); const sz = o.size || 24;
  const x0 = o.align === 'center' ? x - w / 2 : o.align === 'right' ? x - w : x;
  R.texts.push({ id, x: x0, y: y - sz * .65, w, h: sz * 1.3, owner: o.owner || id });
  return w;
}

// ---- icons (simple line glyphs)
function drawIcon(k, x, y, col) {
  ctx.save(); ctx.strokeStyle = col; ctx.fillStyle = col; ctx.lineWidth = 1.8; ctx.lineCap = 'round'; ctx.lineJoin = 'round';
  ctx.beginPath();
  if (k === 'db') { ctx.ellipse(x, y - 8, 10, 4, 0, 0, Math.PI * 2); ctx.moveTo(x - 10, y - 8); ctx.lineTo(x - 10, y + 8); ctx.ellipse(x, y + 8, 10, 4, 0, Math.PI, 0, true); ctx.lineTo(x + 10, y - 8); ctx.stroke(); }
  else if (k === 'user') { ctx.arc(x, y - 6, 5.5, 0, Math.PI * 2); ctx.stroke(); ctx.beginPath(); ctx.arc(x, y + 12, 10, Math.PI * 1.1, Math.PI * 1.9); ctx.stroke(); }
  else if (k === 'chip') { ctx.rect(x - 9, y - 9, 18, 18); for (const d of [-5, 0, 5]) { ctx.moveTo(x + d, y - 9); ctx.lineTo(x + d, y - 13); ctx.moveTo(x + d, y + 9); ctx.lineTo(x + d, y + 13); ctx.moveTo(x - 9, y + d); ctx.lineTo(x - 13, y + d); ctx.moveTo(x + 9, y + d); ctx.lineTo(x + 13, y + d); } ctx.stroke(); }
  else if (k === 'plug') { ctx.rect(x - 8, y - 4, 16, 10); ctx.moveTo(x - 4, y - 4); ctx.lineTo(x - 4, y - 11); ctx.moveTo(x + 4, y - 4); ctx.lineTo(x + 4, y - 11); ctx.moveTo(x, y + 6); ctx.lineTo(x, y + 12); ctx.stroke(); }
  else if (k === 'doc') { ctx.moveTo(x - 8, y - 11); ctx.lineTo(x + 4, y - 11); ctx.lineTo(x + 8, y - 7); ctx.lineTo(x + 8, y + 11); ctx.lineTo(x - 8, y + 11); ctx.closePath(); ctx.moveTo(x - 4, y - 2); ctx.lineTo(x + 4, y - 2); ctx.moveTo(x - 4, y + 4); ctx.lineTo(x + 4, y + 4); ctx.stroke(); }
  else if (k === 'graph') { const P = [[x - 9, y - 6], [x + 8, y - 9], [x + 2, y + 9], [x - 8, y + 7]]; ctx.moveTo(...P[0]); ctx.lineTo(...P[1]); ctx.lineTo(...P[2]); ctx.lineTo(...P[0]); ctx.moveTo(...P[2]); ctx.lineTo(...P[3]); ctx.stroke(); P.forEach(p => { ctx.beginPath(); ctx.arc(p[0], p[1], 3, 0, Math.PI * 2); ctx.fill(); }); }
  else if (k === 'gear') { ctx.arc(x, y, 6, 0, Math.PI * 2); for (let i = 0; i < 8; i++) { const a = i * Math.PI / 4; ctx.moveTo(x + Math.cos(a) * 8, y + Math.sin(a) * 8); ctx.lineTo(x + Math.cos(a) * 11, y + Math.sin(a) * 11); } ctx.stroke(); }
  else if (k === 'bot') { ctx.roundRect(x - 10, y - 7, 20, 16, 4); ctx.moveTo(x, y - 7); ctx.lineTo(x, y - 12); ctx.stroke(); ctx.beginPath(); ctx.arc(x - 4, y, 2, 0, Math.PI * 2); ctx.arc(x + 4, y, 2, 0, Math.PI * 2); ctx.fill(); }
  ctx.restore();
}

// ---- chrome
function background() {
  ctx.fillStyle = C.bg; ctx.fillRect(0, 0, W, H);
  ctx.fillStyle = C.grid; for (let x = 40; x < W; x += 40) for (let y = 40; y < H; y += 40) ctx.fillRect(x - 1, y - 1, 2, 2);
}
function header(chap, title, t) {
  const a = ap(t, 0, .5);
  txt(96, 70, chap, { size: 20, weight: 600, color: C.blue, a });
  ctx.globalAlpha = a; ctx.fillStyle = C.blue; ctx.fillRect(96, 92, 28, 3); ctx.globalAlpha = 1;
  txt(96, 132, title, { size: 34, weight: 700, color: C.text, a: ap(t, .1, .6) });
}
function subtitle(s) {
  if (!s) return;
  txt(W / 2, 1000, s, { size: 34, weight: 500, color: C.text, align: 'center', hl: C.blue });
}
function progress(k) { ctx.fillStyle = C.line; ctx.fillRect(0, H - 4, W, 4); ctx.fillStyle = C.blue; ctx.fillRect(0, H - 4, W * k, 4); }

// ---- verification
function segRect(a, b, r) {   // Liang–Barsky: does segment a-b intersect rect interior
  let t0 = 0, t1 = 1; const dx = b[0] - a[0], dy = b[1] - a[1];
  const P = [-dx, dx, -dy, dy], Q = [a[0] - r.x, r.x + r.w - a[0], a[1] - r.y, r.y + r.h - a[1]];
  for (let i = 0; i < 4; i++) { if (P[i] === 0) { if (Q[i] <= 0) return false; } else { const t = Q[i] / P[i]; if (P[i] < 0) { if (t > t1) return false; if (t > t0) t0 = t; } else { if (t < t0) return false; if (t < t1) t1 = t; } } }
  return t1 - t0 > 1e-6;
}
const shrink = (b, d) => ({ x: b.x + d, y: b.y + d, w: b.w - 2 * d, h: b.h - 2 * d });
const grow = (b, d) => ({ x: b.x - d, y: b.y - d, w: b.w + 2 * d, h: b.h + 2 * d });
function isAncestor(R, gid, bid) { let b = R.boxes.find(x => x.id === bid); while (b && b.parent) { if (b.parent === gid) return true; b = R.boxes.find(x => x.id === b.parent); } return false; }
function segCross(a, b, c, d) {
  const o = (p, q, r) => Math.sign((q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0]));
  return o(a, b, c) * o(a, b, d) < 0 && o(c, d, a) * o(c, d, b) < 0;
}
function ptSeg(p, a, b) { const dx = b[0] - a[0], dy = b[1] - a[1]; const l = dx * dx + dy * dy; let k = l ? ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / l : 0; k = clamp(k); return Math.hypot(p[0] - a[0] - k * dx, p[1] - a[1] - k * dy); }
function segDist(a, b, c, d) { if (segCross(a, b, c, d)) return 0; return Math.min(ptSeg(a, c, d), ptSeg(b, c, d), ptSeg(c, a, b), ptSeg(d, a, b)); }
function verify(R, tag) {
  const out = []; const nodes = R.boxes.filter(b => b.kind === 'node' || b.kind === 'cap');
  const inside = (p, b) => p[0] >= b.x - 1 && p[0] <= b.x + b.w + 1 && p[1] >= b.y - 1 && p[1] <= b.y + b.h + 1;
  for (const L of R.links) {
    const A = R.boxes.find(b => b.id === L.from), B = R.boxes.find(b => b.id === L.to);
    const name = `${L.from}→${L.to}`;
    // endpoints sit on the edges
    if (!inside(L.pts[0], A)) out.push(`[${tag}] ${name}: 시작점이 출발 도형 밖`);
    if (!inside(L.pts.at(-1), B)) out.push(`[${tag}] ${name}: 끝점이 도착 도형 밖`);
    for (let i = 1; i < L.pts.length; i++) {
      const a = L.pts[i - 1], b = L.pts[i];
      for (const n of nodes) {
        if (n.id === L.from || n.id === L.to) { if (segRect(a, b, shrink(n, 2))) out.push(`[${tag}] ${name}: 선이 자기 ${n.id === L.from ? '출발' : '도착'} 도형 내부를 통과`); continue; }
        if (isAncestor(R, n.id, L.from) || isAncestor(R, n.id, L.to)) continue;
        if (segRect(a, b, grow(n, 3))) out.push(`[${tag}] ${name}: 선이 '${n.id}' 도형을 가로지름`);
      }
      for (const P of R.polys) for (let q = 1; q < P.pts.length; q++) if (segDist(a, b, P.pts[q - 1], P.pts[q]) < P.w / 2 + 3) out.push(`[${tag}] ${name}: 선이 '${P.id}'(팔·막대 등)에 닿음`);
      for (const T of R.texts) { if (T.owner === 'link:' + L.from + '>' + L.to) continue; if (segRect(a, b, T)) out.push(`[${tag}] ${name}: 선이 텍스트 '${T.id}'를 가림`); }
    }
    // arrow must point into target: penultimate point outside target
    const pen = L.pts.at(-2), end = L.pts.at(-1);
    const dir = [end[0] - pen[0], end[1] - pen[1]];
    const ctr = [B.x + B.w / 2, B.y + B.h / 2];
    if (dir[0] * (ctr[0] - end[0]) + dir[1] * (ctr[1] - end[1]) <= 0) out.push(`[${tag}] ${name}: 화살표가 도착 도형 반대쪽을 향함`);
  }
  // link-link crossings (warning)
  for (let i = 0; i < R.links.length; i++) for (let j = i + 1; j < R.links.length; j++) {
    const P = R.links[i].pts, Q = R.links[j].pts;
    for (let a = 1; a < P.length; a++) for (let b = 1; b < Q.length; b++) if (segCross(P[a - 1], P[a], Q[b - 1], Q[b])) out.push(`[${tag}] 경고: ${R.links[i].from}→${R.links[i].to} 와 ${R.links[j].from}→${R.links[j].to} 교차`);
  }
  for (const L of R.lines) for (const n of nodes) { if (segRect(L.pts[0], L.pts[1], grow(n, 2))) out.push(`[${tag}] 구분선 '${L.id}'이 '${n.id}' 도형을 가로지름`); }
  // node overlaps (non-nested), text overflow, safe zones
  for (let i = 0; i < nodes.length; i++) {
    const a = nodes[i];
    if (a.textW && a.textW > a.w - 2 * a.pad + 1) out.push(`[${tag}] '${a.id}' 글자가 도형 폭을 넘침 (${a.textW.toFixed(0)} > ${(a.w - 2 * a.pad).toFixed(0)})`);
    if (a.y + a.h > SUB_ZONE.y) out.push(`[${tag}] '${a.id}' 도형이 자막 영역 침범`);
    if (a.x < 40 || a.x + a.w > W - 40 || a.y < 40) out.push(`[${tag}] '${a.id}' 화면 가장자리 침범`);
    for (let j = i + 1; j < nodes.length; j++) {
      const b = nodes[j]; if (isAncestor(R, a.id, b.id) || isAncestor(R, b.id, a.id)) continue;
      if (a.x < b.x + b.w - 1 && b.x < a.x + a.w - 1 && a.y < b.y + b.h - 1 && b.y < a.y + a.h - 1) out.push(`[${tag}] '${a.id}'와 '${b.id}' 도형 겹침`);
    }
  }
  return out;
}
