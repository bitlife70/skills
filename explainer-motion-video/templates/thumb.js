// thumbnail drawn on the same canvas: big 2-line title left, one strong illustration right, one badge
function thumbA() {
  newReg(); background();
  ctx.save(); ctx.beginPath(); ctx.arc(1440, 560, 360, 0, TAU); ctx.fillStyle = rgba(C.blue, .07); ctx.fill(); ctx.restore();
  for (let i = 0; i < 100; i++) { const ring = Math.floor(i / 25), k = i % 25, an = -Math.PI * .95 + k / 24 * Math.PI * 1.9, r = 190 + ring * 62;
    miniBot(1440 + Math.cos(an) * r, 620 + Math.sin(an) * r * .78, 1.5 - ring * .1, ring % 2 ? C.sky : C.blue, 1 - ring * .12); }
  person(1440, 720, 2.1, C.mint, { a: 1 });
  txt(110, 250, '시리즈 · 편 이름', { size: 30, weight: 700, color: C.blue });
  txt(100, 430, '제목 첫 줄', { size: 150, weight: 900, color: C.text });
  txt(100, 640, '강조 줄', { size: 170, weight: 900, color: C.blue });
  ctx.save(); rrect(110, 760, 640, 92, 46); ctx.fillStyle = tone(C.mint, .6); ctx.fill(); ctx.strokeStyle = C.mint; ctx.lineWidth = 3; ctx.stroke(); ctx.restore();
  txt(430, 806, '핵심 숫자나 대비 한 줄', { size: 36, weight: 800, color: C.text, align: 'center' });
}
window.thumb = k => { thumbA(); return cv.toDataURL('image/png'); };
