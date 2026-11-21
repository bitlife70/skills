"""내레이션이 이끄는 시연 편집 — 문장 길이로 컷 길이를 정하고, 같은 표로 내레이션·자막 시각을 만든다.

흐름:
    narr.txt (키<TAB>문장)  →  python narr_len.py narr.txt --rate +18%  →  narr_len.json (키: 초)
    cuts.py      : P = narrcuts.Planner("narr_len.json", __file__) ; CLIPS = [P.still(...), P.clip(...)]
    timeline.py  : TEXT = narrcuts.read_narr("narr.txt", __file__)
                   NARRATION, SUBTITLES = narrcuts.narration_and_subs(TEXT, AT, N, lead=P.lead)

cuts.py 예:
    import os, sys
    sys.path.insert(0, os.path.join(os.path.expanduser("~"), ".claude", "skills", "visual-guide-video", "scripts"))
    import narrcuts
    P = narrcuts.Planner("narr_len.json", __file__, default_src="v2")
    SOURCES = {"v2": "../input/demo.mp4"}
    DEFAULT_SOURCE = "v2"
    CC = 2.3                                            # 챕터 카드 자리(앞 정지)
    CLIPS = [
        P.still("problem", 2.0, "p1", 0.3),             # 원본 2.0초 한 프레임을 문장 p1 길이 + 0.3초 동안
        P.clip("ask", 63.0, 71.6, 2.0, "b1", card=CC),  # 입력 장면 x2.0, 앞에 카드 2.3초, 말이 길면 끝 프레임 정지
        P.still("found", 90.0, ["b2", "b3"], 1.0),      # 한 컷에 두 문장 (사이 gap 초)
    ]

규칙(실제 제작에서 굳어진 값): 컷 시작 → 말 시작 lead 0.25초, 말 끝 → 다음 컷 tail 0.35초, 한 컷 안 문장 사이 gap 0.25초.
내레이션이 바뀌면 narr_len.json 만 다시 만들고 recut → 미리보기. 컷 시각은 자동으로 따라온다.
"""
import json
import os
import re


class Planner:
    def __init__(self, len_json, base_file=None, fps=30, lead=0.25, tail=0.35, gap=0.25, default_src=None):
        base = os.path.dirname(os.path.abspath(base_file)) if base_file else os.getcwd()
        path = len_json if os.path.isabs(len_json) else os.path.join(base, len_json)
        self.N = json.load(open(path, encoding="utf-8"))
        self.fps, self.lead, self.tail, self.gap = fps, lead, tail, gap
        self.default_src = default_src

    def need(self, keys):
        """문장(들)을 다 읽는 데 필요한 컷 길이(초) = lead + Σ문장 + gap·(n-1) + tail."""
        if not keys:
            return 0.0
        keys = keys if isinstance(keys, (list, tuple)) else [keys]
        missing = [k for k in keys if k not in self.N]
        if missing:
            raise KeyError(f"narr_len.json 에 없는 키: {missing} — narr_len.py 를 다시 돌릴 것")
        return self.lead + sum(self.N[k] for k in keys) + self.gap * (len(keys) - 1) + self.tail

    def _src(self, src):
        return src if src is not None else self.default_src

    def still(self, cid, t, keys=None, extra=0.0, src=None, card=0.0, min_dur=2.2):
        """원본 t초 한 프레임 정지. 길이 = max(min_dur, 문장 길이 + extra). card>0 이면 그 앞에 카드 자리 정지."""
        dur = max(min_dur, self.need(keys) + extra)
        src = self._src(src)
        if card:
            tup = (cid, t, t + 1 / self.fps, 1.0, card, dur - 1 / self.fps)
        else:
            tup = (cid, "still", t, dur)
        return tup + ((src,) if src else ())

    def clip(self, cid, a, b, sp, keys=None, card=0.0, src=None, extra=0.0):
        """원본 a→b 를 sp 배속으로. 문장이 본편보다 길면 끝 프레임을 정지해 늘린다."""
        body = (b - a) / sp
        hold = max(0.0, self.need(keys) + extra - body)
        src = self._src(src)
        return (cid, a, b, sp, card, round(hold, 3)) + ((src,) if src else ())


def chunks(text):
    """문장 단위로 자르고, [강조] 대괄호가 문장을 넘으면 양쪽을 닫아 준다."""
    parts = [p for p in re.split(r"(?<=[.?!])\s+", text) if p]
    out, open_ = [], False
    for p in parts:
        q = ("[" + p) if open_ else p
        open_ = q.count("[") > q.count("]")
        out.append(q + ("]" if open_ else ""))
    return out


def narration_and_subs(text, at, lengths, lead=0.25, overlap=0.12):
    """TEXT{키: 문장}, AT{키: 컷 시작 시각}, lengths{키: 초} → (NARRATION, SUBTITLES).

    자막은 문장마다 나누고, 길이는 글자 수(공백·대괄호 제외) 비율로 나눈다.
    """
    narration = [(at[k] + lead, text[k]) for k in text]
    subs = []
    for k in text:
        t = at[k] + lead
        parts = chunks(text[k])
        w = [max(1, len(re.sub(r"[\[\]\s]", "", p))) for p in parts]
        acc = t
        for p, n in zip(parts, w):
            d = lengths[k] * n / sum(w)
            subs.append((acc, acc + d + overlap, p))
            acc += d
    subs.sort(key=lambda s: s[0])
    return narration, subs


def read_narr(path, base_file=None):
    """narr.txt (키<TAB>문장, [강조] 허용) → {키: 문장} (파일 순서 유지). timeline 의 TEXT 를 원고 한 곳에서 관리할 때."""
    if base_file and not os.path.isabs(path):
        path = os.path.join(os.path.dirname(os.path.abspath(base_file)), path)
    out = {}
    for i, ln in enumerate(open(path, encoding="utf-8").read().splitlines()):
        if ln.strip() and not ln.lstrip().startswith("#"):
            k, _, txt = ln.partition("\t") if "\t" in ln else (f"n{i + 1:02d}", "", ln)
            out[k.strip()] = txt.strip()
    return out
