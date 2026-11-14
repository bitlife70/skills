// ===== reusable illustration helpers (collected from the series) =====

const TAU = Math.PI * 2;

// example process stations for flow(): [label, icon key]

const ST = [['주문', 'order'], ['제강', 'ladle'], ['열연', 'hot'], ['냉연', 'cold'], ['출하', 'truck'], ['운송', 'ship']];

function tower(x, g, w, h, col, a = 1) {
  if (a <= 0) return; ctx.save(); ctx.globalAlpha = a; rrect(x, g - h, w, h, [8, 8, 0, 0]); ctx.fillStyle = tone(col, .62); ctx.fill(); ctx.strokeStyle = col; ctx.lineWidth = 1.5; ctx.stroke();
  for (let yy = g - h + 16; yy < g - 26; yy += 30) for (let xx = x + 12; xx < x + w - 18; xx += 26) { ctx.fillStyle = ((xx + yy) % 3 === 0) ? tone(C.butter, .5) : tone(col, .78); ctx.fillRect(xx, yy, 14, 14); }
  ctx.restore();
}

function iconCircle(x, y, r, k, col, a = 1, o = {}) {
  if (a <= 0) return; ctx.save(); ctx.globalAlpha = a; ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2); ctx.fillStyle = tone(col, o.dark ?? .55); ctx.fill(); ctx.strokeStyle = col; ctx.lineWidth = 2; ctx.stroke(); ctx.restore();
  ctx.save(); ctx.globalAlpha = a; glyph(k, x, y, r / 30, o.gc || C.text); ctx.restore();
}

function mixC(a, b, k) { return mix(a, b, clamp(k)); }


function toolbox(x, y, s, col, a = 1) {
  if (a <= 0) return; ctx.save(); ctx.globalAlpha = a; ctx.translate(x, y); ctx.scale(s, s);
  rrect(-34, -14, 68, 40, 6); ctx.fillStyle = tone(col, .6); ctx.fill(); ctx.strokeStyle = col; ctx.lineWidth = 1.6; ctx.stroke();
  ctx.beginPath(); ctx.moveTo(-14, -14); ctx.lineTo(-14, -24); ctx.lineTo(14, -24); ctx.lineTo(14, -14); ctx.stroke();
  ctx.fillStyle = tone(col, .35); ctx.fillRect(-34, 0, 68, 5); ctx.restore();
}

function headProfile(x, y, s, col, a = 1) {   // big human head + shoulders, facing right
  if (a <= 0) return; ctx.save(); ctx.globalAlpha = a; ctx.translate(x, y); ctx.scale(s, s);
  ctx.beginPath(); ctx.moveTo(-90, 170); ctx.quadraticCurveTo(-95, 90, -40, 80); ctx.lineTo(40, 80); ctx.quadraticCurveTo(95, 90, 90, 170); ctx.closePath(); ctx.fillStyle = tone(col, .62); ctx.fill();
  ctx.beginPath(); ctx.arc(0, 0, 70, 0, Math.PI * 2); ctx.fillStyle = tone(col, .5); ctx.fill(); ctx.fillRect(-18, 55, 36, 30);
  ctx.restore();
}

function aiFigure(R, cx, top, s, t, hi, a = 1) {   // compact AI employee; hi = [brain/body, hands, knowledge] glow 0..1
  if (a <= 0) return; const X = x => cx + x * s, Y = y => top + y * s;
  const glow = (k, col, fn) => { if (k <= 0) return; ctx.save(); ctx.globalAlpha = a * k; ctx.strokeStyle = col; ctx.lineWidth = 4; fn(); ctx.stroke(); ctx.restore(); };
  // halo (knowledge)
  const N = [[-148, 26], [-110, -39], [-40, -72], [40, -72], [110, -39], [148, 26], [0, -34]], E = [[0, 1], [1, 2], [2, 3], [3, 4], [4, 5], [1, 6], [6, 4], [2, 6], [6, 3]];
  ctx.save(); ctx.globalAlpha = a * (.55 + .45 * hi[2]); ctx.strokeStyle = rgba(C.blue, .6); ctx.lineWidth = 1.4;
  E.forEach(([p, q]) => { ctx.beginPath(); ctx.moveTo(X(N[p][0]), Y(N[p][1])); ctx.lineTo(X(N[q][0]), Y(N[q][1])); ctx.stroke(); });
  N.forEach((p, i) => { ctx.beginPath(); ctx.arc(X(p[0]), Y(p[1]), (i === 6 ? 10 : 7) * s, 0, Math.PI * 2); ctx.fillStyle = tone(C.blue, .35 - .2 * hi[2]); ctx.fill(); ctx.strokeStyle = C.blue; ctx.stroke(); });
  ctx.restore();
  // legs, arms, torso, head
  ctx.save(); ctx.globalAlpha = a; ctx.fillStyle = tone(C.sky, .68); rrect(X(-56), Y(372), 48 * s, 122 * s, 12 * s); ctx.fill(); rrect(X(8), Y(372), 48 * s, 122 * s, 12 * s); ctx.fill();
  ctx.strokeStyle = tone(C.sky, .6); ctx.lineWidth = 20 * s; ctx.lineCap = 'round'; ctx.lineJoin = 'round';
  ctx.beginPath(); ctx.moveTo(X(-110), Y(180)); ctx.lineTo(X(-168), Y(230)); ctx.lineTo(X(-218), Y(324)); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(X(110), Y(180)); ctx.lineTo(X(168), Y(230)); ctx.lineTo(X(218), Y(324)); ctx.stroke();
  rrect(X(-110), Y(142), 220 * s, 230 * s, [16 * s, 16 * s, 30 * s, 30 * s]); ctx.fillStyle = tone(C.sky, .7); ctx.fill(); ctx.strokeStyle = C.sky; ctx.lineWidth = 1.8; ctx.stroke();
  ctx.fillStyle = tone(C.sky, .7); ctx.fillRect(X(-14), Y(124), 28 * s, 20 * s);
  rrect(X(-75), Y(0), 150 * s, 126 * s, 26 * s); ctx.fillStyle = tone(C.lav, .58); ctx.fill(); ctx.strokeStyle = C.lav; ctx.stroke();
  rrect(X(26), Y(212), 54 * s, 72 * s, 6 * s); ctx.fillStyle = tone(C.blue, .35); ctx.fill(); ctx.strokeStyle = C.blue; ctx.stroke();
  ctx.restore();
  gear(X(-42), Y(248), 30 * s, C.sky, t * .9, { a }); glyph('chip', X(0), Y(62), 2.2 * s, C.text);
  token(X(-220), Y(356), 44 * s, C.mint, { a }); token(X(220), Y(356), 44 * s, C.mint, { a });
  glow(hi[0], C.lav, () => { rrect(X(-80), Y(-5), 160 * s, 136 * s, 28 * s); rrect(X(-115), Y(137), 230 * s, 240 * s, 30 * s); });
  glow(hi[1], C.mint, () => { ctx.beginPath(); ctx.arc(X(-220), Y(356), 30 * s, 0, Math.PI * 2); ctx.moveTo(X(220) + 30 * s, Y(356)); ctx.arc(X(220), Y(356), 30 * s, 0, Math.PI * 2); });
  glow(hi[2], C.blue, () => { ctx.beginPath(); ctx.ellipse(X(0), Y(-24), 175 * s, 72 * s, 0, 0, Math.PI * 2); rrect(X(21), Y(207), 64 * s, 82 * s, 8 * s); });
  reg(R, 'fig', X(-250), Y(-80), 500 * s, 610 * s);
}

function coil(x, y, r, col, a = 1) {   // steel coil, front view
  if (a <= 0) return; ctx.save(); ctx.globalAlpha = a;
  ctx.beginPath(); ctx.arc(x, y, r, 0, TAU); ctx.fillStyle = tone(col, .45); ctx.fill(); ctx.strokeStyle = col; ctx.lineWidth = 1.6; ctx.stroke();
  ctx.strokeStyle = rgba(col, .45); ctx.lineWidth = 1; for (const k of [.8, .62]) { ctx.beginPath(); ctx.arc(x, y, r * k, 0, TAU); ctx.stroke(); }
  ctx.beginPath(); ctx.arc(x, y, r * .38, 0, TAU); ctx.fillStyle = C.bg; ctx.fill(); ctx.strokeStyle = col; ctx.lineWidth = 1.4; ctx.stroke();
  ctx.restore();
}

function shipArt(x, y, s, col, a = 1, cargo) {   // hull bottom-centre at (x,y)
  if (a <= 0) return; ctx.save(); ctx.globalAlpha = a; ctx.translate(x, y); ctx.scale(s, s);
  ctx.beginPath(); ctx.moveTo(-64, -24); ctx.lineTo(70, -24); ctx.lineTo(52, 0); ctx.lineTo(-54, 0); ctx.closePath(); ctx.fillStyle = tone(col, .5); ctx.fill(); ctx.strokeStyle = col; ctx.lineWidth = 1.6 / s; ctx.stroke();
  rrect(-58, -50, 22, 26, 3); ctx.fillStyle = tone(col, .35); ctx.fill(); ctx.stroke();
  const cc = cargo || [C.butter, C.mint, C.peach];
  cc.forEach((c, i) => { rrect(-30 + i * 30, -44, 26, 20, 2); ctx.fillStyle = tone(c, .4); ctx.fill(); ctx.strokeStyle = c; ctx.stroke(); });
  ctx.restore();
}

function waves(x, y, w, t, a = 1, col = C.sky) {
  if (a <= 0) return; ctx.save(); ctx.globalAlpha = a * .7; ctx.strokeStyle = rgba(col, .6); ctx.lineWidth = 1.6;
  for (let r = 0; r < 2; r++) { ctx.beginPath(); for (let i = 0; i <= w; i += 4) { const yy = y + r * 12 + Math.sin(i / 18 + t * 2 + r) * 3; i ? ctx.lineTo(x + i, yy) : ctx.moveTo(x, yy); } ctx.stroke(); }
  ctx.restore();
}

function stIcon(k, x, y, s, col) {   // process station mini illustration (~40px at s=1)
  ctx.save(); ctx.translate(x, y); ctx.scale(s, s); ctx.strokeStyle = col; ctx.lineWidth = 2 / s; ctx.lineJoin = 'round'; ctx.lineCap = 'round';
  const F = (c, k2 = .45) => { ctx.fillStyle = tone(c, k2); ctx.fill(); ctx.stroke(); };
  if (k === 'order') { glyph('doc', 0, 0, 1.15, col); }
  else if (k === 'ladle') { ctx.beginPath(); ctx.moveTo(-16, -8); ctx.lineTo(16, -8); ctx.lineTo(11, 14); ctx.lineTo(-11, 14); ctx.closePath(); F(col); ctx.beginPath(); ctx.ellipse(0, -8, 16, 4, 0, 0, TAU); ctx.fillStyle = C.peach; ctx.fill(); ctx.beginPath(); ctx.arc(0, -10, 20, Math.PI * 1.15, Math.PI * 1.85); ctx.stroke(); }
  else if (k === 'hot') { ctx.fillStyle = tone(C.peach, .3); ctx.fillRect(-22, -2, 44, 4); for (const yy of [-10, 10]) { ctx.beginPath(); ctx.arc(0, yy, 8, 0, TAU); F(col); } }
  else if (k === 'cold') { ctx.fillStyle = tone(C.sky, .3); ctx.fillRect(-22, -1.5, 44, 3); for (const yy of [-8, 8]) { ctx.beginPath(); ctx.arc(-6, yy, 6, 0, TAU); F(col); ctx.beginPath(); ctx.arc(8, yy, 4, 0, TAU); F(col); } }
  else if (k === 'truck') { rrect(-20, -10, 24, 18, 2); F(col); ctx.beginPath(); ctx.moveTo(4, -4); ctx.lineTo(14, -4); ctx.lineTo(20, 2); ctx.lineTo(20, 8); ctx.lineTo(4, 8); ctx.closePath(); F(col, .3); for (const xx of [-12, 12]) { ctx.beginPath(); ctx.arc(xx, 11, 4, 0, TAU); ctx.fillStyle = C.bg; ctx.fill(); ctx.stroke(); } }
  else if (k === 'ship') { ctx.restore(); shipArt(x, y + 12 * s, .3 * s, col); return; }
  else if (k === 'coil') { ctx.restore(); coil(x, y, 15 * s, col); return; }
  else if (k === 'proc') { glyph('workflow', 0, 0, 1.1, col); }
  else if (k === 'equip') { glyph('gear', 0, 0, 1.15, col); }
  else if (k === 'cust') { glyph('person', 0, 0, 1.15, col); }
  ctx.restore();
}

function flow(R, t, o) {
  const a = o.a ?? 1; if (a <= 0) return;
  const xs = o.xs, y = o.y, r = o.r || 50, id = o.id || 'st';
  xs.forEach((x, i) => {
    const ai = a * (o.ap ? o.ap(i) : 1); if (ai <= 0) return;
    const hi = o.hi ? o.hi(i) : 0;
    ctx.save(); ctx.globalAlpha = ai; ctx.beginPath(); ctx.arc(x, y, r, 0, TAU); ctx.fillStyle = tone(hi > .5 ? C.blue : C.panel2, hi > .5 ? .62 : 0); ctx.fill();
    ctx.strokeStyle = hi > .5 ? C.blue : rgba(C.sky, .55); ctx.lineWidth = hi > .5 ? 2.4 : 1.6; ctx.stroke();
    stIcon(ST[i][1], x, y, r / 44, hi > .5 ? C.text : C.sky); ctx.restore();
    reg(R, id + i, x - r, y - r, 2 * r, 2 * r);
    if (o.labels !== false) txt(x, y + r + (o.ld || 28), ST[i][0], { size: o.lsize || 22, weight: 600, color: hi > .5 ? C.text : C.muted, align: 'center', a: ai });
  });
  for (let i = 0; i < xs.length - 1; i++) link(R, id + i, id + (i + 1), { col: C.gray, p: a * (o.lp ? o.lp(i) : 1), lw: 2 });
}

function cloudShape(x, y, w, h, col, a = 1) {
  if (a <= 0) return; ctx.save(); ctx.globalAlpha = a; ctx.fillStyle = tone(col, .82); ctx.strokeStyle = rgba(col, .6); ctx.lineWidth = 1.5;
  const P = [[-.3, .1, .32], [0, -.12, .4], [.3, .08, .34], [.05, .2, .36], [-.18, -.1, .28], [.2, -.14, .27]];
  ctx.beginPath(); P.forEach(([dx, dy, rr]) => { ctx.moveTo(x + dx * w + rr * h, y + dy * h); ctx.ellipse(x + dx * w, y + dy * h, rr * h * 1.25, rr * h, 0, 0, TAU); }); ctx.fill();
  ctx.restore();
}

function magnifier(x, y, s, col, a = 1) { if (a <= 0) return; ctx.save(); ctx.globalAlpha = a; ctx.strokeStyle = col; ctx.lineWidth = 4 * s; ctx.beginPath(); ctx.arc(x, y, 16 * s, 0, TAU); ctx.fillStyle = rgba(col, .12); ctx.fill(); ctx.stroke(); ctx.lineCap = 'round'; ctx.beginPath(); ctx.moveTo(x + 12 * s, y + 12 * s); ctx.lineTo(x + 26 * s, y + 26 * s); ctx.stroke(); ctx.restore(); }

function calendar(x, y, s, col, a = 1) { if (a <= 0) return; ctx.save(); ctx.globalAlpha = a; ctx.translate(x, y); ctx.scale(s, s); ctx.strokeStyle = col; ctx.lineWidth = 1.8 / s; rrect(-20, -16, 40, 36, 5); ctx.fillStyle = tone(col, .7); ctx.fill(); ctx.stroke(); ctx.fillStyle = tone(col, .3); ctx.fillRect(-20, -16, 40, 9); for (let i = 0; i < 3; i++) for (let j = 0; j < 2; j++) { ctx.fillStyle = (i === 2 && j === 1) ? col : tone(col, .45); ctx.fillRect(-14 + i * 11, -2 + j * 10, 7, 6); } ctx.restore(); }

function card(R, id, x, y, w, h, o) {   // icon + title + sub card (registered box)
  const a = o.a ?? 1; if (a <= 0) return null;
  const b = box(R, id, x, y, w, h, { col: o.col, a, fillA: o.fillA ?? .12 }); if (!b) return null;
  const dy = (1 - a) * 10;
  if (o.icon) { ctx.save(); ctx.translate(0, dy); o.icon(x + 50, y + h / 2, a); ctx.restore(); }
  const tx = x + (o.icon ? 96 : 24);
  const w1 = txt(tx, y + h / 2 - (o.sub ? 14 : 0) + dy, o.title, { size: o.size || 24, weight: 700, color: C.text, a });
  const w2 = o.sub ? txt(tx, y + h / 2 + 18 + dy, o.sub, { size: o.ssize || 18, weight: 400, color: C.muted, a }) : 0;
  b.textW = Math.max(w1, w2) + (o.icon ? 78 : 6); b.pad = 18;
  return b;
}

function chair(x, g, s, col, a = 1) { if (a <= 0) return; ctx.save(); ctx.globalAlpha = a; ctx.strokeStyle = col; ctx.fillStyle = tone(col, .55); ctx.lineWidth = 2;
  rrect(x - 30 * s, g - 70 * s, 60 * s, 12 * s, 4); ctx.fill(); ctx.stroke(); rrect(x - 30 * s, g - 130 * s, 12 * s, 60 * s, 4); ctx.fill(); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(x - 24 * s, g - 58 * s); ctx.lineTo(x - 24 * s, g); ctx.moveTo(x + 24 * s, g - 58 * s); ctx.lineTo(x + 24 * s, g); ctx.stroke(); ctx.restore(); }

function lock(x, y, s, col, a = 1) { if (a <= 0) return; ctx.save(); ctx.globalAlpha = a; ctx.strokeStyle = col; ctx.lineWidth = 3 * s; ctx.beginPath(); ctx.arc(x, y - 8 * s, 10 * s, Math.PI, 0); ctx.stroke(); rrect(x - 15 * s, y - 8 * s, 30 * s, 24 * s, 4 * s); ctx.fillStyle = tone(col, .4); ctx.fill(); ctx.lineWidth = 1.6; ctx.stroke(); ctx.restore(); }

function flag(x, g, s, col, a = 1) { if (a <= 0) return; ctx.save(); ctx.globalAlpha = a; ctx.strokeStyle = col; ctx.lineWidth = 2.5; ctx.beginPath(); ctx.moveTo(x, g); ctx.lineTo(x, g - 60 * s); ctx.stroke(); ctx.beginPath(); ctx.moveTo(x, g - 60 * s); ctx.lineTo(x + 34 * s, g - 50 * s); ctx.lineTo(x, g - 40 * s); ctx.closePath(); ctx.fillStyle = col; ctx.fill(); ctx.restore(); }

function star(x, y, r, col, a = 1) { if (a <= 0) return; ctx.save(); ctx.globalAlpha = a; ctx.beginPath(); for (let i = 0; i < 10; i++) { const an = -Math.PI / 2 + i * Math.PI / 5, rr = i % 2 ? r * .45 : r; ctx.lineTo(x + Math.cos(an) * rr, y + Math.sin(an) * rr); } ctx.closePath(); ctx.fillStyle = col; ctx.fill(); ctx.restore(); }

function miniGraph(x, y, s, t, a = 1, o = {}) {
  if (a <= 0) return;
  const N = o.N || [[-1, -.5], [-.2, -.9], [.7, -.6], [1, .2], [.3, .6], [-.6, .5], [.05, -.1]];
  const E = o.E || [[0, 1], [1, 2], [2, 3], [3, 4], [4, 5], [5, 0], [6, 0], [6, 2], [6, 4], [1, 6]];
  const k = o.k ?? 1, col = o.col || C.blue;
  ctx.save(); ctx.globalAlpha = a; ctx.strokeStyle = rgba(col, .7); ctx.lineWidth = 1.6;
  E.forEach(([p, q], i) => { const kk = clamp(k * E.length - i); if (kk <= 0) return; const A = N[p], B = N[q]; ctx.beginPath(); ctx.moveTo(x + A[0] * s, y + A[1] * s); ctx.lineTo(x + lerp(A[0], B[0], kk) * s, y + lerp(A[1], B[1], kk) * s); ctx.stroke(); });
  N.forEach((p, i) => { const r = (o.r || 7) * (i === 6 ? 1.4 : 1) * (1 + .12 * Math.sin(t * 2.5 + i)); ctx.beginPath(); ctx.arc(x + p[0] * s, y + p[1] * s, r, 0, TAU); ctx.fillStyle = tone(col, .35); ctx.fill(); ctx.strokeStyle = col; ctx.stroke(); });
  ctx.restore();
}

function miniBot(x, y, s, col, a = 1) {   // y = feet
  if (a <= 0) return; ctx.save(); ctx.globalAlpha = a; ctx.fillStyle = tone(col, .5); ctx.strokeStyle = col; ctx.lineWidth = 1.2;
  rrect(x - 9 * s, y - 30 * s, 18 * s, 13 * s, 3 * s); ctx.fill(); ctx.stroke();
  rrect(x - 7 * s, y - 15 * s, 14 * s, 15 * s, 3 * s); ctx.fill(); ctx.stroke();
  ctx.fillStyle = C.bg; ctx.fillRect(x - 5 * s, y - 26 * s, 3 * s, 3 * s); ctx.fillRect(x + 2 * s, y - 26 * s, 3 * s, 3 * s); ctx.restore();
}

function zigzagRight(x, y, h, col, a = 1) {   // rough, unfinished edge
  if (a <= 0) return; ctx.save(); ctx.globalAlpha = a; ctx.strokeStyle = col; ctx.lineWidth = 2; ctx.beginPath();
  for (let i = 0; i <= 6; i++) { const yy = y + h * i / 6, xx = x + (i % 2 ? 10 : 0); i ? ctx.lineTo(xx, yy) : ctx.moveTo(xx, yy); } ctx.stroke(); ctx.restore();
}

function arrowArc(cx, cy, r, a0, a1, col, a = 1) {
  if (a <= 0) return; ctx.save(); ctx.globalAlpha = a; ctx.strokeStyle = col; ctx.fillStyle = col; ctx.lineWidth = 2.4;
  ctx.beginPath(); ctx.arc(cx, cy, r, a0, a1); ctx.stroke();
  const x = cx + Math.cos(a1) * r, y = cy + Math.sin(a1) * r, tx = -Math.sin(a1), ty = Math.cos(a1);
  ctx.beginPath(); ctx.moveTo(x + tx * 2, y + ty * 2); ctx.lineTo(x - tx * 12 - ty * 7, y - ty * 12 + tx * 7); ctx.lineTo(x - tx * 12 + ty * 7, y - ty * 12 - tx * 7); ctx.closePath(); ctx.fill(); ctx.restore();
}

function shield(x, y, s, col, a = 1) { if (a <= 0) return; ctx.save(); ctx.globalAlpha = a; ctx.translate(x, y); ctx.scale(s, s);
  ctx.beginPath(); ctx.moveTo(0, -90); ctx.lineTo(80, -60); ctx.lineTo(70, 30); ctx.quadraticCurveTo(40, 80, 0, 100); ctx.quadraticCurveTo(-40, 80, -70, 30); ctx.lineTo(-80, -60); ctx.closePath();
  ctx.fillStyle = tone(col, .6); ctx.fill(); ctx.strokeStyle = col; ctx.lineWidth = 3 / s; ctx.stroke(); ctx.restore(); }
