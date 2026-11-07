#!/bin/bash
# Download one source sample and convert it to mono 44.1 kHz WAV (trimmed).
# Usage (from this folder):
#   mkdir -p raw wav
#   cat sample_urls.txt | tr '\t' '\n' | xargs -n2 -P6 ./fetch_samples.sh
#   # then convert wav/ -> flac/ (or point analyze.py at your folder) and run analyze.py
url="$1"; out="$2"; ext="${url##*.}"
[ -f "wav/${out%.*}.wav" ] && exit 0
curl -sS -m 120 -L "$url" -o "raw/$out" || exit 0
dur=7; case "$out" in *Percussion*|*Timpani*|*Glock*|*Harp*) dur=10;; esac
ffmpeg -nostdin -loglevel error -y -i "raw/$out" -t $dur -ac 1 -ar 44100 -sample_fmt s16 "wav/${out%.*}.wav" && rm -f "raw/$out"
