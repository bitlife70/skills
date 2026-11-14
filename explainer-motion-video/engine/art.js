// ===== art: flat illustration helpers (objects first, text second) =====
function mix(a, b, k) {   // k=0 → a, k=1 → b
  const A = parseInt(a.slice(1), 16), B = parseInt(b.slice(1), 16);
  const ch = s => Math.round(((A >> s) & 255) * (1 - k) + ((B >> s) & 255) * k);
  return '#' + ((1 << 24) | (ch(16) << 16) | (ch(8) << 8) | ch(0)).toString(16).slice(1);
}
const tone = (col, k) => mix(col, C.bg, k);   // darker pastel toward background

function reg(R, id, x, y, w, h, o = {}) { const b = { id, x, y, w, h, kind: o.kind || 'node', parent: o.parent || null }; R.boxes.push(b); return b; }
function poly(R, id, pts, w) { R.polys.push({ id, pts, w }); }
function caption(R, id, x, y, s, o = {}) {      // small explanatory text; registered as node so leaders can attach
  const sz = o.size || 18; const w = txt(x, y, s, { size: sz, weight: o.weight || 600, color: o.color || C.text, align: o.align || 'left', a: o.a, hl: o.hl });
  let sw = 0; if (o.sub) sw = txt(x, y + sz * 1.15, o.sub, { size: sz - 4, weight: 400, color: C.muted, align: o.align || 'left', a: o.a });
  const ww = Math.max(w, sw); const x0 = o.align === 'center' ? x - ww / 2 : o.align === 'right' ? x - ww : x;
  const hh = o.sub ? sz * 2.2 : sz * 1.2;
  return reg(R, id, x0 - 4, y - sz * .65, ww + 8, hh + 4, { kind: 'cap' });
}
// leader line from a caption to an object (no arrowhead, dot at the object end)
function leader(R, from, to, o = {}) {
  const p = o.p ?? 1; if (p <= .001) return;
  const A = R.boxes.find(b => b.id === from), B = R.boxes.find(b => b.id === to); if (!A || !B) return;
  const p0 = o.p0 || sidePt(A, o.fs || 'r', .5), p1 = o.p1 || sidePt(B, o.ts || 'l', .5);
  const pts = [p0, ...(o.pts || []), p1];
  R.links.push({ from, to, pts, leader: true });
  drawPath(pts, p, { col: o.col || C.muted, lw: 1.4, arrow: false, alpha: .8 });
  if (p > .95) { ctx.fillStyle = o.col || C.muted; ctx.beginPath(); ctx.arc(p1[0], p1[1], 3.5, 0, Math.PI * 2); ctx.fill(); }
}

// ---- isometric slab (2:1). top face centre (cx,cy), width w, thickness th
function slab(cx, cy, w, th, col, o = {}) {
  const a = o.a ?? 1; if (a <= 0) return;
  const hw = w / 2, hh = w / 4;
  ctx.save(); ctx.globalAlpha = a;
  const L = [cx - hw, cy], T = [cx, cy - hh], Rr = [cx + hw, cy], B = [cx, cy + hh];
  const face = (pts, fill) => { ctx.beginPath(); ctx.moveTo(...pts[0]); pts.slice(1).forEach(p => ctx.lineTo(...p)); ctx.closePath(); if (fill) { ctx.fillStyle = fill; ctx.fill(); } ctx.strokeStyle = o.ghost ? rgba(col, .45) : rgba(col, .9); ctx.lineWidth = o.lw || 1.4; if (o.ghost) ctx.setLineDash([5, 5]); ctx.stroke(); ctx.setLineDash([]); };
  if (o.ghost) {
    face([L, B, [B[0], B[1] + th], [L[0], L[1] + th]], rgba(col, .03));
    face([B, Rr, [Rr[0], Rr[1] + th], [B[0], B[1] + th]], rgba(col, .03));
    face([L, T, Rr, B], rgba(col, .04));
  } else {
    face([L, B, [B[0], B[1] + th], [L[0], L[1] + th]], tone(col, .72));
    face([B, Rr, [Rr[0], Rr[1] + th], [B[0], B[1] + th]], tone(col, .6));
    face([L, T, Rr, B], tone(col, o.hl ? .3 : .45));
  }
  ctx.restore();
}
// exploded layer stack; layers top→bottom; returns geometry
function stack(R, id, cx, topY, w, layers, o = {}) {
  const th = o.th || 22, gap = o.gap || 14, a = o.a ?? 1;
  const ys = layers.map((_, i) => topY + w / 4 + i * (th + gap));
  for (let i = layers.length - 1; i >= 0; i--) {
    const L = layers[i]; const la = a * (L.a ?? 1);
    slab(cx, ys[i] - (1 - la) * 18, w, th, L.col, { a: la, ghost: L.ghost, hl: L.hl, lw: L.hl ? 2.2 : 1.4 });
  }
  const h = w / 2 + (layers.length - 1) * (th + gap) + th;
  if (a > .01) reg(R, id, cx - w / 2, topY, w, h);
  return { ys, h };
}

// ---- glyphs for app-tile icons (stroke style), s = scale (1 ≈ 44px glyph)
function glyph(k, x, y, s, col) {
  ctx.save(); ctx.translate(x, y); ctx.scale(s, s); ctx.strokeStyle = col; ctx.fillStyle = col; ctx.lineWidth = 2.2 / s * s * 1; ctx.lineWidth = 2.2; ctx.lineCap = 'round'; ctx.lineJoin = 'round';
  const P = (...a) => { ctx.beginPath(); ctx.moveTo(a[0], a[1]); for (let i = 2; i < a.length; i += 2) ctx.lineTo(a[i], a[i + 1]); };
  if (k === 'pen') { P(-12, 12, -8, 2, 8, -14, 14, -8, -2, 8, -12, 12); ctx.stroke(); P(4, -10, 10, -4); ctx.stroke(); }
  else if (k === 'summary') { [-10, -3, 4, 11].forEach((yy, i) => { P(-12, yy, i === 3 ? 2 : 12, yy); ctx.stroke(); }); }
  else if (k === 'translate') { ctx.font = `700 15px ${FONT}`; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.strokeRect(-14, -13, 16, 16); ctx.fillText('A', -6, -5); ctx.strokeRect(-2, -3, 16, 16); ctx.fillText('가', 6, 5.5); }
  else if (k === 'chart') { P(-13, 12, 13, 12); ctx.stroke(); [[-9, 4], [-2, -4], [5, -10]].forEach(([bx, by]) => { ctx.strokeRect(bx, by, 5, 12 - by); }); }
  else if (k === 'code') { P(-6, -9, -13, 0, -6, 9); ctx.stroke(); P(6, -9, 13, 0, 6, 9); ctx.stroke(); P(3, -12, -3, 12); ctx.stroke(); }
  else if (k === 'search') { ctx.beginPath(); ctx.arc(-3, -3, 8, 0, Math.PI * 2); ctx.stroke(); P(3, 3, 12, 12); ctx.stroke(); }
  else if (k === 'doc') { P(-9, -13, 4, -13, 10, -7, 10, 13, -9, 13); ctx.closePath(); ctx.stroke(); P(-4, -2, 5, -2); ctx.stroke(); P(-4, 4, 5, 4); ctx.stroke(); }
  else if (k === 'image') { ctx.strokeRect(-13, -10, 26, 20); P(-10, 7, -3, -1, 2, 4, 6, 0, 11, 7); ctx.stroke(); ctx.beginPath(); ctx.arc(6, -4, 2.5, 0, Math.PI * 2); ctx.fill(); }
  else if (k === 'browser') { ctx.strokeRect(-14, -11, 28, 22); P(-14, -5, 14, -5); ctx.stroke(); P(0, 0, 0, 10, 3, 7, 7, 11); ctx.stroke(); }
  else if (k === 'report') { P(-9, -13, 4, -13, 10, -7, 10, 13, -9, 13); ctx.closePath(); ctx.stroke(); ctx.strokeRect(-5, 3, 3, 6); ctx.strokeRect(0, -1, 3, 10); ctx.strokeRect(5, 5, 0.1, 4); }
  else if (k === 'wrench') { ctx.beginPath(); ctx.arc(6, -6, 6, Math.PI * .9, Math.PI * 2.6); ctx.stroke(); P(2, -2, -11, 11); ctx.stroke(); }
  else if (k === 'scale') { P(0, -13, 0, 12); ctx.stroke(); P(-8, 12, 8, 12); ctx.stroke(); P(-12, -8, 12, -8); ctx.stroke(); P(-12, -8, -15, 2, -9, 2, -12, -8); ctx.stroke(); P(12, -8, 9, 2, 15, 2, 12, -8); ctx.stroke(); }
  else if (k === 'coin') { ctx.beginPath(); ctx.arc(0, 0, 12, 0, Math.PI * 2); ctx.stroke(); ctx.font = `700 15px ${FONT}`; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText('₩', 0, 1); }
  else if (k === 'brief') { ctx.strokeRect(-13, -6, 26, 18); P(-5, -6, -5, -11, 5, -11, 5, -6); ctx.stroke(); P(-13, 2, 13, 2); ctx.stroke(); }
  else if (k === 'headset') { ctx.beginPath(); ctx.arc(0, 0, 11, Math.PI, 0); ctx.stroke(); ctx.strokeRect(-14, 0, 6, 9); ctx.strokeRect(8, 0, 6, 9); P(11, 9, 11, 13, 3, 13); ctx.stroke(); }
  else if (k === 'chip') { ctx.strokeRect(-9, -9, 18, 18); ctx.strokeRect(-4, -4, 8, 8); for (const d of [-5, 0, 5]) { P(d, -9, d, -13); ctx.stroke(); P(d, 9, d, 13); ctx.stroke(); P(-9, d, -13, d); ctx.stroke(); P(9, d, 13, d); ctx.stroke(); } }
  else if (k === 'gear') { ctx.beginPath(); ctx.arc(0, 0, 6, 0, Math.PI * 2); ctx.stroke(); for (let i = 0; i < 8; i++) { const an = i * Math.PI / 4; P(Math.cos(an) * 9, Math.sin(an) * 9, Math.cos(an) * 13, Math.sin(an) * 13); ctx.stroke(); } ctx.beginPath(); ctx.arc(0, 0, 10, 0, Math.PI * 2); ctx.stroke(); }
  else if (k === 'bot') { ctx.strokeRect(-11, -7, 22, 17); P(0, -7, 0, -12); ctx.stroke(); ctx.beginPath(); ctx.arc(0, -13, 2, 0, Math.PI * 2); ctx.fill(); ctx.beginPath(); ctx.arc(-5, 1, 2.4, 0, Math.PI * 2); ctx.arc(5, 1, 2.4, 0, Math.PI * 2); ctx.fill(); }
  else if (k === 'workflow') { ctx.strokeRect(-14, -12, 9, 9); ctx.strokeRect(5, -12, 9, 9); ctx.strokeRect(-4, 4, 9, 9); P(-5, -7.5, 5, -7.5); ctx.stroke(); P(9.5, -3, 9.5, 8.5, 5, 8.5); ctx.stroke(); }
  else if (k === 'person') { ctx.beginPath(); ctx.arc(0, -6, 6, 0, Math.PI * 2); ctx.stroke(); ctx.beginPath(); ctx.arc(0, 14, 12, Math.PI * 1.15, Math.PI * 1.85); ctx.stroke(); }
  else if (k === 'plug') { ctx.strokeRect(-8, -3, 16, 11); P(-4, -3, -4, -11); ctx.stroke(); P(4, -3, 4, -11); ctx.stroke(); P(0, 8, 0, 13); ctx.stroke(); }
  ctx.restore();
}
function tile(x, y, sz, k, col, o = {}) {   // app-icon tile centred at x,y
  const a = o.a ?? 1; if (a <= 0) return; const sc = o.scale ?? 1;
  ctx.save(); ctx.globalAlpha = a; ctx.translate(x, y); ctx.scale(sc, sc);
  rrect(-sz / 2, -sz / 2, sz, sz, sz * .24); ctx.fillStyle = tone(col, o.dark ?? .8); ctx.fill(); ctx.strokeStyle = rgba(col, .8); ctx.lineWidth = 1.5; ctx.stroke();
  glyph(k, 0, 0, sz / 60, col);
  ctx.restore();
}

// ---- figures
function person(x, groundY, s, col, o = {}) {      // simple flat person, feet at groundY
  const a = o.a ?? 1; if (a <= 0) return; ctx.save(); ctx.globalAlpha = a;
  const h = 96 * s;
  rrect(x - 22 * s, groundY - h + 34 * s, 44 * s, h - 34 * s, [18 * s, 18 * s, 4 * s, 4 * s]); ctx.fillStyle = tone(col, .55); ctx.fill();
  ctx.beginPath(); ctx.arc(x, groundY - h + 16 * s, 15 * s, 0, Math.PI * 2); ctx.fillStyle = tone(col, .3); ctx.fill();
  if (o.helmet) { ctx.beginPath(); ctx.arc(x, groundY - h + 13 * s, 17 * s, Math.PI, 0); ctx.fillStyle = col; ctx.fill(); ctx.fillRect(x - 20 * s, groundY - h + 12 * s, 40 * s, 3 * s); }
  ctx.restore();
}
function gear(x, y, r, col, rot, o = {}) {
  ctx.save(); ctx.globalAlpha = o.a ?? 1; ctx.translate(x, y); ctx.rotate(rot);
  ctx.beginPath(); const n = 8;
  for (let i = 0; i < n * 2; i++) { const ang = i * Math.PI / n, rr = i % 2 ? r : r * 1.22; const w = Math.PI / n * .45; ctx.lineTo(Math.cos(ang - w) * rr, Math.sin(ang - w) * rr); ctx.lineTo(Math.cos(ang + w) * rr, Math.sin(ang + w) * rr); }
  ctx.closePath(); ctx.fillStyle = o.fill || tone(col, .45); ctx.fill(); ctx.strokeStyle = col; ctx.lineWidth = 2; ctx.stroke();
  ctx.beginPath(); ctx.arc(0, 0, r * .38, 0, Math.PI * 2); ctx.fillStyle = C.bg; ctx.fill(); ctx.stroke();
  ctx.restore();
}
function rack(x, y, w, h, t, o = {}) {        // server rack (front view)
  const a = o.a ?? 1; if (a <= 0) return; ctx.save(); ctx.globalAlpha = a;
  rrect(x, y, w, h, 8); ctx.fillStyle = tone(C.gray, .62); ctx.fill(); ctx.strokeStyle = rgba(C.gray, .9); ctx.lineWidth = 1.5; ctx.stroke();
  const n = Math.floor((h - 20) / 30);
  for (let i = 0; i < n; i++) { const yy = y + 14 + i * 30; rrect(x + 8, yy, w - 16, 20, 4); ctx.fillStyle = tone(C.gray, .78); ctx.fill();
    const on = Math.sin(t * 3 + i * 1.7 + x) > 0; ctx.fillStyle = on ? C.mint : tone(C.mint, .7); ctx.beginPath(); ctx.arc(x + w - 18, yy + 10, 3, 0, Math.PI * 2); ctx.fill();
    ctx.fillStyle = tone(C.gray, .45); ctx.fillRect(x + 16, yy + 8, w * .35, 3); }
  ctx.restore();
}
function cylinder(x, y, w, h, col, o = {}) {   // database
  const a = o.a ?? 1; if (a <= 0) return; ctx.save(); ctx.globalAlpha = a;
  const ry = w * .18;
  ctx.beginPath(); ctx.moveTo(x, y + ry); ctx.lineTo(x, y + h - ry); ctx.ellipse(x + w / 2, y + h - ry, w / 2, ry, 0, Math.PI, 0, true); ctx.lineTo(x + w, y + ry); ctx.closePath();
  ctx.fillStyle = tone(col, .62); ctx.fill(); ctx.strokeStyle = col; ctx.lineWidth = 1.6; ctx.stroke();
  ctx.beginPath(); ctx.ellipse(x + w / 2, y + ry, w / 2, ry, 0, 0, Math.PI * 2); ctx.fillStyle = tone(col, .42); ctx.fill(); ctx.stroke();
  for (const k of [.42, .7]) { ctx.beginPath(); ctx.ellipse(x + w / 2, y + h * k, w / 2, ry, 0, 0, Math.PI); ctx.stroke(); }
  ctx.restore();
}
function robot(cx, groundY, s, col, o = {}) {
  const a = o.a ?? 1; if (a <= 0) return; ctx.save(); ctx.globalAlpha = a;
  rrect(cx - 26 * s, groundY - 50 * s, 52 * s, 50 * s, 10 * s); ctx.fillStyle = tone(col, .6); ctx.fill(); ctx.strokeStyle = col; ctx.lineWidth = 1.5; ctx.stroke();
  rrect(cx - 22 * s, groundY - 92 * s, 44 * s, 36 * s, 9 * s); ctx.fillStyle = tone(col, .4); ctx.fill(); ctx.stroke();
  ctx.fillStyle = C.bg; ctx.beginPath(); ctx.arc(cx - 8 * s, groundY - 74 * s, 4 * s, 0, Math.PI * 2); ctx.arc(cx + 8 * s, groundY - 74 * s, 4 * s, 0, Math.PI * 2); ctx.fill();
  ctx.restore();
}
function paper(x, y, s, col, o = {}) {
  ctx.save(); ctx.globalAlpha = o.a ?? 1; ctx.translate(x, y);
  ctx.beginPath(); ctx.moveTo(-14 * s, -18 * s); ctx.lineTo(6 * s, -18 * s); ctx.lineTo(14 * s, -10 * s); ctx.lineTo(14 * s, 18 * s); ctx.lineTo(-14 * s, 18 * s); ctx.closePath();
  ctx.fillStyle = tone(col, .25); ctx.fill(); ctx.strokeStyle = col; ctx.lineWidth = 1.2; ctx.stroke();
  ctx.strokeStyle = tone(col, .6); for (const yy of [-6, 0, 6, 12]) { ctx.beginPath(); ctx.moveTo(-8 * s, yy * s); ctx.lineTo(8 * s, yy * s); ctx.stroke(); }
  ctx.restore();
}
function token(x, y, sz, col, o = {}) {   // MCP connector token
  ctx.save(); ctx.globalAlpha = o.a ?? 1; rrect(x - sz / 2, y - sz / 2, sz, sz, sz * .25); ctx.fillStyle = tone(col, .5); ctx.fill(); ctx.strokeStyle = col; ctx.lineWidth = 1.5; ctx.stroke();
  glyph('plug', x, y + 1, sz / 52, C.bg); ctx.restore();
}

// ---- extra props
const beat = (t, a, b, fi = .5, fo = .5) => Math.min(ap(t, a, fi), 1 - ap(t, b - fo, fo));   // visible between a..b
function bubble(R, id, x, y, s, o = {}) {           // speech bubble anchored at tail (x,y), text centred above
  const a = o.a ?? 1; if (a <= 0) return; const sz = o.size || 20; const w = measure(s, sz, 600) + 36, h = sz + 26;
  const bx = x - w / 2 + (o.dx || 0), by = y - h - 14;
  ctx.save(); ctx.globalAlpha = a; rrect(bx, by, w, h, h / 2); ctx.fillStyle = tone(o.col || C.blue, .78); ctx.fill(); ctx.strokeStyle = o.col || C.blue; ctx.lineWidth = 1.5; ctx.stroke();
  ctx.beginPath(); ctx.moveTo(x - 8, by + h - 1); ctx.lineTo(x, y); ctx.lineTo(x + 8, by + h - 1); ctx.fillStyle = tone(o.col || C.blue, .78); ctx.fill(); ctx.restore();
  txt(bx + w / 2, by + h / 2, s, { size: sz, weight: 600, color: C.text, align: 'center', a, hl: o.hl });
  return reg(R, id, bx, by, w, h, { kind: 'cap' });
}
function windowUI(x, y, w, h, title, o = {}) {
  const a = o.a ?? 1; if (a <= 0) return; ctx.save(); ctx.globalAlpha = a;
  rrect(x, y, w, h, 12); ctx.fillStyle = C.panel2; ctx.fill(); ctx.strokeStyle = rgba(C.blue, .5); ctx.lineWidth = 1.4; ctx.stroke();
  ctx.fillStyle = rgba(C.blue, .08); rrect(x, y, w, 40, [12, 12, 0, 0]); ctx.fill();
  [C.rose, C.butter, C.mint].forEach((c, i) => { ctx.beginPath(); ctx.arc(x + 22 + i * 18, y + 20, 5, 0, Math.PI * 2); ctx.fillStyle = tone(c, .2); ctx.fill(); });
  ctx.restore(); txt(x + 84, y + 21, title, { size: 17, weight: 600, color: C.muted, a });
}
function check(x, y, s, col, a = 1) { if (a <= 0) return; ctx.save(); ctx.globalAlpha = a; ctx.beginPath(); ctx.arc(x, y, s, 0, Math.PI * 2); ctx.fillStyle = tone(col, .55); ctx.fill(); ctx.strokeStyle = col; ctx.lineWidth = 2; ctx.stroke(); ctx.beginPath(); ctx.moveTo(x - s * .45, y); ctx.lineTo(x - s * .1, y + s * .38); ctx.lineTo(x + s * .5, y - s * .35); ctx.strokeStyle = C.text; ctx.lineWidth = s * .16; ctx.lineCap = 'round'; ctx.stroke(); ctx.restore(); }
function cross(x, y, s, col, a = 1) { if (a <= 0) return; ctx.save(); ctx.globalAlpha = a; ctx.beginPath(); ctx.arc(x, y, s, 0, Math.PI * 2); ctx.fillStyle = tone(col, .6); ctx.fill(); ctx.strokeStyle = col; ctx.lineWidth = 2; ctx.stroke(); ctx.strokeStyle = C.text; ctx.lineWidth = s * .16; ctx.lineCap = 'round'; ctx.beginPath(); ctx.moveTo(x - s * .38, y - s * .38); ctx.lineTo(x + s * .38, y + s * .38); ctx.moveTo(x + s * .38, y - s * .38); ctx.lineTo(x - s * .38, y + s * .38); ctx.stroke(); ctx.restore(); }
function clockFace(x, y, r, hh, mm, col, a = 1) { if (a <= 0) return; ctx.save(); ctx.globalAlpha = a; ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2); ctx.fillStyle = tone(col, .75); ctx.fill(); ctx.strokeStyle = col; ctx.lineWidth = 2; ctx.stroke();
  for (let i = 0; i < 12; i++) { const an = i * Math.PI / 6; ctx.beginPath(); ctx.moveTo(x + Math.cos(an) * r * .8, y + Math.sin(an) * r * .8); ctx.lineTo(x + Math.cos(an) * r * .9, y + Math.sin(an) * r * .9); ctx.stroke(); }
  const ha = (hh % 12 + mm / 60) / 12 * Math.PI * 2 - Math.PI / 2, ma = mm / 60 * Math.PI * 2 - Math.PI / 2; ctx.lineCap = 'round';
  ctx.lineWidth = 4; ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x + Math.cos(ha) * r * .5, y + Math.sin(ha) * r * .5); ctx.stroke();
  ctx.lineWidth = 2.5; ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x + Math.cos(ma) * r * .75, y + Math.sin(ma) * r * .75); ctx.stroke(); ctx.restore(); }
function moon(x, y, r, a = 1) { if (a <= 0) return; ctx.save(); ctx.globalAlpha = a; ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2); ctx.fillStyle = tone(C.butter, .35); ctx.fill(); ctx.beginPath(); ctx.arc(x + r * .45, y - r * .25, r * .9, 0, Math.PI * 2); ctx.fillStyle = C.bg; ctx.fill(); ctx.restore(); }
function hourglass(x, y, s, k, a = 1) { if (a <= 0) return; ctx.save(); ctx.globalAlpha = a; ctx.translate(x, y);
  ctx.strokeStyle = C.butter; ctx.lineWidth = 2; ctx.fillStyle = tone(C.butter, .5);
  ctx.fillRect(-30 * s, -52 * s, 60 * s, 6 * s); ctx.fillRect(-30 * s, 46 * s, 60 * s, 6 * s);
  ctx.beginPath(); ctx.moveTo(-24 * s, -46 * s); ctx.lineTo(24 * s, -46 * s); ctx.lineTo(3 * s, 0); ctx.lineTo(24 * s, 46 * s); ctx.lineTo(-24 * s, 46 * s); ctx.lineTo(-3 * s, 0); ctx.closePath(); ctx.stroke();
  const top = 1 - k; ctx.fillStyle = tone(C.butter, .25);
  ctx.beginPath(); const ty = -46 * s + (1 - top) * 40 * s; const tw = 24 * s * (1 - (ty + 46 * s) / (46 * s)); ctx.moveTo(-tw, ty); ctx.lineTo(tw, ty); ctx.lineTo(0, -2 * s); ctx.closePath(); if (top > .02) ctx.fill();
  ctx.beginPath(); const by = 46 * s - k * 36 * s; const bw = 24 * s * ((by) / (46 * s)); ctx.moveTo(-24 * s, 46 * s); ctx.lineTo(24 * s, 46 * s); ctx.lineTo(Math.max(bw, 2), by); ctx.lineTo(-Math.max(bw, 2), by); ctx.closePath(); if (k > .02) ctx.fill();
  if (k > .02 && k < .98) { ctx.strokeStyle = tone(C.butter, .25); ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(0, by); ctx.stroke(); }
  ctx.restore(); }
function laptop(x, y, s, col, a = 1) { if (a <= 0) return; ctx.save(); ctx.globalAlpha = a; rrect(x - 46 * s, y - 62 * s, 92 * s, 58 * s, 6 * s); ctx.fillStyle = tone(col, .7); ctx.fill(); ctx.strokeStyle = col; ctx.lineWidth = 1.5; ctx.stroke();
  ctx.fillStyle = tone(col, .5); ctx.beginPath(); ctx.moveTo(x - 58 * s, y); ctx.lineTo(x + 58 * s, y); ctx.lineTo(x + 48 * s, y - 4 * s); ctx.lineTo(x - 48 * s, y - 4 * s); ctx.closePath(); ctx.fill(); ctx.stroke();
  ctx.strokeStyle = tone(col, .2); ctx.lineWidth = 2; for (let i = 0; i < 3; i++) { ctx.beginPath(); ctx.moveTo(x - 32 * s, y - 48 * s + i * 13 * s); ctx.lineTo(x + (i === 2 ? 2 : 26) * s, y - 48 * s + i * 13 * s); ctx.stroke(); } ctx.restore(); }
function cartridge(x, y, w, h, label, col, o = {}) {   // swappable runtime module (pins at bottom)
  const a = o.a ?? 1; if (a <= 0) return; ctx.save(); ctx.globalAlpha = a;
  ctx.fillStyle = tone(col, .5); for (let i = 0; i < 5; i++) ctx.fillRect(x + w * .15 + i * w * .16, y + h, w * .07, 12);
  rrect(x, y, w, h, 10); ctx.fillStyle = tone(col, o.dim ? .82 : .6); ctx.fill(); ctx.strokeStyle = o.dim ? rgba(col, .4) : col; ctx.lineWidth = 1.6; ctx.stroke();
  rrect(x + 10, y + 10, w - 20, 10, 5); ctx.fillStyle = tone(col, .35); ctx.fill(); ctx.restore();
  txt(x + w / 2, y + h / 2 + 8, label, { size: o.size || 18, weight: 700, color: o.dim ? C.muted : C.text, align: 'center', a });
}
function mapSheet(x, y, w, h, col, o = {}) {   // stylised map: contour grid + nodes/edges, progress k reveals
  const a = o.a ?? 1, k = o.k ?? 1; if (a <= 0) return; ctx.save(); ctx.globalAlpha = a;
  rrect(x, y, w, h, 14); ctx.fillStyle = tone(col, .86); ctx.fill(); ctx.strokeStyle = rgba(col, .7); ctx.lineWidth = 1.5; ctx.stroke();
  ctx.save(); rrect(x, y, w, h, 14); ctx.clip();
  ctx.strokeStyle = rgba(col, .18); ctx.lineWidth = 1; for (let i = 1; i < 6; i++) { ctx.beginPath(); for (let xx = 0; xx <= w; xx += 10) { const yy = y + h * i / 6 + Math.sin(xx / 60 + i) * 10; xx ? ctx.lineTo(x + xx, yy) : ctx.moveTo(x, yy); } ctx.stroke(); }
  const N = o.nodes || [[.2, .3], [.45, .2], [.7, .35], [.3, .65], [.6, .7], [.85, .6]]; const E = o.edges || [[0, 1], [1, 2], [0, 3], [3, 4], [4, 5], [2, 5], [1, 4]];
  const n = Math.round(E.length * k); ctx.strokeStyle = rgba(col, .8); ctx.lineWidth = 2;
  E.slice(0, n).forEach(([p, q]) => { ctx.beginPath(); ctx.moveTo(x + N[p][0] * w, y + N[p][1] * h); ctx.lineTo(x + N[q][0] * w, y + N[q][1] * h); ctx.stroke(); });
  N.forEach((p, i) => { if (i / N.length > k + .01) return; ctx.beginPath(); ctx.arc(x + p[0] * w, y + p[1] * h, o.r || 8, 0, Math.PI * 2); ctx.fillStyle = tone(col, .3); ctx.fill(); ctx.strokeStyle = col; ctx.stroke(); });
  ctx.restore(); ctx.restore();
}
function coins(x, y, n, col, a = 1) { if (a <= 0) return; ctx.save(); ctx.globalAlpha = a; for (let i = 0; i < n; i++) { const yy = y - i * 9; ctx.beginPath(); ctx.ellipse(x, yy, 28, 9, 0, 0, Math.PI * 2); ctx.fillStyle = tone(col, i === n - 1 ? .3 : .55); ctx.fill(); ctx.strokeStyle = col; ctx.lineWidth = 1.2; ctx.stroke(); } ctx.restore(); }
function signal(x, y, w, amp, t, col, a = 1) { if (a <= 0) return; ctx.save(); ctx.globalAlpha = a; ctx.strokeStyle = col; ctx.lineWidth = 2.2; ctx.beginPath(); for (let i = 0; i <= w; i += 3) { const e = Math.exp(-Math.pow((i - w * .6) / (w * .18), 2)); const yy = y + Math.sin(i / 6 + t * 10) * (3 + amp * e); i ? ctx.lineTo(x + i, yy) : ctx.moveTo(x, yy); } ctx.stroke(); ctx.restore(); }
function machine(x, y, w, h, col, t, o = {}) {   // factory equipment (front), optional shake
  const a = o.a ?? 1; if (a <= 0) return; const sh = o.shake ? Math.sin(t * 40) * 2 : 0; ctx.save(); ctx.globalAlpha = a; ctx.translate(sh, 0);
  rrect(x, y + h * .25, w, h * .75, 10); ctx.fillStyle = tone(col, .62); ctx.fill(); ctx.strokeStyle = col; ctx.lineWidth = 1.6; ctx.stroke();
  rrect(x + w * .15, y, w * .35, h * .3, 6); ctx.fill(); ctx.stroke();
  ctx.beginPath(); ctx.arc(x + w * .7, y + h * .6, h * .17, 0, Math.PI * 2); ctx.fillStyle = tone(col, .4); ctx.fill(); ctx.stroke();
  ctx.fillStyle = tone(col, .4); ctx.fillRect(x + w * .12, y + h * .5, w * .3, 6); ctx.fillRect(x + w * .12, y + h * .62, w * .22, 6); ctx.restore();
}
function crane(x, groundY, s, k, a = 1) {   // construction crane building a frame (k = progress)
  if (a <= 0) return; ctx.save(); ctx.globalAlpha = a; ctx.strokeStyle = C.butter; ctx.lineWidth = 3;
  ctx.beginPath(); ctx.moveTo(x, groundY); ctx.lineTo(x, groundY - 220 * s); ctx.lineTo(x + 170 * s, groundY - 220 * s); ctx.moveTo(x - 40 * s, groundY - 220 * s); ctx.lineTo(x, groundY - 220 * s); ctx.stroke();
  for (let i = 0; i < 8; i++) { ctx.beginPath(); ctx.moveTo(x - 8 * s, groundY - i * 27 * s); ctx.lineTo(x + 8 * s, groundY - (i + 1) * 27 * s); ctx.stroke(); }
  ctx.lineWidth = 1.5; ctx.beginPath(); ctx.moveTo(x + 140 * s, groundY - 220 * s); ctx.lineTo(x + 140 * s, groundY - 220 * s + 60 * s + 40 * s * Math.sin(k * 6)); ctx.stroke();
  ctx.strokeStyle = rgba(C.butter, .6); const fl = Math.floor(k * 4); for (let i = 0; i < fl; i++) ctx.strokeRect(x + 90 * s, groundY - (i + 1) * 30 * s, 100 * s, 30 * s);
  ctx.restore(); }
function bigNum(x, y, s, sz, col, a = 1) { txt(x, y, s, { size: sz, weight: 800, color: col, align: 'center', a }); }
