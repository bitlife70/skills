"""Tchaikovsky - Swan Lake Op.20, Act II No.10 Scene (Moderato), bars 1-9, transcribed from the full score
(P. Tchaikovsky, Complete Works vol.11, Muzgiz 1957 / RSP re-engraving 1966, IMSLP #1056592, pp. 257-258).
Scoring in these bars: solo oboe, harp, strings (vn/vla tremolo, vc/cb pizz, vc arco from bar 7).
Only change: the oboe's last-beat pickup in bar 9 (B4 quarter leading into bar 10) is held as the final note."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from orchestra import Score

s = Score(bpm=72, seed=11, rt=2.4)
def at(m, b=0.0): return (m - 1) * 4 + b

# ---------------------------------------------------------------- oboe I (p espress.)
OB = [(2, 'F#5:2 B4:.5 C#5:.5 D5:.5 E5:.5'),
      (3, 'F#5:1.5 D5:.5 F#5:1.5 D5:.5'),
      (4, 'F#5:1.5 B4:.5 D5:.5 B4:.5 G4:.5 D5:.5'),
      (5, 'B4:2 B4:.5 E5:.5 D5:.5 C#5:.5'),
      (6, 'F#5:3 B4:.25 C#5:.25 D5:.25 E5:.25'),
      (7, 'F#5:1.5 D5:.5 F#5:1.5 D5:.5'),
      (8, 'F#5:1.5 B4:.5 D5:.5 B4:.5 G4:.5 D5:.5')]
s.line('oboe_solo', at(2), ' '.join(t for _, t in OB), dyn='p', legato=True, gain=3)
s.note('oboe_solo', at(9), 'B4', 4, dyn='p', dyn_end='pp', legato_from='D5', gain=3)

# ---------------------------------------------------------------- strings (measured tremolo)
def trem(part, m, seq, dyn='p', dyn_end=None):
    b = 0.0
    for p, d in seq:
        for q in (p if isinstance(p, list) else [p]):
            s.note(part, at(m, b), q, d, dyn=dyn, dyn_end=dyn_end, art='trem')
        b += d
VN1 = {1: [('F#4', 4)], 2: [('F#4', 2), ('G4', 2)], 3: [('F#4', 4)], 4: [('F#4', 2), ('E#4', 1), ('E4', 1)],
       5: [('D4', 1), ('G4', 1), ('F#4', 1), ('E4', 1)], 6: [(['B3', 'D4'], 2), (['B3', 'D4'], 1), ('B3', 1)],
       7: [('B3', 1), ('B3', 1), ('C#4', 1), ('D4', 1)], 8: [('E4', 1), ('D4', 1), ('D4', 1), ('E4', 1)],
       9: [('D4', 1), ('F#4', 1), ('B4', 1), ('F#4', 1)]}
VN2 = {1: [('D4', 4)], 2: [('D4', 2), ('E4', 2)], 3: [('D4', 4)], 4: [('D4', 2), ('B3', 1), ('B3', .5), ('A#3', .5)],
       5: [('B3', 1), ('B4', 1), ('A4', 1), ('G4', 1)], 6: [('F#4', 2), ('E#4', 1), ('E4', 1)],
       7: [('D4', 1), ('G#3', 1), ('A#3', 1), ('B3', 1)], 8: [('A#3', 1), ('B3', 1), ('B3', 1), ('B3', .5), ('A#3', .5)],
       9: [('B3', 1), ('D4', 1), ('F#4', 1), ('D4', 1)]}
VLA = {1: [('B3', 4)], 2: [('B3', 4)], 3: [('B3', 4)], 4: [('B3', 2), ('G#3', 1), ('G3', .5), ('F#3', .5)],
       5: [('F#3', 1), ('B3', 3)], 6: [('B3', 1), ('A3', 1), ('G#3', 1), ('G3', 1)], 7: [('F#3', 4)],
       8: [('F#3', 2), ('E#3', 1), ('E3', 1)], 9: [('F#3', 1), ('B3', 1), ('D4', 2)]}
for part, tab in (('violins1', VN1), ('violins2', VN2), ('violas', VLA)):
    for m, seq in tab.items():
        trem(part, m, seq, *(('f', 'p') if m == 1 else ('p',)))   # bar 1: sf > p

# celli / basses (basses sound an octave below the written note)
for m in (2, 5):
    s.note('celli', at(m), 'B2', 0.5, dyn='p', art='pizz')
    s.note('basses', at(m), 'B1', 0.5, dyn='p', art='pizz')
for b, p in ((1, 'F#3'), (2, 'E3'), (3, 'D3')):
    s.note('celli', at(7, b), p, 1, dyn='p', art='trem')                              # arco
for b, p, d in ((0, 'C#3', 1), (1, 'B2', .5), (1.5, 'A2', .5), (2, 'G#2', 1), (3, 'G2', .5), (3.5, 'F#2', .5)):
    s.note('celli', at(8, b), p, d, dyn='p', art='trem')
s.note('celli', at(9), 'B2', 0.5, dyn='p')                                          # arco eighth
s.note('celli', at(9, 2), 'B3', 0.5, dyn='p', art='pizz')
s.note('basses', at(9), 'B1', 0.5, dyn='p', art='pizz'); s.note('basses', at(9, 2), 'B2', 0.5, dyn='p', art='pizz')

# ---------------------------------------------------------------- harp (mf), bars 1-6
def harp(m, notes, step, start=0.0):
    for k, n in enumerate(notes):
        s.hit('harp', at(m, start + k * step), n, dyn='mf')
BM = ['B2', 'F#3', 'B3', 'D4', 'F#4', 'B4', 'D5', 'B4', 'F#4', 'D4', 'B3', 'F#3']
harp(1, BM, 1 / 3); harp(3, BM, 1 / 3)
harp(2, ['B2', 'F#3', 'B3', 'D4', 'F#4', 'B4', 'E3', 'G3', 'B3', 'E4', 'G4', 'B4'], 1 / 3)
harp(4, ['B2', 'F#3', 'B3', 'D4', 'F#4', 'B4'], 1 / 3); harp(4, ['B3', 'B4', 'B5'], 0.5, start=2.0)
harp(5, ['F#6', 'D6', 'B5', 'F#5', 'D5', 'B4', 'F#4', 'D4',      # 32nd-note cascades
         'D6', 'B5', 'G5', 'D5', 'B4', 'G4', 'D4', 'B3',
         'A5', 'F#5', 'D5', 'B4', 'A4', 'F#4', 'D4', 'B3',
         'G5', 'E5', 'B4', 'G4', 'E4', 'B3', 'G3', 'E3'], 1 / 8)
harp(6, ['B1', 'D2', 'F#2', 'B2', 'D3', 'F#3', 'B3', 'D4', 'F#4', 'B4', 'D5', 'F#5'], 2 / 12)   # 12 in 2 beats
s.hit('harp', at(6, 2.0), 'B5', dyn='mf')

if __name__ == '__main__':
    s.render(sys.argv[1] if len(sys.argv) > 1 else 'swan_lake_no10.wav', tail=3.5)
