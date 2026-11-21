"""메모리를 아끼는 분할 렌더 — 짧은 구간마다 새 프로세스로 렌더하고(누수 초기화), 이미 만든 구간은 건너뛴다.

4분 넘는 영상이나 메모리가 작은 PC(VDI 등)에서 build.py 가 중간에 멈출 때 쓴다. 끊겨도 다시 실행하면 이어서 한다.

    python render_segmented.py timeline.py [--seg 600] [--workers 1] [--voice edge]

  --seg      구간 길이(프레임). 600 = 20초 @30fps. 메모리가 부족하면 더 줄인다.
  --workers  동시에 렌더할 구간 수. 메모리가 빠듯하면 1.
  결과: OUTPUT(mp4) + 같은 이름의 .srt

주의: 타임라인을 바꾼 뒤에는 <build>/segments 폴더와 <build>/audio_final.wav 를 먼저 지울 것
      (지우지 않으면 예전 구간·오디오를 그대로 이어 붙인다).
"""
import argparse
import multiprocessing as mp
import os
import subprocess
import sys

SK = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SK)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def main():
    import build
    import tl as tlmod
    from media import ffmpeg_exe

    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("timeline")
    ap.add_argument("--seg", type=int, default=600)
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--voice", default="edge")
    a = ap.parse_args()

    t = tlmod.load(a.timeline)
    audio = os.path.join(t.build_dir, "audio_final.wav")
    if not os.path.exists(audio):
        src = build.build_audio(t, a.voice, None, False)
        os.replace(src, audio)
    print("[audio]", audio, flush=True)

    n = int(round(t.duration * t.fps))
    seg_dir = os.path.join(t.build_dir, "segments")
    os.makedirs(seg_dir, exist_ok=True)
    jobs, k = [], 0
    while k < n:
        k1 = min(n, k + a.seg)
        out = os.path.join(seg_dir, f"seg_{k:06d}_{k1:06d}.mp4")
        jobs.append((t.timeline_path, k, k1, out, len(jobs)))
        k = k1
    todo = [j for j in jobs if not (os.path.exists(j[3]) and os.path.getsize(j[3]) > 1000)]
    print(f"[render] {n} frames · {len(jobs)} segments · todo {len(todo)} · workers={a.workers}", flush=True)
    if todo:
        with mp.get_context("spawn").Pool(a.workers, maxtasksperchild=1) as pool:
            for done in pool.imap_unordered(_one, todo):
                print(f"  [seg] {done} done", flush=True)

    lst = os.path.join(seg_dir, "list.txt")
    with open(lst, "w", encoding="utf-8") as f:
        for j in jobs:
            f.write(f"file '{os.path.basename(j[3])}'\n")
    os.makedirs(os.path.dirname(os.path.abspath(t.output)), exist_ok=True)
    subprocess.run([ffmpeg_exe(), "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-i", audio,
                    "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest",
                    "-movflags", "+faststart", t.output], check=True)
    srt = os.path.splitext(t.output)[0] + ".srt"
    build.write_srt(t, srt)
    info = tlmod.probe(t.output)
    print(f"[done] {t.output}  {info['duration']:.2f}s (expected {t.duration:.2f}s), {os.path.getsize(t.output) / 1e6:.1f} MB")
    print("[srt]", srt)


def _one(job):
    sys.path.insert(0, SK)
    import build
    tmp = job[3] + ".part.mp4"
    build._render_range((job[0], job[1], job[2], tmp, job[4]))
    os.replace(tmp, job[3])
    return os.path.basename(job[3])


if __name__ == "__main__":
    main()
