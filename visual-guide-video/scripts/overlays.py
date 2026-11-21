"""시연 영상에 늘 필요한 작은 오버레이 — 개인정보 흐림 · 고정 고지 문구 · 챕터 카드 위 시각 칩.

    import overlays
    BLUR = [(S("login"), E("login"), (392, 170, 545, 206)), ...]          # (출력 시작, 끝, 원본 좌표 rect)
    CUSTOM_FRAME_FX = [overlays.make_blur_fx(BLUR)]                          # 줌을 따라 움직이는 모자이크+흐림
    CUSTOM_LAYERS = [
        overlays.make_disclaimer_layer("※ 화면의 숫자는 모두 지어낸 예시입니다",
                                       spans=[(S("e_ask"), E("g_kind"))], skip=[(S("slate2"), E("slate2"))]),
        overlays.make_clock_layer({S("a_ask"): "🕗 08:50", S("e_ask"): "🕥 10:30"}, card=CHAPTER_CARD),
    ]

블러는 렌더 단계(CUSTOM_FRAME_FX)에서 프레임에 직접 입히므로, 미리보기·최종 영상 모두에 똑같이 들어간다.
이메일·로그인 ID·사내 링크·실명 계정은 화면에 잠깐 보여도 반드시 BLUR 에 넣는다.
"""
import cv2

import gfx
import story


def make_blur_fx(regions, cell=14, soften=3):
    """CUSTOM_FRAME_FX 용 개인정보 흐림. regions = [(t0, t1, (x0, y0, x1, y1)), ...] — rect 는 원본 화면 좌표.

    ctx.view.rect() 로 현재 카메라(줌) 좌표로 바꿔서 가리므로 줌인 중에도 정확히 따라간다.
    cell: 모자이크 칸 크기(px, 클수록 더 뭉개짐) · soften: 모자이크 위 가우시안 흐림 σ.
    """
    regions = [(float(a), float(b), tuple(r)) for a, b, r in regions]

    def blur_fx(ctx):
        img = None
        for a, b, r in regions:
            if not (a <= ctx.ts <= b):
                continue
            x0, y0, x1, y1 = [int(v) for v in ctx.view.rect(r)]
            x0, y0, x1, y1 = max(0, x0), max(0, y0), min(ctx.W, x1), min(ctx.H, y1)
            if x1 - x0 < 4 or y1 - y0 < 4:
                continue
            if img is None:
                img = ctx.frame.copy()
            roi = img[y0:y1, x0:x1]
            small = cv2.resize(roi, (max(1, (x1 - x0) // cell), max(1, (y1 - y0) // cell)), interpolation=cv2.INTER_AREA)
            big = cv2.resize(small, (x1 - x0, y1 - y0), interpolation=cv2.INTER_LINEAR)
            img[y0:y1, x0:x1] = cv2.GaussianBlur(big, (0, 0), soften) if soften else big
        return img

    return blur_fx


def make_disclaimer_layer(text, spans=None, skip=(), size=19, color=(225, 229, 238), alpha=0.85, margin=(14, 10)):
    """오른쪽 아래 고정 고지 문구 (예: 「※ 화면의 ERP는 시연용 모의 시스템이며, 숫자는 지어낸 예시입니다」).

    spans: 보이는 구간 [(t0, t1)] (None 이면 내내). skip: 숨길 구간(슬레이트·간지 등).
    """
    spans = [(float(a), float(b)) for a, b in spans] if spans else None
    skip = [(float(a), float(b)) for a, b in skip]
    sp = {}

    def disclaimer_layer(ctx):
        t = ctx.t
        if spans is not None and not any(a <= t <= b for a, b in spans):
            return
        if any(a <= t <= b for a, b in skip):
            return
        if "s" not in sp:
            sp["s"] = story.text_sprite(text, size, color, False)
        ctx.cv.sprite(sp["s"], ctx.W - margin[0], ctx.H - margin[1], alpha, anchor=(1, 1))

    return disclaimer_layer


def make_clock_layer(clocks, card=2.4, xy=(196, 262), size=30):
    """챕터 카드 위에 뜨는 시각 칩. clocks = {챕터 시작(출력 시각): "🕗 08:50"}.

    「하루 일과」 형식의 시연에서 장마다 시각을 보여 준다. 글은 짧게(시각만) — 카드는 2초 남짓이라 길면 못 읽는다.
    people.make_person_layer 의 사람 칩(CHIP_XY=(196,190))이 바로 위에 온다.
    """
    items = [(float(t), txt) for t, txt in (clocks.items() if isinstance(clocks, dict) else clocks)]
    cache = {}

    def clock_layer(ctx):
        for a, txt in items:
            w = gfx.window(ctx.t, a, a + card, 0.2, 0.35)
            if not w:
                continue
            if txt not in cache:
                cache[txt] = gfx.pill_sprite(txt, size=size, fg=(240, 242, 250), bg=(18, 20, 34, 230),
                                             padx=24, pady=10, border=gfx.ACCENT)
            ctx.cv.sprite(cache[txt], xy[0], xy[1], w[0], anchor=(0, 0.5))

    return clock_layer
