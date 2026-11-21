"""레시피: 긴 시연 녹화 → 3~5분 발표·소개 영상 (제품/서비스 피치).

구조 (실제 16분 화면녹화 → 4분 발표 영상으로 검증)
  문제 제기(빨리감기) → 타이틀 슬레이트 → [챕터마다] 챕터 카드 → 요청(강조) → 결과(줌·강조·카드) → 다른 시스템에 반영된 화면
  → … → (선택) 문제 제기 슬레이트 → 해결 장면 → 효과 요약 슬레이트 → 관리·운영 챕터 → 아웃트로 요약
설득 포인트
  - 기술 자랑보다 '누구의 어떤 불편이 사라지는가'. 각 챕터 부제는 효과 문장으로("출근하면, 비서가 먼저 챙깁니다").
  - 사용자 입력은 자막에 [대괄호] 로 그대로 보여 주고(성우가 읽음), 결과는 강조 박스 라벨로 짧게.
  - 여러 계정이 나오면 TAGS 로 '누구 화면인지' 항상 표시. 건너뛴 대기·승인은 NOTICES 로 솔직하게 알린다.

작업 순서
  1. analyze.py 로 시트 → 장면 메모. 애매한 구간은 frames.py VIDEO a:b:1 로 1초 간격 확인.
  2. 내레이션 원고(narr.txt) → narr_len.py 로 문장 길이 측정.
  3. recipes/product_pitch_cuts.py → cuts.py 작성 → recut.py cuts.py → frames.py build/edit.mp4 로 클립 확인.
  4. 이 파일 → timeline.py, [1. 채울 값] 작성. 시각은 O(원본초) / S(클립) / E(클립).
  5. build.py --preview-out … 로 확인 → build.py --voice edge.
"""
import os

import recut

_HERE = os.path.dirname(os.path.abspath(__file__))
C = recut.load(os.path.join(_HERE, "cuts.py"))
O, S, E = C.O, C.S, C.E

# ============================================================ 1. 채울 값
PROFILE = "screen"
SRC = C.edit_rel(__file__)
OUTPUT = "output/pitch.mp4"
FPS = 30
THEME = dict(accent=(255, 184, 28), cyan=(124, 134, 255), green=(72, 214, 150))   # 브랜드 색
CAPTION = dict(size=38, bottom=40)
FADE_OUT = 0.8
TITLE = None                                  # 타이틀은 SLATES 로 (문제 제기 컷 뒤에 오므로)

PRODUCT = "🐝 Product  [제품명]"
TAGLINE = "한 줄로 말하는 [핵심 가치]"
PILLARS = [("🤖", "강점 1"), ("🧠", "강점 2"), ("🔌", "강점 3"), ("🛠️", "강점 4")]

CHAPTERS = [  # (시작, 번호, 제목, 효과 문장[, 태그 끝])
    (S("c1_ask"), "01", "첫 번째 시나리오", "누구의 어떤 불편이 사라지는지", E("c1_result")),
    (S("c2_ask"), "02", "두 번째 시나리오", "효과 문장", E("c2_result")),
]
TAGS = [(S("c1_ask"), E("c2_result"), "🙋 사용자 화면", "cyan")]
NOTICES = [(S("c2_result"), "⏭ 대기 시간 생략")]

# 자막 겸 내레이션: (시각, 문장). 사용자 발화는 [대괄호]. 시각 = 그 장면이 시작하는 출력 시각
NARRATION_LINES = [
    (0.4, "지금 우리는 여러 도구를 오가며 [찾고 옮기는 일]에 시간을 씁니다."),
    (S("title") + 1.0, "그래서 만들었습니다. [제품명]입니다."),
    (O(35.6), "[오늘 할 일 알려 줘.] 한마디면,"),
    (O(44.2), "흩어진 정보를 모아 한눈에 정리합니다."),
]

HIGHLIGHTS = [  # (t0, t1, 사각형, 라벨, 색, 배치) — 요청 입력창 / 결과 / 선제 제안
    (O(36.0), O(38.3), (864, 606, 1524, 676), "🗣️ 말로 요청", "accent", "below"),
    (O(46.0), O(51.2), (528, 430, 1250, 600), "📅 자동 정리", "cyan", "right"),
]
SHOTS = [(0.0, 0.0, "full"), (O(44.4), 0.8, 1040, 590, 1.32), (E("c1_result") - 0.3, 0.3, "full"),
         (S("outro"), 13.0, "full", 1.08)]
CARDS = []                                    # (t0, t1, 이모지, 제목, [줄…], 배지) — 기능 설명 카드
CARD_POS = (1884, 470)
OUTRO = dict(start=S("outro") + 0.6, top=230, chip="🐝 PRODUCT", title="한 문장 [마무리 메시지]",
             stats=[("🤖", "강점 1", "짧게"), ("🧠", "강점 2", "짧게"), ("🛠️", "강점 3", "짧게")],   # 부제 12자 이내
             footer="부가 강점 · 부가 강점 · 부가 강점")

# ============================================================ 2. 자동 구성 (보통 그대로)
SLATES = [dict(range=(S("title"), E("title")), bg="navy", chip="CATEGORY  ·  한 줄 분류",
               title=PRODUCT, sub=TAGLINE, tokens=PILLARS)]
CHAPTER_CARD = 2.4
BADGES = C.badges(min_speed=2)
SUBTITLES = []
NARRATION = []
for i, (t, line) in enumerate(NARRATION_LINES):
    nxt = NARRATION_LINES[i + 1][0] if i + 1 < len(NARRATION_LINES) else t + 4
    SUBTITLES.append((t, min(nxt - 0.05, t + 0.35 + len(line) / 7.5), line))   # 한국어 ≈ 7.5자/초 (narr_len 으로 보정)
    NARRATION.append((t, line))
VOICE = dict(provider="edge", voice="ko-KR-SunHiNeural", rate="+8%")
PARTICLES = [(S("title") + 0.2, E("title"), "bokeh", dict(at="screen", rate=6, alpha=0.35, sfx=False)),
             (S("outro") + 0.6, S("outro") + 3.5, "confetti", dict(at=(960, 1080), burst=90, angle=-90, jitter=40, sfx=False))]
MUSIC = dict(enabled=True, style="pop", drop=CHAPTERS[min(2, len(CHAPTERS) - 1)][0], volume=0.55, duck=0.6, end_fx="fade")
SFX = ([(c[0] + 0.05, "whoosh", 0.55) for c in CHAPTERS]
       + [(S("title") - 0.6, "riser", 0.5), (S("title") + 0.3, "boom", 0.35), (S("title") + 0.9, "bling", 0.5),
          (S("outro") + 0.6, "party_horn", 0.35)])
SFX_VOLUME = 0.85
