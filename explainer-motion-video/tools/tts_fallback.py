#!/usr/bin/env python3
"""Fallback narration when Typecast (desktop link) is unavailable — Supertonic 3 via sherpa-onnx, runs offline on CPU.

Setup (once per container):
  pip install --break-system-packages sherpa-onnx soundfile numpy
  curl -L -o st.tar.bz2 https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/sherpa-onnx-supertonic-3-tts-int8-2026-05-11.tar.bz2
  tar xjf st.tar.bz2   # -> sherpa-onnx-supertonic-3-tts-int8-2026-05-11/

Usage:
  python3 tts_fallback.py lines.json --voice m10 [--model-dir DIR] [--speed 1.25] [--steps 16]
  (writes each line's `tts` text to its `file` path; same lines.json as the Typecast flow)

User-approved voices (sample numbers 1-10 = sid 0-9; 1-5 female, 6-10 male), preference order:
  female: f5 (sid 4) > f1 (sid 0)      male: m10 (sid 9) > m7 (sid 6)
"""
import argparse, json, os, sys
import numpy as np, soundfile as sf, sherpa_onnx

VOICES = {'f5': 4, 'f1': 0, 'm10': 9, 'm7': 6}

def load(d):
    c = sherpa_onnx.OfflineTtsSupertonicModelConfig(
        duration_predictor=f'{d}/duration_predictor.int8.onnx', text_encoder=f'{d}/text_encoder.int8.onnx',
        vector_estimator=f'{d}/vector_estimator.int8.onnx', vocoder=f'{d}/vocoder.int8.onnx',
        tts_json=f'{d}/tts.json', unicode_indexer=f'{d}/unicode_indexer.bin', voice_style=f'{d}/voice.bin')
    return sherpa_onnx.OfflineTts(sherpa_onnx.OfflineTtsConfig(model=sherpa_onnx.OfflineTtsModelConfig(supertonic=c, num_threads=2, provider='cpu')))

def say(tts, text, out, sid, speed, steps):
    g = sherpa_onnx.GenerationConfig(); g.sid = sid; g.num_steps = steps; g.speed = speed; g.extra['lang'] = 'ko'
    a = tts.generate(text, g); os.makedirs(os.path.dirname(out) or '.', exist_ok=True)
    sf.write(out, np.array(a.samples, dtype=np.float32), a.sample_rate, subtype='PCM_16'); return len(a.samples) / a.sample_rate

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('lines'); ap.add_argument('--voice', default='m10', choices=VOICES)
    ap.add_argument('--model-dir', default='sherpa-onnx-supertonic-3-tts-int8-2026-05-11'); ap.add_argument('--speed', type=float, default=1.25)
    ap.add_argument('--steps', type=int, default=16); ap.add_argument('--only', default='', help='comma-separated n list to (re)generate')
    a = ap.parse_args(); tts = load(a.model_dir); only = {int(x) for x in a.only.split(',') if x}
    for l in json.load(open(a.lines)):
        if only and l['n'] not in only: continue
        print(l['n'], round(say(tts, l['tts'], l['file'], VOICES[a.voice], a.speed, a.steps), 2), flush=True)
