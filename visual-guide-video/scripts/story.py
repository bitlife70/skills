"""스토리 구조 그래픽: 발표·소개 영상용 슬레이트, 챕터 카드, 상단 태그, 공지 배지.

긴 시연을 몇 분짜리 발표 영상으로 만들 때 "지금 무슨 이야기인지 / 누구 화면인지 / 무엇을 건너뛰었는지" 를
화면이 말해 준다. 모든 시각은 원본(SRC) 시각 — recut 편집본이면 C.O()/C.S() 로 적는다.

SLATES   = [dict(range=(t0, t1), bg="navy"|"blur"|"none", chip="…", title="…[강조]…", sub="…",
                 lines=["…", …], pills=["🗄️ …", …], tokens=[("🤖", "이름"), …], title_size=110)]
           영상 위를 덮는 전면 카드. 타이틀(tokens), 문제 제기(lines), 효과 요약(pills) 등에 쓴다.
           bg="navy" 는 원본을 가리고 남색 그라데이션, "blur" 는 원본을 흐리게 깔고 그 위에 글자.
CHAPTERS = [(t, "01", "제목", "부제"[, 태그 끝 시각])]
           t 부터 CHAPTER_CARD 초 동안 왼쪽 정렬 큰 번호 카드(배경 흐림). 이어서 상단 가운데에
           "[01] 제목" 태그를 다음 챕터 직전까지(또는 지정 시각까지) 띄운다.
           recut 에서 클립 앞 정지(hold0)를 CHAPTER_CARD 와 같게 주면 카드가 정지 화면 위에 뜬다.
CHAPTER_CARD = 2.4
TAGS     = [(t0, t1, "👤 김OO 님 화면", 색)]   우상단 태그 (화면 주인공·역할). 색 = (r,g,b) | "accent|cyan|green"
NOTICES  = [(t, "⏭ 대기 1분 생략"[, 길이])]     상단 가운데 강조 배지 (건너뛴 구간 알림)
BADGES   = [(t0, t1, "⏩ x2.4")]               좌상단 작은 배지 (recut 의 C.badges())
"""
import math
from functools import lru_cache

import numpy as np
from PIL import Image, ImageDraw

import gfx
from gfx import W, H, clamp01, ease_back, ease_out, window

TL = None
D = dict(slates=[], chapters=[], tags=[], notices=[], badges=[], card=2.4, title_size=86)


def _col(c):
    return gfx.COLORS[c] if isinstance(c, str) else tuple(c)


def setup(tl):
    global TL
    TL = tl
    m = tl.module
    g = lambda k, d=None: getattr(m, k, d)  # noqa: E731
    D["card"] = float(g("CHAPTER_CARD", 2.4))
    D["title_size"] = int(g("CHAPTER_TITLE_SIZE", 86))  # 보조 글 없이 제목만 크게 쓸 때 키운다
    D["slates"] = []
    for s in g("SLATES", []) or []:
        s = dict(s)
        s["range"] = tl.span(*s["range"])
        D["slates"].append(s)
    ch = sorted([(tl.out(c[0]), *c[1:]) for c in g("CHAPTERS", []) or []], key=lambda c: c[0])
    end_all = tl.outro["start"] if tl.outro else tl.duration
    D["chapters"] = []
    for i, c in enumerate(ch):
        nxt = ch[i + 1][0] if i + 1 < len(ch) else end_all
        tag_end = tl.out(c[4]) if len(c) > 4 and c[4] is not None else nxt
        D["chapters"].append(dict(t=c[0], num=c[1], title=c[2], sub=c[3] if len(c) > 3 else "", tag_end=tag_end))
    D["tags"] = [(*tl.span(a, b), txt, _col(col)) for a, b, txt, col in g("TAGS", []) or []]
    D["notices"] = [(tl.out(n[0]), n[1], n[2] if len(n) > 2 else 1.6) for n in g("NOTICES", []) or []]
    D["badges"] = [(*tl.span(a, b), txt) for a, b, txt in g("BADGES", []) or []]


def active():
    return bool(D["slates"] or D["chapters"] or D["tags"] or D["notices"] or D["badges"])


# ---------------------------------------------------------------- sprites
@lru_cache(None)
def _navy():
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    k = np.clip(np.sqrt(((x - W * 0.5) / W) ** 2 + ((y - H * 0.45) / H) ** 2) * 1.6, 0, 1)[..., None]
    mid, edge = np.array([58, 30, 26], np.float32), np.array([22, 12, 10], np.float32)  # BGR
    return (mid * (1 - k) + edge * k).astype(np.uint8)


@lru_cache(None)
def text_sprite(text, size, color=(255, 255, 255), bold=True):
    segs = gfx.parse_rich(text, color, gfx.ACCENT)
    w = int(gfx.rich_width(segs, size, bold)) + 24
    img = Image.new("RGBA", (w, int(size * 1.5)), (0, 0, 0, 0))
    gfx.draw_rich(ImageDraw.Draw(img), 12, int(size * 1.12), segs, size, bold)
    img, pad = gfx.with_shadow(img, radius=16, opacity=0.7)
    return gfx.Sprite(img, pad)


@lru_cache(None)
def token_sprite(emo, name):
    im = Image.new("RGBA", (220, 200), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse([55, 6, 165, 116], fill=(22, 24, 40, 240), outline=gfx.ACCENT, width=4)
    ew = gfx.rich_width([(emo, (255, 255, 255))], 58)
    gfx.draw_rich(d, 110 - ew / 2, 80, [(emo, (255, 255, 255))], 58)
    tw = gfx.rich_width([(name, (255, 255, 255))], 25)
    gfx.draw_rich(d, 110 - tw / 2, 162, [(name, (232, 235, 245))], 25)
    im, p = gfx.with_shadow(im, radius=12)
    return gfx.Sprite(im, p)


def _blur_dim(frame, k, dim=0.6):
    import render
    img = render.blur_bg(frame, 0.9 * k)
    return (img.astype(np.float32) * (1 - dim * k)).astype(np.uint8)


def _slate_at(t):
    for s in D["slates"]:
        if s["range"][0] <= t < s["range"][1]:
            return s
    return None


def _card_at(t):
    for c in D["chapters"]:
        if c["t"] <= t < c["t"] + D["card"]:
            return c
    return None


# ---------------------------------------------------------------- frame (배경)
def frame(img, t):
    s = _slate_at(t)
    if s:
        bg = s.get("bg", "navy")
        if bg == "navy":
            return _navy().copy()
        if bg == "blur":
            a, b = s["range"]
            w = window(t, a, b, 0.3, 0.4)
            return _blur_dim(img, w[0] if w else 0, 0.62)
        return img
    c = _card_at(t)
    if c:
        w = window(t, c["t"], c["t"] + D["card"], 0.25, 0.4)
        if w:
            return _blur_dim(img, w[0], 0.62)
    return img


# ---------------------------------------------------------------- overlay
def _el(cv, sp, x, y, t, t0, anchor=(0.5, 0.5), dy=34, fade=1.0, pop=False):
    u = clamp01((t - t0) / 0.45)
    if u <= 0:
        return
    sc = 0.7 + 0.3 * ease_back(u) if pop else 1.0
    cv.sprite(sp, x, y + dy * (1 - ease_out(u)), ease_out(u) * fade, sc, anchor=anchor)


def _slate(cv, t, s):
    a, b = s["range"]
    f = 1 - clamp01((t - (b - 0.45)) / 0.45)
    y = s.get("top", 270 if not s.get("tokens") else 250)
    k = a + 0.1
    if s.get("chip"):
        _el(cv, gfx.pill_sprite(s["chip"], size=24, fg=gfx.INK, bg=gfx.ACCENT, padx=22, pady=8), W / 2, y, t, k, fade=f, pop=True)
        y += 125
        k += 0.2
    if s.get("title"):
        size = s.get("title_size", 132 if s.get("tokens") else 92)
        _el(cv, text_sprite(s["title"], size), W / 2, y, t, k, fade=f)
        y += int(size * 0.95)
        k += 0.35
    if s.get("sub"):
        _el(cv, text_sprite(s["sub"], 50, (226, 230, 242)), W / 2, y, t, k, fade=f)
        y += 90
        k += 0.4
    for i, ln in enumerate(s.get("lines", [])):
        _el(cv, text_sprite(ln, 40, (255, 214, 120), bold=False), W / 2, y + 40 + i * 72, t, k + 0.3 + i * 0.55, fade=f)
    pills = s.get("pills", [])
    for i, p in enumerate(pills):
        sp = gfx.pill_sprite(p, size=36, fg=(255, 255, 255), bg=(30, 34, 60, 235), padx=28, pady=14, border=gfx.ACCENT)
        _el(cv, sp, W / 2 + (i - (len(pills) - 1) / 2) * 330, y + 90, t, k + 0.6 + i * 0.35, fade=f, pop=True)
    toks = s.get("tokens", [])
    for i, (e, n) in enumerate(toks):
        _el(cv, token_sprite(e, n), W / 2 + (i - (len(toks) - 1) / 2) * 240, y + 110, t, k + 0.5 + i * 0.13, fade=f, pop=True)


def _chapter_card(cv, t, c):
    a = c["t"]
    w = window(t, a, a + D["card"], 0.2, 0.35)
    if not w:
        return
    f, x0 = w[0], 200
    _el(cv, text_sprite(c["num"], 190, gfx.ACCENT), x0 - 12, 400, t, a + 0.05, anchor=(0, 0.5), dy=0, fade=f)
    _el(cv, gfx.pill_sprite(f"CHAPTER {c['num']}", size=22, fg=gfx.INK, bg=gfx.ACCENT, padx=18, pady=6),
        x0 + 230, 360, t, a + 0.15, anchor=(0, 0.5), dy=0, fade=f)
    size = D["title_size"]
    tsp = text_sprite(c["title"], size)
    while tsp.body[0] > W - (x0 + 218) - 60 and size > 48:
        size -= 6
        tsp = text_sprite(c["title"], size)
    _el(cv, tsp, x0 + 218, 450 + (size - 86) * 0.3, t, a + 0.25, anchor=(0, 0.5), dy=24, fade=f)
    if c["sub"]:
        _el(cv, text_sprite(c["sub"], 40, (205, 212, 230), bold=False), x0 - 4, 600, t, a + 0.55, anchor=(0, 0.5), dy=18, fade=f)
    u = ease_out(clamp01((t - a - 0.2) / 0.6))
    ly = 655 if c["sub"] else 560
    gfx.draw_rrect(cv, (x0, ly, x0 + 760 * u, ly + 6), gfx.ACCENT, 1, 3, f, fill=(*gfx.ACCENT, 255), glow=6)


def layer(cv, t):
    s = _slate_at(t)
    if s:
        _slate(cv, t, s)
        return
    card = _card_at(t)
    if card:
        _chapter_card(cv, t, card)
    for c in D["chapters"]:
        w = window(t, c["t"] + D["card"], c["tag_end"], 0.35, 0.3)
        if w:
            sp = gfx.pill_sprite(f"[{c['num']}]  {c['title']}", size=22, fg=(240, 242, 250), bg=(18, 20, 34, 225),
                                 padx=20, pady=6, border=(255, 255, 255, 50))
            cv.sprite(sp, W / 2, 6, w[0], anchor=(0.5, 0))
    if not card:
        for a, b, txt, col in D["tags"]:
            w = window(t, a, b, 0.3, 0.25)
            if w:
                cv.sprite(gfx.pill_sprite(txt, size=22, fg=gfx.INK, bg=col, padx=18, pady=6), W - 160, 6, w[0], anchor=(1, 0))
        for a, b, txt in D["badges"]:
            w = window(t, a, b, 0.2, 0.2)
            if w:
                sp = gfx.pill_sprite(txt, size=22, fg=(255, 255, 255), bg=(18, 20, 34, 225), padx=16, pady=6,
                                     border=(255, 255, 255, 50))
                cv.sprite(sp, 150, 6, w[0], anchor=(0, 0))
    for a, txt, dur in D["notices"]:
        w = window(t, a, a + dur, 0.15, 0.35)
        if w:
            sp = gfx.pill_sprite(txt, size=26, fg=gfx.INK, bg=gfx.ACCENT, padx=20, pady=8)
            cv.sprite(sp, W / 2, 120 - 20 * (1 - ease_out(w[1])), w[0], anchor=(0.5, 0))
