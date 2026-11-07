"""Closed-loop validation: synthesize notes, re-analyse them with the SAME analyser used on the real
recordings, compare, and calibrate the per-player detune of every section so that the synthetic
section's spectral line spread matches the measured real section."""
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..'))
PROFILES = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..', 'profiles.json')

import json, sys, numpy as np, soundfile as sf
import analyze as A
import orchestra as O
from catalog import load_catalog

CACHE = {}
ONLY = []
_orig_load = A.load
def _load(path):
    k = path.split('/')[-1]
    return CACHE[k] if k in CACHE else _orig_load(path)
A.load = _load

def synth_mono(inst_key, m, dur, dyn, art, voices, detune=None, seed=5, vib_scale=None):
    inst = O.Inst(inst_key)
    y = O.tonal_note(inst, m, dur, dyn, None, art, voices=voices, detune=detune, seed=seed, pan=0.0, width=0.0, vib_scale=vib_scale)
    y = y.mean(1)
    return np.concatenate([np.zeros(2205), y])

def reanalyse(y, rec, tag):
    key = f'synth__{tag}.flac'; CACHE[key] = y
    r = dict(rec, file=key)
    return A.analyze_tonal(r)

def compare(real, syn, H=20):
    a = np.array(real['harm_sus'][:H]); b = np.array(syn['harm_sus'][:H]); n = min(len(a), len(b))
    a, b = a[:n], b[:n]; m = a > -50
    f = real['f0'] * np.arange(1, n + 1)
    cen = lambda v: float((f * 10 ** (v / 10)).sum() / (10 ** (v / 10)).sum())
    return dict(spec_err_db=float(np.mean(np.abs(a[m] - b[m]))), centroid_real=cen(a), centroid_syn=cen(b),
                t90_real=real['t90'], t90_syn=syn['t90'], ens_real=real['ens_cents'], ens_syn=syn['ens_cents'],
                noise_err_db=float(np.mean(np.abs(np.array(real['noise_sus']) - np.array(syn['noise_sus'])))))

VOICES = {v['inst']: v['voices'] for v in O.PARTS.values()}

def calibrate(prof):
    raw = json.load(open('analysis_raw.json'))
    cat = {c['file']: c for c in load_catalog()}
    out = {}
    for inst, p in prof['instruments'].items():
        if p['kind'] != 'tonal' or not p.get('ensemble') or 'sus' not in p['arts']: continue
        if ONLY and inst not in ONLY: continue
        target = p['arts']['sus']['ens_cents']
        reals = [r for r in raw if r.get('inst') == inst and r.get('art') == 'sus' and r.get('ens_cents') is not None]
        reals = sorted(reals, key=lambda r: r['midi'])
        picks = [reals[len(reals) // 4], reals[len(reals) // 2], reals[3 * len(reals) // 4]]
        nv = VOICES.get(inst, 4)
        res = []
        for det in (0.0, 3.0, 6.0, 10.0, 15.0, 22.0):
            w = []
            for r in picks:
                y = synth_mono(inst, r['midi'], 3.2, r['dyn'], 'sus', nv, detune=det)
                s = reanalyse(y, cat[r['file']], f'{inst}_{det}')
                if s['ens_cents'] is not None: w.append(s['ens_cents'])
            res.append((det, float(np.median(w))))
        dets, ws = zip(*res)
        # monotone interpolation of measured width -> detune
        ws_m = np.maximum.accumulate(np.array(ws))
        vsc = 1.0
        if target < ws_m[0]:      # even perfectly in tune players are too wide -> reduce per-player vibrato/drift
            vres = [(1.0, ws_m[0])]
            for sc in (0.7, 0.45, 0.25, 0.1):
                w = []
                for r in picks:
                    y = synth_mono(inst, r['midi'], 3.2, r['dyn'], 'sus', nv, detune=0.0, vib_scale=sc)
                    s = reanalyse(y, cat[r['file']], f'{inst}_v{sc}')
                    if s['ens_cents'] is not None: w.append(s['ens_cents'])
                vres.append((sc, float(np.median(w))))
            scs, wv = zip(*sorted(vres))
            vsc = float(np.interp(target, np.maximum.accumulate(np.array(wv)), scs))
            print(f'   {inst}: vibrato scale curve {[(a, round(b, 1)) for a, b in vres]} -> {vsc:.2f}', flush=True)
        if target <= ws_m[0]: d = 0.0
        elif target >= ws_m[-1]: d = dets[-1]
        else: d = float(np.interp(target, ws_m, dets))
        out[inst] = dict(target=target, curve=res, detune=round(d, 1), vib_scale=round(vsc, 2))
        print(f'{inst:14s} real spread {target:5.1f} c | synth width by detune {[(a, round(b, 1)) for a, b in res]} -> detune {d:.1f} c', flush=True)
    return out

def report(prof):
    raw = json.load(open('analysis_raw.json'))
    cat = {c['file']: c for c in load_catalog()}
    rows = []
    for inst, p in prof['instruments'].items():
        if p['kind'] != 'tonal': continue
        for art in p['arts']:
            reals = sorted([r for r in raw if r.get('inst') == inst and r.get('art') == art and 'harm_sus' in r], key=lambda r: r['midi'])
            if not reals: continue
            for r in [reals[len(reals) // 3], reals[2 * len(reals) // 3]]:
                dur = 3.0 if art in ('sus', 'trem') else 0.6
                y = synth_mono(inst, r['midi'], dur, r['dyn'], art, VOICES.get(inst, 1))
                s = reanalyse(y, cat[r['file']], f'rep_{inst}_{art}')
                c = compare(r, s); c.update(inst=inst, art=art, midi=round(r['midi'], 1), file=r['file'])
                rows.append(c)
                print(f"{inst:14s} {art:9s} m{c['midi']:5.1f} spec err {c['spec_err_db']:4.1f} dB | centroid {c['centroid_real']:6.0f}/{c['centroid_syn']:6.0f} Hz"
                      f" | t90 {c['t90_real']:.2f}/{c['t90_syn']:.2f}s | spread {c['ens_real'] and round(c['ens_real'], 1)}/{c['ens_syn'] and round(c['ens_syn'], 1)}c", flush=True)
    return rows

def perc_calibrate(prof, iters=3):
    """analysis-by-synthesis for percussion: correct each mode's amplitude/decay and the noise residual
    so that re-analysing the synthetic hit gives the same modal peaks and band envelopes as the recording."""
    raw = [r for r in json.load(open('analysis_raw.json')) if 'modes' in r]
    O._P = prof
    for inst_key, p in prof['instruments'].items():
        if p['kind'] != 'perc': continue
        inst = O.Inst(inst_key)
        errs0, errs1 = [], []
        for art, a in p['arts'].items():
            reals = [r for r in raw if r['inst'] == inst_key and r['art'] == art]
            for h, r in zip(a['hits'], reals):
                real_tot = np.array(r['bands']) + r['band_ref_db']
                real_modes = {round(m['f'], 2): m for m in r['modes']}
                B0 = np.array(h['bands'])
                pe = np.array(prof['meta']['PBAND_EDGES']); bw = np.diff(pe); mdom = np.zeros_like(B0, bool)
                for gi, tg in enumerate(A.PGRID):
                    mp = np.zeros(len(bw))
                    for md in h['modes']:
                        b_ = np.searchsorted(pe, md['f']) - 1
                        if 0 <= b_ < len(bw):
                            a_ = 10 ** (float(O.mode_db(md, np.array([tg]))[0]) / 20)
                            mp[b_] += a_ * a_ / 2 / bw[b_]
                    mdom[gi] = (mp > 0.25 * 10 ** (real_tot[gi] / 10)) & (inst_key in ('glockenspiel', 'xylophone', 'chimes', 'timpani', 'triangle'))
                for it in range(iters):
                    y = O.perc_hit(inst, None, h['dyn'], art, seed=11, hit=h).mean(1) * np.sqrt(2)
                    CACHE['pc.flac'] = np.concatenate([np.zeros(64), y])
                    s = A.analyze_perc(dict(file='pc.flac', inst=inst_key, art=art, dyn='mf', src='x', label=None))
                    syn_tot = np.array(s['bands']) + s['band_ref_db']
                    e = np.mean(np.abs((syn_tot - real_tot)[:14][real_tot[:14] > real_tot.max() - 70]))
                    (errs0 if it == 0 else errs1).append(e) if it in (0, iters - 1) else None
                    # modes: match measured peak amplitude / decay at the same frequency
                    for md in h['modes']:
                        sm = min(s['modes'], key=lambda q: abs(q['f'] - md['f'])) if s['modes'] else None
                        rm = min(r['modes'], key=lambda q: abs(q['f'] - md['f']))
                        if sm and abs(sm['f'] / md['f'] - 1) < 0.01:
                            dlt = round(0.8 * float(np.clip(rm['amp'] - sm['amp'], -12, 12)), 1)
                            md['amp'] = round(md['amp'] + dlt, 1)
                            if 'trk' in md: md['trk'] = [round(x + dlt, 1) for x in md['trk']]
                            if 't0' in rm: md['t0'] = rm['t0']
                            if 'dec2' not in md and 'trk' not in md: md['dec'] = round(min(-0.5, md['dec'] + 0.6 * np.clip(rm['dec'] - sm['dec'], -20, 20)), 1)
                    # noise residual: close the band-envelope gap
                    B = np.array(h['bands'])
                    B = B + 0.8 * np.clip(real_tot - syn_tot, -15, 15)
                    B = np.clip(B, B0 - 6, B0 + 6)          # calibration may fine-tune the analysed residual by +-6 dB only
                    B = np.where(mdom, np.minimum(B, B0), B)  # bands dominated by ringing partials: noise may only go down
                    h['bands'] = np.round(np.minimum(np.maximum(B, real_tot - 40), real_tot), 1).tolist()
        if errs0:
            print(f'{inst_key:13s} band-envelope error {np.median(errs0):5.1f} dB -> {np.median(errs1):5.1f} dB  ({len(errs0)} hits)', flush=True)
    return prof

def noise_calibrate(prof, iters=3, per=5):
    """closed loop for the noise component: what the analyser calls 'noise' on a real note also contains
    harmonic leakage (decaying-line skirts, window sidelobes). Synthesize, re-measure with the same analyser,
    and store pitch-dependent corrections (at `per` pitches, interpolated between) so the re-measured noise
    equals the real one."""
    raw = json.load(open('analysis_raw.json'))
    cat = {c['file']: c for c in load_catalog()}
    O._P = prof
    for inst, p in prof['instruments'].items():
        if p['kind'] != 'tonal': continue
        for art, a in p['arts'].items():
            reals = sorted([r for r in raw if r.get('inst') == inst and r.get('art') == art and 'noise_grid' in r], key=lambda r: r['midi'])
            if not reals: continue
            idx = sorted(set(int(round(q * (len(reals) - 1))) for q in np.linspace(0.0, 1.0, per)))
            picks = [reals[i] for i in idx]
            G = len(A.GRID); nb = len(A.BAND_CTR)
            cg = np.zeros((len(picks), G, nb)); cs = np.zeros((len(picks), nb))
            a['ncorr_m'] = [round(r['midi'], 2) for r in picks]
            for k in ('ng_corr', 'ns_corr'): a.pop(k, None)
            errs = []
            for it in range(iters):
                a['ng_corrs'] = np.round(cg, 1).tolist(); a['ns_corrs'] = np.round(cs, 1).tolist()
                e_it = []
                for j, r in enumerate(picks):
                    dur = 3.0 if art in ('sus', 'trem') else 0.8
                    y = synth_mono(inst, r['midi'], dur, r['dyn'], art, VOICES.get(inst, 1))
                    s_ = reanalyse(y, cat[r['file']], f'nc_{inst}_{art}')
                    dg = np.array(r['noise_grid']) - np.array(s_['noise_grid'])
                    ds = np.array(r['noise_sus']) - np.array(s_['noise_sus'])
                    e_it.append(float(np.median(np.abs(dg))))
                    cg[j] = np.clip(cg[j] + 0.8 * np.clip(dg, -20, 12), -45, 15)
                    cs[j] = np.clip(cs[j] + 0.8 * np.clip(ds, -20, 12), -45, 15)
                errs.append(float(np.median(e_it)))
            a['ng_corrs'] = np.round(cg, 1).tolist(); a['ns_corrs'] = np.round(cs, 1).tolist()
            print(f'{inst:14s} {art:9s} noise-grid error by iteration {[round(e, 1) for e in errs]} dB', flush=True)
    return prof

if __name__ == '__main__':
    if 'noisecal' in sys.argv:
        prof = json.load(open(PROFILES))
        prof = noise_calibrate(prof)
        json.dump(prof, open(PROFILES, 'w'), separators=(',', ':'))
    if 'perccal' in sys.argv:
        prof = json.load(open(PROFILES))
        prof = perc_calibrate(prof)
        json.dump(prof, open(PROFILES, 'w'), separators=(',', ':'))
    prof = json.load(open(PROFILES))
    if 'calib' in sys.argv:
        ONLY[:] = [a.split('=')[1] for a in sys.argv if a.startswith('only=')][0].split(',') if any(a.startswith('only=') for a in sys.argv) else []
        cal = calibrate(prof)
        for k, v in cal.items(): prof['instruments'][k]['calib_detune'] = v['detune']; prof['instruments'][k]['calib_vib_scale'] = v['vib_scale']
        json.dump(prof, open(PROFILES, 'w'), separators=(',', ':'))
        json.dump(cal, open('calibration.json', 'w'), indent=1)
    if 'report' in sys.argv:
        O._P = None
        rows = report(json.load(open(PROFILES)))
        json.dump(rows, open('validation.json', 'w'), indent=1)
        e = [r['spec_err_db'] for r in rows]
        print('median spectral error %.2f dB, 90th pct %.2f dB over %d notes' % (np.median(e), np.percentile(e, 90), len(e)))
