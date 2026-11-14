# explainer-motion-video

사내 설득용 **가로 1920×1080 설명 모션그래픽 영상**을 만드는 Claude 스킬과 엔진입니다.
대본 검증·설득 구성 → Typecast 내레이션 → canvas 2D 일러스트 장면 → **선 자동 검증** → 장면별 렌더 → 음성·자막 합성 → 유튜브 설명/썸네일까지 한 흐름으로 다룹니다.

*A Claude skill + canvas engine for landscape explainer videos aimed at persuading internal audiences: script fact-checking, narration, illustration-first scenes, automatic line/overlap verification, per-scene rendering, mixing, subtitles and YouTube assets.*

## 구성
| 경로 | 내용 |
|---|---|
| `SKILL.md` | 스킬 문서 (작업 흐름, 설득 구조, 디자인 규칙, 검증, 전달) |
| `engine/core.js` | 팔레트·텍스트·박스·링크·헤더·자막·진행바, 검증기 `verify` |
| `engine/art.js` | 사람·로봇·창·문서·서버·달력·시계·지도 등 일러스트 |
| `engine/helpers.js` | 시리즈에서 모은 소품(카드, 미니봇 군집, 미니 그래프, 구름, 자물쇠, 깃발, 방패, 공정 라인 …) |
| `engine/main.js`, `engine/index.html` | 타임라인·자막·페이드·`verifyAll`·`still`, 글자 배율 |
| `templates/` | 예시 장면(`scenes.js`), 예시 타이밍, 썸네일 템플릿 |
| `tools/check.mjs` | 0.25초 간격 전 장면 검증 + 스틸 캡처 |
| `tools/render.mjs` | 장면별 mp4 렌더(병렬, 기존 파일 건너뜀) |
| `tools/build_timing.py` | 녹음 파일 → 줄 시작 시각·자막 분할(`src/timing.js`) |
| `tools/mix.py` | 내레이션 믹스·라우드니스·SRT·장면 연결·합성 |
| `tools/thumb.mjs` | 썸네일 PNG |

## 빠른 시작
```bash
mkdir -p proj/src && cd proj
cp ../explainer-motion-video/engine/* src/
cp ../explainer-motion-video/templates/{scenes.js,timing.js,thumb.js,thumb.html} src/
cp -r ../explainer-motion-video/tools .
(cd src && npm i pretendard@1.3.9)
SRC=src node tools/check.mjs all '[["D0",4],["D1",12],["D2",4]]' _stills   # VERIFY OK + 스틸
ONLY=D1 SRC=src node tools/render.mjs                                      # _scenes/D1.mp4
```
필요: Node 18+, Playwright(Chromium), ffmpeg, Python 3 + numpy, Pillow(썸네일 축소).
