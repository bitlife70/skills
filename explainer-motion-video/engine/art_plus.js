// ===== detailed illustration set (agent-factory episode) =====
// Flat pastel, one darker shade for depth, thin outline, no gradients. All pure functions of their args.
const SKIN = '#E2C6B2', HAIR = '#2E3850', PANTS = '#3A4660';
function _f(fill, stroke, lw = 1.6) { ctx.fillStyle = fill; ctx.fill(); if (stroke) { ctx.strokeStyle = stroke; ctx.lineWidth = lw; ctx.stroke(); } }
function shadowEl(x, y, w, a = .35) { ctx.save(); ctx.globalAlpha *= a; ctx.beginPath(); ctx.ellipse(x, y, w, w * .18, 0, 0, TAU); ctx.fillStyle = '#000'; ctx.fill(); ctx.restore(); }

// person with role props: o.prop = 'laptop' | 'headset' | 'tablet' | 'wrench' | 'clipboard' | 'monitor' ; o.hair = 'short'|'long'
function worker(x, g, s, col, o = {}) {
  const a = o.a ?? 1; if (a <= 0) return; ctx.save(); ctx.globalAlpha = a; ctx.translate(x, g); ctx.scale(s, s);
  shadowEl(0, 0, 30);
  // legs + shoes
  rrect(-15, -44, 13, 42, 5); _f(PANTS); rrect(2, -44, 13, 42, 5); _f(PANTS);
  rrect(-18, -6, 17, 7, 3); _f('#1E2638'); rrect(1, -6, 17, 7, 3); _f('#1E2638');
  // torso (shirt) + jacket edges
  rrect(-24, -92, 48, 52, [16, 16, 6, 6]); _f(tone(col, .35), col, 1.4);
  ctx.beginPath(); ctx.moveTo(-8, -92); ctx.lineTo(0, -80); ctx.lineTo(8, -92); ctx.closePath(); _f('#EEF2F8');
  ctx.strokeStyle = rgba(col, .8); ctx.lineWidth = 1.2; ctx.beginPath(); ctx.moveTo(0, -80); ctx.lineTo(0, -44); ctx.stroke();
  if (o.badge !== false) { rrect(7, -74, 11, 8, 2); _f(tone(col, .1)); }
  // arms
  const arm = o.prop === 'laptop' || o.prop === 'tablet' || o.prop === 'clipboard';
  rrect(-33, -88, 11, arm ? 30 : 40, 5); _f(tone(col, .45), col, 1.2);
  rrect(22, -88, 11, arm ? 30 : 40, 5); _f(tone(col, .45), col, 1.2);
  // neck + head
  if (o.hair === 'long') { rrect(-19, -132, 38, 44, [19, 19, 8, 8]); _f(HAIR); }
  ctx.fillStyle = SKIN; ctx.fillRect(-5, -100, 10, 10);
  ctx.beginPath(); ctx.arc(0, -112, 15, 0, TAU); _f(SKIN);
  ctx.beginPath(); ctx.arc(-15, -111, 3.5, 0, TAU); ctx.arc(15, -111, 3.5, 0, TAU); _f(SKIN);
  ctx.beginPath(); ctx.arc(0, -114, 15.5, Math.PI * 1.02, Math.PI * 1.98); ctx.lineTo(13, -118); ctx.quadraticCurveTo(0, -122, -13, -117); ctx.closePath(); _f(HAIR);
  ctx.fillStyle = '#2A2F3D'; ctx.beginPath(); ctx.arc(-5, -110, 1.8, 0, TAU); ctx.arc(5, -110, 1.8, 0, TAU); ctx.fill();
  // props
  const p = o.prop;
  if (p === 'laptop') { ctx.save(); ctx.translate(0, -58); rrect(-26, -4, 52, 6, 2); _f('#B9C4D6'); ctx.beginPath(); ctx.moveTo(-22, -4); ctx.lineTo(-18, -30); ctx.lineTo(18, -30); ctx.lineTo(22, -4); ctx.closePath(); _f('#C9D3E2'); ctx.beginPath(); ctx.arc(0, -17, 3, 0, TAU); _f(col); ctx.restore(); }
  if (p === 'tablet') { ctx.save(); ctx.translate(2, -66); ctx.rotate(-.12); rrect(-20, -16, 40, 28, 4); _f('#26324A', '#B9C4D6', 1.4); ctx.strokeStyle = col; ctx.lineWidth = 1.4;
    ctx.beginPath(); ctx.moveTo(-13, 4); ctx.lineTo(-3, -8); ctx.lineTo(6, 0); ctx.lineTo(13, -9); ctx.stroke(); [[-13, 4], [-3, -8], [6, 0], [13, -9]].forEach(q => { ctx.beginPath(); ctx.arc(q[0], q[1], 2.4, 0, TAU); _f(col); }); ctx.restore(); }
  if (p === 'clipboard') { ctx.save(); ctx.translate(0, -64); rrect(-15, -18, 30, 36, 3); _f('#C9A27E'); rrect(-12, -14, 24, 30, 2); _f('#F2F4F8'); rrect(-6, -21, 12, 6, 2); _f('#8A97AD');
    ctx.strokeStyle = '#8A97AD'; ctx.lineWidth = 1.4; for (let i = 0; i < 3; i++) { ctx.beginPath(); ctx.moveTo(-7, -6 + i * 8); ctx.lineTo(8, -6 + i * 8); ctx.stroke(); } ctx.strokeStyle = C.mint; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(-9, -7); ctx.lineTo(-7, -5); ctx.lineTo(-4, -9); ctx.stroke(); ctx.restore(); }
  if (p === 'headset') { ctx.strokeStyle = '#C9D3E2'; ctx.lineWidth = 3; ctx.beginPath(); ctx.arc(0, -113, 18, Math.PI * 1.05, Math.PI * 1.95); ctx.stroke(); rrect(-21, -117, 6, 12, 3); _f(col); rrect(15, -117, 6, 12, 3); _f(col);
    ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(-18, -106); ctx.quadraticCurveTo(-14, -98, -5, -100); ctx.stroke(); }
  if (p === 'wrench') { ctx.save(); ctx.translate(30, -50); ctx.rotate(.5); rrect(-3, -4, 6, 30, 2); _f('#B9C4D6'); ctx.beginPath(); ctx.arc(0, -8, 8, 0, TAU); _f('#B9C4D6'); ctx.fillStyle = tone(col, .35); ctx.fillRect(-3, -16, 6, 8); ctx.restore(); }
  ctx.restore();
}

// AI agent robot: antenna light, visor face, ear discs, chest screen, arms, wheel base
function agentBot(x, g, s, col, o = {}) {
  const a = o.a ?? 1; if (a <= 0) return; const t = o.t || 0; ctx.save(); ctx.globalAlpha = a; ctx.translate(x, g); ctx.scale(s, s);
  shadowEl(0, 0, 26);
  rrect(-20, -16, 40, 14, 7); _f(tone(col, .55), col, 1.2); ctx.beginPath(); ctx.arc(-11, -4, 5, 0, TAU); ctx.arc(11, -4, 5, 0, TAU); _f('#1E2638');
  rrect(-6, -24, 12, 10, 2); _f(tone(col, .5));
  rrect(-22, -66, 44, 44, 12); _f(tone(col, .3), col, 1.6);
  rrect(-12, -56, 24, 16, 4); _f('#1A2233'); ctx.strokeStyle = col; ctx.lineWidth = 1.6; ctx.beginPath(); ctx.moveTo(-8, -46); ctx.lineTo(-3, -46); ctx.lineTo(0, -53); ctx.lineTo(3, -44); ctx.lineTo(8, -48); ctx.stroke();
  rrect(-34, -62, 11, 30, 5); _f(tone(col, .45), col, 1.2); rrect(23, -62, 11, 30, 5); _f(tone(col, .45), col, 1.2);
  ctx.beginPath(); ctx.arc(-28.5, -30, 5.5, 0, TAU); ctx.arc(28.5, -30, 5.5, 0, TAU); _f(tone(col, .2));
  ctx.fillStyle = tone(col, .5); ctx.fillRect(-4, -72, 8, 7);
  rrect(-24, -106, 48, 36, 14); _f(tone(col, .2), col, 1.6);
  rrect(-17, -98, 34, 18, 9); _f('#1A2233');
  const bl = Math.abs(Math.sin(t * 1.3)) < .06 ? .2 : 1;
  ctx.fillStyle = col; rrect(-11, -92, 7, 6 * bl, 3); ctx.fill(); rrect(4, -92, 7, 6 * bl, 3); ctx.fill();
  ctx.beginPath(); ctx.arc(-26, -88, 5, 0, TAU); ctx.arc(26, -88, 5, 0, TAU); _f(tone(col, .45), col, 1.2);
  ctx.strokeStyle = col; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(0, -106); ctx.lineTo(0, -118); ctx.stroke();
  ctx.beginPath(); ctx.arc(0, -121, 4.5, 0, TAU); _f(o.lamp || C.mint);
  ctx.restore();
}

// factory hall: sawtooth roof, chimney smoke, window row, roller door, name plate
function factory(x, g, w, h, col, o = {}) {
  const a = o.a ?? 1; if (a <= 0) return; const t = o.t || 0; ctx.save(); ctx.globalAlpha = a;
  shadowEl(x + w / 2, g, w * .55, .3);
  const cx = x + w * .78, ch = h * (o.chimney ?? .42);
  rrect(cx - 16, g - h - ch, 32, ch + 10, 3); _f(tone(C.gray, .45), C.gray, 1.4); ctx.fillStyle = col; ctx.fillRect(cx - 16, g - h - ch + 12, 32, 6);
  for (let i = 0; i < 3; i++) { const k = ((t * .35 + i / 3) % 1), r = 10 + k * 18; ctx.save(); ctx.globalAlpha *= (1 - k) * .55; ctx.beginPath(); ctx.arc(cx + k * 30, g - h - ch - 10 - k * 60, r, 0, TAU); ctx.fillStyle = '#C9D3E2'; ctx.fill(); ctx.restore(); }
  const n = 3, tw = w / n, rh = h * .28;
  ctx.beginPath(); ctx.moveTo(x, g - h + rh); for (let i = 0; i < n; i++) { ctx.lineTo(x + i * tw, g - h); ctx.lineTo(x + (i + 1) * tw, g - h + rh); } ctx.lineTo(x + w, g); ctx.lineTo(x, g); ctx.closePath(); _f(tone(col, .5), col, 1.8);
  for (let i = 0; i < n; i++) { ctx.beginPath(); ctx.moveTo(x + i * tw + 4, g - h + 6); ctx.lineTo(x + i * tw + 4, g - h + rh - 2); ctx.lineTo(x + (i + 1) * tw - 10, g - h + rh - 2); ctx.closePath(); _f(rgba(C.sky, .55)); }
  ctx.fillStyle = tone(col, .35); ctx.fillRect(x, g - h + rh, w, 10);
  const wy = g - h + rh + 26, ww = (w - 60) / 4;
  for (let i = 0; i < 4; i++) { rrect(x + 18 + i * (ww + 8), wy, ww, 26, 4); _f(i % 2 ? rgba(C.butter, .7) : rgba(C.butter, .45)); }
  const dw = w * .3, dh = h * .38; rrect(x + w * .12, g - dh, dw, dh, [6, 6, 0, 0]); _f(tone(C.gray, .55), C.gray, 1.2);
  ctx.strokeStyle = rgba(C.gray, .9); ctx.lineWidth = 1; for (let yy = g - dh + 8; yy < g; yy += 8) { ctx.beginPath(); ctx.moveTo(x + w * .12 + 4, yy); ctx.lineTo(x + w * .12 + dw - 4, yy); ctx.stroke(); }
  if (o.label) { rrect(x + w * .5, g - dh - 6, w * .42, 34, 6); _f(tone(col, .2), col, 1.2); txt(x + w * .71, g - dh + 11, o.label, { size: o.lsize || 18, weight: 800, color: C.text, align: 'center' }); }
  ctx.restore();
}

// conveyor belt from x1 to x2 at belt-top y; items move with t
function conveyor(x1, x2, y, t, col, o = {}) {
  const a = o.a ?? 1; if (a <= 0) return; ctx.save(); ctx.globalAlpha = a;
  rrect(x1, y, x2 - x1, 18, 9); _f('#2A3449', rgba(col, .8), 1.4);
  ctx.strokeStyle = rgba(col, .45); ctx.lineWidth = 2; const off = (t * 40) % 24; for (let xx = x1 + 10 + off; xx < x2 - 6; xx += 24) { ctx.beginPath(); ctx.moveTo(xx, y + 3); ctx.lineTo(xx - 6, y + 15); ctx.stroke(); }
  for (let xx = x1 + 14; xx < x2 - 6; xx += 46) { ctx.beginPath(); ctx.arc(xx, y + 9, 5, 0, TAU); _f('#5B6880'); }
  for (let xx = x1 + 30; xx < x2; xx += 120) { rrect(xx - 4, y + 18, 8, 26, 2); _f('#3A4660'); }
  ctx.restore();
}

// database with highlight, ring bands and status LEDs
function dbArt(x, y, w, h, col, o = {}) {
  const a = o.a ?? 1; if (a <= 0) return; const t = o.t || 0; ctx.save(); ctx.globalAlpha = a; const ry = w * .17;
  shadowEl(x + w / 2, y + h + 4, w * .55, .3);
  const seg = 3, sh = (h - ry) / seg;
  for (let i = seg - 1; i >= 0; i--) { const yy = y + ry + i * sh;
    ctx.beginPath(); ctx.moveTo(x, yy); ctx.lineTo(x, yy + sh - 4); ctx.ellipse(x + w / 2, yy + sh - 4, w / 2, ry, 0, Math.PI, 0, true); ctx.lineTo(x + w, yy); ctx.ellipse(x + w / 2, yy, w / 2, ry, 0, 0, Math.PI); ctx.closePath(); _f(tone(col, .55 - i * .04), col, 1.4);
    ctx.fillStyle = rgba('#FFFFFF', .08); ctx.fillRect(x + w * .1, yy + 4, w * .1, sh - 12);
    for (let k = 0; k < 3; k++) { const on = Math.sin(t * 3 + i * 2 + k) > -.2; ctx.beginPath(); ctx.arc(x + w * .62 + k * 12, yy + sh * .55, 3.2, 0, TAU); ctx.fillStyle = on ? (k === 2 ? C.butter : C.mint) : tone(C.mint, .7); ctx.fill(); } }
  ctx.beginPath(); ctx.ellipse(x + w / 2, y + ry, w / 2, ry, 0, 0, TAU); _f(tone(col, .3), col, 1.4);
  ctx.beginPath(); ctx.ellipse(x + w / 2, y + ry, w * .3, ry * .55, 0, 0, TAU); ctx.strokeStyle = rgba(col, .7); ctx.lineWidth = 1.2; ctx.stroke();
  if (o.label) txt(x + w / 2, y + h + 26, o.label, { size: o.lsize || 18, weight: 800, color: C.text, align: 'center' });
  ctx.restore();
}

// document with folded corner, title bar, lines, mini chart and stamp
function docArt(x, y, w, h, col, o = {}) {
  const a = o.a ?? 1; if (a <= 0) return; ctx.save(); ctx.globalAlpha = a; const f = w * .2;
  shadowEl(x + w / 2, y + h + 4, w * .5, .25);
  ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x + w - f, y); ctx.lineTo(x + w, y + f); ctx.lineTo(x + w, y + h); ctx.lineTo(x, y + h); ctx.closePath(); _f('#E6ECF5', rgba(col, .9), 1.4);
  ctx.beginPath(); ctx.moveTo(x + w - f, y); ctx.lineTo(x + w - f, y + f); ctx.lineTo(x + w, y + f); ctx.closePath(); _f('#B9C4D6');
  ctx.fillStyle = col; ctx.fillRect(x + w * .1, y + h * .1, w * .5, h * .07);
  ctx.fillStyle = '#9AA6BA'; for (let i = 0; i < 4; i++) ctx.fillRect(x + w * .1, y + h * (.26 + i * .09), w * (i === 3 ? .45 : .78), h * .03);
  for (let i = 0; i < 4; i++) { const bh = h * [.1, .16, .12, .2][i]; ctx.fillStyle = tone(col, .2); ctx.fillRect(x + w * (.12 + i * .1), y + h * .9 - bh, w * .07, bh); }
  ctx.save(); ctx.translate(x + w * .74, y + h * .78); ctx.rotate(-.25); ctx.strokeStyle = C.rose; ctx.lineWidth = 2; ctx.beginPath(); ctx.arc(0, 0, w * .12, 0, TAU); ctx.stroke(); ctx.restore();
  ctx.restore();
}

// shipping crate = reusable asset box (lid, tape, label tag)
function assetCrate(x, g, s, col, o = {}) {
  const a = o.a ?? 1; if (a <= 0) return; ctx.save(); ctx.globalAlpha = a; ctx.translate(x, g); ctx.scale(s, s);
  shadowEl(0, 0, 40, .3);
  ctx.beginPath(); ctx.moveTo(-36, -56); ctx.lineTo(0, -70); ctx.lineTo(36, -56); ctx.lineTo(0, -42); ctx.closePath(); _f(tone(col, .25), col, 1.4);
  ctx.beginPath(); ctx.moveTo(-36, -56); ctx.lineTo(0, -42); ctx.lineTo(0, 0); ctx.lineTo(-36, -14); ctx.closePath(); _f(tone(col, .45), col, 1.4);
  ctx.beginPath(); ctx.moveTo(36, -56); ctx.lineTo(0, -42); ctx.lineTo(0, 0); ctx.lineTo(36, -14); ctx.closePath(); _f(tone(col, .6), col, 1.4);
  ctx.beginPath(); ctx.moveTo(-18, -63); ctx.lineTo(18, -49); ctx.lineTo(18, -42); ctx.lineTo(-18, -56); ctx.closePath(); _f(rgba(C.butter, .85));
  ctx.save(); ctx.transform(1, -.39, 0, 1, 0, 0); rrect(8, -26, 22, 14, 2); _f('#E6ECF5'); ctx.restore();
  ctx.restore();
}

// folded paper map with grid, ontology graph, dashed route and pin
function mapArt(x, y, w, h, col, o = {}) {
  const a = o.a ?? 1; if (a <= 0) return; const k = o.k ?? 1; ctx.save(); ctx.globalAlpha = a;
  shadowEl(x + w / 2, y + h + 6, w * .52, .3);
  const pw = w / 3, sk = h * .06;
  for (let i = 0; i < 3; i++) { const x0 = x + i * pw, up = i % 2 ? sk : 0; ctx.beginPath(); ctx.moveTo(x0, y + (i % 2 ? 0 : sk)); ctx.lineTo(x0 + pw, y + up); ctx.lineTo(x0 + pw, y + h + up - sk); ctx.lineTo(x0, y + h - (i % 2 ? sk : 0)); ctx.closePath(); _f(i % 2 ? tone(col, .62) : tone(col, .72), col, 1.4); }
  ctx.save(); ctx.beginPath(); for (let i = 0; i < 3; i++) { const x0 = x + i * pw, up = i % 2 ? sk : 0; ctx.moveTo(x0, y + (i % 2 ? 0 : sk)); ctx.lineTo(x0 + pw, y + up); ctx.lineTo(x0 + pw, y + h + up - sk); ctx.lineTo(x0, y + h - (i % 2 ? sk : 0)); ctx.closePath(); } ctx.clip(); ctx.strokeStyle = rgba(col, .18); ctx.lineWidth = 1; for (let xx = x + 24; xx < x + w; xx += 24) { ctx.beginPath(); ctx.moveTo(xx, y); ctx.lineTo(xx, y + h); ctx.stroke(); } for (let yy = y + 24; yy < y + h; yy += 24) { ctx.beginPath(); ctx.moveTo(x, yy); ctx.lineTo(x + w, yy); ctx.stroke(); }
  ctx.fillStyle = rgba(C.mint, .16); ctx.beginPath(); ctx.ellipse(x + w * .3, y + h * .65, w * .18, h * .16, .3, 0, TAU); ctx.fill(); ctx.restore();
  const N = [[.14, .3], [.36, .2], [.6, .34], [.84, .24], [.26, .66], [.52, .7], [.8, .7]].map(p => [x + p[0] * w, y + p[1] * h]);
  const E = [[0, 1], [1, 2], [2, 3], [0, 4], [4, 5], [2, 5], [5, 6], [3, 6], [1, 4]];
  ctx.strokeStyle = rgba(C.text, .7); ctx.lineWidth = 2; E.forEach(([p, q], i) => { const kk = clamp(k * E.length - i); if (kk <= 0) return; ctx.beginPath(); ctx.moveTo(...N[p]); ctx.lineTo(lerp(N[p][0], N[q][0], kk), lerp(N[p][1], N[q][1], kk)); ctx.stroke(); });
  if (o.route !== false) { ctx.strokeStyle = C.mint; ctx.lineWidth = 4; ctx.setLineDash([10, 7]); ctx.beginPath(); ctx.moveTo(...N[0]); ctx.lineTo(...N[4]); ctx.lineTo(...N[5]); ctx.lineTo(...N[6]); ctx.stroke(); ctx.setLineDash([]); }
  N.forEach((p, i) => { ctx.beginPath(); ctx.arc(...p, i === 5 ? 8 : 6, 0, TAU); _f(i === 5 ? C.mint : '#E6ECF5'); });
  const pin = N[6]; ctx.beginPath(); ctx.arc(pin[0], pin[1] - 26, 11, Math.PI, 0); ctx.lineTo(pin[0], pin[1] - 4); ctx.closePath(); _f(C.rose); ctx.beginPath(); ctx.arc(pin[0], pin[1] - 26, 4, 0, TAU); _f('#FBE3E7');
  ctx.restore();
}

// control room desk: 3 monitors (chart / bars / alert list), keyboard, chair
function controlDesk(x, g, s, col, o = {}) {
  const a = o.a ?? 1; if (a <= 0) return; const t = o.t || 0; ctx.save(); ctx.globalAlpha = a; ctx.translate(x, g); ctx.scale(s, s);
  shadowEl(0, 0, 150, .3);
  rrect(-150, -64, 300, 14, 4); _f('#3A4660', '#5B6880', 1.2); rrect(-138, -50, 12, 50, 2); _f('#2A3449'); rrect(126, -50, 12, 50, 2); _f('#2A3449');
  [[-100, -.12], [0, 0], [100, .12]].forEach(([mx, r], i) => { ctx.save(); ctx.translate(mx, -132); ctx.rotate(r);
    rrect(-46, -34, 92, 62, 6); _f('#1A2233', '#8D9AB2', 1.6); ctx.fillStyle = '#5B6880'; ctx.fillRect(-4, 28, 8, 26); rrect(-16, 52, 32, 5, 2); _f('#5B6880');
    if (i === 0) { ctx.strokeStyle = col; ctx.lineWidth = 2; ctx.beginPath(); for (let k = 0; k <= 16; k++) { const xx = -38 + k * 4.75, yy = 6 - Math.sin(k * .7 + t * 2) * 10 - k * .6; k ? ctx.lineTo(xx, yy) : ctx.moveTo(xx, yy); } ctx.stroke(); }
    if (i === 1) { for (let k = 0; k < 6; k++) { const bh = 10 + ((k * 37 + Math.floor(t * 2) * 13) % 30); ctx.fillStyle = k === 4 ? C.butter : tone(col, .25); ctx.fillRect(-36 + k * 12, 20 - bh, 8, bh); } }
    if (i === 2) { for (let k = 0; k < 4; k++) { ctx.fillStyle = k === 1 ? C.rose : (k === 3 ? C.butter : C.mint); ctx.beginPath(); ctx.arc(-32, -18 + k * 13, 3.5, 0, TAU); ctx.fill(); ctx.fillStyle = '#5B6880'; ctx.fillRect(-24, -20 + k * 13, 52 - k * 6, 4); } }
    ctx.restore(); });
  rrect(-40, -72, 80, 8, 2); _f('#5B6880');
  ctx.restore();
}

// ---- v2 (feedback): simpler bust person, round cute AI character ----
// bust person: head + shoulders (no legs). g = bottom of bust. props: laptop | tablet | clipboard | headset | wrench | plug | gear | none
function bust(x, g, s, col, o = {}) {
  const a = o.a ?? 1; if (a <= 0) return; ctx.save(); ctx.globalAlpha = a; ctx.translate(x, g); ctx.scale(s, s);
  rrect(-36, -54, 72, 54, [28, 28, 8, 8]); _f(tone(col, .35), col, 1.5);
  ctx.beginPath(); ctx.moveTo(-10, -54); ctx.lineTo(0, -40); ctx.lineTo(10, -54); ctx.closePath(); _f('#EEF2F8');
  if (o.hair === 'long') { rrect(-24, -106, 48, 52, [24, 24, 10, 10]); _f(HAIR); }   // back hair: one piece behind the head, falls to the shoulders
  ctx.fillStyle = SKIN; ctx.fillRect(-6, -64, 12, 12);
  ctx.beginPath(); ctx.arc(0, -82, 19, 0, TAU); _f(SKIN);
  ctx.beginPath(); ctx.arc(0, -85, 19.5, Math.PI * 1.03, Math.PI * 1.97); ctx.lineTo(16, -90); ctx.quadraticCurveTo(0, -95, -16, -89); ctx.closePath(); _f(HAIR);
  ctx.fillStyle = '#2A2F3D'; ctx.beginPath(); ctx.arc(-6, -80, 2, 0, TAU); ctx.arc(6, -80, 2, 0, TAU); ctx.fill();
  ctx.strokeStyle = '#B07A68'; ctx.lineWidth = 1.6; ctx.beginPath(); ctx.arc(0, -75, 4.5, .2 * Math.PI, .8 * Math.PI); ctx.stroke();
  const p = o.prop;
  if (p === 'laptop') { ctx.save(); ctx.translate(0, -8); ctx.beginPath(); ctx.moveTo(-26, 4); ctx.lineTo(-20, -26); ctx.lineTo(20, -26); ctx.lineTo(26, 4); ctx.closePath(); _f('#C9D3E2'); ctx.beginPath(); ctx.arc(0, -12, 3.2, 0, TAU); _f(col); ctx.restore(); }
  if (p === 'tablet') { ctx.save(); ctx.translate(0, -22); ctx.rotate(-.1); rrect(-22, -16, 44, 30, 5); _f('#26324A', '#B9C4D6', 1.4); ctx.strokeStyle = col; ctx.lineWidth = 1.6;
    const q = [[-14, 6], [-4, -7], [6, 1], [14, -9]]; ctx.beginPath(); q.forEach((v, i) => i ? ctx.lineTo(...v) : ctx.moveTo(...v)); ctx.stroke(); q.forEach(v => { ctx.beginPath(); ctx.arc(v[0], v[1], 2.6, 0, TAU); _f(col); }); ctx.restore(); }
  if (p === 'clipboard') { ctx.save(); ctx.translate(0, -22); rrect(-15, -18, 30, 34, 3); _f('#C9A27E'); rrect(-12, -14, 24, 28, 2); _f('#F2F4F8');
    ctx.strokeStyle = C.mint; ctx.lineWidth = 2; for (let i = 0; i < 3; i++) { ctx.beginPath(); ctx.moveTo(-8, -6 + i * 8); ctx.lineTo(-6, -4 + i * 8); ctx.lineTo(-3, -8 + i * 8); ctx.stroke(); ctx.fillStyle = '#9AA6BA'; ctx.fillRect(0, -7 + i * 8, 8, 2.4); } ctx.restore(); }
  if (p === 'headset') { ctx.strokeStyle = '#C9D3E2'; ctx.lineWidth = 3.2; ctx.beginPath(); ctx.arc(0, -84, 23, Math.PI * 1.05, Math.PI * 1.95); ctx.stroke(); rrect(-26, -90, 7, 14, 3); _f(col); rrect(19, -90, 7, 14, 3); _f(col);
    ctx.lineWidth = 2.2; ctx.beginPath(); ctx.moveTo(-22, -77); ctx.quadraticCurveTo(-17, -66, -7, -68); ctx.stroke(); }
  if (p === 'plug') { ctx.save(); ctx.translate(0, -22); ctx.strokeStyle = '#B9C4D6'; ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(-30, 10); ctx.quadraticCurveTo(-20, -12, -8, -4); ctx.stroke();
    rrect(-10, -14, 20, 20, 4); _f(col); ctx.fillStyle = '#E6ECF5'; ctx.fillRect(10, -10, 9, 3.5); ctx.fillRect(10, -1, 9, 3.5); ctx.restore(); }
  if (p === 'gear') { ctx.save(); ctx.translate(0, -24); ctx.beginPath(); for (let i = 0; i < 16; i++) { const an = i * Math.PI / 8, r = i % 2 ? 11 : 15; ctx.lineTo(Math.cos(an) * r, Math.sin(an) * r); } ctx.closePath(); _f('#C9D3E2'); ctx.beginPath(); ctx.arc(0, 0, 5, 0, TAU); _f(tone(col, .3)); ctx.restore(); }
  if (p === 'wrench') { ctx.save(); ctx.translate(30, -26); ctx.rotate(.45); rrect(-3.5, -6, 7, 30, 2); _f('#B9C4D6'); ctx.beginPath(); ctx.arc(0, -10, 9, 0, TAU); _f('#B9C4D6'); ctx.fillStyle = tone(col, .35); ctx.fillRect(-3.5, -19, 7, 9); ctx.restore(); }
  ctx.restore();
}

// round, friendly AI character: big round head with face screen, small egg body, stubby arms, floats
function aiPal(x, g, s, col, o = {}) {
  const a = o.a ?? 1; if (a <= 0) return; const t = o.t || 0, bob = Math.sin(t * 2.2 + x * .01) * 3; ctx.save(); ctx.globalAlpha = a; ctx.translate(x, g); ctx.scale(s, s);
  shadowEl(0, 0, 18, .3 - bob * .02);
  ctx.translate(0, bob - 8);
  ctx.beginPath(); ctx.ellipse(0, -22, 17, 15, 0, 0, TAU); _f(tone(col, .38), col, 1.5);
  ctx.beginPath(); ctx.arc(-20, -24, 6, 0, TAU); ctx.arc(20, -24, 6, 0, TAU); _f(tone(col, .25), col, 1.2);
  ctx.beginPath(); ctx.arc(0, -22, 4, 0, TAU); _f(o.lamp || C.mint);
  ctx.beginPath(); ctx.arc(0, -60, 27, 0, TAU); _f(tone(col, .18), col, 1.8);
  ctx.beginPath(); ctx.arc(-27, -60, 5, 0, TAU); ctx.arc(27, -60, 5, 0, TAU); _f(tone(col, .4), col, 1.2);
  rrect(-19, -73, 38, 26, 13); _f('#1A2233');
  const bl = Math.abs(Math.sin(t * 1.1 + x * .02)) < .07;
  ctx.fillStyle = col; if (bl) { ctx.fillRect(-11, -61, 8, 2); ctx.fillRect(3, -61, 8, 2); } else { rrect(-10.5, -66, 7, 10, 3.5); ctx.fill(); rrect(3.5, -66, 7, 10, 3.5); ctx.fill(); }
  ctx.strokeStyle = col; ctx.lineWidth = 1.8; ctx.beginPath(); ctx.arc(0, -55, 4, .15 * Math.PI, .85 * Math.PI); ctx.stroke();
  ctx.strokeStyle = col; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(0, -87); ctx.lineTo(0, -93); ctx.stroke(); ctx.beginPath(); ctx.arc(0, -96, 4.5, 0, TAU); _f(o.lamp || C.mint);
  ctx.restore();
}
