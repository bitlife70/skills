"""Build src/timing.js from lines.json + recorded narration.
lines.json: [{"n":1,"scene":"D1","sub":"자막 원문","tts":"발음 표기","file":"voice/p01.wav"}, ...]
Edit HL (highlight keywords), EXTRA (extra pause after line n), OVR (manual subtitle chunks for awkward splits), TITLE (silent title scene).
Usage: python3 tools/build_timing.py   (run from the project root)"""
import json, re, wave, numpy as np
L = json.load(open('lines.json'))
LEAD, GAP, TAIL = 0.7, 0.45, 1.3          # lead-in, gap between lines, tail after a scene's last line
TITLE = ('D0', 6.5)                        # silent title scene (id, seconds) or None
EXTRA = {}                                 # {line_n: extra_seconds} — breathing room at scene ends (0.3–0.5)
HL = []                                    # keywords to highlight in subtitles (first match per chunk)
OVR = {}                                   # {line_n: ['chunk 1', 'chunk 2', ...]} — must concatenate to the sub text
CLOSING_HOLD = {}                          # {scene_id: extra seconds at the very end}
def chunks(s, mx=30):
    parts = re.split(r'(?<=[.,?])\s+', s); out = []; cur = ''
    for p in parts:
        if not cur: cur = p
        elif len(cur) + 1 + len(p) <= mx: cur += ' ' + p
        else: out.append(cur); cur = p
    if cur: out.append(cur)
    res = []
    for c in out:
        while len(c) > mx + 8:
            sp = [m.start() for m in re.finditer(' ', c)]; k = min(sp, key=lambda x: abs(x - len(c) / 2)); res.append(c[:k]); c = c[k + 1:]
        res.append(c)
    return res
def hl(c):
    for w in HL:
        if w in c: return c.replace(w, '*' + w + '*', 1)
    return c
def meta(f):
    w = wave.open(f); n = w.getnframes(); sr = w.getframerate(); ch = w.getnchannels(); sw = w.getsampwidth()
    a = np.frombuffer(w.readframes(n), dtype=np.int16 if sw == 2 else np.int32).astype(float)
    if ch > 1: a = a.reshape(-1, ch).mean(1)
    a = np.abs(a); idx = np.where(a > a.max() * 0.02)[0]          # speech start/end at 2% of peak
    return {'dur': n / sr, 's': idx[0] / sr, 'e': idx[-1] / sr}
for n, cs in OVR.items():
    assert ''.join(cs).replace(' ', '') == L[n - 1]['sub'].replace(' ', ''), f'OVR {n} does not match its subtitle'
scenes = {}; order = []
for l in L:
    v = meta(l['file']); sc = l['scene']
    if sc not in scenes: scenes[sc] = {'lines': [], 't': LEAD}; order.append(sc)
    S = scenes[sc]; t0 = S['t']; s, e = v['s'], v['e']
    cs = OVR.get(l['n']) or chunks(l['sub']); tot = sum(len(c) for c in cs); acc = 0; subs = []
    for c in cs:
        a = t0 + s + (e - s) * acc / tot; acc += len(c); b = t0 + s + (e - s) * acc / tot
        subs.append([round(float(a), 3), round(float(b), 3), hl(c)])
    S['lines'].append({'n': l['n'], 't0': round(float(t0), 3), 's': round(float(t0 + s), 3), 'e': round(float(t0 + e), 3), 'file': l['file'], 'subs': subs})
    S['t'] = t0 + v['dur'] + GAP + EXTRA.get(l['n'], 0)
out = []; T = 0
if TITLE: out.append({'id': TITLE[0], 't0': 0, 'dur': TITLE[1], 'lines': []}); T = TITLE[1]
for sc in order:
    S = scenes[sc]; d = round(float(S['t'] - GAP + TAIL + CLOSING_HOLD.get(sc, 0)), 3)
    out.append({'id': sc, 't0': round(T, 3), 'dur': d, 'lines': S['lines']}); T += d
open('src/timing.js', 'w').write('const TM=' + json.dumps(out, ensure_ascii=False) + ';\n')
json.dump(out, open('timing.json', 'w'), ensure_ascii=False)
print('total', round(T, 1), 's')
for s in out: print(s['id'], round(s['t0'], 1), round(s['dur'], 1), [round(x['s'], 1) for x in s['lines']])
