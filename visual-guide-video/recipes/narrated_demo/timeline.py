"""레시피: 내레이션이 이끄는 시연 영상 — 타임라인. (cuts.py · narr.txt · narr_len.json 과 한 묶음)

    python "$SKILL_DIR/scripts/build.py" timeline.py --preview-out 3,12,40       # 출력 시각 미리보기 (sheet 를 Read)
    python "$SKILL_DIR/scripts/render_segmented.py" timeline.py --seg 600 --workers 1   # 최종 (메모리 아낌 · 이어하기)
    python "$SKILL_DIR/scripts/voice_pack.py" timeline.py                        # 외부 성우용 대본·타임라인

연출 원칙 (사용자 피드백으로 굳어진 것)
  - BGM 없음, 내레이션 + 자막 + 시선 유도(정지 화면마다 강조 박스 한 곳). 효과음은 전환 whoosh 정도만.
  - 줌은 입력 글을 읽을 때만(type_zoom). 결과 화면은 full + 강조 박스.
  - 강조 박스는 그 내용을 말하는 자막과 같은 순간에 뜬다(늦게 뜨면 어색) — hl(t0=…) 로 맞춘다.
  - 챕터 카드는 2초 남짓이라 보조 글은 못 읽는다 → 제목만 크게(CHAPTER_TITLE_SIZE), 시각 칩은 「🕗 08:50」 처럼 짧게.
  - 누구 화면인지 늘 보이게(people: 테두리 + 이름판), 사람이 바뀌면 밀어내기 전환.
  - 이메일·로그인 ID·사내 링크는 BLUR. 지어낸 숫자가 나오면 고정 고지 문구(DISCLAIMER).
  - 슬레이트(제목·간지)는 무음 — 발표자가 말한다. 배속 배지는 이름판과 겹치므로 끈다.
  - 쉬운 말로. 「고리가 닫힌다」 같은 추상어, 「코드 0줄」 같은 과장 대신 「코딩 없이」.
"""
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.expanduser("~"), ".claude", "skills", "visual-guide-video", "scripts"))
import narrcuts  # noqa: E402
import overlays  # noqa: E402
import people  # noqa: E402
import recut  # noqa: E402

C = recut.load(os.path.join(_HERE, "cuts.py"))
O, S, E, B = C.O, C.S, C.E, C.B
N = json.load(open(os.path.join(_HERE, "narr_len.json"), encoding="utf-8"))
L0 = 0.25  # 컷 시작 → 말 시작 (cuts 의 Planner lead 와 같게)

# ============================================================ 기본
PROFILE = "screen"
SRC = C.edit_rel(__file__)
OUTPUT = "output/demo_v1.mp4"
FPS = 30
QUALITY = 20
THEME = dict(accent=(255, 184, 28), cyan=(124, 134, 255), green=(72, 214, 150))
CAPTION = dict(size=40, bottom=36)
FADE_OUT = 1.0
TITLE = None
PROGRESS = True

# ============================================================ 스토리 그래픽
SLATES = [
    dict(range=(S("cast"), E("cast")), bg="navy", chip="🐝 제품 시연", title="우리 팀의 [하루]", title_size=104,
         sub="실적을 맡은 나 · 대시보드를 만드는 동료 · 회사 전체를 보는 관리자",
         tokens=[("👤", "나"), ("🧑", "동료"), ("🛡️", "관리자")]),
    dict(range=(S("problem"), E("problem")), bg="navy", chip="출발점",
         title="AI가 있어도, 연결은 [여전히 사람]", title_size=84,
         lines=["— 정보 모으기: 메일 · 일정 · 공지를 하나씩 열어 정리",
                "— 매번 설명하기: 대화마다 나와 우리 팀을 처음부터",
                "— 노하우는 사람 머릿속에만"]),
    dict(range=(S("slate"), E("slate")), bg="navy", chip="🐝 오후", top=215,
         title="나의 [요령]이 자산이 되는 과정", title_size=88,
         sub="하루의 일이 모두 한곳에서 이루어지면",
         lines=["자료와 행동뿐 아니라 대화 속 [요령]까지 회사의 자산이 됩니다",
                "지금부터 그 과정을 보여 드립니다"]),
]
CHAPTER_CARD = 2.3
CHAPTER_TITLE_SIZE = 112   # 보조 글 없이 제목만 크게 (길면 자동으로 줄어듦)
CHAPTERS = [
    (S("a_ask"), "01", "출근 — 나를 아는 비서", ""),
    (S("b_ask"), "02", "대화로 만드는 대시보드", ""),
    (S("c_console"), "03", "관리자 — 회사 전체 관리", ""),
]
CLOCKS = {S("a_ask"): "🕗  08:50", S("b_ask"): "🕥  10:30"}   # 챕터 카드 위 시각 칩
NOTICES = [(S("a_rule"), "⏭ 대기 30초 생략", 1.6)]
TAGS = []      # 이름판(people)이 대신한다
BADGES = []    # 배속 배지는 이름판과 겹쳐서 끔

# 화면 주인 — (출력 시작, 끝, 인물키). 장 중간에 사람이 바뀌는 곳은 컷 경계여야 한다(밀어내기).
people.set_people({"me": ("👤", "나", THEME["cyan"]), "peer": ("🧑", "동료", THEME["green"]),
                   "admin": ("🛡️", "관리자", (200, 205, 220))})
PERSONS = [
    (S("a_ask"), E("a_rule"), "me"),
    (S("b_ask"), E("b_app"), "peer"),
    (S("b_deploy"), E("b_deploy"), "me"),
    (S("c_console"), E("c_repeat"), "admin"),
]

# ============================================================ 카메라 — 줌은 입력 글을 읽을 때만
ZIN, ZOUT = 0.9, 0.7


def type_zoom(cid, cx, cy, z, t_in=None, t_out=None):
    a = (B(cid) + 0.15) if t_in is None else t_in
    b = (E(cid) - ZOUT - 0.05) if t_out is None else t_out
    return [(a, ZIN, cx, cy, z), (b, ZOUT, "full")]


SHOTS = [(0.0, 0.0, "full")]
SHOTS += type_zoom("a_ask", 1190, 700, 1.7)      # 입력창 중심 (crops.py 로 잰 원본 좌표)
SHOTS += type_zoom("b_ask", 1195, 625, 1.6)
SHOTS.sort(key=lambda s: s[0])


# ============================================================ 시선 유도: 정지 화면마다 강조 박스 한 곳
def hl(cid, rect, label, col="accent", place="right", a=0.45, b=0.3, t0=None, t1=None):
    return ((S(cid) + a) if t0 is None else t0, (E(cid) - b) if t1 is None else t1, rect, label, col, place)


def split_at(cid, k=0.5):
    return S(cid) + (E(cid) - S(cid)) * k


HIGHLIGHTS = [
    hl("a_brief", (510, 215, 1560, 620), "📅 정한 일 · 담당 · 기한", "cyan", "below"),
    hl("a_rule", (520, 732, 1480, 764), "💬 회의 자료가 필요하신가요?", "accent", "above"),
    hl("b_app", (965, 175, 1890, 812), "📊 계획 · 실적 · 차트", "green", "left", t1=split_at("b_app", 0.5)),
    hl("b_deploy", (522, 445, 1582, 925), "🚀 「저장하고 배포해 줘」", "green", "left", t0=B("b_deploy") + 0.3),
    hl("c_console", (276, 162, 1724, 211), "🗂️ 심사 · 회사 규칙 · 회사 지식 · 공유 심사", "accent", "below", t0=B("c_console") + 0.4),
    hl("c_repeat", (285, 715, 1890, 1000), "🔁 반복 업무 패턴 — 발견되면 여기에", "cyan", "above"),
]
# 기능 목록 카드 — 문장의 그 단어가 나올 때 뜨게 (예: 문장 중간 = 길이 × 0.5)
CARDS = [
    (split_at("b_app", 0.52), E("b_app") - 0.3, "🗣️", "대화로 만드는 자산", ["📱 앱 · 대시보드", "📄 문서", "📊 슬라이드"], None),
]
CARD_POS = (1884, 250)
CLICKS = []

# ============================================================ 개인정보 가림 + 고정 고지 + 시각 칩
BLUR = [
    (S("b_deploy"), E("b_deploy"), (392, 170, 545, 206)),   # 로그인 ID (원본 좌표)
]
DISCLAIMER = "※ 화면의 숫자는 모두 지어낸 예시입니다"

_CHS = [c[0] for c in CHAPTERS]
CUSTOM_FRAME_FX = [overlays.make_blur_fx(BLUR),
                   people.make_push_fx(os.path.join(_HERE, "build", "edit.mp4"), people.push_list(PERSONS, _CHS, CHAPTER_CARD))]
CUSTOM_LAYERS = [
    overlays.make_disclaimer_layer(DISCLAIMER, spans=[(S("b_ask"), E("c_repeat"))], skip=[(S("slate"), E("slate"))]),
    overlays.make_clock_layer(CLOCKS, card=CHAPTER_CARD),
    people.make_person_layer(PERSONS, _CHS, CHAPTER_CARD, mode="push"),
    # people.make_signboard_layer(S("office"), E("office"), "에이전트 모니터링룸"),   # 특정 장면 간판
]
SWITCH_TIMES = people.switch_times(PERSONS, _CHS, CHAPTER_CARD, mode="push")

# ============================================================ 내레이션 · 자막 (원고는 narr.txt 한 곳에서)
TEXT = narrcuts.read_narr("narr.txt", __file__)
AT = {   # 문장이 놓인 컷 — 챕터 첫 컷은 B()(카드 뒤), 나머지는 S()
    "p1": S("problem"),
    "a1": B("a_ask"), "a2": S("a_brief"), "a3": S("a_rule"),
    "b1": B("b_ask"), "b2": S("b_app"), "b3": B("b_deploy"),
    "c1": B("c_console"), "c2": S("c_repeat"),
    "z1": S("outro"),
}
NARRATION, SUBTITLES = narrcuts.narration_and_subs(TEXT, AT, N, lead=L0)

OUTRO = dict(start=S("outro") + 0.3, top=250, chip="🐝 제품", title="나는 [가치 있는 일]에, 나머지는 [비서]에게",
             stats=[("🗣️", "말로 만든다", "코딩 없이"), ("🏢", "회사에 남긴다", "노하우가 자산으로"),
                    ("🧠", "나를 닮는다", "나를 아는 비서")])

# ============================================================ 오디오: BGM 없음
VOICE = dict(enabled=True, provider="edge", voice="ko-KR-SunHiNeural", rate="+18%", gain_db=1.5)
MUSIC = dict(enabled=False)
SOURCE_AUDIO = dict(enabled=False)
SFX = ([(c[0] + 0.05, "whoosh", 0.4) for c in CHAPTERS]
       + [(t + 0.02, "whoosh", 0.22) for t in SWITCH_TIMES]
       + [(S("slate") + 0.1, "whoosh", 0.35), (S("outro") + 0.4, "bling", 0.35)])
SFX_VOLUME = 0.5

# ============================================================ 외부 성우용 패키지 (voice_pack.py)
VOICE_READ = [("AI", "에이아이")]                      # 영어·약어 → 소리 나는 대로
VOICE_SILENT = [("오프닝 제목(발표자)", S("cast"), E("cast")), ("간지(발표자)", S("slate"), E("slate"))]
