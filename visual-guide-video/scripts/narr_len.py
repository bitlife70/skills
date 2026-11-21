"""내레이션 원고 길이 측정 — 컷 편집 전에 '말하는 데 몇 초 걸리는지' 먼저 잰다.

발표·소개 영상은 내레이션이 영상 길이를 정한다. 원고를 쓰고 → 문장별 길이를 재고 → 그 길이에 맞춰
컷(cuts.py)의 구간·배속·정지 길이를 잡으면, 성우가 넘치거나(overflow) 화면이 비는 일이 없다.

  python narr_len.py narr.txt [--voice ko-KR-SunHiNeural] [--rate +8%] [--provider edge|sapi]
     narr.txt: 한 줄에 한 문장 ('키<TAB>문장' 또는 문장만). 결과 → narr_len.json (키별 초)
  python narr_len.py timeline.py      # timeline 의 NARRATION 문장을 잰다

한국어 Edge 음성 ≈ 7음절/초(+8%면 약 7.5). 합성 결과는 build/voice_cache 에 남아 최종 렌더 때 재사용된다.
--provider edge 는 문장을 Microsoft TTS 서버로 보낸다.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import voice  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("--voice", default="ko-KR-SunHiNeural")
    ap.add_argument("--rate", default="+0%")
    ap.add_argument("--provider", default="edge")
    args = ap.parse_args()
    base = os.path.dirname(os.path.abspath(args.src))
    if args.src.endswith(".py"):
        import tl
        t = tl.load(args.src)
        items = [(f"{n[0]:.2f}", n[1]) for n in (t.narration or [])]
        args.voice = t.voice.get("voice", args.voice)
        args.rate = t.voice.get("rate", args.rate)
    else:
        items = []
        for i, ln in enumerate(open(args.src, encoding="utf-8").read().splitlines()):
            if ln.strip():
                k, _, txt = ln.partition("\t") if "\t" in ln else (f"n{i + 1:02d}", "", ln)
                items.append((k, txt.strip()))
    cache = os.path.join(base, "build", "voice_cache")
    out, total = {}, 0.0
    for k, txt in items:
        x = voice.synth(voice.clean_text(txt), args.provider, args.voice, args.rate, cache)
        d = len(x) / voice.SR
        out[k] = round(d, 2)
        total += d
        print(f"{k:>8} {d:5.2f}s  {voice.clean_text(txt)}")
    print(f"total {total:.1f}s ({len(items)}문장)")
    path = os.path.join(base, "narr_len.json")
    json.dump(out, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(path)


if __name__ == "__main__":
    main()
