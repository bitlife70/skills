"""재편집(recut): 긴 원본에서 필요한 구간만 골라 순서를 바꾸고, 구간별 배속·앞뒤 정지·이미지 삽입을 적용한
편집본(build/edit.mp4, CFR)을 만든다. 10분 넘는 시연 녹화를 3~5분 발표 영상으로 줄일 때 쓴다.

TRIM·SPEED·FREEZE 는 원본 순서를 유지한 채 한 구간을 다루지만, recut 은 '장면 재배치' 가 된다.
timeline.py 는 SRC = 편집본으로 두고, 시각은 C.O(원본 시각) 으로 적는다 → 원본 시각으로 생각하면서 편집본에 배치.

컷 파일 (cuts.py):
    SRC = "../demo.mp4"            # 컷 파일 기준 상대경로 (VFR 이면 CFR 사본으로 자동 변환 → 시각 = 실제 타임스탬프)
    FPS = 30
    AUDIO = False                  # 원본 소리를 편집본에 넣을지 (배속 구간은 atempo, 정지·이미지 구간은 무음)
    CLIPS = [
        ("intro", 0.0, 19.0, 2.4),             # (id, 시작, 끝, 배속[, 앞 정지초[, 뒤 정지초]])
        ("ch1",   35.2, 38.4, 1.3, 2.4),       #   앞 정지 2.4초 = 챕터 카드 자리 (CHAPTERS 와 함께)
        ("wf",    "img", "../workflow.png", 4.5),  # 이미지 삽입 (16:9 로 패딩)
        ("end",   "still", 432.0, 13.0),       # 원본 한 프레임 정지 (아웃트로 배경)
    ]

여러 원본을 섞을 때 (SOURCES):
    SOURCES = {"a": "../demo_a.mp4", "b": "../demo_b.mp4"}
    SOURCE_VF = {"b": "scale=1920:952:flags=lanczos,pad=1920:1080:0:64:color=white"}  # 소스별 전처리(크기 맞춤 등)
    DEFAULT_SOURCE = "a"
    CLIPS = [("x1", 12.0, 18.0, 1.5), ("x2", "still", 40.0, 3.0, "b")]   # 튜플 맨 끝에 소스 키 → 그 원본에서
    O(40.0, src="b")               # 원본 시각 → 편집본 시각 (소스 지정)

timeline.py 에서:
    import recut
    C = recut.load(os.path.join(os.path.dirname(os.path.abspath(__file__)), "cuts.py"))
    SRC = C.edit_rel(__file__)     # 편집본 경로 (timeline 기준 상대)
    O, S, E = C.O, C.S, C.E        # O(원본초[, 클립id]) → 편집본 시각, S(id)/E(id) = 클립 시작/끝
    BADGES = C.badges(min_speed=2) # "⏩ x2.4" 배속 배지

CLI:
    python recut.py cuts.py            # → build/edit.mp4 (컷 파일 폴더 기준)
    python recut.py cuts.py --list     # 클립별 편집본 시각표
"""
import argparse
import importlib.util
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from media import ensure_cfr, ffmpeg_exe  # noqa: E402


class Cuts:
    def __init__(self, path):
        self.path = os.path.abspath(path)
        self.base = os.path.dirname(self.path)
        spec = importlib.util.spec_from_file_location("cuts_" + str(abs(hash(self.path))), self.path)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        self.m = m
        self.fps = int(getattr(m, "FPS", 30))
        self.audio = bool(getattr(m, "AUDIO", False))
        self.src = os.path.join(self.base, m.SRC) if getattr(m, "SRC", None) else None  # 레이아웃만 쓸 땐 없어도 됨
        self.sources = {k: os.path.join(self.base, v) for k, v in getattr(m, "SOURCES", {}).items()}
        self.source_vf = dict(getattr(m, "SOURCE_VF", {}))
        self.default_src = getattr(m, "DEFAULT_SOURCE", None)
        self.edit = os.path.join(self.base, getattr(m, "EDIT", "build/edit.mp4"))
        self.layout, t = {}, 0.0
        for c in m.CLIPS:
            sk = None
            if len(c) > 3 and isinstance(c[-1], str) and c[-1] in self.sources:
                sk, c = c[-1], c[:-1]
            cid, fps = c[0], self.fps
            if cid in self.layout:
                raise ValueError(f"클립 id 중복: {cid}")
            if c[1] in ("img", "still"):
                n = round(c[3] * fps)
                r = dict(kind=c[1], src=c[2], frames=n, n0=0, nb=n, n1=0)
            else:
                a, b, sp = float(c[1]), float(c[2]), float(c[3])
                h0 = c[4] if len(c) > 4 else 0
                h1 = c[5] if len(c) > 5 else 0
                n0, nb, n1 = round(h0 * fps), round((b - a) / sp * fps), round(h1 * fps)
                r = dict(kind="clip", a=a, b=b, sp=sp, n0=n0, nb=nb, n1=n1, frames=n0 + nb + n1)
            r["srckey"] = sk or self.default_src
            r["start"] = t
            r["body"] = t + r["n0"] / fps
            r["end"] = t + r["frames"] / fps
            self.layout[cid] = r
            t = r["end"]
        self.total = t

    # ---- 시각 변환
    def O(self, ts, cid=None, src=None):
        """원본 시각 → 편집본 시각 (그 시각을 포함하는 첫 클립, cid·src 로 지정 가능)."""
        src = src or self.default_src
        for k, r in self.layout.items():
            if r["kind"] != "clip" or (cid and k != cid) or (not cid and src and r["srckey"] != src):
                continue
            if r["a"] - 1e-6 <= ts <= r["b"] + 1e-6:
                return r["body"] + (ts - r["a"]) / r["sp"]
        raise ValueError(f"원본 {ts}s 를 포함하는 클립이 없습니다" + (f" ({cid})" if cid else ""))

    def S(self, cid):
        return self.layout[cid]["start"]

    def E(self, cid):
        return self.layout[cid]["end"]

    def B(self, cid):
        """앞 정지가 끝나고 본편이 시작하는 시각."""
        return self.layout[cid]["body"]

    def badges(self, min_speed=2.0, fmt="⏩ x{sp:g}"):
        out = []
        for r in self.layout.values():
            if r["kind"] == "clip" and r["sp"] >= min_speed:
                out.append((r["body"] + 0.1, r["body"] + r["nb"] / self.fps, fmt.format(sp=r["sp"])))
        return out

    def edit_rel(self, timeline_file):
        return os.path.relpath(self.edit, os.path.dirname(os.path.abspath(timeline_file)))

    def table(self):
        for k, r in self.layout.items():
            what = f"{r['a']:8.2f}→{r['b']:8.2f} x{r['sp']:g}" if r["kind"] == "clip" else f"{r['kind']} {r['src']}"
            if r.get("srckey"):
                what += f"  [{r['srckey']}]"
            print(f"{k:10} {r['start']:7.2f} → {r['end']:7.2f} ({r['end'] - r['start']:5.2f}s)  {what}")
        print(f"TOTAL {self.total:.2f}s = {int(self.total // 60)}:{self.total % 60:04.1f}")


def load(path):
    return Cuts(path)


def _atempo(sp):
    parts = []
    while sp > 2.0:
        parts.append("atempo=2.0")
        sp /= 2.0
    while sp < 0.5:
        parts.append("atempo=0.5")
        sp /= 0.5
    parts.append(f"atempo={sp:.5f}")
    return ",".join(parts)


def _has_audio(path):
    r = subprocess.run([ffmpeg_exe(), "-hide_banner", "-i", path], capture_output=True, text=True, errors="replace")
    return "Audio:" in r.stderr


def build(c, workers=4):
    from concurrent.futures import ThreadPoolExecutor
    if not c.src and not c.sources:
        raise SystemExit("컷 파일에 SRC 나 SOURCES 가 없습니다")
    used = {r["srckey"] for r in c.layout.values() if r["kind"] != "img"}
    path_of = dict(c.sources)
    if c.src:
        path_of.setdefault(None, c.src)
    missing = [k for k in used if k not in path_of]
    if missing:
        raise SystemExit(f"소스 키를 찾을 수 없습니다: {missing} (SOURCES/DEFAULT_SOURCE 확인)")
    srcs = {k: ensure_cfr(path_of[k]) for k in used}
    audio = c.audio and bool(srcs) and all(_has_audio(v) for v in srcs.values())
    tmp = os.path.join(os.path.dirname(c.edit), "recut_clips")
    os.makedirs(tmp, exist_ok=True)
    venc = ["-c:v", "libx264", "-preset", "medium", "-crf", "12", "-pix_fmt", "yuv420p", "-r", str(c.fps)]
    aenc = ["-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2"] if audio else ["-an"]
    silent = ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo"] if audio else []

    def one(item):
        cid, r = item
        src = srcs.get(r["srckey"])
        pre = c.source_vf.get(r["srckey"], "")
        pre = pre + "," if pre else ""
        out = os.path.join(tmp, f"{cid}.mp4")
        n, dur = r["frames"], r["frames"] / c.fps
        if r["kind"] == "img":
            vf = (f"scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=0xF5F6FA,"
                  f"setsar=1,fps={c.fps}")
            inp = ["-loop", "1", "-i", os.path.join(c.base, r["src"])] + silent
            args = inp + ["-vf", vf, "-frames:v", str(n)] + (["-map", "0:v", "-map", "1:a", "-t", f"{dur:.3f}"] if audio else [])
        elif r["kind"] == "still":
            inp = ["-ss", f"{r['src']:.3f}", "-i", src] + silent
            vf = f"{pre}fps={c.fps},trim=end_frame=1,tpad=stop=-1:stop_mode=clone"  # 첫 프레임만 남기고 복제 = 정지
            args = inp + ["-vf", vf, "-frames:v", str(n)] + (["-map", "0:v", "-map", "1:a", "-t", f"{dur:.3f}"] if audio else [])
        else:
            a, b, sp = r["a"], r["b"], r["sp"]
            vf = f"{pre}setpts=(PTS-STARTPTS)/{sp:.6f},fps={c.fps}"
            if r["n0"]:
                vf += f",tpad=start={r['n0']}:start_mode=clone"
            vf += ",tpad=stop=-1:stop_mode=clone"
            args = ["-ss", f"{a:.3f}", "-t", f"{b - a + 0.5:.3f}", "-i", src, "-vf", vf, "-frames:v", str(n)]
            if audio:
                af = f"asetpts=PTS-STARTPTS,{_atempo(sp)},adelay={int(r['n0'] / c.fps * 1000)}:all=1,apad,atrim=0:{dur:.4f}"
                args += ["-af", af]
        p = subprocess.run([ffmpeg_exe(), "-y", "-loglevel", "error"] + args + venc + aenc + [out],
                           capture_output=True, text=True)
        if p.returncode:
            raise RuntimeError(f"{cid}: {p.stderr[-600:]}")
        return out

    with ThreadPoolExecutor(workers) as ex:
        outs = list(ex.map(one, c.layout.items()))
    lst = os.path.join(tmp, "list.txt")
    with open(lst, "w", encoding="utf-8") as f:
        for o in outs:
            f.write(f"file '{os.path.basename(o)}'\n")
    p = subprocess.run([ffmpeg_exe(), "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", c.edit],
                       capture_output=True, text=True)
    if p.returncode:
        raise RuntimeError(p.stderr[-600:])
    print(f"[recut] {c.edit}  {len(outs)} clips · {c.total:.2f}s · audio={'on' if audio else 'off'}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cuts")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()
    c = load(args.cuts)
    c.table()
    if not args.list:
        build(c, args.workers)


if __name__ == "__main__":
    main()
