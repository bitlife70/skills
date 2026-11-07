"""Demo: 30-second Shorts cue 'Ignite' (E minor, 112 bpm) - hook on the first beat, phone-audible voicing,
rendered with master='shorts'. Pass 'narration' as 2nd arg to carve the voice pocket."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from orchestra import Score, bpm_for

BARS = 14
s = Score(bpm=round(bpm_for(30, BARS), 2), seed=3, rt=2.0)
B = 4
def bar(n): return (n - 1) * B
CH = {'Em': ['E', 'G', 'B'], 'C': ['C', 'E', 'G'], 'G': ['G', 'B', 'D'], 'D': ['D', 'F#', 'A'],
      'Am': ['A', 'C', 'E'], 'B': ['B', 'D#', 'F#']}
LOW = {'Em': 'E2', 'C': 'C2', 'G': 'G1', 'D': 'D2', 'Am': 'A1', 'B': 'B1'}
def o(n, k): return n + str(k)
def up(p, k=1): return p[:-1] + str(int(p[-1]) + k)

prog = ['Em', 'Em', 'Em', 'C', 'G', 'D', 'Am', 'C', 'D', 'B', 'Em', 'C', 'D', 'Em']
# ---------------- ostinato (whole cue except the last bar): celli double the bass an octave up (phones)
for i, ch in enumerate(prog[:-1]):
    b = bar(i + 1); r = LOW[ch]; lvl = 'mf' if i < 6 else 'f'
    for k in range(8):
        acc = 'f' if k in (0, 3, 6) else lvl
        s.note('basses', b + k * 0.5, r, 0.4, dyn=acc, art='staccato', voices=3)
        s.note('celli', b + k * 0.5, up(r), 0.4, dyn=acc, art='staccato', voices=4)
        s.note('violas', b + k * 0.5, o(CH[ch][2 if k % 2 else 0], 3 if CH[ch][0] in ('G', 'A', 'B') else 4), 0.4, dyn=lvl, art='staccato', voices=4)
    s.hit('timpani', b, 'E2' if ch in ('Em', 'C', 'Am') else 'B2' if ch in ('B', 'G') else 'D2', dyn='f')
    s.hit('timpani', b + 1.5, 'E2' if ch in ('Em', 'C', 'Am') else 'B2' if ch in ('B', 'G') else 'D2', dyn='mf')
    if i >= 2:
        s.hit('snare', b + 1, dyn='mp'); s.hit('snare', b + 3, dyn='mp'); s.hit('snare', b + 3.5, dyn='p')
# ---------------- hook: first beat stab + violin motif (bars 1-2)
s.chord('horns', 0, ['E3', 'B3', 'E4', 'G4'], 1, dyn='ff', art='marcato')
s.chord('trombones', 0, ['E2', 'B2', 'E3'], 1, dyn='f', art='marcato')
s.hit('cymbals', 0, dyn='f'); s.hit('bass_drum', 0, dyn='f')
HOOK = 'E5:.5 E5:.5 G5:.5 F#5:.5 E5:1 B4:1 | E5:.5 E5:.5 G5:.5 A5:.5 B5:2'
s.line('violins1', 0, HOOK, dyn='f', art='staccato', gap=0.08)
s.line('violins2', 0, HOOK.replace('5:', '4:'), dyn='f', art='staccato', gap=0.08)
# ---------------- theme (bars 3-6) horns + violins in octaves
THEME = 'B4:1.5 A4:.5 G4:1 F#4:1 | E4:1 G4:1 C5:2 | B4:1.5 A4:.5 G4:1 B4:1 | A4:2 F#4:2'
s.line('horns', bar(3), THEME.replace('5:', '4:').replace('4:', '4:'), dyn='f', legato=True)
s.line('violins1', bar(3), ' '.join(t if ':' not in t else up(t.split(':')[0]) + ':' + t.split(':')[1] for t in THEME.split()), dyn='f', legato=True)
for i, ch in enumerate(prog[2:6]):
    s.chord('violins2', bar(3 + i), [o(CH[ch][1], 4), o(CH[ch][2], 4)], B, dyn='mp', dyn_end='mf')
s.roll('sus_cymbal', bar(6), B, dyn='p', dyn_end='f')
# ---------------- climax (bars 7-12): trumpets + violins octave up, choir pad
CLIMAX = 'E5:1.5 D5:.5 C5:1 E5:1 | G5:2 E5:2 | F#5:1.5 E5:.5 D5:1 F#5:1 | D#5:2 B4:2 | E5:1.5 F#5:.5 G5:1 B5:1 | A5:2 G5:1 E5:1'
s.hit('cymbals', bar(7), dyn='ff'); s.hit('bass_drum', bar(7), dyn='ff')
s.line('trumpets', bar(7), CLIMAX, dyn='f', legato=True)
s.line('violins1', bar(7), ' '.join(t if ':' not in t else up(t.split(':')[0]) + ':' + t.split(':')[1] for t in CLIMAX.split()), dyn='f', legato=True)
s.line('horns', bar(7), CLIMAX.replace('5:', '4:'), dyn='f', legato=True)
for i, ch in enumerate(prog[6:12]):
    b = bar(7 + i)
    s.chord('violins2', b, [o(CH[ch][1], 4), o(CH[ch][2], 4)], B, dyn='f')
    s.chord('trombones', b, [o(CH[ch][0], 3), o(CH[ch][2], 3)], B, dyn='mf')
    s.chord('choir_female', b, [o(CH[ch][0], 5) if CH[ch][0] in ('C', 'D') else o(CH[ch][0], 4), o(CH[ch][2], 4) if CH[ch][2] in ('G', 'A', 'B') else o(CH[ch][2], 5)], B, dyn='mp')
    s.note('tuba', b, LOW[ch], B, dyn='mf')
    s.hit('bass_drum', b + 2, dyn='mf')
s.hit('cymbals', bar(11), dyn='f')
s.roll('timpani', bar(12) + 2, 2, 'D2', dyn='mf', dyn_end='ff')
# ---------------- ending (bars 13-14): stabs -> final hit (last bar returns to Em -> loopable)
for bt, dyn in ((0, 'f'), (1.5, 'f'), (3, 'ff')):
    s.chord('horns', bar(13) + bt, ['D3', 'A3', 'D4', 'F#4'], 0.5, dyn=dyn, art='marcato')
    s.chord('trumpets', bar(13) + bt, ['A4', 'D5', 'F#5'], 0.5, dyn=dyn, art='marcato')
    s.chord('violins1', bar(13) + bt, ['D5', 'A5'], 0.5, dyn=dyn, art='staccato')
    s.hit('timpani', bar(13) + bt, 'D2', dyn=dyn)
fin = bar(14)
s.chord('horns', fin, ['E3', 'B3', 'E4', 'G4'], 1.5, dyn='ff', art='marcato')
s.chord('trumpets', fin, ['G4', 'B4', 'E5'], 1.5, dyn='ff', art='marcato')
s.chord('trombones', fin, ['E2', 'B2', 'E3'], 1.5, dyn='ff', art='marcato')
s.chord('violins1', fin, ['E5', 'B5'], 1.5, dyn='ff'); s.chord('violins2', fin, ['G4', 'E5'], 1.5, dyn='ff')
s.note('celli', fin, 'E3', 1.5, dyn='ff'); s.note('basses', fin, 'E2', 1.5, dyn='ff'); s.note('tuba', fin, 'E2', 1.5, dyn='f')
s.hit('timpani', fin, 'E2', dyn='ff'); s.hit('bass_drum', fin, dyn='ff'); s.hit('cymbals', fin, dyn='ff')

if __name__ == '__main__':
    narr = len(sys.argv) > 2 and sys.argv[2] == 'narration'
    s.render(sys.argv[1] if len(sys.argv) > 1 else 'ignite_shorts.wav', tail=2.5, master='shorts', narration=narr)
