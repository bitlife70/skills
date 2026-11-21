# Changelog

## 1.3 — 2026-11-21 · 두 갈래 병합 (promo·쇼츠 + 발표·내레이션 시연)

1.0 이후 따로 발전한 두 갈래를 하나로 합쳤다.
- GitHub `bitlife70/skills` 갈래(원 저장소 `1816e61`, `5602869`): `promo` 프로필(`scripts/promo.py` — 원본 글씨 지우기·광고 타이포·낙관·먹물 전환·빛 번짐·레터박스, zen 국악풍 BGM), 세로 쇼츠 캔버스(`CANVAS`·`BACKDROP`·`SPEED_RAMP`·`slam`), `recipes/promo_film.py`·`recipes/promo_shorts.py`.
- 별도 작업 갈래: 아래 1.1·1.2 전부.

**병합 처리**
- `scripts/render.py` — 같은 자리에 양쪽이 넣은 호출을 모두 유지: `story.setup` → `promo.setup`, `story.layer` → `promo.layer_type`.
- `scripts/tl.py`, `templates/timeline_template.py` — 자동 병합(겹치는 줄 없음).
- `SKILL.md`, `README.md` — 프로필 설명·레시피 표·파일 구성·검증 문구를 양쪽 모두 담도록 합침.

**검증** (합성 테스트 영상): 같은 타임라인을 원래 엔진과 병합 엔진으로 미리보기 → 픽셀 차이 0
- `recipes/narrated_demo/` — 1.2 엔진과 동일 (8컷)
- `recipes/promo_film.py`, `recipes/promo_shorts.py` — GitHub 엔진과 동일 (각 8컷)
- 오디오 믹스(zen BGM, 내레이션 없음)·`voice_pack.py` 정상 동작

## 1.2 — 2026-11-21 · 내레이션 주도 시연 영상

여러 시연 녹화를 섞어 약 4분 발표 영상을 8차까지 고치며 프로젝트 폴더에 쌓인 도구를 스킬로 옮겼다.

**새 스크립트**
- `scripts/narrcuts.py` — 문장 길이(narr_len.json)로 컷 길이를 자동으로 정하는 `Planner.still/clip`, 원고 읽기 `read_narr`, 내레이션·자막 시각 생성 `narration_and_subs`(문장 단위 분할, [강조] 대괄호 이어 닫기).
- `scripts/people.py` — 누구 화면인지: 사람 색 테두리·이름판, 밀어내기(push)/와이프 전환, 챕터 카드 사람 칩, 매달린 간판. `set_people()` 로 등장인물 정의.
- `scripts/overlays.py` — 개인정보 흐림 `make_blur_fx`(줌을 따라감), 고정 고지 문구 `make_disclaimer_layer`, 챕터 카드 시각 칩 `make_clock_layer`.
- `scripts/render_segmented.py` — 구간마다 새 프로세스로 렌더하고 이어 붙이는 분할 렌더(메모리 누수 차단, 끊겨도 이어하기) + SRT.
- `scripts/voice_pack.py` — 외부 성우·TTS 용 내레이션 패키지: 문장별 시작·최대 길이·읽기 문장(csv/json/txt/md), `VOICE_READ`·`VOICE_SILENT`·`VOICE_ENDING`.

**바뀐 것**
- `scripts/recut.py` — `SOURCES`/`SOURCE_VF`/`DEFAULT_SOURCE` 로 여러 원본 섞기(튜플 끝에 소스 키), 소스별 전처리 필터, `O(t, src=)`, `--list` 에 소스 표시. 단일 `SRC` 컷 파일은 그대로 동작하고 원본 소리(AUDIO)도 유지.
- `scripts/story.py` — `CHAPTER_TITLE_SIZE` 옵션(기본 86): 보조 글 없이 제목만 크게 쓰면 길이에 맞춰 자동 축소, 밑줄 위치 조정.
- `templates/timeline_template.py` — `CHAPTER_TITLE_SIZE` 설명 추가.

**새 레시피**
- `recipes/narrated_demo/` (narr.txt · narr_len.json · cuts.py · timeline.py) — 하루 일과형 내레이션 주도 시연. 실제 녹화 3개로 recut → 미리보기까지 확인.

**문서**
- SKILL.md 「3-2. 내레이션 주도 시연」 절과 피드백에서 굳어진 연출 규칙(BGM 없음, 줌은 입력 글만, 강조는 자막과 같은 순간, 카드는 제목만, 무음 슬레이트, 개인정보 흐림·고지 문구 등), 분할 렌더·성우 패키지 안내.

**검증**
- 4분 시연 영상(v8)의 타임라인을 새 모듈로 바꿔 미리보기 6장을 렌더 → 원래 결과와 픽셀 차이 0, 컷 배치·자막·성우 패키지 동일.

## 1.1 — 2026-10-22 · 긴 시연 → 발표 영상

- `recut.py`(장면 재배치·배속·정지·이미지 삽입), `story.py`(슬레이트·챕터 카드·태그·알림·배지), `narr_len.py`, `frames.py`, `media.py`(VFR → CFR) 추가.
- `recipes/product_pitch.py` + `product_pitch_cuts.py` 추가. 사내 SSL 프록시용 truststore 자동 적용(voice.py).

## 1.0 — 2026-10-17

- 첫 공개: screen / game / vlog / anim 프로필, 추적, 색보정, 신스 BGM 4종, 효과음, TTS, 커스텀 훅, 병렬 렌더.
