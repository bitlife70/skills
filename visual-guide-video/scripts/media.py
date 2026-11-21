"""원본 영상 정규화: 가변 프레임레이트(VFR) 영상을 고정 프레임레이트(CFR) 사본으로 바꾼다.

엔진은 '프레임 번호 / fps = 시각' 을 전제로 한다. 화면녹화(OBS·Windows 녹화·Teams 녹화)는 대개 VFR 이라
이 전제가 깨져 시트·미리보기·렌더의 시각이 실제 타임스탬프와 수 초씩 어긋나고, 원본 소리와도 싱크가 틀어진다
(실제 사례: 16분 녹화에서 최대 7초). analyze / crops / tracks / build 는 모두 이 모듈로 원본을 열기 때문에
VFR 원본은 한 번만 CFR 사본으로 바꾸고, 이후 모든 시각은 '실제 타임스탬프' 와 일치한다.

  ensure_cfr(path) → 원본이 CFR 이면 그대로, VFR 이면 <영상 폴더>/.vguide/<이름>.cfr<fps>.mp4 (캐시)
  VGUIDE_NO_CFR=1 이면 변환하지 않는다.
"""
import os
import re
import subprocess


def ffmpeg_exe():
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def probe_rates(path):
    """ffmpeg 배너에서 (평균 fps, tbr) — 둘이 다르면 VFR."""
    r = subprocess.run([ffmpeg_exe(), "-hide_banner", "-i", path], capture_output=True, text=True, errors="replace")
    m = re.search(r"Video:.*?([\d.]+) fps,\s*([\d.]+k?) tbr", r.stderr)
    if not m:
        return None, None
    tbr = m.group(2)
    tbr = float(tbr[:-1]) * 1000 if tbr.endswith("k") else float(tbr)
    return float(m.group(1)), tbr


def is_vfr(path):
    fps, tbr = probe_rates(path)
    return bool(fps and tbr and abs(fps - tbr) / tbr > 0.01)


def ensure_cfr(path, quiet=False):
    path = os.path.abspath(path)
    if os.environ.get("VGUIDE_NO_CFR") or path.endswith(".cfr.mp4") or ".cfr" in os.path.basename(path):
        return path
    fps, tbr = probe_rates(path)
    if not (fps and tbr and abs(fps - tbr) / tbr > 0.01):
        return path
    rate = int(round(tbr)) if tbr <= 60 else 30
    d = os.path.join(os.path.dirname(path), ".vguide")
    os.makedirs(d, exist_ok=True)
    out = os.path.join(d, f"{os.path.splitext(os.path.basename(path))[0]}.cfr{rate}.mp4")
    st = os.stat(path)
    stamp = out + ".src"
    key = f"{st.st_size}:{int(st.st_mtime)}"
    if os.path.exists(out) and os.path.exists(stamp) and open(stamp).read() == key:
        return out
    if not quiet:
        print(f"[media] VFR 원본 (평균 {fps:g}fps, tbr {tbr:g}) → CFR {rate}fps 사본 생성: {out}", flush=True)
    r = subprocess.run([ffmpeg_exe(), "-y", "-loglevel", "error", "-i", path, "-fps_mode", "cfr", "-r", str(rate),
                        "-c:v", "libx264", "-preset", "veryfast", "-crf", "14", "-pix_fmt", "yuv420p",
                        "-c:a", "aac", "-b:a", "192k", out], capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(f"CFR 변환 실패: {r.stderr[-800:]}")
    with open(stamp, "w") as f:
        f.write(key)
    return out
