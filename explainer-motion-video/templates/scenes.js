// ===== demo episode: replace with your own scenes =====
// Each scene: function ID(R, t, L) — R = registry for verification, t = scene time (s), L = line start times (scene-relative)
// Rules: frame is a pure function of t · register every shape a line could hit (box/reg/caption) · call caption only when a > 0
//        crossfading beats must not overlap in time · keep everything above the subtitle zone (y < 930)
const CH1 = '1막 · 문제', CH2 = '맺음';

function D0(R, t, L) {   // silent title (6.5 s)
  const a = ap(t, .3, .9);
  txt(150, 330, '시리즈 이름 · 편 이름', { size: 22, weight: 700, color: C.blue, a });
  ctx.globalAlpha = a; ctx.fillStyle = C.blue; ctx.fillRect(150, 360, 36, 3); ctx.globalAlpha = 1;
  txt(150, 460, '큰 제목 첫 줄', { size: 76, weight: 800, color: C.text, a: ap(t, .6, .9) });
  txt(150, 565, '강조 둘째 줄', { size: 76, weight: 800, color: C.blue, a: ap(t, .9, .9) });
  txt(150, 665, '부제 한 줄', { size: 30, weight: 500, color: C.muted, a: ap(t, 1.6, .9) });
  for (let i = 0; i < 16; i++) { const an = i / 16 * TAU + t * .3; miniBot(1340 + Math.cos(an) * 170, 540 + Math.sin(an) * 140, 1.3, C.sky, ap(t, 1 + i * .05, .3)); }
  person(1340, 600, 1.6, C.mint, { a: ap(t, .8, .6) });
}

function D1(R, t, L) {   // illustration first, a small verified system diagram second
  header(CH1, '사람이 병목이 되는 구조', t);
  const a0 = ap(t, L[0], .6);
  person(330, 720, 1.5, C.peach, { a: a0 });
  const nq = Math.round(6 * ap(t, L[0] + 1, 3));
  for (let i = 0; i < nq; i++) { ctx.save(); ctx.globalAlpha = a0; rrect(450 + i * 44, 520, 36, 48, 6); ctx.fillStyle = tone(C.rose, .6); ctx.fill(); ctx.strokeStyle = C.rose; ctx.stroke(); ctx.restore(); }
  caption(R, 'cBn', 330, 800, '결국 *사람이 병목*', { align: 'center', size: 28, color: C.text, hl: C.rose, a: a0 * ap(t, L[0] + 3, .5) });
  const a1 = ap(t, L[1], .6);
  box(R, 'goal', 1000, 300, 300, 84, { label: '목표 · 기준', col: C.butter, a: a1, fillA: .2, lsize: 26 });
  box(R, 'ag', 1500, 300, 320, 84, { label: 'AI 에이전트', col: C.sky, a: a1 * ap(t, L[1] + .8, .5), fillA: .2, lsize: 26 });
  box(R, 'chk', 1000, 500, 300, 84, { label: '사람이 검증', col: C.mint, a: a1 * ap(t, L[1] + 1.6, .5), fillA: .2, lsize: 26 });
  box(R, 'bld', 1500, 500, 320, 84, { label: '설계 · 구현 · 테스트', col: C.sky, a: a1 * ap(t, L[1] + 1.2, .5), lsize: 24 });
  link(R, 'goal', 'ag', { p: a1 * ap(t, L[1] + .8, .5), col: C.butter, label: '맡긴다', lsize: 19, lcol: C.text });
  link(R, 'ag', 'bld', { fs: 'b', ts: 't', p: a1 * ap(t, L[1] + 1.2, .5), col: C.sky });
  link(R, 'bld', 'chk', { fs: 'l', ts: 'r', p: a1 * ap(t, L[1] + 1.6, .5), col: C.sky });
  link(R, 'chk', 'goal', { fs: 't', ts: 'b', p: a1 * ap(t, L[1] + 2.2, .5), col: C.mint, label: '보완 지시', lsize: 19, lcol: C.text });
}

function D2(R, t, L) {   // closing: last line as big text (main.js NOSUB_LAST hides its subtitle)
  const a = ap(t, L[0] + .1, .8);
  txt(960, 480, '기억에 남을 마지막 한 문장,', { size: 52, weight: 800, color: C.text, align: 'center', a });
  txt(960, 600, '*강조*로 끝낸다.', { size: 60, weight: 800, color: C.text, hl: C.blue, align: 'center', a: ap(t, L[0] + 1, .8) });
}

window.SCENE_FNS = { D0, D1, D2 };
window.NOSUB_LAST = 1;
