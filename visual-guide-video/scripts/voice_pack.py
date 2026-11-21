"""외부 성우·TTS 솔루션용 「내레이션 패키지」 — 문장별 시작 시각·최대 길이·녹음용 읽기 문장을 파일로 뽑는다.

내레이션을 다른 솔루션(사람 성우, Typecast, ElevenLabs 등)으로 다시 만들 때 넘겨줄 입력이다.

    python voice_pack.py timeline.py [--out output]

timeline.py 에 있어야 하는 것 (narrcuts 흐름이면 이미 있음):
    TEXT = {키: "문장 ([강조] 대괄호 허용)"}     AT = {키: 그 문장이 놓인 컷 시작 시각(출력)}
    N    = {키: 지금 TTS 길이(초)}               L0 = 컷 시작 → 말 시작 (없으면 0.25)
    CHAPTERS / SLATES / OUTPUT                  (장 이름·경계·파일 이름에 씀)
선택:
    VOICE_READ   = [("ERP", "이알피"), ("AI", "에이아이"), ("Teams", "팀즈")]   영어·약어 → 소리 나는 대로
    VOICE_SILENT = [("오프닝 제목(발표자)", t0, t1), ...]                        무음 구간 안내
    VOICE_NOTE   = "톤: 밝고 차분한 안내 톤, 약 7자/초"                          대본 머리말에 넣을 한 줄
    VOICE_ENDING = t   이 시각 이후 문장은 「끝」 장으로 (기본: OUTRO["start"] - 0.3)

결과 (<out>/<OUTPUT 이름>_내레이션…):
    _타임라인.csv (엑셀용, utf-8-sig) · _타임라인.json · _읽기대본.txt (한 줄 = 한 문장) · 대본.md (사람용 표)
녹음 파일은 <키>.wav 로 받아 voice/ 폴더에 두고, narr_len.py 로 길이를 다시 재서 컷을 맞춘다.
"""
import argparse
import csv
import importlib.util
import json
import os
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def mmss(x):
    return f"{int(x // 60)}:{x % 60:04.1f}"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("timeline")
    ap.add_argument("--out", default=None, help="출력 폴더 (기본: OUTPUT 과 같은 폴더)")
    ap.add_argument("--end", type=float, default=None, help="영상 끝 시각(초). 기본: tl.load 로 계산")
    a = ap.parse_args()

    tpath = os.path.abspath(a.timeline)
    tdir = os.path.dirname(tpath)
    sys.path.insert(0, tdir)
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    spec = importlib.util.spec_from_file_location("tl_voice_pack", tpath)
    T = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(T)

    lead = float(getattr(T, "L0", 0.25))
    N, TEXT, AT = T.N, T.TEXT, T.AT
    end = a.end
    if end is None:
        import tl as tlmod
        end = tlmod.load(tpath).duration
    chapters = sorted(getattr(T, "CHAPTERS", []) or [], key=lambda c: c[0])
    slates = getattr(T, "SLATES", []) or []
    read_subs = list(getattr(T, "VOICE_READ", []))
    silent = list(getattr(T, "VOICE_SILENT", []))
    note = getattr(T, "VOICE_NOTE", "톤: 밝고 차분한 안내 톤, 기준 속도 약 7자/초(공백 제외).")

    out_mp4 = os.path.join(tdir, T.OUTPUT)
    stem = os.path.splitext(os.path.basename(out_mp4))[0]
    out_dir = os.path.abspath(a.out) if a.out else os.path.dirname(out_mp4)
    os.makedirs(out_dir, exist_ok=True)
    base = os.path.join(out_dir, f"{stem}_내레이션")

    start = {k: AT[k] + lead for k in TEXT}
    order = sorted(TEXT, key=lambda k: start[k])
    bounds = sorted([c[0] for c in chapters] + [s["range"][0] for s in slates] + [end])

    outro = getattr(T, "OUTRO", None) or {}
    ending = getattr(T, "VOICE_ENDING", outro.get("start", end + 1) - 0.3)   # 이 시각 이후 문장은 「끝」 장

    def chapter_of(t):
        if t >= ending:
            return "끝"
        name = "프롤로그"
        for c in chapters:
            if c[0] <= t + 0.01:
                name = f"{c[1]} {c[2]}".strip()
        return name

    def reading(t):
        for x, y in read_subs:
            t = t.replace(x, y)
        return t

    rows = []
    for i, k in enumerate(order):
        nxt = [start[j] for j in order[i + 1:i + 2]]
        b = min([x for x in bounds if x > start[k] + 0.05] + nxt)
        plain = re.sub(r"[\[\]]", "", TEXT[k])
        rows.append(dict(번호=i + 1, 키=k, 장=chapter_of(start[k]), 시작=round(start[k], 2), 시작_분초=mmss(start[k]),
                         현재길이=round(N[k], 2), 최대길이=round(b - start[k] - 0.3, 2), 파일명=f"{k}.wav",
                         자막=plain, 읽기=reading(plain)))
    if not rows:
        raise SystemExit("TEXT 가 비어 있습니다")

    with open(base + "_타임라인.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    json.dump(dict(video=os.path.relpath(out_mp4, tdir).replace("\\", "/"), total=round(end, 2),
                   silent=[dict(name=n, start=round(s, 2), end=round(e, 2)) for n, s, e in silent], lines=rows),
              open(base + "_타임라인.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    open(base + "_읽기대본.txt", "w", encoding="utf-8").write("\n".join(r["읽기"] for r in rows) + "\n")

    md = [f"# {stem} — 내레이션 대본 · 타임라인", "",
          f"- 영상: `{os.path.basename(out_mp4)}` ({mmss(end)}) · 자막: `{stem}.srt`",
          "- 성우는 아래 「읽기」 문장을 문장마다 따로 녹음하고, 파일 이름을 「파일명」 칸대로(예: `a1.wav`) 저장해 주세요.",
          "- 「최대길이」는 지금 영상 그대로 쓸 때 문장이 들어갈 수 있는 길이(초)입니다. 넘더라도 컷을 다시 맞추면 되니 자연스러운 속도를 우선해 주세요."]
    if read_subs:
        md.append("- 「읽기」는 영어·약어를 소리 나는 대로 바꾼 문장입니다(" + ", ".join(f"{x}→{y}" for x, y in read_subs) + "). 자막은 「자막」 칸 표기를 씁니다.")
    md += [f"- {note}", ""]
    if silent:
        md += ["## 무음 구간 — 발표자가 직접 말함", "", "| 구간 | 시작 | 끝 | 길이 |", "|---|---|---|---|"]
        md += [f"| {n} | {mmss(s)} | {mmss(e)} | {e - s:.1f}초 |" for n, s, e in silent]
        md.append("")
    md += ["## 문장별 타임라인", "", "| # | 파일명 | 시작 | 현재 길이 | 최대 길이 | 장 | 읽기(녹음용) |", "|---|---|---|---|---|---|---|"]
    md += [f"| {r['번호']} | `{r['파일명']}` | {r['시작_분초']} | {r['현재길이']:.1f}초 | {r['최대길이']:.1f}초 | {r['장']} | {r['읽기']} |"
           for r in rows]
    md += ["", "## 자막 표기(영상에 나가는 글)"]
    cur = None
    for r in rows:
        if r["장"] != cur:
            cur = r["장"]
            md += ["", f"**{cur}**", ""]
        md.append(f"- `{r['키']}` {r['자막']}")
    open(base + "대본.md", "w", encoding="utf-8").write("\n".join(md) + "\n")

    over = [(r["키"], r["현재길이"], r["최대길이"]) for r in rows if r["현재길이"] > r["최대길이"]]
    print(f"[voice_pack] {len(rows)} lines → {base}_타임라인.csv/.json · _읽기대본.txt · 대본.md")
    print("  over-slot:", over or "없음")


if __name__ == "__main__":
    main()
