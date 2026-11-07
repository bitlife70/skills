"""A/B listening file: real recording -> synthesized reproduction, for several instruments."""
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..'))
PROFILES = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..', 'profiles.json')

import json, numpy as np, soundfile as sf
from scipy.signal import fftconvolve
import orchestra as O

SR = 44100
PAIRS = [  # (file, part used for synthesis, articulation, seconds)
    ('sso__1st_Violins__1st-violins-sus-a#4.flac', 'violins1', 'sus', 3.0),
    ('sso__Celli__celli-sus-d#3.flac', 'celli', 'sus', 3.0),
    ('sso__Celli__celli-piz-rr1-a3.flac', 'celli', 'pizz', 1.2),
    ('sso__Violas__violas-stc-rr1-c4.flac', 'violas', 'staccato', 0.8),
    ('sso__Flutes__flutes-sus-a4.flac', 'flutes', 'sus', 3.0),
    ('sso__Oboe__oboe-a#4.flac', 'oboe_solo', 'sus', 3.0),
    ('sso__Clarinets__clarinets-sus-d4.flac', 'clarinets', 'sus', 3.0),
    ('sso__Horns__horns-sus-ff-a#3-PB-loop.flac', 'horns', 'sus', 3.0),
    ('sso__Trumpets__trumpets-sus-c#5.flac', 'trumpets', 'sus', 3.0),
    ('sso__Trombones__trombones-sus-a#2.flac', 'trombones', 'sus', 3.0),
    ('sso__Harp__harp-c4.flac', 'harp', 'hit', 2.0),
    ('sso__Chorus__chorus-female-a4.flac', 'choir_female', 'sus', 3.0),
    ('sso__Percussion__timpani-f-rh-a1.flac', 'timpani', 'hit', 2.5),
    ('sso__Percussion__piatti.flac', 'cymbals', 'hit', 3.0),
    ('sso__Percussion__glockenspiel-c6.flac', 'glockenspiel', 'hit', 2.0),
]

def room(x, rt=0.9, mix=0.18, seed=3):
    ir = O.hall_ir(rt, seed=seed, predelay=0.008)[:, 0]
    w = fftconvolve(x, ir)[: len(x)]
    return x + w / (np.abs(w).max() + 1e-9) * np.abs(x).max() * mix

def main(out='ab_real_vs_synth.wav'):
    raw = {r['file']: r for r in json.load(open('analysis_raw.json'))}
    seq = []; log = []; pairs = []
    for f, part, art, sec in PAIRS:
        try:
            x, sr = __import__('soundfile').read('flac/' + f)
        except Exception as ex:
            print('skip', f, ex); continue
        r = raw.get(f)
        x = x[: int(sec * SR)]
        x = x * np.minimum(1, (len(x) - np.arange(len(x))) / (0.05 * SR))
        cfg = O.PARTS[part]; inst = O.Inst(cfg['inst'])
        if inst.kind == 'perc':
            m = None if part == 'cymbals' else (r and None)
            ref_m = None
            if part == 'timpani':
                h = min(inst.p['arts']['hit']['hits'], key=lambda h: 0 if f.endswith(h.get('src', '')) else 1)
            hits = [h for a in inst.p['arts'].values() for h in a['hits']]
            raws = [q for q in json.load(open('analysis_raw.json')) if q.get('inst') == cfg['inst'] and 'modes' in q]
            order = [q['file'] for a_ in inst.p['arts'] for q in raws if q['art'] == a_]
            h = hits[order.index(f)] if f in order else hits[0]
            y = O.perc_hit(inst, None, h['dyn'], seed=2, hit=h).mean(1)
        else:
            m = r['midi']; d = O.DYN.get(r['dyn'], 4 / 7)
            y = O.tonal_note(inst, m, sec * (0.85 if art == 'sus' else 1), d, None, art, voices=cfg['voices'], seed=4).mean(1)
        y = room(y)[: int(sec * SR)]
        y = y * np.minimum(1, (len(y) - np.arange(len(y))) / (0.05 * SR))
        # loudness-match (RMS)
        y = y / (np.sqrt(np.mean(y ** 2)) + 1e-12) * np.sqrt(np.mean(x ** 2))
        seq += [x, np.zeros(int(0.45 * SR)), y, np.zeros(int(1.0 * SR))]; pairs.append((part + ' ' + art, x, y))
        log.append(f'{part:13s} {art:8s} real -> synth')
    a = np.concatenate(seq); a = a / np.abs(a).max() * 0.89
    sf.write(out, np.stack([a, a], 1), SR, subtype='PCM_16')
    print('\n'.join(log)); print('wrote', out, len(a) / SR, 's')
    return pairs

def spectrograms(pairs, png='ab_spectrograms.png'):
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    from scipy.signal import spectrogram
    rows = (len(pairs) + 2) // 3
    fig, ax = plt.subplots(rows, 6, figsize=(18, 2.6 * rows)); ax = ax.ravel()
    for i, (n, r, s) in enumerate(pairs):
        for j, seg in enumerate((r, s)):
            f, tt, S = spectrogram(seg, SR, nperseg=2048, noverlap=1536)
            A = ax[2 * i + j]; A.pcolormesh(tt, f, 10 * np.log10(S + 1e-12), vmin=-115, vmax=-30, shading='auto', cmap='magma')
            A.set_ylim(0, 9000 if any(k in n for k in ('cymbal', 'glock')) else 5000)
            A.set_title(n + (' - REAL' if j == 0 else ' - SYNTH'), fontsize=9); A.tick_params(labelsize=6)
    for k in range(2 * len(pairs), len(ax)): ax[k].axis('off')
    plt.tight_layout(); plt.savefig(png, dpi=70)

if __name__ == '__main__':
    spectrograms(main())
