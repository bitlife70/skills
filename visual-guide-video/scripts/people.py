"""「누구 화면인가」 연출 — 화면 주인 테두리 · 이름판 · 밀어내기(push)/와이프 전환 · 매달린 간판.
여러 사람이 차례로 등장하는 시연(나 → 동료 → 관리자 …)에서 지금 화면이 누구 것인지 한눈에 보이게 한다.
CUSTOM_LAYERS / CUSTOM_FRAME_FX 용 공장 함수만 있으므로 timeline.py 에서 골라 쓴다.

    import people
    people.set_people({"me":   ("👤", "나", THEME["cyan"]),
                       "peer": ("🧑", "동료", THEME["green"]),
                       "admin": ("🛡️", "관리자", (200, 205, 220))})
    PERSONS = [(B("a_ask"), E("a_done"), "me"), (S("e_ask"), E("e_app"), "peer"), ...]   # 출력 시각
    CHS = [c[0] for c in CHAPTERS]                     # 챕터 카드 시작 시각 (카드 안의 변경은 「칩」으로)
    TAGS = []                                          # 이름판이 TAGS 를 대신한다

  밀어내기(push) 전환 — 이전 화면이 왼쪽으로 밀리며 새 화면이 들어온다 (은은함, 권장):
    CUSTOM_FRAME_FX = [people.make_push_fx(EDIT_MP4, people.push_list(PERSONS, CHS, CHAPTER_CARD))]
    CUSTOM_LAYERS = [people.make_person_layer(PERSONS, CHS, CHAPTER_CARD, mode="push"),
                     people.make_signboard_layer(S("office"), E("office"), "에이전트 모니터링룸")]
    SFX += [(t, "whoosh", 0.25) for t in people.switch_times(PERSONS, CHS, CHAPTER_CARD, mode="push")]

  와이프 전환 — 사람 색 패널이 화면을 쓸고 지나가며 「○○의 화면」 을 크게 보여 준다:
    CUSTOM_LAYERS = [people.make_person_layer(PERSONS, CHS, CHAPTER_CARD)]       # mode="wipe"
    SFX += [(t, "whoosh", 0.35) for t in people.switch_times(PERSONS, CHS, CHAPTER_CARD)]

시각은 모두 출력 시각(ctx.t 기준). recut 편집본(TRIM/SPEED/FREEZE 없음)에서는 S()/E()/B() 값이 그대로 출력 시각이다.
push 는 사람 변경 지점이 컷 경계와 같아야 한다(이전 컷 마지막 프레임을 편집본에서 읽는다).
컷 파일에서 그 자리에 앞 정지 0.6초(PUSH_DUR)를 두면 전환 중에도 새 화면이 멈춰 있어 깔끔하다.
"""
from functools import lru_cache

import cv2
import numpy as np
from PIL import Image, ImageDraw

import gfx
import story
from gfx import W, H, clamp01, ease_back, ease_out

# ------------------------------------------------------------ 인물
# key → (이모지, 이름, RGB 색). set_people() 로 바꾼다. 렌더 전에(모듈 수준에서) 한 번만 부를 것 — 스프라이트가 캐시된다.
PEOPLE = {
    "me": ("👤", "나", (124, 134, 255)),
    "peer": ("🧑", "동료", (72, 214, 150)),
    "lead": ("👔", "팀장", (255, 184, 28)),
    "admin": ("🛡️", "관리자", (200, 205, 220)),
}


def set_people(mapping, replace=True):
    """등장인물 정의 {key: (이모지, 이름, (r, g, b))}. replace=False 면 기본값에 더한다."""
    if replace:
        PEOPLE.clear()
    PEOPLE.update(mapping)
    for f in (_plate_sprite, _chip_sprite, _edge_sprites, _wipe_title, _wipe_sub):
        f.cache_clear()


INK = (16, 18, 28)
NAVY = (14, 16, 30)

# 전환 와이프 시간 (초): 들어옴 → 정지 → 빠져나감. 화면 컷(t0) 순간에 패널이 화면을 완전히 덮도록
# 와이프는 t0 - WIPE_IN 에 시작한다 → 컷이 패널 뒤에서 일어난다.
WIPE_IN, WIPE_HOLD, WIPE_OUT = 0.3, 0.4, 0.3
SLANT = 170          # 패널 앞/뒤 가장자리 기울기(px)
EDGE = 7             # 화면 테두리 두께(px)
EDGE_ALPHA = 0.85
PLATE_XY = (20, 18)  # 좌상단 이름판 위치 (anchor 좌상단)
CHIP_XY = (196, 190)  # 챕터 카드 위 사람 칩 — 시각 칩(overlays.make_clock_layer, 196,262) 바로 위.
#   (196,332) 는 챕터 번호(190px, story 가 이 레이어 위에 그림)에 가려진다


def _mix(c, d, k):
    return tuple(int(round(a * (1 - k) + b * k)) for a, b in zip(c, d))


def _person(who):
    if who not in PEOPLE:
        raise KeyError(f"알 수 없는 인물 키 {who!r} — PEOPLE: {list(PEOPLE)} (people.set_people 로 정의)")
    return PEOPLE[who]


def _ease_in(u):
    u = clamp01(u)
    return u ** 3


# ------------------------------------------------------------ 전환 시각 계산
def _in_card(t, chapter_starts, card, eps=0.05):
    return any(c - eps <= t <= c + card + eps for c in chapter_starts)


def _changes(segments, chapter_starts, card):
    """사람이 바뀌는 지점 → [(t0, prev_who|None, who, 'wipe'|'chip', chapter_start|None)]."""
    out, prev = [], None
    for t0, t1, who in sorted(segments, key=lambda s: s[0]):
        _person(who)
        if who != prev:
            c = next((c for c in chapter_starts if c - 0.05 <= t0 <= c + card + 0.05), None)
            out.append((t0, prev, who, "chip" if c is not None else "wipe", c))
        prev = who
    return out


def switch_times(segments, chapter_starts, card=2.4, mode="wipe"):
    """장 중간 전환이 시작하는 시각 목록 (효과음용, 출력 시각).
    mode="wipe": 와이프 패널이 들어오기 시작하는 시각(컷 - WIPE_IN). mode="push": 컷 시각 t0 그대로."""
    lead = WIPE_IN if mode == "wipe" else 0.0
    return [t0 - lead for t0, _p, _w, kind, _c in _changes(segments, chapter_starts, card) if kind == "wipe"]


def push_list(segments, chapter_starts, card=2.4, fps=30):
    """make_push_fx 용 pushes — 장 중간 사람 변경마다 (t0, t0 - 1/fps, who).
    출력 시각 = edit 시각이고 컷이 이어 붙어 있으면 t0 - 1/fps 가 이전 컷의 마지막 프레임 (= E(prev) - 1/fps)."""
    return [(t0, t0 - 1.0 / fps, w) for t0, _p, w, kind, _c in _changes(segments, chapter_starts, card) if kind == "wipe"]


# ------------------------------------------------------------ 스프라이트
@lru_cache(None)
def _plate_sprite(who):
    _e, name, col = _person(who)
    return gfx.pill_sprite(f"💻 {name}의 화면", size=34, fg=INK, bg=(*col, 245), padx=26, pady=10,
                           radius=18, border=(255, 255, 255, 230))


@lru_cache(None)
def _chip_sprite(who):
    _e, name, col = _person(who)
    return gfx.pill_sprite(f"💻 {name}의 화면", size=30, fg=INK, bg=(*col, 245), padx=24, pady=10,
                           border=(255, 255, 255, 230))


@lru_cache(None)
def _edge_sprites(who):
    """화면 가장자리 테두리 4조각 (상·하·좌·우). 전면 스프라이트 대신 얇은 띠로 합성 비용을 줄인다."""
    col = _person(who)[2]

    def strip(w, h):
        im = Image.new("RGBA", (w, h), (*col, 255))
        return gfx.Sprite(im, 0)

    return strip(W, EDGE), strip(W, EDGE), strip(EDGE, H - 2 * EDGE), strip(EDGE, H - 2 * EDGE)


@lru_cache(None)
def _wipe_title(who):
    """흰 원 아바타(이모지) + 「○○의 화면」 72px. 👤 같은 어두운 이모지도 패널 위에서 보이게 원 안에 둔다."""
    e, name, col = _person(who)
    size, dia, gap = 72, 116, 26
    segs = [(f"{name}의 화면", (255, 255, 255))]
    tw = int(gfx.rich_width(segs, size)) + 4
    w, h = dia + gap + tw, max(dia, int(size * 1.4))
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cy = h // 2
    d.ellipse([0, cy - dia // 2, dia - 1, cy + dia // 2 - 1], fill=(250, 251, 255, 255), outline=(*col, 255), width=6)
    ew = gfx.rich_width([(e, (0, 0, 0))], 64)
    gfx.draw_rich(d, dia / 2 - ew / 2, cy + 24, [(e, (0, 0, 0))], 64)
    gfx.draw_rich(d, dia + gap, cy + int(size * 0.36), segs, size)
    img, pad = gfx.with_shadow(img, radius=16, opacity=0.6)
    return gfx.Sprite(img, pad)


@lru_cache(None)
def _wipe_sub(prev, who):
    n1 = _person(prev)[1] if prev else None
    n2 = _person(who)[1]
    txt = f"{n1}  →  {n2}" if n1 else f"{n2}의 화면으로"
    return story.text_sprite(txt, 36, (236, 239, 248), False)


@lru_cache(None)
def _wipe_label():
    return gfx.pill_sprite("화면 전환", size=24, fg=INK, bg=(255, 255, 255, 235), padx=20, pady=6)


# ------------------------------------------------------------ 그리기
def _draw_edges(ctx, who, a, dx=0.0):
    top, bot, lft, rgt = _edge_sprites(who)
    a *= EDGE_ALPHA
    ctx.cv.sprite(top, dx, 0, a, anchor=(0, 0))
    ctx.cv.sprite(bot, dx, H, a, anchor=(0, 1))
    ctx.cv.sprite(lft, dx, EDGE, a, anchor=(0, 0))
    ctx.cv.sprite(rgt, W + dx, EDGE, a, anchor=(1, 0))


def _draw_person(ctx, who, a, dx=0.0, plate=True, scale=1.0):
    """테두리 + 좌상단 이름판을 dx 만큼 옆으로 옮겨 그린다 (push 전환용)."""
    _draw_edges(ctx, who, a, dx)
    if plate:
        ctx.cv.sprite(_plate_sprite(who), PLATE_XY[0] + dx, PLATE_XY[1], a, scale=scale, anchor=(0, 0))


# ------------------------------------------------------------ push(밀어내기) 전환
PUSH_DUR = 0.6
PUSH_LINE = 5         # 두 화면 경계선 두께(px)
PUSH_SHADOW = 46      # 경계에서 이전 화면 쪽으로 드리우는 그림자 폭(px)
PUSH_SHADOW_K = 0.38  # 그림자 최대 어둡기
PULSE_DUR = 0.8       # push 직후 새 이름판 강조 길이


def push_progress(t, t0, dur=PUSH_DUR):
    """push 구간이면 이징된 진행도 p(0→1), 아니면 None. 화면과 이름판이 같은 값을 쓴다."""
    if t0 <= t <= t0 + dur:
        return gfx.ease_io((t - t0) / dur)
    return None


def make_push_fx(edit_path, pushes, dur=PUSH_DUR):
    """CUSTOM_FRAME_FX 용 「밀어내기」 화면 전환 (ctx → 바꾼 BGR 배열 또는 None).

    edit_path: 편집본(build/edit.mp4) 경로 — 이전 컷 마지막 프레임을 처음 쓸 때 한 번만 읽어 캐시한다.
    pushes:    [(t0, t_prev[, who]), ...]  t0 = 새 컷 시작(출력 시각), t_prev = 이전 컷 마지막 프레임의
               edit 시각 (= E(prev) - 1/30). who 를 주면 경계선이 그 사람 색, 없으면 흰색. push_list() 참고.
    t ∈ [t0, t0+dur] 동안 p = ease_io: 이전 프레임 x = -p·W, 현재 프레임(ctx.frame) x = (1-p)·W.
    전환 구간 카메라는 full 이라고 가정 (이전 프레임은 letterbox 만 거친다).
    """
    items = sorted([(float(p[0]), float(p[1]), p[2] if len(p) > 2 else None) for p in pushes])
    cache = {}

    def prev_frame(ctx, ts):
        if ts not in cache:
            cap = cv2.VideoCapture(edit_path)
            fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
            cap.set(cv2.CAP_PROP_POS_FRAMES, int(round(ts * fps)))
            ok, fr = cap.read()
            cap.release()
            if not ok or fr is None:
                raise RuntimeError(f"push: {edit_path} 에서 {ts:.3f}s 프레임을 읽지 못했습니다")
            fr = ctx.render.letterbox(fr)  # cv2 는 BGR — ctx.frame 도 BGR 1920x1080
            if fr.shape[:2] != (H, W):
                fr = cv2.resize(fr, (W, H), interpolation=cv2.INTER_AREA)
            cache[ts] = fr
        return cache[ts]

    def push_fx(ctx):
        t = ctx.t
        for t0, tp, who in items:
            p = push_progress(t, t0, dur)
            if p is None:
                continue
            cur = ctx.frame
            prev = prev_frame(ctx, tp)
            bx = int(round((1.0 - p) * W))  # 경계 x: 이전 화면 [0,bx) · 현재 화면 [bx,W)
            out = np.empty_like(cur)
            if bx > 0:
                out[:, :bx] = prev[:, W - bx:]
            if bx < W:
                out[:, bx:] = cur[:, :W - bx]
            # 은은한 그림자: 들어오는 화면이 밀려나는 화면 위에 드리움
            sw = min(PUSH_SHADOW, bx)
            if sw > 0:
                ramp = PUSH_SHADOW_K * np.linspace(0.0, 1.0, sw, dtype=np.float32) ** 1.8
                seg = out[:, bx - sw:bx].astype(np.float32)
                out[:, bx - sw:bx] = (seg * (1.0 - ramp)[None, :, None]).astype(np.uint8)
            # 새 사람 색 경계선
            col = _person(who)[2] if who else (255, 255, 255)
            x0, x1 = max(0, bx - PUSH_LINE // 2), min(W, bx + (PUSH_LINE + 1) // 2)
            if x1 > x0:
                out[:, x0:x1] = (col[2], col[1], col[0])  # RGB → BGR
            return out
        return None

    return push_fx


def _draw_panel(cv, who, xl):
    """평행사변형 전면 패널. xl = 패널 왼쪽 아래 꼭짓점 x. xl == -SLANT 이면 화면을 정확히 덮는다."""
    col = _person(who)[2]
    fill = _mix(col, NAVY, 0.45)
    pw = W + 2 * SLANT
    poly = np.array([(xl + SLANT, 0), (xl + pw, 0), (xl + pw - SLANT, H), (xl, H)], np.float64)
    band = 34

    def fn(img, ox, oy):
        def P(pts):
            return ((np.asarray(pts, np.float64) - (ox, oy)) * gfx.SC).astype(np.int32)

        cv2.fillPoly(img, [P(poly)], gfx.rgba(fill), cv2.LINE_AA, gfx.SH)
        # 앞(왼쪽)·뒤(오른쪽) 가장자리: 사람 색 띠 + 흰 선
        for sx, d in ((xl, 1), (xl + pw - SLANT, -1)):
            b = [(sx + SLANT, 0), (sx + SLANT + d * band, 0), (sx + d * band, H), (sx, H)]
            cv2.fillPoly(img, [P(b)], gfx.rgba(col), cv2.LINE_AA, gfx.SH)
            l0 = sx + d * (band + 6)
            ln = [(l0 + SLANT, 0), (l0 + SLANT + d * 5, 0), (l0 + d * 5, H), (l0, H)]
            cv2.fillPoly(img, [P(ln)], (255, 255, 255, 235), cv2.LINE_AA, gfx.SH)

    x0, x1 = max(0, xl), min(W, xl + pw)
    if x1 > x0:
        cv.shape((x0, 0, x1, H), fn, 1.0)
    return xl + pw / 2  # 패널 중심 x


def _wipe(ctx, t, t0, prev, who):
    ts = t0 - WIPE_IN
    te = t0 + WIPE_HOLD + WIPE_OUT
    if not (ts <= t <= te):
        return
    pw = W + 2 * SLANT
    if t < t0:                      # 오른쪽 → 왼쪽으로 쓸고 들어옴
        u = ease_out((t - ts) / WIPE_IN)
        xl = W + (-SLANT - W) * u
    elif t < t0 + WIPE_HOLD:        # 정지
        xl = -SLANT
    else:                           # 왼쪽으로 빠져나감
        u = _ease_in((t - t0 - WIPE_HOLD) / WIPE_OUT)
        xl = -SLANT + (-pw - (-SLANT)) * u
    cx = _draw_panel(ctx.cv, who, xl)
    # 글자: 패널과 함께 움직이고, 정지 구간엔 살짝 떠오르며 또렷해진다
    k = clamp01((t - (t0 - 0.12)) / 0.25)
    ctx.cv.sprite(_wipe_label(), cx, H / 2 - 112, 0.6 + 0.4 * k, anchor=(0.5, 0.5))
    ctx.cv.sprite(_wipe_title(who), cx, H / 2 - 18 + 10 * (1 - ease_out(k)), 1.0, anchor=(0.5, 0.5))
    ctx.cv.sprite(_wipe_sub(prev, who), cx, H / 2 + 72, 0.4 + 0.6 * k, anchor=(0.5, 0.5))


def make_person_layer(segments, chapter_starts, card=2.4, mode="wipe", push_dur=PUSH_DUR):
    """누구 화면인지 보여 주는 CUSTOM_LAYERS 함수.

    segments: [(t0, t1, who), ...] 출력 시각, who ∈ PEOPLE.
    구간 내내 사람 색 화면 테두리 + 좌상단 이름판. 장 중간에 사람이 바뀌면
      mode="wipe": 전환 와이프 패널 (컷 0.3초 전부터 1초)
      mode="push": 패널 없이, push_dur 동안 이전 사람의 테두리·이름판은 왼쪽으로 밀려 나가고 새 사람 것이
                   오른쪽에서 들어온다 (make_push_fx 와 같은 이징). 끝나면 새 이름판이 PULSE_DUR 동안
                   살짝 커졌다 돌아온다. 화면 자체의 밀어내기는 make_push_fx 가 CUSTOM_FRAME_FX 에서 한다.
    챕터 카드 안의 변경은 두 모드 모두 카드 위 사람 칩.
    """
    if mode not in ("wipe", "push"):
        raise ValueError(f"mode 는 'wipe' 또는 'push': {mode!r}")
    segs = sorted([(float(a), float(b), w) for a, b, w in segments], key=lambda s: s[0])
    chs = [float(c) for c in chapter_starts]
    changes = _changes(segs, chs, card)
    wipes = [(t0, p, w) for t0, p, w, kind, _c in changes if kind == "wipe"]
    chips = [(c, w) for _t0, _p, w, kind, c in changes if kind == "chip"]

    def person_layer(ctx):
        t = ctx.t
        in_card = _in_card(t, chs, card, eps=0.0)
        pushing = False
        if mode == "push":
            for t0, prev, who in wipes:
                p = push_progress(t, t0, push_dur)
                if p is None:
                    continue
                if prev:
                    _draw_person(ctx, prev, 1.0, dx=-p * W, plate=not in_card)
                _draw_person(ctx, who, 1.0, dx=(1.0 - p) * W, plate=not in_card)
                pushing = True
                break
        for i, (a, b, who) in enumerate(segs if not pushing else []):
            if not (a <= t <= b):
                continue
            # 앞뒤 구간과 이어지면 페이드 없이 (와이프/푸시가 경계를 처리)
            fin = 0.0 if (i > 0 and abs(segs[i - 1][1] - a) < 0.05) else 0.25
            fout = 0.0 if (i + 1 < len(segs) and abs(segs[i + 1][0] - b) < 0.05) else 0.25
            w = gfx.window(t, a, b, fin, fout)
            if not w:
                continue
            sc = 1.0
            if mode == "push":  # push 직후 이름판이 살짝 커졌다 돌아온다
                for t0, _p, pw in wipes:
                    u = (t - t0 - push_dur) / PULSE_DUR
                    if pw == who and 0.0 <= u <= 1.0:
                        sc = 1.0 + 0.07 * float(np.sin(np.pi * u))
            # 카드가 떠 있는 동안 이름판은 숨김 (story 의 TAGS 와 같은 규칙)
            _draw_person(ctx, who, w[0], plate=not in_card, scale=sc)
            break
        for c, who in chips:
            w = gfx.window(t, c, c + card, 0.2, 0.35)
            if w:
                dy = 16 * (1 - ease_out(clamp01((t - c - 0.15) / 0.35)))
                a = w[0] * clamp01((t - c - 0.15) / 0.25)
                ctx.cv.sprite(_chip_sprite(who), CHIP_XY[0], CHIP_XY[1] + dy, a, anchor=(0, 0.5))
        if mode == "wipe":
            for t0, prev, who in wipes:
                _wipe(ctx, t, t0, prev, who)

    return person_layer


# ------------------------------------------------------------ 간판
GOLD = (255, 184, 28)


@lru_cache(None)
def _sign_sprite(text, hang):
    """매달린 간판 한 장 (끈 포함). hang = 화면 위끝에서 판 윗변까지 끈 길이(px)."""
    size, padx, pady = 46, 46, 22
    segs = [("🖥️ " + text, (255, 255, 255))]
    tw = int(gfx.rich_width(segs, size)) + 2
    bw, bh = tw + padx * 2, int(size * 1.35) + pady * 2
    m = 20  # 그림자 여유
    iw, ih = bw + m * 2, hang + bh + m
    img = Image.new("RGBA", (iw, ih), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    bx0, by0 = m, hang
    # 끈 두 줄 (위로 화면 밖까지)
    for sx in (bx0 + bw * 0.2, bx0 + bw * 0.8):
        d.line([(sx, 0), (sx, by0 + 8)], fill=(40, 34, 20, 255), width=7)
        d.line([(sx, 0), (sx, by0 + 8)], fill=(*GOLD, 255), width=3)
        d.ellipse([sx - 8, by0 - 2, sx + 8, by0 + 14], fill=(*GOLD, 255), outline=(60, 44, 10, 255), width=2)
    # 판: 짙은 남색 + 금색 이중 테두리
    d.rounded_rectangle([bx0, by0, bx0 + bw - 1, by0 + bh - 1], 16, fill=(16, 22, 52, 248), outline=(*GOLD, 255), width=5)
    d.rounded_rectangle([bx0 + 10, by0 + 10, bx0 + bw - 11, by0 + bh - 11], 10, outline=(*GOLD, 140), width=2)
    gfx.draw_rich(d, bx0 + padx, by0 + pady + int(size * 1.05), segs, size)
    img, pad = gfx.with_shadow(img, radius=14, offset=(0, 10), opacity=0.6, pad=30)
    return gfx.Sprite(img, pad), m, hang


def make_signboard_layer(t0, t1, text="에이전트 모니터링룸", x=960, y=64, drop=0.4, fade=0.35):
    """상단 중앙에 매달린 간판. (x, y) = 판 윗변 가운데 (y=40 이면 챕터 태그(상단 가운데, ~48px)에 판 윗변이 가려져 64). t0 에 위에서 내려와 튕기고, t1 직전 페이드아웃."""
    t0, t1 = float(t0), float(t1)

    def signboard_layer(ctx):
        t = ctx.t
        if not (t0 <= t <= t1):
            return
        sp, m, hang = _sign_sprite(text, int(y))
        u = clamp01((t - t0) / drop)
        k = ease_back(u, 2.2)                        # 1 을 넘었다가 돌아옴 → 살짝 튕김
        a = clamp01((t - t0) / 0.12) * clamp01((t1 - t) / fade)
        # 스프라이트 본체 윗변 = 화면 위끝(끈 시작). 시작은 판 전체가 화면 위로 숨은 위치.
        off = -(sp.h - 2 * sp.pad) * (1 - k)
        ctx.cv.sprite(sp, x, off, a, anchor=(0.5, 0))

    return signboard_layer
