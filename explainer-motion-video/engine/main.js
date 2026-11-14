// ===== timeline & entry points (generic) =====
// Requires: TM (timing.js), scene functions registered in window.SCENE_FNS = { ID: fn, ... }
// Options:  window.FONT_SCALE (default 1.22), window.NOSUB_LAST (number of final lines shown only as big on-screen text)
const cv = document.getElementById('c'); cv.width = W; cv.height = H;
const ctx = cv.getContext('2d');
{ const k = window.FONT_SCALE ?? 1.22; if (k !== 1) { const _f = font; font = (sz, wt) => _f(sz * k, wt); } }
const FN = window.SCENE_FNS;
const SCENES = TM.map(s => ({ ...s, fn: FN[s.id], L: s.lines.map(l => l.s) }));
const TOTAL = SCENES.reduce((a, s) => a + s.dur, 0);
const NOSUB = (n => new Set(n ? TM.at(-1).lines.slice(-n).map(l => l.n) : []))(window.NOSUB_LAST || 0);
function sceneAt(t) { for (const s of SCENES) if (t < s.t0 + s.dur) return s; return SCENES.at(-1); }
function drawScene(s, lt) {
  const R = newReg(); background();
  s.fn(R, lt, s.L);
  let sub = ''; for (const l of s.lines) for (const [a, b, tx] of l.subs) if (lt >= a - .05 && lt < b + .35 && !NOSUB.has(l.n)) sub = tx;
  subtitle(sub);
  if (s !== SCENES[0]) progress((s.t0 + lt) / TOTAL);
  const fin = s.noIn ? 0 : 1 - clamp(lt / .45), fout = s.noOut ? 0 : clamp((lt - (s.dur - .5)) / .5);
  const k = Math.max(fin, fout); if (k > 0) { ctx.fillStyle = rgba(C.bg, k); ctx.fillRect(0, 0, W, H); }
  return R;
}
window.SC = SCENES; window.TOTAL = TOTAL;
window.drawAt = t => { const s = sceneAt(t); return drawScene(s, t - s.t0); };
window.still = (id, lt) => { const s = SCENES.find(x => x.id === id); drawScene(s, lt); return cv.toDataURL('image/png'); };
window.verifyAll = (step = .5, only) => {
  const issues = new Map();
  for (const s of SCENES) { if (only && !only.includes(s.id)) continue; for (let lt = .5; lt <= s.dur - .5; lt += step) { const R = drawScene(s, lt); verify(R, s.id).forEach(x => { if (!issues.has(x)) issues.set(x, lt.toFixed(1)); }); } }
  return [...issues].map(([k, v]) => k + ' @' + v);
};
(async () => {
  const f = new FontFace(FONT, 'url(node_modules/pretendard/dist/web/variable/woff2/PretendardVariable.woff2)', { weight: '45 920' });
  await f.load(); document.fonts.add(f); await document.fonts.ready;
  window.ready = true;
})();
