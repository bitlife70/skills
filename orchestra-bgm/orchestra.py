"""orchestra.py - profile-driven orchestral synthesizer.

Every instrument is re-synthesized from parameters measured on real recordings (profiles.json):
harmonic spectra per pitch, attack/decay evolution, bow/breath noise, vibrato, dynamic-dependent
timbre, and for sections the measured ensemble spread. A section part is rendered as N virtual
players (own detune, vibrato, timing, timbre deviation, seat position) so that the sum behaves
like a real section rather than one instrument made louder.

Quick use:
    from orchestra import Score
    s = Score(bpm=90)
    s.chord('violins1', 0, ['D5', 'F5'], 4, dyn='p', dyn_end='mf')
    s.line('horns', 0, 'D4:1 F4:1 A4:2', dyn='mf', legato=True)
    s.hit('timpani', 0, 'D2', dyn='f')
    s.render('out.wav')
"""
import os, json, re, functools, zlib
import numpy as np
from scipy.signal import fftconvolve, butter, sosfilt

SR = 44100
HERE = os.path.dirname(os.path.abspath(__file__))
_P = None

def profiles():
    global _P
    if _P is None:
        _P = json.load(open(os.environ.get('ORCH_PROFILES', os.path.join(HERE, 'profiles.json'))))
    return _P

def meta(k): return np.array(profiles()['meta'][k])

DYN = {'ppp': 0.0, 'pp': 1 / 7, 'p': 2 / 7, 'mp': 3 / 7, 'mf': 4 / 7, 'f': 5 / 7, 'ff': 6 / 7, 'fff': 1.0}
PC = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}

def midi(p):
    """'C#4' / 'Bb3' / 60 -> midi number (C4 = 60)."""
    if isinstance(p, (int, float, np.integer, np.floating)): return float(p)
    m = re.fullmatch(r'\s*([A-Ga-g])([#b]*)(-?\d)\s*', p)
    if not m: raise ValueError('bad pitch ' + p)
    return float(12 * (int(m.group(3)) + 1) + PC[m.group(1).upper()] + m.group(2).count('#') - m.group(2).count('b'))

def dynv(d):
    if d is None: return None
    return float(np.clip(DYN[d] if isinstance(d, str) else d, 0, 1))

def mtof(m): return 440.0 * 2 ** ((m - 69) / 12)

# ------------------------------------------------------------------ parts (orchestra seating)
# inst: profile key, voices: virtual players, pan: seat centre (-1 L .. 1 R), width: spread of the
# section across the stage, depth: 1 = front of stage .. 4 = back wall, gain: balance at equal dynamic (dB)
PARTS = {
    'violins1':     dict(inst='violins', voices=8, pan=-0.62, width=0.38, depth=1.0, gain=0.0),
    'violins2':     dict(inst='violins', voices=7, pan=-0.22, width=0.30, depth=1.3, gain=-1.0),
    'violas':       dict(inst='violas', voices=6, pan=0.18, width=0.28, depth=1.3, gain=-0.5),
    'celli':        dict(inst='celli', voices=6, pan=0.48, width=0.30, depth=1.2, gain=0.0),
    'basses':       dict(inst='basses', voices=5, pan=0.72, width=0.22, depth=1.8, gain=-1.0),
    'flutes':       dict(inst='flutes', voices=2, pan=-0.14, width=0.10, depth=2.2, gain=-3.0),
    'piccolo':      dict(inst='piccolo', voices=1, pan=-0.22, width=0.0, depth=2.2, gain=-6.0),
    'oboes':        dict(inst='oboes', voices=2, pan=0.10, width=0.10, depth=2.2, gain=-3.0),
    'clarinets':    dict(inst='clarinets', voices=2, pan=-0.12, width=0.10, depth=2.6, gain=-3.0),
    'bassoons':     dict(inst='bassoons', voices=2, pan=0.14, width=0.10, depth=2.6, gain=-2.0),
    'contrabassoon':dict(inst='contrabassoon', voices=1, pan=0.25, width=0.0, depth=2.7, gain=-3.0),
    'horns':        dict(inst='horns', voices=4, pan=-0.42, width=0.22, depth=3.0, gain=1.0),
    'trumpets':     dict(inst='trumpets', voices=3, pan=0.12, width=0.14, depth=3.2, gain=0.0),
    'trombones':    dict(inst='trombones', voices=3, pan=0.38, width=0.16, depth=3.2, gain=0.0),
    'tuba':         dict(inst='tuba', voices=1, pan=0.54, width=0.0, depth=3.2, gain=-1.0),
    'harp':         dict(inst='harp', voices=1, pan=-0.70, width=0.0, depth=1.8, gain=-2.0),
    'choir_female': dict(inst='choir_female', voices=6, pan=-0.25, width=0.5, depth=3.8, gain=-2.0),
    'choir_male':   dict(inst='choir_male', voices=6, pan=0.25, width=0.5, depth=3.8, gain=-2.0),
    'violin_solo':  dict(inst='violin_solo', voices=1, pan=-0.35, width=0.0, depth=0.7, gain=-1.0),
    'cello_solo':   dict(inst='cello_solo', voices=1, pan=0.30, width=0.0, depth=0.7, gain=-1.0),
    'flute_solo':   dict(inst='flute', voices=1, pan=-0.12, width=0.0, depth=2.2, gain=-3.0),
    'oboe_solo':    dict(inst='oboe', voices=1, pan=0.08, width=0.0, depth=2.2, gain=-3.0),
    'clarinet_solo':dict(inst='clarinet', voices=1, pan=-0.10, width=0.0, depth=2.6, gain=-3.0),
    'bassoon_solo': dict(inst='bassoon', voices=1, pan=0.12, width=0.0, depth=2.6, gain=-3.0),
    'horn_solo':    dict(inst='horn', voices=1, pan=-0.40, width=0.0, depth=3.0, gain=-1.0),
    'trumpet_solo': dict(inst='trumpet', voices=1, pan=0.12, width=0.0, depth=3.2, gain=-2.0),
    'trombone_solo':dict(inst='trombone', voices=1, pan=0.36, width=0.0, depth=3.2, gain=-2.0),
    'timpani':      dict(inst='timpani', voices=1, pan=-0.08, width=0.0, depth=3.6, gain=0.0),
    'bass_drum':    dict(inst='bass_drum', voices=1, pan=0.30, width=0.0, depth=3.8, gain=-2.0),
    'cymbals':      dict(inst='cymbals', voices=1, pan=0.35, width=0.0, depth=3.8, gain=-4.0),
    'sus_cymbal':   dict(inst='sus_cymbal', voices=1, pan=0.40, width=0.0, depth=3.8, gain=-5.0),
    'snare':        dict(inst='snare', voices=1, pan=0.25, width=0.0, depth=3.8, gain=-5.0),
    'tamtam':       dict(inst='tamtam', voices=1, pan=0.45, width=0.0, depth=3.9, gain=-3.0),
    'triangle':     dict(inst='triangle', voices=1, pan=0.30, width=0.0, depth=3.7, gain=-8.0),
    'glockenspiel': dict(inst='glockenspiel', voices=1, pan=0.20, width=0.0, depth=3.5, gain=-8.0),
    'xylophone':    dict(inst='xylophone', voices=1, pan=0.22, width=0.0, depth=3.5, gain=-7.0),
    'chimes':       dict(inst='chimes', voices=1, pan=0.35, width=0.0, depth=3.7, gain=-7.0),
}
ART_ALIAS = {'spiccato': 'staccato', 'stac': 'staccato', 'tremolo': 'trem', 'pizzicato': 'pizz', 'legato': 'sus',
             'sustain': 'sus', 'arco': 'sus'}
DEFAULT_DETUNE = {'strings': 6.0, 'woodwinds': 4.0, 'brass': 3.5, 'choir': 8.0, 'plucked': 2.0}

# ------------------------------------------------------------------ spectral model
def _shape_rows(rows):
    """normalise each grid row so its total harmonic power is 0 dB (spectral shape only)."""
    rows = np.asarray(rows, float)
    tot = 10 * np.log10(np.sum(10 ** (rows / 10), axis=-1, keepdims=True) + 1e-12)
    return rows - tot

def _map_env(levels, f0n, fq, roll=15.0):
    """dB at harmonics of f0n -> dB at frequencies fq (log-frequency spectral envelope)."""
    levels = np.asarray(levels, float); H = len(levels)
    fh = f0n * np.arange(1, H + 1)
    out = np.interp(np.log(fq), np.log(fh), levels)
    hi = fq > fh[-1]
    out[hi] = levels[-1] - roll * np.log2(fq[hi] / fh[-1])
    return out

class Inst:
    """interpolating access to one instrument profile."""
    def __init__(self, key):
        P = profiles()['instruments']
        if key not in P: raise KeyError('no profile for ' + key)
        self.key, self.p = key, P[key]
        self.kind = self.p['kind']
        self.grid = meta('GRID'); self.bands = meta('BAND_CTR')
        self.tilt = np.array(self.p.get('dyn_tilt', [0] * len(self.bands)))
        self.dyn_db = self.p.get('dyn_db_per_unit', 30.0)
        self.det = self.p.get('calib_detune', DEFAULT_DETUNE.get(self.p.get('family'), 4.0))
        self.vscale = self.p.get('calib_vib_scale', 1.0)

    def art(self, a):
        a = ART_ALIAS.get(a, a) if a else 'sus'
        arts = self.p['arts']
        if a in arts: return a, False
        if a in ('staccato',) and 'sus' in arts: return 'sus', 'short'
        if a in ('trem',) and 'sus' in arts: return 'sus', 'trem'
        if a == 'marcato' and 'sus' in arts: return 'sus', 'marcato'
        return next(iter(arts)), False

    def neighbours(self, art, m, d):
        """notes bracketing pitch m (all dynamics at the 2 nearest pitches), weighted."""
        notes = self.p['arts'][art]['notes']
        ms = np.array([n['m'] for n in notes])
        lo = ms[ms <= m + 1e-6]; hi = ms[ms >= m - 1e-6]
        picks = []
        if len(lo) and len(hi):
            a, b = lo.max(), hi.min()
            if abs(b - a) < 1e-6: picks = [(a, 1.0)]
            else: picks = [(a, (b - m) / (b - a)), (b, (m - a) / (b - a))]
        else:
            picks = [((lo.max() if len(lo) else hi.min()), 1.0)]
        out = []
        for pm, w in picks:
            cand = [n for n in notes if abs(n['m'] - pm) < 0.35]
            ws = np.array([1.0 / (0.06 + abs(n['dyn'] - d)) ** 2 for n in cand]); ws /= ws.sum()
            out += [(n, w * wi) for n, wi in zip(cand, ws)]
        return out

    @functools.lru_cache(maxsize=4096)
    def spec(self, art, m, d):
        """-> dict: f0, H, shape (G,H) dB over GRID, sus (H) dB, level curve, noise, stats."""
        f0 = mtof(m)
        H = int(max(1, min(64, (0.46 * SR) // (f0 * 1.02))))
        fq = f0 * np.arange(1, H + 1)
        ftilt = np.interp(np.log(fq), np.log(self.bands), self.tilt)
        G = len(self.grid)
        shape = np.zeros((G, H)); sus = np.zeros(H); wsum = 0
        env = None; ns = np.zeros(len(self.bands)); na = np.zeros(len(self.bands)); ng = np.zeros((G, len(self.bands)))
        hd = np.zeros(H); hd_w = 0; dur = 0; sus_lvl = 0; lastrow = 0
        for n, w in self.neighbours(art, m, d):
            f0n = mtof(n['m']); corr = (d - n['dyn']) * ftilt
            hg = np.array(n['hg'])
            rows = np.array([_map_env(r, f0n, fq) for r in hg]) + corr
            if len(rows) < G: rows = np.vstack([rows, np.repeat(rows[-1:], G - len(rows), 0)])
            lastrow += w * (len(hg) - 1)
            shape += w * _shape_rows(rows)
            sus += w * _shape_rows(_map_env(n['hs'], f0n, fq) + corr)
            e = np.array(n['env']) - (n['sus_lvl'] if art == 'sus' else 0.0)
            env = w * e if env is None else env + w * e
            ns += w * np.array(n['ns']); na += w * np.array(n['na'])
            g_ = np.array(n.get('ng') or [n['na']] * G); g_ = np.vstack([g_, np.repeat(g_[-1:], G - len(g_), 0)]) if len(g_) < G else g_[:G]
            ng += w * g_
            dur += w * n['dur']; sus_lvl += w * n['sus_lvl']
            if n.get('hd'):
                hd += w * _map_env(np.array(n['hd']), f0n, fq, roll=-3.0); hd_w += w
            wsum += w
        A = self.p['arts'][art]
        if A.get('ncorr_m'):   # pitch-dependent noise correction from the closed-loop calibration
            cm = np.array(A['ncorr_m']); j = int(np.clip(np.searchsorted(cm, m), 1, len(cm) - 1)) if len(cm) > 1 else 0
            if len(cm) > 1:
                w1 = float(np.clip((m - cm[j - 1]) / max(cm[j] - cm[j - 1], 1e-6), 0, 1)); j0 = j - 1
            else:
                w1, j0, j = 0.0, 0, 0
            cgs = np.array(A['ng_corrs']); css = np.array(A['ns_corrs'])
            ng = ng + ((1 - w1) * cgs[j0] + w1 * cgs[j]) * wsum
            ns = ns + ((1 - w1) * css[j0] + w1 * css[j]) * wsum
        return dict(f0=f0, H=H, shape=shape / wsum, sus=sus / wsum, env=env / wsum, ns=ns / wsum, na=na / wsum, ng=ng / wsum,
                    hd=(hd / hd_w) if hd_w else None, dur=dur / wsum, lastrow=int(round(lastrow / wsum)),
                    release=float(np.clip(A.get('release_dbps') or -90, -400, -30)),
                    vib=self.p.get('vib', dict(rate=5.2, depth=0.0)))

ENV_T = np.concatenate([np.arange(0, 1.0, 0.01), np.arange(1.0, 7.0, 0.1)])

def _smooth_noise(rng, n, rate_hz, ctrl_sr):
    """slow random curve (unit variance) for drifts / wobble."""
    k = max(2, int(n * rate_hz / ctrl_sr) + 3)
    pts = rng.standard_normal(k)
    return np.interp(np.linspace(0, k - 1, n), np.arange(k), pts)

CTRL = 64  # control hop (samples)

def tonal_note(inst, m, dur, d=0.57, d_end=None, art='sus', voices=1, detune=None, seed=0,
               legato_from=None, pan=0.0, width=0.0, release=None, vib_scale=None):
    """render one (section) note -> stereo array (n, 2) starting at the note onset."""
    rng = np.random.default_rng(seed)
    art0, mode = inst.art(art)
    d0 = dynv(d); d1 = dynv(d_end) if d_end is not None else d0
    S = inst.spec(art0, round(float(m), 2), round(d0, 3))
    S1 = inst.spec(art0, round(float(m), 2), round(d1, 3)) if abs(d1 - d0) > 1e-3 else S
    short = art0 in ('staccato', 'pizz', 'hit') or mode == 'short'
    natural = S['dur'] if short else None
    if mode == 'short': natural = min(0.35, dur)
    rel = release if release is not None else S['release']
    if short and art0 in ('pizz', 'hit'):
        body = max(dur, natural)                    # plucked notes ring
    elif short:
        body = min(dur, natural) if mode != 'short' else min(dur, 0.3)
    else:
        body = dur
    tail = min(3.0, 60.0 / -rel) if not (short and art0 in ('pizz', 'hit')) else 0.2
    T = body + tail + 0.05
    M = int(T * SR / CTRL) + 2
    tc = np.arange(M) * CTRL / SR                    # control time axis
    H = S['H']; G = inst.grid
    # ---- level curve (dB): measured envelope (attack / decay), sustain hold, release
    env = np.interp(tc, ENV_T, S['env'], right=S['env'][-1])
    if not short:
        hold = tc > 0.9
        env[hold] = np.interp(tc[hold], [0.9, 1.6], [np.interp(0.9, ENV_T, S['env']), 0.0], right=0.0)
        if legato_from is not None:
            env = np.minimum(0.0, -6 + 6 * np.clip(tc / 0.05, 0, 1))
        if mode == 'marcato':
            env = env + 4 * np.exp(-tc / 0.09)
    elif art0 in ('pizz', 'hit'):
        ipk = int(np.argmax(np.where(tc < 0.08, env, -999)))
        epk = env[ipk]
        env[: ipk + 1] = np.where(tc[: ipk + 1] < 0.002, epk - 30 * (1 - tc[: ipk + 1] / 0.002), epk)
    elif art0 == 'staccato' or mode == 'short':
        if mode == 'short':   # compress the measured sustain attack into a short note
            env = np.interp(tc * 2.5, ENV_T, S['env'])
    # dynamics (level + timbre handled through the spectrum blend below)
    dcur = d0 + (d1 - d0) * np.clip(tc / max(body, 1e-3), 0, 1)
    level = env + (dcur - 4 / 7) * inst.dyn_db
    # release after note off
    off = tc > body
    level[off] += rel * (tc[off] - body)
    # ---- spectral shape over time (H x M), blended between dynamic endpoints
    def shape_t(Sx):
        if short:
            lr = max(Sx['lastrow'], 1)
            Gs = G[: lr + 1]
            sh = np.array([np.interp(tc, Gs, Sx['shape'][: lr + 1, h]) for h in range(H)])
            if Sx['hd'] is not None:   # beyond the measured grid: per-harmonic decay slopes
                beyond = tc > Gs[-1]
                rel_dec = (Sx['hd'] - np.max(Sx['hd'])) [:, None] * (tc[beyond] - Gs[-1])[None, :]
                sh[:, beyond] += np.minimum(rel_dec, 0)
            return sh
        k = np.searchsorted(G, 0.55)
        Gs = np.concatenate([G[:k], [0.9]])
        rows = np.vstack([Sx['shape'][:k], Sx['sus'][None, :]])
        if legato_from is not None:
            rows = np.repeat(Sx['sus'][None, :], len(Gs), 0)
        return np.array([np.interp(tc, Gs, rows[:, h]) for h in range(H)])
    sh = shape_t(S)
    if S1 is not S:
        w = np.clip(tc / max(body, 1e-3), 0, 1)[None, :]
        sh = sh * (1 - w) + shape_t(S1) * w
    # higher harmonics die faster in the release
    if off.any():
        hh = np.arange(H)[:, None]
        sh[:, off] += rel * 0.015 * hh * (tc[off] - body)[None, :]
    Adb = sh + level[None, :]
    Adb = np.maximum(Adb, -140)
    keep = Adb.max(1) > Adb.max() - 75
    hidx = np.where(keep)[0]
    # ---- voices
    nv = max(1, int(voices)); det = inst.det if detune is None else detune
    vs = (inst.vscale if vib_scale is None else vib_scale) if nv > 1 else 1.0
    vib = S['vib']; ns_len = int(T * SR)
    out = np.zeros((ns_len + int(0.06 * SR), 2))
    f0 = S['f0']
    nsamp = np.arange(ns_len) / SR
    pos = np.linspace(-0.5, 0.5, nv) if nv > 1 else np.zeros(1)
    rng.shuffle(pos)
    harm_power = np.zeros(M)
    pluck = art0 in ('pizz', 'hit')
    shifts = [int(abs(rng.normal(0, (0.004 if pluck else 0.008) if nv > 1 else 0.002)) * SR) for _ in range(nv)]
    phases = [(-np.pi / 2 + rng.normal(0, 0.3, H)) if pluck else rng.random(H) * 2 * np.pi for _ in range(nv)]
    coh = np.ones(H)
    if short and nv > 1:
        # short notes: no time for detune/vibrato to move the interference, and plucks share a sharp (phase-aligned) pluck shape, so low harmonics add coherently across players
        # while high ones add randomly. Compensate per harmonic with the actual offsets so the section's power
        # spectrum equals the measured one.
        hh = np.arange(1, H + 1)
        ph = np.array([phases[v] - 2 * np.pi * hh * f0 * shifts[v] / SR for v in range(nv)])
        C = np.abs(np.exp(1j * ph).sum(0)) ** 2 / nv
        coh = 1 / np.sqrt(np.clip(C, 1 / 16, 16))
    for v in range(nv):
        cents_off = rng.normal(0, det) if nv > 1 else rng.normal(0, 1.0)
        rate = vib['rate'] * (1 + 0.07 * rng.standard_normal())
        depth = vs * vib['depth'] * float(np.clip(1 + 0.25 * rng.standard_normal(), 0.4, 1.6))
        if short: depth *= 0.3
        vdelay = 0.18 + 0.12 * rng.random()
        vfade = np.clip((tc - vdelay) / 0.35, 0, 1)
        drift = _smooth_noise(rng, M, 0.7, SR / CTRL) * (2.5 if inst.p['family'] != 'brass' else 1.5) * vs
        ratej = 1 + 0.04 * _smooth_noise(rng, M, 0.5, SR / CTRL)
        vph = 2 * np.pi * np.cumsum(rate * ratej) * CTRL / SR + rng.random() * 6.3
        cents = cents_off + drift + depth * vfade * np.sin(vph)
        if legato_from is not None:
            glide = (midi(legato_from) - m) * 100 * np.exp(-tc / 0.035)
            cents = cents + glide
        if art0 == 'sus' and inst.p['family'] == 'brass' and legato_from is None:
            cents = cents - 18 * np.exp(-tc / 0.03)        # lip scoop into the note
        fctrl = f0 * 2 ** (cents / 1200)
        f = np.interp(nsamp, tc, fctrl)
        phi = 2 * np.pi * np.cumsum(f) / SR
        # per-player timbre deviation (static) + slow loudness wobble
        tdev = rng.normal(0, 1.2, H)
        wob = 0.6 * _smooth_noise(rng, M, 1.5, SR / CTRL)
        # vibrato sweeps each harmonic across body/formant resonances -> per-harmonic AM
        fam = inst.p['family']
        amk = {'strings': 1.0, 'choir': 0.9, 'woodwinds': 0.45, 'brass': 0.3}.get(fam, 0.3)
        amd = amk * (inst.p.get('am_db') or 3.5) * np.clip(depth / 12.0, 0, 1.5)
        hsign = rng.choice([-1.0, 1.0], H) * rng.uniform(0.4, 1.0, H) * np.minimum(1, np.arange(1, H + 1) / 2.5)
        bodyam = amd * hsign[:, None] * (vfade * np.sin(vph))[None, :]
        lin = 10 ** ((Adb + tdev[:, None] + wob[None, :] + bodyam) / 20) / np.sqrt(nv) * coh[:, None]
        if mode == 'trem':
            tr_rate = 11 + 3 * rng.random()
            stroke = 0.55 + 0.45 * np.abs(np.sin(np.pi * np.cumsum(np.full(M, tr_rate)) * CTRL / SR + rng.random() * 3))
            lin = lin * stroke[None, :]
        harm_power += (lin ** 2).sum(0) / 2
        y = np.zeros(ns_len)
        idx = np.minimum(np.arange(ns_len) // CTRL, M - 2); frac = (np.arange(ns_len) % CTRL) / CTRL
        th = phases[v]
        fmax = 0.47 * SR
        C = 65536
        for s0 in range(0, ns_len, C):
            sl = slice(s0, min(ns_len, s0 + C)); ii = idx[sl]; fr = frac[sl]
            for h in hidx:
                if (h + 1) * f[sl].max() > fmax: break
                a = lin[h, ii] * (1 - fr) + lin[h, ii + 1] * fr
                y[sl] += a * np.cos((h + 1) * phi[sl] + th[h])
        # timing jitter + seat position
        sh_s = shifts[v]
        p = float(np.clip(pan + pos[v] * width, -1, 1))
        gl, gr = np.sqrt(0.5 * (1 - p)), np.sqrt(0.5 * (1 + p))
        dl = int(max(0, p) * 0.0006 * SR); dr = int(max(0, -p) * 0.0006 * SR)   # tiny inter-aural delay
        out[sh_s + dl: sh_s + dl + ns_len, 0] += y * gl
        out[sh_s + dr: sh_s + dr + ns_len, 1] += y * gr
    # ---- noise component (bow / breath / chiff), stereo-decorrelated
    nz = _note_noise(rng, S, harm_power, tc, body, short, legato_from is not None, ns_len, (dcur - 4 / 7) * inst.dyn_db, rel, inst.grid)
    gl, gr = np.sqrt(0.5 * (1 - pan)), np.sqrt(0.5 * (1 + pan))
    out[:ns_len, 0] += nz[0] * gl * (1 + 0.3 * width); out[:ns_len, 1] += nz[1] * gr * (1 + 0.3 * width)
    return out

def _note_noise(rng, S, harm_power, tc, body, short, legato, n, dynlev, rel, G):
    """noise (bow / breath / pluck thump / chiff) with the measured time evolution:
    PSD(t,f) = Pref(t) * noise_grid(t,f) during the measured attack/decay grid, then
    harmonic power(t) * noise_sus(f) for the sustained part; STFT overlap-add shaping of white noise."""
    N, hop = 1024, 256
    bands = meta('BAND_CTR')
    fb = np.fft.rfftfreq(N, 1 / SR); fb[0] = fb[1]
    lf, lb = np.log(fb), np.log(bands)
    rel_s = 10 ** (np.interp(lf, lb, S['ns']) / 10)
    ngf = 10 ** (np.array([np.interp(lf, lb, row) for row in S['ng']]) / 10)      # (G, bins)
    nfr = n // hop + 2
    tf = np.arange(nfr) * hop / SR
    P = np.interp(tf, tc, harm_power)
    if short:
        m_ = (tc > 0.02) & (tc < 0.25)
        Pref = np.full(nfr, np.median(harm_power[m_]) if m_.any() else harm_power.max())
        Tg = G[min(S['lastrow'], len(G) - 1)]
        x0, x1 = Tg, Tg + 1e-3
    else:
        Pref = 0.5 * 10 ** (np.interp(tf, tc, dynlev) / 10)
        Tg = 0.9; x0, x1 = 0.55, 0.9
    after = np.where(tf > body, 10 ** (rel * (tf - body) / 10), 1.0)
    w = np.hanning(N)
    out = []
    for ch in range(2):
        x = rng.standard_normal(nfr * hop + N)
        y = np.zeros_like(x)
        for i in range(nfr):
            t = tf[i]
            if legato:
                psd = P[i] * rel_s
            else:
                gi = np.interp(min(t, Tg), G, np.arange(len(G)))
                g0 = int(gi); g1 = min(g0 + 1, len(G) - 1); fr = gi - g0
                grid = Pref[i] * (ngf[g0] * (1 - fr) + ngf[g1] * fr) * after[i]
                if short:
                    if t > Tg:   # beyond the measured grid: follow the harmonic decay
                        tg_i = int(min(np.searchsorted(tf, Tg), nfr - 1))
                        grid = grid * (P[i] / max(P[tg_i], 1e-30))
                    psd = grid
                else:
                    a = float(np.clip((t - x0) / (x1 - x0), 0, 1))
                    psd = grid * (1 - a) + P[i] * rel_s * a
            X = np.fft.rfft(x[i * hop: i * hop + N] * w)
            X *= np.sqrt(psd * SR / 2)
            y[i * hop: i * hop + N] += np.fft.irfft(X, N) * w
        y /= 1.5   # hann^2 overlap-add gain at 75 % overlap
        out.append(y[N // 2: N // 2 + n])
    return out

# ------------------------------------------------------------------ percussion
def mode_db(md, t):
    """level (dB) of a modal partial at times t (s): measured level curve when stored (strongest partials),
    else bloom rise to t0 + one- or two-stage decay."""
    if 'trk' in md:
        tg = np.concatenate([[0.0], md['trk_t']]); lv = np.concatenate([[md['amp']], md['trk']])
        return np.where(t <= tg[-1], np.interp(t, tg, lv), lv[-1] + md.get('dec_tail', md['dec']) * (t - tg[-1]))
    t0 = md.get('t0', 0.0); u = np.maximum(t - t0, 0)
    d = md['dec'] * u if 'dec2' not in md else md['dec'] * np.minimum(u, md['tk']) + md['dec2'] * np.maximum(u - md['tk'], 0)
    lv = md['amp'] + d
    if t0 > 0:
        lv = lv + 20 * np.log10(np.maximum(0.5 - 0.5 * np.cos(np.pi * np.clip(t / t0, 0, 1)), 1e-6))
    return lv

_HIT_CACHE = {}
LINE_FRAC = 1.0   # share of metal residual power in fixed partials (1.0 matched the measured peak-to-floor ratio of the cymbals)

def perc_hit(inst, m=None, d=0.57, art='hit', seed=0, pan=0.0, length=None, hit=None):
    """one percussion stroke. Identical requests (same stroke, dynamic within 0.02, pitch, length) reuse a
    cached render so rolls of hundreds of strokes stay fast; round-robin variety comes from the different
    recorded strokes and the per-stroke dynamic jitter."""
    if hit is None:
        key = (inst.key, art, None if m is None else round(float(m), 2), round(dynv(d) / 0.02), length, seed % 3, round(pan, 2))
        if key in _HIT_CACHE: return _HIT_CACHE[key]
        out = _perc_hit(inst, m, d, art, seed % 3, pan, length, None)
        if len(_HIT_CACHE) > 400: _HIT_CACHE.clear()
        _HIT_CACHE[key] = out
        return out
    return _perc_hit(inst, m, d, art, seed, pan, length, hit)

def _perc_hit(inst, m, d, art, seed, pan, length, hit):
    rng = np.random.default_rng(seed)
    arts = inst.p['arts']
    a = art if art in arts else ('hit' if 'hit' in arts else next(iter(arts)))
    hits = arts[a]['hits']
    d = dynv(d)
    # nearest dynamic, then nearest pitch for tuned instruments (round-robin among equals)
    def cost(h):
        c = 3 * abs(h['dyn'] - d)
        if m is not None and h['ref_f']: c += abs(12 * np.log2(mtof(m) / h['ref_f'])) / 6
        return c + rng.random() * 0.05
    h = hit if hit is not None else min(hits, key=cost)
    ratio = mtof(m) / h['ref_f'] if (m is not None and h['ref_f']) else 1.0
    pg = meta('PGRID'); pbc = meta('PBAND_CTR')
    L = length or min(pg[-1], 9.0)
    if inst.key in ('cymbals', 'tamtam', 'sus_cymbal'): L = length or 8.0
    n = int(L * SR); t = np.arange(n) / SR
    gain_db = (d - h['dyn']) * 28.0 if hit is None else 0.0
    bright = (d - h['dyn']) * 6.0 if hit is None else 0.0        # dB/oct around 1 kHz
    y = np.zeros(n)
    top = max([md['amp'] for md in h['modes']] or [0]) + gain_db
    for md in h['modes']:
        f = md['f'] * ratio
        if f > 0.46 * SR or f < 20: continue
        a0 = md['amp'] + gain_db + bright * np.log2(f / 1000)
        sc = 1 + 0.15 * (ratio - 1)
        slow = md.get('dec_tail', md.get('dec2', md['dec'])) * sc
        nk = int(min(n, max(0.0, (a0 - (top - 95)) / max(-slow, 0.3) + md.get('tk', 0) + md.get('t0', 0) + (md['trk_t'][-1] if 'trk_t' in md else 0)) * SR))
        if nk < 16: continue
        tk = t[:nk]
        m2 = dict(md, amp=a0, dec=md['dec'] * sc, **({'dec2': md['dec2'] * sc} if 'dec2' in md else {}))
        if 'trk' in md:
            sh = a0 - md['amp']
            m2['trk'] = [v + sh for v in md['trk']]; m2['trk_t'] = [x / sc for x in md['trk_t']]
            m2['dec_tail'] = md.get('dec_tail', md['dec']) * sc
        y[:nk] += 10 ** (mode_db(m2, tk) / 20) * np.cos(2 * np.pi * f * (1 + 0.0005 * rng.standard_normal()) * tk + rng.random() * 6.28)
    y *= np.minimum(1, t / 0.0007)
    # noise residual: band PSD over time (independent noise per channel = natural width, mono-safe)
    N, hop = 1024, 256; nfr = n // hop + 2; w = np.hanning(N)
    fb = np.fft.rfftfreq(N, 1 / SR); fb[0] = fb[1]
    B = np.array(h['bands'])                       # (len(pg), bands) absolute PSD dB
    nr = ratio ** 0.5
    G = np.empty((nfr, len(fb)))
    for i in range(nfr):
        tt = i * hop / SR
        row = np.array([np.interp(tt, pg, B[:, b], right=B[-1, b] - 30 * (tt - pg[-1])) for b in range(B.shape[1])])
        G[i] = np.sqrt(10 ** ((np.interp(np.log(fb / nr), np.log(pbc), row) + gain_db + bright * np.log2(fb / 1000)) / 10) * SR / 2)
    metal = inst.key in ('cymbals', 'tamtam', 'sus_cymbal', 'triangle')
    chans = []
    if metal:
        # metal residual = dense fixed partials (random frequencies, ~1 per 2.5 Hz, matching the measured partial density) whose band amplitudes follow
        # the measured band envelopes -> spiky, shimmering spectrum like the real plate instead of smooth hiss
        pe = meta('PBAND_EDGES') * nr; tf = np.arange(nfr) * hop / SR
        Bt = np.array([[np.interp(tt, pg, B[:, b], right=B[-1, b] - 30 * (tt - pg[-1])) for b in range(B.shape[1])] for tt in tf])
        Bt = Bt + gain_db + bright * np.log2(np.sqrt(pe[:-1] * pe[1:]) / 1000)[None, :]
        nfft = n + (n % 2); dfn = SR / nfft
        for ch in range(2):
            z = np.zeros(nfft)
            for b in range(len(pe) - 1):
                lo, hi = pe[b], min(pe[b + 1], 0.46 * SR)
                if hi <= lo or lo < 20: continue
                k0, k1 = int(lo / dfn) + 1, int(hi / dfn)
                if k1 <= k0: continue
                nl = int(np.clip((hi - lo) / 2.5, 1, k1 - k0))
                spec = np.zeros(nfft // 2 + 1, complex)
                bins = rng.choice(np.arange(k0, k1), nl, replace=False)
                spec[bins] = rng.rayleigh(1.0, nl) * np.exp(2j * np.pi * rng.random(nl))
                sig = np.fft.irfft(spec, nfft); sig /= np.sqrt(np.mean(sig ** 2)) + 1e-12
                if LINE_FRAC < 1:   # continuous floor under the partials (measured peak-to-floor ratio)
                    gs = np.zeros(nfft // 2 + 1, complex); kk = np.arange(k0, k1)
                    gs[kk] = rng.standard_normal(len(kk)) + 1j * rng.standard_normal(len(kk))
                    gsig = np.fft.irfft(gs, nfft); gsig /= np.sqrt(np.mean(gsig ** 2)) + 1e-12
                    sig = np.sqrt(LINE_FRAC) * sig + np.sqrt(1 - LINE_FRAC) * gsig
                env = np.sqrt(10 ** (Bt[:, b] / 10) * (hi - lo))
                z += sig * np.interp(np.arange(nfft), np.arange(nfr) * hop, env)
            chans.append(z[:n])
    if not metal:
        x = rng.standard_normal(nfr * hop + N); z = np.zeros_like(x)
        for i in range(nfr):
            X = np.fft.rfft(x[i * hop: i * hop + N] * w) * G[i]
            z[i * hop: i * hop + N] += np.fft.irfft(X, N) * w
        chans.append(z[N // 2: N // 2 + n] / 1.5)
    zl, zr = chans[0], chans[-1]
    gl, gr = np.sqrt(0.5 * (1 - pan)), np.sqrt(0.5 * (1 + pan))
    if metal:   # keep total noise power equal to the mono model
        return np.stack([(y + zl) * gl, (y + zr) * gr], 1)
    sig = y + zl
    return np.stack([sig * gl, sig * gr], 1)

def perc_roll(inst, m, dur, d0, d1, seed=0, pan=0.0, rate=None):
    rng = np.random.default_rng(seed)
    rate = rate or {'timpani': 13.0, 'snare': 18.0, 'sus_cymbal': 11.0, 'bass_drum': 11.0}.get(inst.key, 12.0)
    n = int((dur + 4.0) * SR); out = np.zeros((n, 2))
    k = 0; t = 0.0
    while t < dur:
        dd = dynv(d0) + (dynv(d1) - dynv(d0)) * (t / max(dur, 1e-3))
        dd = float(np.clip(dd + rng.normal(0, 0.025) - (0.03 if k % 2 else 0), 0, 1))
        hit = perc_hit(inst, m, dd, 'hit', seed=seed * 1000 + k, pan=pan + (0.02 if k % 2 else -0.02),
                       length=min(3.0, dur - t + 2.5))
        i = int(t * SR); e = min(n, i + len(hit)); out[i:e] += hit[: e - i] * (0.55 if inst.key != 'snare' else 0.4)
        t += 1.0 / rate * (1 + 0.06 * rng.standard_normal()); k += 1
    return out

# ------------------------------------------------------------------ hall
def hall_ir(rt=2.2, seed=7, predelay=0.018):
    rng = np.random.default_rng(seed)
    n = int(rt * 1.6 * SR); N, hop = 1024, 256
    fb = np.fft.rfftfreq(N, 1 / SR); fb[0] = 20
    rtf = rt * np.interp(np.log(fb), np.log([60, 250, 1000, 4000, 12000]), [1.35, 1.15, 1.0, 0.7, 0.4])
    chans = []
    for ch in range(2):
        x = rng.standard_normal(n + N); y = np.zeros_like(x); w = np.hanning(N)
        for i in range(0, n, hop):
            t = i / SR
            g = np.exp(-6.9 * t / rtf) * np.minimum(1, (t + 0.002) / 0.03)
            X = np.fft.rfft(x[i:i + N] * w) * g
            y[i:i + N] += np.fft.irfft(X, N) * w
        y = y[:n]
        # early reflections
        er = np.zeros(n)
        for k in range(18):
            dt = rng.uniform(0.006, 0.085); g = 0.9 * np.exp(-dt / 0.06) * rng.uniform(0.4, 1.0) * (1 if rng.random() > 0.5 else -1)
            er[int(dt * SR)] += g
        er = sosfilt(butter(2, 7000, 'low', fs=SR, output='sos'), er)
        y = y / np.sqrt(np.sum(y ** 2)) + er * 0.35 / np.sqrt(np.sum(er ** 2) + 1e-9)
        y = np.concatenate([np.zeros(int(predelay * SR)), y])
        chans.append(y)
    L = max(map(len, chans))
    return np.stack([np.pad(c, (0, L - len(c))) for c in chans], 1)

# ------------------------------------------------------------------ mastering
def _biquad(kind, f0, q, gain_db=0.0):
    """RBJ biquad -> sos row."""
    A = 10 ** (gain_db / 40); w0 = 2 * np.pi * f0 / SR; al = np.sin(w0) / (2 * q); c = np.cos(w0)
    if kind == 'peak':
        b = [1 + al * A, -2 * c, 1 - al * A]; a = [1 + al / A, -2 * c, 1 - al / A]
    elif kind == 'highshelf':
        sq = 2 * np.sqrt(A) * al
        b = [A * ((A + 1) + (A - 1) * c + sq), -2 * A * ((A - 1) + (A + 1) * c), A * ((A + 1) + (A - 1) * c - sq)]
        a = [(A + 1) - (A - 1) * c + sq, 2 * ((A - 1) - (A + 1) * c), (A + 1) - (A - 1) * c - sq]
    elif kind == 'lowshelf':
        sq = 2 * np.sqrt(A) * al
        b = [A * ((A + 1) - (A - 1) * c + sq), 2 * A * ((A - 1) - (A + 1) * c), A * ((A + 1) - (A - 1) * c - sq)]
        a = [(A + 1) + (A - 1) * c + sq, -2 * ((A - 1) + (A + 1) * c), (A + 1) + (A - 1) * c - sq]
    elif kind == 'highpass':
        b = [(1 + c) / 2, -(1 + c), (1 + c) / 2]; a = [1 + al, -2 * c, 1 - al]
    b = np.array(b) / a[0]; a = np.array(a) / a[0]
    return np.concatenate([b, a])[None, :]

def _eq(x, rows):
    sos = np.vstack(rows)
    return np.stack([sosfilt(sos, x[:, c]) for c in range(x.shape[1])], 1)

def loudness(x):
    """integrated loudness (ITU-R BS.1770-4, K-weighted, gated) in LUFS."""
    k = _eq(x, [_biquad('highshelf', 1500.0, 0.7071, 4.0), _biquad('highpass', 38.0, 0.5)])
    blk, hop = int(0.4 * SR), int(0.1 * SR)
    if len(k) < blk: blk = hop = len(k)
    ms = np.array([np.mean(k[i:i + blk] ** 2, 0).sum() for i in range(0, len(k) - blk + 1, hop)])
    lk = -0.691 + 10 * np.log10(ms + 1e-15)
    g = ms[lk > -70]
    if not len(g): return -70.0
    rel = -0.691 + 10 * np.log10(g.mean()) - 10
    g = ms[(lk > -70) & (lk > rel)]
    return float(-0.691 + 10 * np.log10(g.mean()))

def limit(x, ceiling_db=-1.0, attack=0.004, release=0.08):
    """look-ahead peak limiter (4x oversampled peak estimate)."""
    from scipy.ndimage import maximum_filter1d
    from scipy.signal import resample_poly, lfilter
    thr = 10 ** (ceiling_db / 20)
    pk = np.abs(resample_poly(x, 4, 1, axis=0)).max(1).reshape(-1, 4).max(1)[: len(x)]
    pk = maximum_filter1d(pk, int(attack * SR) * 2 + 1)
    g = np.minimum(1.0, thr / np.maximum(pk, 1e-9))
    a = np.exp(-1 / (release * SR))
    gr = 1 - g                                   # gain reduction, smoothed (fast attack via max filter)
    gr = np.maximum(gr, lfilter([1 - a], [1, -a], gr))
    g = 1 - gr
    d = int(attack * SR)
    y = np.vstack([x[d:], np.zeros((d, x.shape[1]))]) * g[:, None] if False else x * g[:, None]
    return np.clip(y, -thr, thr)

def bpm_for(seconds, bars, beats_per_bar=4):
    """tempo that makes `bars` bars last `seconds` (for fitting a cue to a video)."""
    return 60.0 * bars * beats_per_bar / seconds

MASTER = {
    # concert: natural dynamics, peak-normalised
    'concert': dict(hp=28, rt_scale=1.0, wet=0.9, lufs=None, eq=[]),
    # shorts: phone speakers / feed playback - clearer (less hall), audible low end, loud and even
    'shorts': dict(hp=45, rt_scale=0.72, wet=0.65, lufs=-14.0,
                   eq=[('lowshelf', 90, 0.7, -2.5), ('peak', 180, 0.9, 1.5), ('peak', 3200, 0.9, 1.5), ('highshelf', 9000, 0.7, 1.0)]),
}
NARRATION_EQ = [('peak', 2300, 0.8, -4.0), ('peak', 900, 1.0, -1.5)]   # leaves a pocket for a voice

# ------------------------------------------------------------------ score
class Score:
    def __init__(self, bpm=100, seed=1, rt=2.2):
        self.bpm = bpm; self.events = []; self.seed = seed; self.rt = rt
        self.tempo = [(0.0, bpm)]

    def set_tempo(self, beat, bpm):
        self.tempo.append((float(beat), bpm)); self.tempo.sort()

    def sec(self, beat):
        """beat -> seconds (piecewise constant tempo)."""
        t = 0.0; prev_b, prev_bpm = self.tempo[0]
        for b, bpm in self.tempo[1:]:
            if beat <= b: break
            t += (b - prev_b) * 60 / prev_bpm; prev_b, prev_bpm = b, bpm
        return t + (beat - prev_b) * 60 / prev_bpm

    def note(self, part, beat, pitch, beats, dyn='mf', dyn_end=None, art='sus', legato_from=None, gain=0.0, **kw):
        t0 = self.sec(beat); t1 = self.sec(beat + beats)
        self.events.append(dict(kind='note', part=part, t=t0, dur=t1 - t0, m=midi(pitch), d=dyn, d_end=dyn_end,
                                art=art, legato_from=legato_from, gain=gain, kw=kw))
        return self

    def chord(self, part, beat, pitches, beats, **kw):
        for p in pitches: self.note(part, beat, p, beats, **kw)
        return self

    def line(self, part, beat, text, dyn='mf', art='sus', legato=False, gap=0.0, **kw):
        """'D4:1 E4:.5 F#4:.5 r:1 A4:2' - pitch:beats, 'r' rest, '|' ignored, '(f)' changes dynamic."""
        b = beat; prev = None; cur = dyn
        for tok in text.split():
            if tok == '|': continue
            if tok.startswith('(') and tok.endswith(')'): cur = tok[1:-1]; continue
            p, l = tok.split(':'); l = float(l)
            if p.lower() == 'r': prev = None; b += l; continue
            self.note(part, b, p, l - gap, dyn=cur, art=art, legato_from=prev if legato else None, **kw)
            prev = p; b += l
        return b

    def hit(self, part, beat, pitch=None, dyn='mf', art='hit', gain=0.0):
        self.events.append(dict(kind='hit', part=part, t=self.sec(beat), m=None if pitch is None else midi(pitch),
                                d=dyn, art=art, gain=gain))
        return self

    def roll(self, part, beat, beats, pitch=None, dyn='p', dyn_end='f', gain=0.0):
        t0 = self.sec(beat)
        self.events.append(dict(kind='roll', part=part, t=t0, dur=self.sec(beat + beats) - t0,
                                m=None if pitch is None else midi(pitch), d=dyn, d_end=dyn_end, gain=gain))
        return self

    def length(self):
        return max(e['t'] + e.get('dur', 0) for e in self.events)

    def render(self, path=None, tail=3.5, peak_db=-1.0, workers=2, verbose=True, stems=False,
               master='concert', narration=False, lufs=None):
        """master='concert' (default, natural dynamics, peak -1 dBFS) or 'shorts'
        (YouTube Shorts / Reels / TikTok: tighter hall, phone-audible low end, -14 LUFS, -1 dBTP).
        narration=True carves a 1-3 kHz pocket for a voice-over. lufs overrides the loudness target."""
        import time
        M = MASTER[master]
        t_start = time.time()
        total = self.length() + tail
        n = int(total * SR) + SR
        parts = sorted({e['part'] for e in self.events})
        jobs = [(p, [e for e in self.events if e['part'] == p], self.seed, n) for p in parts]
        if workers > 1 and len(jobs) > 1:
            from multiprocessing import get_context
            with get_context('fork').Pool(workers) as pool: res = pool.map(_render_part, jobs)
        else:
            res = [_render_part(j) for j in jobs]
        dry = np.zeros((n, 2)); send = np.zeros((n, 2)); stem_out = {}
        for p, buf in zip(parts, res):
            cfg = PARTS[p]; dpt = cfg['depth']
            g = 10 ** ((cfg['gain'] - 2.2 * (dpt - 1)) / 20)
            fc = 16000 - 2200 * (dpt - 1)
            sig = np.stack([sosfilt(butter(1, fc, 'low', fs=SR, output='sos'), buf[:, c]) for c in range(2)], 1) * g
            dry += sig * (1.0 - 0.06 * dpt); send += sig * (0.18 + 0.09 * dpt)
            if stems: stem_out[p] = sig
        ir = hall_ir(self.rt * M['rt_scale'])
        wet = np.stack([fftconvolve(send[:, c], ir[:, c])[:n] for c in range(2)], 1)
        mix = dry + wet * M['wet']
        mix = np.stack([sosfilt(butter(2, M['hp'], 'high', fs=SR, output='sos'), mix[:, c]) for c in range(2)], 1)
        rows = [_biquad(*e) for e in M['eq']] + ([_biquad(*e) for e in NARRATION_EQ] if narration else [])
        if rows: mix = _eq(mix, rows)
        target = lufs if lufs is not None else M['lufs']
        mix = mix / (np.abs(mix).max() + 1e-12)
        if target is None:
            mix = np.tanh(mix * 1.6) / np.tanh(1.6)                      # gentle bus glue
            mix = mix / (np.abs(mix).max() + 1e-12) * 10 ** (peak_db / 20)
        else:
            for _ in range(3):                                           # gain -> limiter, converge on target
                mix = mix * 10 ** ((target - loudness(mix)) / 20)
                mix = limit(mix, peak_db)
        last = np.where(np.abs(mix).max(1) > 10 ** (-70 / 20))[0]
        mix = mix[: (last[-1] + int(0.2 * SR)) if len(last) else n]
        if path:
            import soundfile as sf
            sf.write(path, mix, SR, subtype='PCM_16')
        if verbose:
            print(f'rendered {len(mix) / SR:.1f}s in {time.time() - t_start:.1f}s -> {path}  '
                  f'[{master}{" +narration" if narration else ""}] {loudness(mix):.1f} LUFS, peak {20 * np.log10(np.abs(mix).max()):.1f} dBFS')
        return (mix, stem_out) if stems else mix

def _render_part(job):
    part, events, seed, n = job
    cfg = PARTS[part]; inst = Inst(cfg['inst'])
    buf = np.zeros((n, 2))
    for k, e in enumerate(events):
        sd = zlib.crc32(f'{part}|{k}|{seed}'.encode())
        if e['kind'] == 'note':
            if inst.kind == 'perc':
                s = perc_hit(inst, e['m'], e['d'], seed=sd, pan=cfg['pan'])
            else:
                s = tonal_note(inst, e['m'], e['dur'], e['d'], e['d_end'], e['art'], voices=e['kw'].get('voices', cfg['voices']),
                               seed=sd, legato_from=e['legato_from'], pan=cfg['pan'], width=cfg['width'])
        elif e['kind'] == 'hit':
            if inst.kind == 'perc':
                s = perc_hit(inst, e['m'], e['d'], e['art'], seed=sd, pan=cfg['pan'])
            else:
                s = tonal_note(inst, e['m'] if e['m'] else 60, 0.3, e['d'], None, 'pizz' if 'pizz' in inst.p['arts'] else 'staccato',
                               voices=cfg['voices'], seed=sd, pan=cfg['pan'], width=cfg['width'])
        else:
            s = perc_roll(inst, e['m'], e['dur'], e['d'], e['d_end'], seed=sd, pan=cfg['pan'])
        i = int(e['t'] * SR); j = min(n, i + len(s))
        buf[i:j] += s[: j - i] * 10 ** (e.get('gain', 0) / 20)
    return buf
