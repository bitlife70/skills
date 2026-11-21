"""시각 목록의 프레임을 한 장의 접촉 시트로 (장면 내용 확인·컷 경계 확인·최종 출력 검수용).

  python frames.py VIDEO 556,558,559.5,561 --out build/chk.jpg [--cols 3]
  python frames.py VIDEO 478:532:2 --out build/dense.jpg --cols 4        # 시작:끝:간격

analyze.py 시트(2초 간격)보다 촘촘하게 '무슨 일이 언제 일어나는지' 확인할 때 쓴다.
VFR 원본도 CFR 사본으로 열기 때문에 시각은 실제 타임스탬프 = timeline.py 에 적는 시각과 같다.
"""
import argparse
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from media import ensure_cfr, ffmpeg_exe  # noqa: E402


def parse_times(s):
    out = []
    for part in s.split(","):
        if ":" in part:
            a, b, st = (float(x) for x in part.split(":"))
            out += list(np.arange(a, b + 1e-6, st))
        elif part:
            out.append(float(part))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("times")
    ap.add_argument("--out", required=True)
    ap.add_argument("--cols", type=int, default=3)
    args = ap.parse_args()
    src = ensure_cfr(args.video)
    tw, th = 1920 // args.cols, 1080 // args.cols

    def grab(t):
        r = subprocess.run([ffmpeg_exe(), "-loglevel", "error", "-ss", f"{t:.3f}", "-i", src, "-frames:v", "1",
                            "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{tw}x{th}", "-"], capture_output=True)
        f = np.frombuffer(r.stdout, np.uint8)
        f = f.reshape(th, tw, 3).copy() if f.size == tw * th * 3 else np.zeros((th, tw, 3), np.uint8)
        cv2.rectangle(f, (0, 0), (118, 30), (0, 0, 200), -1)
        cv2.putText(f, f"{t:.1f}", (6, 23), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 255), 2)
        return f

    with ThreadPoolExecutor(8) as ex:
        tiles = list(ex.map(grab, parse_times(args.times)))
    while len(tiles) % args.cols:
        tiles.append(np.zeros_like(tiles[0]))
    rows = [np.hstack(tiles[i:i + args.cols]) for i in range(0, len(tiles), args.cols)]
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    cv2.imwrite(args.out, np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 86])
    print(args.out)


if __name__ == "__main__":
    main()
