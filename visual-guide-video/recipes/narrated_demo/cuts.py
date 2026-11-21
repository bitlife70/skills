"""레시피: 내레이션이 이끄는 시연 영상 — 컷 파일. (timeline.py · narr.txt · narr_len.json 과 한 묶음)

여러 시연 녹화(장면 다시 찍기 포함)를 섞어 「하루 일과」 형식의 약 4분 발표 영상을 만들 때 쓴다.
정지 컷 길이는 narr_len.json(문장별 TTS 길이)에서 자동으로 정해진다 → 원고를 고치면 길이만 다시 재면 된다.

    python "$SKILL_DIR/scripts/narr_len.py" narr.txt --rate +18%     # → narr_len.json (여기 있는 건 예시 값)
    python "$SKILL_DIR/scripts/recut.py" cuts.py --list               # 클립별 편집본 시각표 · 전체 길이
    python "$SKILL_DIR/scripts/recut.py" cuts.py --workers 2          # → build/edit.mp4

  P.still(id, 원본시각, 문장키(들), 여유초, 소스, card=앞정지, min_dur=최소길이)
  P.clip(id, a, b, 배속, 문장키(들), 앞정지, 소스, extra=여유초)
  앞정지(card) = 챕터 카드(CC) 또는 화면 주인 밀어내기 전환(SW) 자리.

컷 고르는 원칙 (4분 시연 영상을 여러 번 고치며 굳어진 것)
  - 한 장면 = 한 문장. 결과 화면은 정지(still)로 두고 문장 길이만큼 보여 준다. 대기·확인 대화는 버린다.
  - 입력 타이핑은 clip 1.2~2.2배 (줌은 입력 글을 읽을 때만 — timeline 의 type_zoom).
  - 「요청 → 곧바로 추가 요청」처럼 어색한 연속 입력은 뒤의 입력만 보여 주고 앞 내용은 내레이션으로 말한다.
  - 버튼을 눌러 결과가 바뀌는 순간(적용 → 생성)은 1.0~1.2배로 천천히.
  - 슬레이트(제목·간지)는 무음 정지 — 발표자가 직접 말한다. 글을 읽을 시간(간지 8~10초)을 준다.
  - 같은 이야기에 무관한 내용(뺀 업무 등)이 화면에 남으면 다른 장면을 고르거나 timeline 의 BLUR 로 가린다.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.expanduser("~"), ".claude", "skills", "visual-guide-video", "scripts"))
import narrcuts  # noqa: E402

SOURCES = {                                   # 컷 파일 기준 상대경로
    "main": "../input/demo_main.mp4",
    "retake": "../input/demo_retake.mp4",      # 다시 찍은 장면
    "phone": "../input/demo_small.mp4",        # 크기가 다른 녹화 → SOURCE_VF 로 1920x1080 에 맞춤
}
SOURCE_VF = {"phone": "scale=1920:952:flags=lanczos,pad=1920:1080:0:64:color=white"}
DEFAULT_SOURCE = "main"
EDIT = "build/edit.mp4"
FPS = 30
AUDIO = False

CC = 2.3      # 챕터 카드 (timeline.CHAPTER_CARD 와 같게)
SW = 0.6      # 화면 주인 밀어내기 전환 (people.PUSH_DUR)
P = narrcuts.Planner("narr_len.json", __file__, fps=FPS, lead=0.25, tail=0.35, gap=0.25, default_src=DEFAULT_SOURCE)
still, clip = P.still, P.clip

CLIPS = [
    # ===== 프롤로그 (무음 제목 → 출발점)
    still("cast", 2.0, None, min_dur=4.0),
    still("problem", 2.0, "p1", 0.3),

    # ===== 01 08:50 출근 (나)
    clip("a_ask", 12.0, 18.0, 1.4, "a1", CC),          # 입력 장면 + 챕터 카드
    still("a_brief", 31.0, "a2", 0.1),
    still("a_rule", 44.0, "a3", 0.2),

    # ===== 02 10:30 대시보드 (동료 → 나: 밀어내기 전환)
    clip("b_ask", 120.0, 128.0, 2.0, "b1", CC, "phone"),
    still("b_app", 166.0, "b2", 0.2, "phone"),
    still("b_deploy", 40.0, "b3", 0.2, "retake", card=SW),

    # ===== 간지 (무음 — 발표자가 읽을 시간)
    still("slate", 1.0, None, min_dur=9.0),

    # ===== 03 관리자
    still("c_console", 300.0, "c1", 0.2, card=CC),
    still("c_repeat", 310.0, "c2", 0.3),

    # ===== 아웃트로
    still("outro", 310.0, "z1", 0.6, min_dur=7.0),
]
