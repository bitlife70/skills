"""Acoustic analysis of real orchestral recordings -> compact instrument profiles.

Tonal notes  : f0, harmonic spectrum (sustain + time-evolving attack/decay grid), noise residual
               spectrum (bow/breath), vibrato, broadband envelope, ensemble metrics
               (pitch spread in cents after removing the common pitch track, amplitude-modulation
               depth of harmonics, attack rise time).
Percussive   : modal partials (freq, amp, decay) + time-varying noise-band envelope.
"""
import numpy as np, soundfile as sf, json, sys
from scipy.signal import medfilt, find_peaks
from catalog import load_catalog

SR = 44100
GRID = np.array([0.0, 0.01, 0.025, 0.05, 0.08, 0.12, 0.18, 0.26, 0.38, 0.55, 0.8, 1.15, 1.6, 2.2, 3.0, 4.2])  # s after onset
NBAND = 24
BAND_EDGES = np.geomspace(40, 18000, NBAND + 1)
BAND_CTR = np.sqrt(BAND_EDGES[:-1] * BAND_EDGES[1:])
PGRID = np.array([0, .004, .01, .02, .035, .06, .1, .15, .22, .32, .45, .65, .9, 1.25, 1.7, 2.3, 3.2, 4.4, 6, 8.5])
PNBAND = 32
PBAND_EDGES = np.geomspace(30, 19000, PNBAND + 1)
PBAND_CTR = np.sqrt(PBAND_EDGES[:-1] * PBAND_EDGES[1:])
EPS = 1e-12

def db(x): return 10 * np.log10(np.maximum(x, EPS))

def load(path):
    x, sr = sf.read(path, dtype='float64')
    if x.ndim > 1: x = x.mean(1)
    assert sr == SR
    return x

def fine_env(x, hop=220):
    """RMS envelope, 5 ms hop."""
    n = len(x) // hop
    e = np.sqrt(np.mean(x[: n * hop].reshape(n, hop) ** 2, 1) + EPS)
    return e

def find_onset(x):
    e = fine_env(x); pk = e.max()
    i = np.argmax(e > pk * 10 ** (-30 / 20))
    # refine to sample level: first sample above 10% of the local peak amplitude
    s = max(0, i * 220 - 440); seg = np.abs(x[s: s + 4410])
    j = np.argmax(seg > 0.1 * seg.max()) if seg.max() > 0 else 0
    return s + j

def stft(x, N, hop):
    w = np.hanning(N)
    nfr = 1 + max(0, (len(x) - N) // hop)
    idx = np.arange(N)[None, :] + hop * np.arange(nfr)[:, None]
    X = np.fft.rfft(x[idx] * w, axis=1)
    return X, w

# ------------------------------------------------------------------ pitch
def harm_score(mag_db, df, f, H=16):
    hs = np.arange(1, H + 1); hs = hs[(hs * f < max(4000, 3.5 * f))]
    def pk(fr):
        out = []
        for c in fr:
            a, b = int((c * 0.985) / df), int((c * 1.015) / df) + 2
            out.append(mag_db[a:b].max() if b < len(mag_db) else -120)
        return np.array(out)
    return pk(hs * f).mean() - pk((hs + 0.5) * f).mean()

def estimate_f0(x, onset, label, art):
    """long-window spectrum + harmonic score among label +/- octaves (handles library octave conventions)."""
    if art in ('pizz', 'hit', 'staccato'):
        seg = x[onset + int(0.02 * SR): onset + int(0.6 * SR)]
    else:
        seg = x[onset + int(0.3 * SR): onset + int(2.3 * SR)]
    if len(seg) < 4096: seg = x[onset: onset + int(0.6 * SR)]
    Nf = 1 << 17
    sp = np.abs(np.fft.rfft(seg * np.hanning(len(seg)), Nf)); df = SR / Nf
    mdb = 20 * np.log10(sp / sp.max() + 1e-6); mdb = np.maximum(mdb, -70)
    best = None
    for k in (-2, -1, 0, 1, 2):
        m0 = label + 12 * k
        if not (20 <= m0 <= 108): continue
        for c in np.arange(-0.6, 0.61, 0.05):
            f = 440 * 2 ** ((m0 + c - 69) / 12)
            s = harm_score(mdb, df, f)
            if best is None or s > best[0]: best = (s, f)
    f = best[1]
    # refine on the strongest of the first 4 harmonics
    hs = np.arange(1, 5)
    amps = [sp[int(h * f * 0.98 / df): int(h * f * 1.02 / df) + 1].max() for h in hs]
    href = hs[int(np.argmax(amps))]
    a, b = int(href * f * 0.98 / df), int(href * f * 1.02 / df) + 1
    k = a + np.argmax(sp[a:b])
    if 0 < k < len(sp) - 1:
        y0, y1, y2 = np.log(sp[k - 1:k + 2] + EPS); d = 0.5 * (y0 - y2) / (y0 - 2 * y1 + y2 + EPS)
        f = (k + d) * df / href
    return f, href

def track_f0(x, f0, href, N, hop):
    X, w = stft(x, N, hop); mag = np.abs(X); df = SR / N
    tr = np.full(len(mag), f0)
    for i, row in enumerate(mag):
        c = href * f0; a, b = int(c * 0.94 / df), int(c * 1.06 / df) + 2
        if b >= len(row) - 1: continue
        k = a + np.argmax(row[a:b])
        y0, y1, y2 = np.log(row[k - 1:k + 2] + EPS); d = 0.5 * (y0 - y2) / (y0 - 2 * y1 + y2 + EPS)
        tr[i] = (k + np.clip(d, -0.5, 0.5)) * df / href
    cents = 1200 * np.log2(tr / f0)
    cents = np.clip(cents, -80, 80)
    cents = medfilt(cents, 5)
    return f0 * 2 ** (cents / 1200), X, w

def win_len(f0):
    n = int(2 ** np.ceil(np.log2(6 * SR / f0)))
    return int(np.clip(n, 1024, 16384))

# ------------------------------------------------------------------ tonal analysis
def harmonic_frames(X, w, f0tr, N, H):
    """per-frame harmonic amplitudes (band power, robust to ensemble line broadening) + noise PSD bands."""
    P = np.abs(X) ** 2; df = SR / N; sw2 = np.sum(w ** 2)
    nfr = len(P); A = np.zeros((nfr, H)); noise = np.full((nfr, NBAND), np.nan)
    fb = np.arange(P.shape[1]) * df
    for i in range(nfr):
        f0 = f0tr[i]
        for h in range(1, H + 1):
            c = h * f0; half = max(0.35 * f0, 2.5 * df)
            a, b = int((c - half) / df), int((c + half) / df) + 1
            if b >= P.shape[1]: break
            A[i, h - 1] = 2 * np.sqrt(P[i, a:b].sum() / (N * sw2))
        # noise: bins far from any harmonic
        rel = (fb / f0) % 1.0; far = ((np.abs(rel - 0.5) < 0.22) | (fb < 0.7 * f0)) & (fb > 25)
        if f0 < 4 * df: far[:] = False
        psd = 2 * P[i] / (SR * sw2)              # one-sided PSD (power / Hz)
        bi = np.digitize(fb, BAND_EDGES) - 1
        for b_ in range(NBAND):
            m = far & (bi == b_)
            if m.sum() >= 2: noise[i, b_] = np.median(psd[m]) * 1.4   # median->mean for chi2
    return A, noise

def fill_bands(v):
    v = np.array(v, float); ok = np.isfinite(v)
    if ok.sum() == 0: return np.full(len(v), -120.0)
    return np.interp(np.arange(len(v)), np.where(ok)[0], v[ok])

def vibrato(cents, frame_rate):
    if len(cents) < frame_rate * 1.2: return dict(rate=0.0, depth=0.0)
    c = cents - np.convolve(cents, np.ones(int(frame_rate)) / int(frame_rate), 'same')
    c = c[int(frame_rate / 2): -int(frame_rate / 2)]
    if len(c) < 16: return dict(rate=0.0, depth=0.0)
    n = 1 << 14; sp = np.abs(np.fft.rfft(c * np.hanning(len(c)), n)); fr = np.fft.rfftfreq(n, 1 / frame_rate)
    m = (fr > 3.5) & (fr < 8.5)
    rate = fr[m][np.argmax(sp[m])]
    # depth: peak-to-peak /2 of band-passed vibrato -> use RMS * sqrt2
    depth = np.sqrt(2) * np.std(c)
    return dict(rate=float(rate), depth=float(depth))

def ensemble_width(x, onset, f0, f0tr, hop, N):
    """remove the common pitch track by time-warping, then measure harmonic line width (cents)."""
    t_fr = (np.arange(len(f0tr)) * hop + N / 2) / SR
    s0, s1 = onset + int(0.35 * SR), min(len(x), onset + int(3.0 * SR))
    if s1 - s0 < int(1.0 * SR): return None
    t = np.arange(s0, s1) / SR
    fi = np.interp(t, t_fr, f0tr)
    ph = np.cumsum(fi / f0) / SR                     # warped time
    tau = np.arange(ph[0], ph[-1], 1 / SR)
    y = np.interp(tau, ph, x[s0:s1])
    L = len(y); Nf = 1 << int(np.ceil(np.log2(L * 4)))
    win = np.hanning(L)
    P = np.abs(np.fft.rfft(y * win, Nf)) ** 2; df = SR / Nf
    ref = np.abs(np.fft.rfft(np.cos(2 * np.pi * 1000 * np.arange(L) / SR) * win, Nf)) ** 2   # window line shape
    def spread(Pspec, c, half):
        """power-weighted std (Hz) of the line cluster around c, floor-subtracted"""
        a, b = int((c - half) / df), int((c + half) / df) + 1
        seg = Pspec[a:b].astype(float)
        if len(seg) < 7 or seg.max() <= 0: return None
        fl = np.median(np.concatenate([seg[: len(seg) // 6], seg[-len(seg) // 6:]]))
        seg = np.maximum(seg - fl, 0)
        if seg.sum() <= 0: return None
        fr = (np.arange(a, b)) * df
        mu = (fr * seg).sum() / seg.sum()
        return np.sqrt(((fr - mu) ** 2 * seg).sum() / seg.sum())
    out = []
    for h in range(2, 11):
        c = h * f0
        if c > 6000: break
        half = min(0.3 * f0, c * (2 ** (60 / 1200) - 1))
        s_ = spread(P, c, half); s0 = spread(ref, 1000, 1000 * half / c)
        if s_ is None or s0 is None: continue
        eff = np.sqrt(max(s_ ** 2 - s0 ** 2, 0))
        out.append(1200 * np.log2(1 + eff / c))
    return float(np.median(out)) if out else None

def analyze_tonal(rec):
    x = load('flac/' + rec['file'])
    onset = find_onset(x)
    f0, href = estimate_f0(x, onset, rec['label'], rec['art'])
    N = win_len(f0); hop = N // 8
    xs = x[max(0, onset - N // 2):]                      # frame 0 centred at onset
    f0tr, X, w = track_f0(xs, f0, href, N, hop)
    H = int(min(60, (min(16000, SR * 0.45)) // f0))
    A, noise = harmonic_frames(X, w, f0tr, N, H)
    tfr = np.arange(len(A)) * hop / SR                   # time after onset of frame centre
    tot = (A ** 2).sum(1) / 2 + EPS                       # harmonic power per frame
    e = fine_env(x[onset:]); te = np.arange(len(e)) * 220 / SR
    edb = 20 * np.log10(e / e.max() + 1e-9)
    # sustain region
    peak_i = int(np.argmax(e))
    if rec['art'] == 'sus':
        lvl = np.median(e[(te > 0.35) & (te < 2.5)]) if (te > 0.35).sum() > 20 else e.max()
        above = np.where((te > 0.3) & (e > lvl * 10 ** (-9 / 20)))[0]
        sus_end = te[above[-1]] if len(above) else te[-1]
        sus = (tfr > 0.3) & (tfr < min(sus_end - N / SR / 2, 3.5))
        if sus.sum() < 3: sus = (tfr > 0.15) & (tfr < max(sus_end, 0.5))
    else:
        sus = (tfr >= 0.02) & (tfr < 0.25)
        sus_end = te[np.where(e > e.max() * 0.03)[0][-1]] if (e > e.max() * 0.03).any() else te[-1]
    if sus.sum() == 0: sus = tfr < 0.3
    Adb = 20 * np.log10(A + 1e-9)
    harm_sus = np.median(Adb[sus], 0)
    ref_db = harm_sus.max()
    harm_sus = np.maximum(harm_sus - ref_db, -90)
    # time grid: absolute harmonic levels (dB re sustain strongest harmonic)
    harm_grid = np.zeros((len(GRID), H)); valid = np.zeros(len(GRID), bool)
    for gi, tg in enumerate(GRID):
        if tg <= tfr[-1]:
            harm_grid[gi] = np.interp(tg, tfr, np.zeros(len(tfr))) + np.array([np.interp(tg, tfr, Adb[:, h]) for h in range(H)]) - ref_db
            valid[gi] = True
    harm_grid = np.maximum(harm_grid, -100)
    # noise relative to harmonic power (dB re total harmonic power, per Hz)
    nrel = db(noise) - db(tot)[:, None]
    noise_sus = fill_bands(np.nanmedian(np.where(sus[:, None], nrel, np.nan), 0))
    att = tfr < 0.06
    noise_att = fill_bands(np.nanmedian(np.where(att[:, None], nrel, np.nan), 0)) if att.any() else noise_sus
    # absolute noise in attack (dB re sustain harmonic power) -> captures bow scratch / chiff even when harmonics are low
    sus_pow = np.median(tot[sus])
    noise_att_abs = fill_bands(np.nanmedian(np.where(att[:, None], db(noise) - db(sus_pow), np.nan), 0)) if att.any() else noise_sus
    nabs = db(noise) - db(sus_pow)
    noise_grid = []
    for tg in GRID:
        if tg > tfr[-1]: noise_grid.append(noise_grid[-1] if noise_grid else noise_sus); continue
        i = int(np.argmin(np.abs(tfr - tg)))
        lo, hi = max(0, i - 1), min(len(tfr), i + 2)
        noise_grid.append(fill_bands(np.nanmedian(nabs[lo:hi], 0)))
    noise_grid = np.maximum(np.array(noise_grid), -150)
    # vibrato & pitch
    cents = 1200 * np.log2(f0tr / f0)
    vib = vibrato(cents[sus], SR / hop) if rec['art'] == 'sus' else dict(rate=0.0, depth=0.0)
    # envelope summary
    env_t = np.concatenate([np.arange(0, 1.0, 0.01), np.arange(1.0, 7.0, 0.1)])
    env = np.interp(env_t, te, edb, right=-100)
    sus_lvl_db = 20 * np.log10(np.median(e[(te > 0.35) & (te < sus_end)]) / e.max() + 1e-9) if rec['art'] == 'sus' and ((te > 0.35) & (te < sus_end)).sum() > 5 else 0.0
    # attack rise time 10%->90% of the sustain level (or of peak for short notes)
    target = e.max() if rec['art'] != 'sus' else 10 ** (sus_lvl_db / 20) * e.max()
    r10 = te[np.argmax(e > 0.1 * target)]; r90 = te[np.argmax(e > 0.9 * target)]
    # amplitude-modulation depth of harmonics in sustain (ensemble beating)
    am = None
    if rec['art'] == 'sus' and sus.sum() > 12:
        seg = Adb[sus][:, : min(10, H)]
        trend = np.array([np.polyval(np.polyfit(np.arange(len(seg)), seg[:, h], 2), np.arange(len(seg))) for h in range(seg.shape[1])]).T
        am = float(np.median(np.std(seg - trend, 0)[1:]))
    # release: decay slope after sustain end (dB/s)
    rel = None
    if rec['art'] == 'sus':
        m = (te > sus_end) & (te < sus_end + 0.6) & (edb > -60)
        if m.sum() > 10: rel = float(np.polyfit(te[m], edb[m], 1)[0])
    ens_w = ensemble_width(xs, N // 2, f0, f0tr, hop, N) if rec['art'] == 'sus' else None
    # per-harmonic decay (plucked / short): slope dB/s over 0.05..1.5 s
    hdec = None
    if rec['art'] in ('pizz', 'hit', 'staccato'):
        m = (tfr > 0.05) & (tfr < min(1.5, sus_end))
        if m.sum() > 4:
            hdec = [float(np.polyfit(tfr[m], Adb[m, h], 1)[0]) for h in range(H)]
    return dict(
        file=rec['file'], inst=rec['inst'], art=rec['art'], dyn=rec['dyn'], ens=rec['ens'], src=rec['src'],
        f0=float(f0), midi=float(69 + 12 * np.log2(f0 / 440)), label=rec['label'],
        level_db=float(20 * np.log10(np.sqrt(sus_pow) + 1e-9)),
        harm_sus=np.round(harm_sus, 1).tolist(), harm_grid=np.round(harm_grid, 1).tolist(), grid_valid=valid.tolist(),
        noise_sus=np.round(noise_sus, 1).tolist(), noise_att=np.round(noise_att, 1).tolist(), noise_att_abs=np.round(noise_att_abs, 1).tolist(), noise_grid=np.round(noise_grid, 1).tolist(),
        vib=vib, env=np.round(env, 1).tolist(), sus_lvl_db=float(sus_lvl_db), dur=float(sus_end),
        rise=float(max(r90 - r10, 0.0)), t90=float(r90), am_db=am, release_dbps=rel, ens_cents=ens_w,
        hdecay=None if hdec is None else np.round(hdec, 1).tolist(),
    )

# ------------------------------------------------------------------ percussion
def analyze_perc(rec):
    x = load('flac/' + rec['file'])
    onset = find_onset(x); y = x[max(0, onset - 64):]
    # band envelopes on a short STFT
    N, hop = 2048, 256
    X, w = stft(np.concatenate([y, np.zeros(N)]), N, hop); P = np.abs(X) ** 2
    psd = 2 * P / (SR * np.sum(w ** 2)); fb = np.fft.rfftfreq(N, 1 / SR)
    bi = np.digitize(fb, PBAND_EDGES) - 1
    B = np.stack([psd[:, bi == b].mean(1) if (bi == b).any() else np.zeros(len(psd)) for b in range(PNBAND)], 1)
    tfr = np.arange(len(B)) * hop / SR
    Bdb = db(B); ref = Bdb.max()
    bands = np.array([[np.interp(tg, tfr, Bdb[:, b], right=-140) for b in range(PNBAND)] for tg in PGRID]) - ref
    modes = extract_modes(y, KMAX.get(rec['inst'], 60), prom_db=5.0 if rec['inst'] in ('cymbals', 'sus_cymbal', 'tamtam', 'triangle') else 7.0, Nt=16384 if rec['inst'] in ('timpani', 'bass_drum', 'tamtam', 'chimes') else 8192)
    e = fine_env(y); te = np.arange(len(e)) * 220 / SR
    return dict(file=rec['file'], inst=rec['inst'], art=rec['art'], dyn=rec['dyn'], src=rec['src'], label=rec['label'],
                peak_db=float(20 * np.log10(np.abs(y).max() + 1e-9)), band_ref_db=float(ref),
                bands=np.round(bands, 1).tolist(), modes=modes,
                env=np.round(np.interp(PGRID, te, 20 * np.log10(e / e.max() + 1e-9), right=-100), 1).tolist())

TONAL_PERC = ('glockenspiel', 'xylophone', 'chimes')
KMAX = {'cymbals': 1500, 'sus_cymbal': 1500, 'tamtam': 1500, 'triangle': 150, 'snare': 100, 'bass_drum': 50,
        'timpani': 70, 'glockenspiel': 30, 'xylophone': 30, 'chimes': 50}

def extract_modes(y, kmax, prom_db=7.0, floor_db=-80.0, Nt=8192):
    """modal partials: peaks of the 1 s spectrum, each tracked through time; amplitude at t=0 and
    decay (dB/s) from a straight-line fit of its dB track (no window-average bias)."""
    from scipy.ndimage import median_filter
    L = min(len(y), SR); Nf = 1 << 18; w = np.hanning(L)
    sp = np.abs(np.fft.rfft(y[:L] * w, Nf)); df = SR / Nf
    sdb = 20 * np.log10(sp / sp.max() + 1e-9)
    dec = 8; k = int(60 / df / dec) | 1
    base = np.repeat(median_filter(np.maximum(sdb[::dec], -110), size=k, mode='nearest'), dec)[: len(sdb)]
    pk, _ = find_peaks(sdb, height=floor_db, distance=max(1, int(2.2 * SR / Nt / df)))
    f = pk * df
    pk = pk[(sdb[pk] - base[pk] > prom_db) & (f > 25) & (f < 18500)]
    pk = pk[np.argsort(-sdb[pk])]
    # drop "modes" that are only the skirt/leakage of a much stronger neighbouring partial
    keep = []
    for p in pk:
        fp = p * df
        # Lorentzian skirt of a decaying partial: level falls ~20 dB/decade of offset (half-width ~2 Hz)
        if any(sdb[p] < sdb[q] - 20 * np.log10(max(abs(fp - q * df), 2.0) / 2.0) + 8 for q in keep if sdb[q] > sdb[p] + 12):
            continue
        keep.append(p)
        if len(keep) >= kmax: break
    pk = np.array(keep, int)
    if len(pk) == 0: return []
    hop = 512
    yy = np.concatenate([np.zeros(Nt // 2), y[: int(6 * SR)], np.zeros(Nt)])
    X, wt = stft(yy, Nt, hop); M = np.abs(X); dft = SR / Nt
    tt = np.arange(len(M)) * hop / SR
    amp_scale = 2 / np.sum(wt)
    out = []
    for p in pk:
        fr = p * df; kk = int(round(fr / dft))
        tr = 20 * np.log10(M[:, max(kk - 1, 1): kk + 2].max(1) * amp_scale + 1e-12)
        i0 = int(np.argmax(tr[: max(2, int(0.15 * SR / hop))]))
        pkdb = tr[i0]
        tail = np.median(tr[-max(3, len(tr) // 8):])
        stop = np.where(tr[i0:] < max(pkdb - 45, tail + 6))[0]
        i1 = i0 + (stop[0] if len(stop) else len(tr) - i0)
        i1 = min(i1, i0 + int(4 * SR / hop))
        seg = slice(i0, max(i1, i0 + 2))
        if i1 - i0 >= 4:
            b, a = np.polyfit(tt[seg], tr[seg], 1)
        else:
            b, a = -80.0, pkdb + 80.0 * tt[i0]
        b = float(min(b, -0.3))
        # two-stage decay (fast initial + slow tail, e.g. glockenspiel/vibraphone bars, timpani): piecewise
        # linear dB fit with the knee searched on the track; kept only if it clearly beats one slope
        two = None
        if i1 - i0 >= 10:
            T, Y = tt[seg], tr[seg]
            e1 = np.sqrt(np.mean((np.polyval([b, a], T) - Y) ** 2))
            best = None
            for k in range(3, len(T) - 3):
                b1, a1 = np.polyfit(T[: k + 1], Y[: k + 1], 1)
                yk = a1 + b1 * T[k]
                b2 = np.sum((T[k:] - T[k]) * (Y[k:] - yk)) / max(np.sum((T[k:] - T[k]) ** 2), 1e-9)
                pred = np.where(T <= T[k], a1 + b1 * T, yk + b2 * (T - T[k]))
                e = np.sqrt(np.mean((pred - Y) ** 2))
                if best is None or e < best[0]: best = (e, a1, b1, b2, T[k])
            if best and best[0] < e1 - 1.5 and best[3] > best[2] + 6:
                _, a, b, b2, tk = best
                b = float(min(b, -0.3)); two = (float(min(b2, -0.3)), float(tk))
        # onset type: modes that genuinely bloom (reach -3 dB of their peak later than the window smear of an
        # instantaneous onset) start at t0 with a rise; others start at t=0 (fit intercept, capped).
        rise = np.where(tr[: i0 + 1] > pkdb - 3)[0]
        t_rise = float(tt[rise[0]]) if len(rise) else 0.0
        if t_rise > 0.6 * Nt / 2 / SR:
            md = dict(f=round(float(fr), 2), amp=round(float(min(a + b * t_rise, pkdb + 1)), 1), dec=round(b, 1), t0=round(t_rise, 3))
        else:
            md = dict(f=round(float(fr), 2), amp=round(float(min(a, pkdb + 3)), 1), dec=round(b, 1))
        if two: md['dec2'], md['tk'] = round(two[0], 1), round(two[1] - md.get('t0', 0.0), 3)
        # strongest partials keep their measured level curve (plateaus, beating, multi-stage decay)
        if len(out) < 12 and tt[i1 - 1] >= 0.3:
            tg = np.array([0.1, 0.14, 0.2, 0.27, 0.35, 0.45, 0.57, 0.72, 0.9, 1.1, 1.35, 1.65, 2.0, 2.5, 3.1, 3.8])
            tg = tg[tg <= tt[min(i1, len(tt)) - 1]]
            if len(tg) >= 3:
                trk = np.interp(tg, tt, np.convolve(tr, np.ones(3) / 3, 'same'))
                md['trk_t'] = tg.round(3).tolist(); md['trk'] = trk.round(1).tolist()
                k = len(tg) // 2
                md['dec_tail'] = round(float(min((trk[-1] - trk[k]) / max(tg[-1] - tg[k], 1e-3), 0.7 * b, -0.3)), 1)   # never slower than 0.7x the fitted decay
        out.append(md)
    return out


def analyze(rec):
    try:
        if rec['inst'] in ('timpani', 'bass_drum', 'cymbals', 'sus_cymbal', 'snare', 'tamtam', 'triangle') + TONAL_PERC:
            r = analyze_perc(rec)
            if rec['inst'] in ('timpani',) + TONAL_PERC and r['modes']:
                pass
            return r
        return analyze_tonal(rec)
    except Exception as ex:
        return dict(file=rec['file'], error=repr(ex))

if __name__ == '__main__':
    from multiprocessing import Pool
    cat = load_catalog()
    if len(sys.argv) > 1: cat = [c for c in cat if any(s in c['file'] for s in sys.argv[1:])]
    with Pool(2) as p: res = p.map(analyze, cat, chunksize=4)
    bad = [r for r in res if 'error' in r]
    print('analyzed', len(res), 'errors', len(bad)); [print(b) for b in bad[:10]]
    json.dump([r for r in res if 'error' not in r], open('analysis_raw.json' if len(sys.argv) == 1 else 'analysis_test.json', 'w'))
