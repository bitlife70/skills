"""Aggregate raw per-sample analysis into compact instrument profiles (profiles.json)."""
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..'))
PROFILES = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..', 'profiles.json')

import json, numpy as np, collections
from catalog import DYN_VAL
from analyze import GRID, BAND_CTR, PGRID, PBAND_CTR, PBAND_EDGES, SR

raw = json.load(open('analysis_raw.json'))
# which solo instrument supplies per-player vibrato for each section
VIB_SOURCE = {'violins': 'violin_solo', 'violas': 'violin_solo', 'celli': 'cello_solo', 'basses': 'contrabass_solo',
              'flutes': 'flute', 'oboes': 'oboe', 'clarinets': 'clarinet', 'bassoons': 'bassoon',
              'horns': 'horn', 'trumpets': 'trumpet', 'trombones': 'trombone'}
# solo instrument whose dynamic-dependent timbre is borrowed when a section has one dynamic layer
DYN_SOURCE = dict(VIB_SOURCE, violas='violin_solo', choir_female=None, choir_male=None)
FAMILY = {'violins': 'strings', 'violas': 'strings', 'celli': 'strings', 'basses': 'strings', 'violin_solo': 'strings',
          'cello_solo': 'strings', 'contrabass_solo': 'strings', 'harp': 'plucked',
          'flutes': 'woodwinds', 'flute': 'woodwinds', 'piccolo': 'woodwinds', 'oboes': 'woodwinds', 'oboe': 'woodwinds',
          'clarinets': 'woodwinds', 'clarinet': 'woodwinds', 'bassoons': 'woodwinds', 'bassoon': 'woodwinds',
          'contrabassoon': 'woodwinds', 'horns': 'brass', 'horn': 'brass', 'trumpets': 'brass', 'trumpet': 'brass',
          'trombones': 'brass', 'trombone': 'brass', 'tuba': 'brass', 'choir_female': 'choir', 'choir_male': 'choir'}

def med(v, default=None):
    v = [x for x in v if x is not None and np.isfinite(x)]
    return float(np.median(v)) if v else default

tonal = [r for r in raw if 'harm_sus' in r]
perc = [r for r in raw if 'modes' in r]

# ---- sanity filter: detected pitch must be within +-2 octaves (+1 semitone) of the label
ok = []
for r in tonal:
    if r['label'] is not None:
        d = r['midi'] - r['label']
        if min(abs(d - 12 * k) for k in range(-2, 3)) > 1.0: continue
    if max(r['harm_sus']) < -1: continue
    ok.append(r)
tonal = ok

profiles = {}
by = collections.defaultdict(list)
for r in tonal: by[(r['inst'], r['art'])].append(r)

for (inst, art), rs in sorted(by.items()):
    p = profiles.setdefault(inst, dict(kind='tonal', family=FAMILY.get(inst, 'other'), arts={}))
    notes = []
    for r in sorted(rs, key=lambda r: (r['midi'], DYN_VAL[r['dyn']])):
        G = np.array(r['harm_grid']); valid = np.array(r['grid_valid'])
        last = np.where(valid)[0].max()
        notes.append(dict(m=round(r['midi'], 2), dyn=DYN_VAL[r['dyn']], lvl=round(r['level_db'], 1),
                          hs=r['harm_sus'], hg=G[: last + 1].tolist(),
                          ns=r['noise_sus'], na=r['noise_att_abs'], ng=r['noise_grid'], env=r['env'], sus_lvl=round(r['sus_lvl_db'], 1),
                          dur=round(r['dur'], 2), t90=round(r['t90'], 3), hd=r['hdecay'], src=r['src']))
    p['arts'][art] = dict(notes=notes,
                          rise=med([r['rise'] for r in rs]), t90=med([r['t90'] for r in rs]),
                          release_dbps=med([r['release_dbps'] for r in rs], -90.0),
                          ens_cents=med([r['ens_cents'] for r in rs]), am_db=med([r['am_db'] for r in rs]),
                          vib_rate=med([r['vib']['rate'] for r in rs if r['vib']['rate'] > 0]),
                          vib_depth=med([r['vib']['depth'] for r in rs if r['vib']['rate'] > 0]))
    p['ensemble'] = bool(rs[0]['ens'])

for inst, p in profiles.items():
    allm = [n['m'] for a in p['arts'].values() for n in a['notes']]
    p['range'] = [round(min(allm), 1), round(max(allm), 1)]
    sa_ = p['arts'].get('sus')
    if sa_ and sa_.get('am_db'): p['am_db'] = round(sa_['am_db'], 2)
    # per-player vibrato: own (solo) or borrowed from the solo counterpart
    src = VIB_SOURCE.get(inst, inst)
    sp = profiles.get(src, p)
    sa = sp['arts'].get('sus') or next(iter(sp['arts'].values()))
    p['vib'] = dict(rate=sa['vib_rate'] or 5.2, depth=sa['vib_depth'] or 0.0, source=src)
    # dynamic -> level (dB per unit dynamic) from notes of the same pitch measured at several dynamics
    def dyn_slope(prof):
        slopes = []
        for a in prof['arts'].values():
            g = collections.defaultdict(list)
            for n in a['notes']: g[round(n['m'])].append(n)
            for ns in g.values():
                if len(ns) >= 2:
                    ns = sorted(ns, key=lambda n: n['dyn'])
                    if ns[-1]['dyn'] - ns[0]['dyn'] > 0.1 and ns[0]['src'] == ns[-1]['src']:
                        slopes.append((ns[-1]['lvl'] - ns[0]['lvl']) / (ns[-1]['dyn'] - ns[0]['dyn']))
        return med(slopes)
    # dynamic -> timbre: spectral tilt (dB per unit dynamic) vs frequency, from same-source/same-pitch pairs
    def dyn_tilt(prof):
        diffs = []
        for a in prof['arts'].values():
            g = collections.defaultdict(list)
            for n in a['notes']: g[(round(n['m']), n['src'])].append(n)
            for ns in g.values():
                ns = sorted(ns, key=lambda n: n['dyn'])
                if len(ns) < 2 or ns[-1]['dyn'] - ns[0]['dyn'] < 0.1: continue
                lo, hi = ns[0], ns[-1]; f0 = 440 * 2 ** ((lo['m'] - 69) / 12)
                H = min(len(lo['hs']), len(hi['hs'])); fh = f0 * np.arange(1, H + 1)
                d = (np.array(hi['hs'][:H]) - np.array(lo['hs'][:H])) / (hi['dyn'] - lo['dyn'])
                v = np.interp(np.log(BAND_CTR), np.log(fh), d, left=np.nan, right=np.nan)
                diffs.append(v)
        if not diffs: return None
        t = np.nanmedian(np.array(diffs), 0)
        ok = np.isfinite(t)
        if ok.sum() < 3: return None
        t = np.interp(np.arange(len(t)), np.where(ok)[0], t[ok])
        return np.clip(t - np.interp(np.log(500), np.log(BAND_CTR), t), -40, 40)   # 0 dB at 500 Hz; level handled separately
    tl = dyn_tilt(p)
    if tl is None and DYN_SOURCE.get(inst) and DYN_SOURCE[inst] in profiles: tl = dyn_tilt(profiles[DYN_SOURCE[inst]])
    if tl is None:   # family default: +~9 dB/oct brighter per unit dynamic above 500 Hz
        tl = np.clip(9 * np.log2(BAND_CTR / 500), -12, 36)
    p['dyn_tilt'] = np.round(tl, 1).tolist()
    s = dyn_slope(p)
    if s is None and DYN_SOURCE.get(inst): s = dyn_slope(profiles.get(DYN_SOURCE[inst], {'arts': {}}))
    p['dyn_db_per_unit'] = float(np.clip(s if s is not None else 30.0, 24, 45))
    p['dyn_timbre_source'] = DYN_SOURCE.get(inst) if len({n['dyn'] for a in p['arts'].values() for n in a['notes']}) < 2 else inst

# ---- percussion
def series_f0(modes):
    """timpani: principal tone f such that modes sit near f*{1,1.5,2,2.5} (membrane under air loading)."""
    best = (0, None)
    for f in np.geomspace(60, 260, 400):
        sc = 0
        for m in modes:
            for k, w in ((1, 1.0), (1.5, 1.0), (2, 0.8), (2.5, 0.5)):
                if abs(m['f'] / (f * k) - 1) < 0.025: sc += w * 10 ** (m['amp'] / 20)
        if sc > best[0]: best = (sc, f)
    return best[1]

def _mode_db(md, t):
    from orchestra import mode_db
    return float(mode_db(md, np.array([float(t)]))[0])

def mode_band_power(modes, t):
    """predicted modal PSD per band (power/Hz) at time t -> used to split modes from noise residual"""
    out = np.zeros(len(PBAND_CTR))
    bw = np.diff(PBAND_EDGES)
    for m in modes:
        b = np.searchsorted(PBAND_EDGES, m['f']) - 1
        if 0 <= b < len(out):
            a = 10 ** (float(_mode_db(m, t)) / 20)
            out[b] += a * a / 2 / bw[b]
    return out

pby = collections.defaultdict(list)
for r in perc: pby[(r['inst'], r['art'])].append(r)
L = SR  # modal analysis window length used in analyze_perc (1 s)
wh = np.hanning(L); n = np.arange(L) / SR
for (inst, art), rs in sorted(pby.items()):
    p = profiles.setdefault(inst, dict(kind='perc', family='percussion', arts={}))
    hits = []
    for r in rs:
        modes = []
        for m in r['modes']:
            modes.append(dict(m))   # f, amp (at t=0, or at t0 for blooming modes), dec, [t0]
        ref = None
        if inst == 'timpani':
            ref = series_f0(modes)
        elif r['label'] is not None and modes:
            # tuned bars: lowest octave of the label that holds a strong mode (within 24 dB of the strongest)
            top = max(m['amp'] for m in modes)
            for k in range(-1, 4):
                fl = 440 * 2 ** ((r['label'] + 12 * k - 69) / 12)
                near = [m for m in modes if abs(m['f'] / fl - 1) < 0.04 and m['amp'] > top - 24]
                if near: ref = max(near, key=lambda m: m['amp'])['f']; break
        # noise residual = measured band PSD - modal PSD (keeps >= -30 dB of total)
        B = np.array(r['bands']) + r['band_ref_db']
        resid = []
        for gi, t in enumerate(PGRID):
            tot = 10 ** (B[gi] / 10); mp = mode_band_power(modes, t)
            res = np.maximum(tot - mp, tot * 1e-3)
            # where ringing partials dominate the band, what is left is mostly subtraction error, not noise
            if inst in ('glockenspiel', 'xylophone', 'chimes', 'timpani', 'triangle'):   # tuned: leftovers near ringing partials are subtraction error
                res = np.where(mp > 0.25 * tot, np.minimum(res, 0.001 * tot), res)
            resid.append(10 * np.log10(res))
        hits.append(dict(dyn=DYN_VAL[r['dyn']], ref_f=None if ref is None else round(float(ref), 2),
                         modes=modes, bands=np.round(np.array(resid), 1).tolist(), env=r['env'],
                         peak_db=round(r['peak_db'], 1), src=r['src']))
    p['arts'][art] = dict(hits=hits)
    refs = [h['ref_f'] for h in hits if h['ref_f']]
    p['range'] = [round(float(69 + 12 * np.log2(min(refs) / 440)), 1), round(float(69 + 12 * np.log2(max(refs) / 440)), 1)] if refs else None

meta = dict(GRID=GRID.tolist(), BAND_CTR=BAND_CTR.tolist(), PGRID=PGRID.tolist(), PBAND_CTR=PBAND_CTR.tolist(),
            PBAND_EDGES=PBAND_EDGES.tolist(), SR=SR,
            sources=['VSCO-2 Community Edition (CC0) by Versilian Studios',
                     'Sonatina Symphonic Orchestra (CC Sampling+ 1.0) by Mattias Westlund'],
            note='Profiles contain only measured acoustic parameters, no audio.')
json.dump(dict(meta=meta, instruments=profiles), open(PROFILES, 'w'), separators=(',', ':'))
for k, p in profiles.items():
    print(k.ljust(16), p['kind'], p.get('range'), {a: len(v.get('notes', v.get('hits', []))) for a, v in p['arts'].items()},
          'vib', p.get('vib'), 'dyn', p.get('dyn_db_per_unit'),
          'ens', {a: v.get('ens_cents') and round(v['ens_cents'], 1) for a, v in p['arts'].items() if 'ens_cents' in v})
import os; print('size MB', os.path.getsize(PROFILES) / 1e6)
