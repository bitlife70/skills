"""Demo: 'Rising Horizon' - cinematic orchestral cue in D minor (~78 s), written with the Score API."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from orchestra import Score

s = Score(bpm=84, seed=7, rt=2.3)
B = 4  # beats per bar
def bar(n): return (n - 1) * B

CH = {'Dm': ['D', 'F', 'A'], 'Gm': ['G', 'Bb', 'D'], 'F': ['F', 'A', 'C'], 'C': ['C', 'E', 'G'],
      'Bb': ['Bb', 'D', 'F'], 'A': ['A', 'C#', 'E'], 'D': ['D', 'F#', 'A']}
ROOT2 = {'Dm': 'D2', 'Gm': 'G1', 'F': 'F2', 'C': 'C2', 'Bb': 'Bb1', 'A': 'A1', 'D': 'D2'}
def up(n, o): return n + str(o)

# ---------------------------------------------------------------- intro (bars 1-4): mist
for b, ch in zip(range(1, 5), ['Dm', 'Dm', 'Bb', 'A']):
    r = ROOT2[ch]
    s.note('basses', bar(b), r[:-1] + str(int(r[-1]) + 1), B, dyn='pp', dyn_end='p', art='trem')
    s.note('celli', bar(b), r[:-1] + str(int(r[-1]) + 1), B, dyn='pp', dyn_end='p', art='trem')
    s.chord('violas', bar(b), [up(CH[ch][1], 3) if ch != 'A' else 'C#4', up(CH[ch][2], 3) if ch not in ('Bb',) else 'F4'], B, dyn='pp', dyn_end='p', art='trem')
    s.chord('violins2', bar(b), [up(CH[ch][0], 4), up(CH[ch][2], 4)], B, dyn='pp', dyn_end='mp')
    s.chord('violins1', bar(b), [up(CH[ch][1], 5)], B, dyn='pp', dyn_end='mp')
s.roll('timpani', bar(1), 2 * B, 'D2', dyn='pp', dyn_end='mp')
s.roll('timpani', bar(3), 2 * B - 0.5, 'A2', dyn='pp', dyn_end='mf')
s.roll('sus_cymbal', bar(4), B, dyn='pp', dyn_end='mf')
for b, ch in zip(range(1, 5), ['Dm', 'Dm', 'Bb', 'A']):          # harp arpeggios
    notes = [up(CH[ch][0], 3), up(CH[ch][2], 3), up(CH[ch][0], 4), up(CH[ch][1], 4), up(CH[ch][2], 4), up(CH[ch][0], 5)]
    for k, n in enumerate(notes + notes[::-1][1:3]):
        s.hit('harp', bar(b) + k * 0.5, n, dyn='mp')
s.chord('horns', bar(3), ['F3', 'Bb3', 'D4'], B, dyn='pp', dyn_end='mp')
s.chord('horns', bar(4), ['E3', 'A3', 'C#4'], B, dyn='mp', dyn_end='p')

# ---------------------------------------------------------------- theme A (bars 5-12)
PROG = ['Dm', 'Gm', 'F', 'C', 'Dm', 'Gm', 'Bb', 'A']
MEL = ('A4:1 D5:1.5 E5:.5 F5:1 | G5:2 F5:1 E5:1 | F5:1.5 E5:.5 C5:2 | E5:2 G5:2 | '
       'A5:1.5 G5:.5 F5:1 E5:1 | D5:1 Bb4:1 D5:1 G5:1 | F5:2 E5:1 D5:1 | C#5:2 A4:2')
s.line('violins1', bar(5), MEL, dyn='mp', legato=True)
s.line('flutes', bar(9), ' '.join(t if ':' not in t else t.split(':')[0][:-1] + str(int(t.split(':')[0][-1]) + 1) + ':' + t.split(':')[1]
                                    for t in MEL.split('|', 4)[-1].split()), dyn='p', legato=True)
for i, ch in enumerate(PROG):
    b = bar(5 + i)
    s.note('basses', b, ROOT2[ch], B, dyn='mp')
    s.note('celli', b, ROOT2[ch][:-1] + str(int(ROOT2[ch][-1]) + 1), 2, dyn='mp')
    s.note('celli', b + 2, up(CH[ch][2], 2 if CH[ch][2] in ('A', 'Bb', 'C#', 'G') else 3), 2, dyn='mp')
    s.chord('violas', b, [up(CH[ch][0], 4) if CH[ch][0] in ('C', 'D') else up(CH[ch][0], 3)], B, dyn='p', dyn_end='mp')
    s.chord('violins2', b, [up(CH[ch][1], 4), up(CH[ch][2], 4)], B, dyn='p', dyn_end='mp')
    s.chord('clarinets', b, [up(CH[ch][1], 4)], B, dyn='pp', dyn_end='p')
    s.chord('bassoons', b, [up(CH[ch][0], 3)], B, dyn='pp', dyn_end='p')
    if i >= 4:
        s.chord('horns', b, [up(CH[ch][0], 3), up(CH[ch][2], 3)], B, dyn='p', dyn_end='mp')

# ---------------------------------------------------------------- build (bars 13-16): ostinato
BUILD = ['Bb', 'C', 'Dm', 'A']
for i, ch in enumerate(BUILD):
    b = bar(13 + i); r = ROOT2[ch]
    lvl = ['mp', 'mf', 'mf', 'f'][i]
    for k in range(8):
        acc = 'f' if k % 4 == 0 else lvl
        s.note('celli', b + k * 0.5, r[:-1] + str(int(r[-1]) + 1), 0.45, dyn=acc, art='staccato')
        s.note('basses', b + k * 0.5, r if k % 2 == 0 else r[:-1] + str(int(r[-1]) + 1), 0.45, dyn=acc, art='staccato')
        s.note('violas', b + k * 0.5, up(CH[ch][2 if k % 2 else 0], 4 if CH[ch][0] in ('C', 'D') else 3), 0.45, dyn=lvl, art='staccato')
        s.note('violins2', b + k * 0.5, up(CH[ch][1], 4) if k % 2 == 0 else up(CH[ch][2], 4), 0.45, dyn=lvl, art='staccato')
    s.chord('violins1', b, [up(CH[ch][0], 5), up(CH[ch][1], 5)], B, dyn='mp', dyn_end='f')
    s.chord('horns', b, [up(CH[ch][0], 3), up(CH[ch][1], 3), up(CH[ch][2], 3)], B, dyn='mp', dyn_end='f')
    s.chord('trombones', b, [up(CH[ch][0], 2) if CH[ch][0] in ('C', 'D') else up(CH[ch][0], 2), up(CH[ch][2], 3)], B, dyn='p', dyn_end='mf')
    s.note('tuba', b, r, B, dyn='p', dyn_end='mf')
    s.hit('timpani', b, 'D2' if ch in ('Dm', 'Bb') else 'A2', dyn=lvl)
    s.hit('timpani', b + 2.5, 'A2', dyn='mp')
s.roll('snare', bar(15), 2 * B, dyn='p', dyn_end='f')
s.roll('sus_cymbal', bar(16), B, dyn='p', dyn_end='f')
s.roll('timpani', bar(16), B, 'A2', dyn='mf', dyn_end='ff')
s.chord('trumpets', bar(16), ['A4', 'C#5', 'E5'], B, dyn='mp', dyn_end='f')

# ---------------------------------------------------------------- climax (bars 17-24): tutti theme
s.line('horns', bar(17), MEL.replace('4:', '3:').replace('5:', '4:'), dyn='f', legato=True)
s.line('trumpets', bar(17), MEL, dyn='mf', legato=True)
s.line('violins1', bar(17), ' '.join(t if ':' not in t else t.split(':')[0][:-1] + str(int(t.split(':')[0][-1]) + 1) + ':' + t.split(':')[1]
                                        for t in MEL.split()), dyn='f', legato=True)
s.line('violins2', bar(17), MEL, dyn='f', legato=True)
s.line('flutes', bar(17), ' '.join(t if ':' not in t else t.split(':')[0][:-1] + str(int(t.split(':')[0][-1]) + 1) + ':' + t.split(':')[1]
                                     for t in MEL.split()), dyn='mf', legato=True)
for i, ch in enumerate(PROG):
    b = bar(17 + i); r = ROOT2[ch]
    s.note('basses', b, r, B, dyn='f')
    s.note('tuba', b, r, B, dyn='mf')
    s.note('celli', b, r[:-1] + str(int(r[-1]) + 1), B, dyn='f')
    s.chord('violas', b, [up(CH[ch][1], 4) if CH[ch][1] not in ('F#',) else 'F#3', up(CH[ch][2], 3)], B, dyn='f')
    s.chord('trombones', b, [up(CH[ch][0], 3), up(CH[ch][1], 3)], B, dyn='mf')
    s.chord('bassoons', b, [up(CH[ch][0], 3)], B, dyn='mf')
    s.chord('clarinets', b, [up(CH[ch][1], 4), up(CH[ch][2], 4)], B, dyn='mf')
    s.chord('choir_female', b, [up(CH[ch][1], 5) if CH[ch][1] in ('C', 'C#', 'D') else up(CH[ch][1], 4), up(CH[ch][2], 5) if CH[ch][2] in ('C', 'C#', 'D') else up(CH[ch][2], 4)], B, dyn='mp', dyn_end='mf')
    s.chord('choir_male', b, [up(CH[ch][0], 3), up(CH[ch][2], 3)], B, dyn='mp', dyn_end='mf')
    s.hit('timpani', b, 'D2' if ch in ('Dm', 'Bb', 'Gm') else 'A2', dyn='f')
    s.hit('bass_drum', b, dyn='mf' if i % 2 else 'f')
s.hit('cymbals', bar(17), dyn='f'); s.hit('tamtam', bar(17), dyn='mf')
s.hit('cymbals', bar(21), dyn='mf')
s.roll('timpani', bar(24), B, 'A2', dyn='mf', dyn_end='ff')

# ---------------------------------------------------------------- final chord (bars 25-26): D major
fin = bar(25)
s.chord('violins1', fin, ['D5', 'F#5', 'A5', 'D6'], 2 * B, dyn='ff', dyn_end='mf')
s.chord('violins2', fin, ['A4', 'D5', 'F#5'], 2 * B, dyn='ff', dyn_end='mf')
s.chord('violas', fin, ['D4', 'A4'], 2 * B, dyn='ff', dyn_end='mf')
s.note('celli', fin, 'D3', 2 * B, dyn='ff', dyn_end='mf'); s.note('celli', fin, 'D2', 2 * B, dyn='ff', dyn_end='mf')
s.note('basses', fin, 'D2', 2 * B, dyn='ff', dyn_end='mf')
s.chord('horns', fin, ['D3', 'F#3', 'A3', 'D4'], 2 * B, dyn='ff', dyn_end='mf')
s.chord('trumpets', fin, ['D5', 'F#5', 'A5'], 2 * B, dyn='f', dyn_end='mp')
s.chord('trombones', fin, ['D3', 'A3'], 2 * B, dyn='f', dyn_end='mp')
s.note('tuba', fin, 'D2', 2 * B, dyn='f', dyn_end='mp')
s.chord('flutes', fin, ['F#5', 'A5'], 2 * B, dyn='f', dyn_end='mp')
s.chord('choir_female', fin, ['F#4', 'A4', 'D5'], 2 * B, dyn='f', dyn_end='mp')
s.chord('choir_male', fin, ['D3', 'A3', 'F#3'], 2 * B, dyn='f', dyn_end='mp')
s.hit('timpani', fin, 'D2', dyn='ff'); s.hit('bass_drum', fin, dyn='ff'); s.hit('cymbals', fin, dyn='ff')
for k, n in enumerate(['D6', 'F#6', 'A6', 'D7']):
    s.hit('glockenspiel', fin + 0.5 + k * 0.5, n, dyn='mp')
for k, n in enumerate(['D3', 'A3', 'D4', 'F#4', 'A4', 'D5', 'F#5', 'A5']):
    s.hit('harp', fin + k * 0.25, n, dyn='mf')

if __name__ == '__main__':
    s.render(sys.argv[1] if len(sys.argv) > 1 else 'rising_horizon.wav', tail=4.5)
