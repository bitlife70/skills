"""Narration mixdown + loudness normalisation + SRT, then concat scenes and mux.
Usage: python3 tools/mix.py OUTPUT.mp4 [SUBS.srt]   (run from the project root after tools/render.mjs)
Env: NOSUB_LAST=n — the last n lines are on-screen big text; the SRT gets one combined cue for them."""
import json, wave, numpy as np, subprocess, sys, os
T = json.load(open('timing.json')); SR = 44100
out_mp4 = sys.argv[1] if len(sys.argv) > 1 else 'output.mp4'; out_srt = sys.argv[2] if len(sys.argv) > 2 else out_mp4.rsplit('.', 1)[0] + '.srt'
nosub = int(os.environ.get('NOSUB_LAST', '0'))
tot = T[-1]['t0'] + T[-1]['dur']; buf = np.zeros(int(tot * SR) + SR)
def load(f):
    w = wave.open(f); sr = w.getframerate(); ch = w.getnchannels(); a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    if ch > 1: a = a.reshape(-1, ch).mean(1)
    if sr != SR: a = np.interp(np.arange(0, len(a), sr / SR), np.arange(len(a)), a)
    return a
def ts(x): h = int(x // 3600); m = int(x % 3600 // 60); s = x % 60; return ('%02d:%02d:%06.3f' % (h, m, s)).replace('.', ',')
lines = [(sc, l) for sc in T for l in sc['lines']]; tail = lines[-nosub:] if nosub else []
srt = []; k = 1
for sc, l in lines:
    a = load(l['file']); i = int((sc['t0'] + l['t0']) * SR); buf[i:i + len(a)] += a
    if (sc, l) in tail: continue
    for j, (a0, b0, tx) in enumerate(l['subs']):
        e = b0 + (.3 if j == len(l['subs']) - 1 else 0)
        srt.append('%d\n%s --> %s\n%s\n' % (k, ts(sc['t0'] + a0), ts(sc['t0'] + e), tx.replace('*', ''))); k += 1
if tail:
    sc, l = tail[0]; txt = ' '.join(''.join(s[2] for s in x['subs']).replace('*', '') for _, x in tail)
    srt.append('%d\n%s --> %s\n%s\n' % (k, ts(sc['t0'] + l['s']), ts(tot - .5), txt))
open(out_srt, 'w').write('\n'.join(srt))
buf = np.clip(buf, -1, 1); w = wave.open('_narr.wav', 'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((buf * 32767).astype(np.int16).tobytes()); w.close()
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', '_narr.wav', '-af', 'highpass=f=70,loudnorm=I=-16:TP=-1.5:LRA=11', '-ar', '48000', '-ac', '2', '_narr_n.wav'], check=True)
open('_list.txt', 'w').write(''.join("file '_scenes/%s.mp4'\n" % s['id'] for s in T))
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', '_list.txt', '-c', 'copy', '_video.mp4'], check=True)
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', '_video.mp4', '-i', '_narr_n.wav', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart', out_mp4], check=True)
print('done', out_mp4, round(tot, 1), 's,', k, 'subtitle cues')
