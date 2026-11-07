"""'Ashen Throne' - dark-fantasy soulslike BGM in D minor (~2 min).
Form: funeral-bell intro (1-6) -> theme in low male choir (7-14) -> ostinato build (15-22)
-> tutti theme with choir & brass (23-30) -> aftermath, last ember of the motif (31-35)."""
import sys, os, re
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from orchestra import Score

s = Score(bpm=72, seed=23, rt=2.8)                 # cathedral-like hall
B = 4
def bar(n, b=0.0): return (n - 1) * B + b

PC = {'C': 0, 'C#': 1, 'D': 2, 'Eb': 3, 'E': 4, 'F': 5, 'F#': 6, 'G': 7, 'Ab': 8, 'A': 9, 'Bb': 10, 'B': 11}
CH = {'Dm': ('D', 'F', 'A'), 'A': ('A', 'C#', 'E'), 'Gm': ('G', 'Bb', 'D'), 'Bb': ('Bb', 'D', 'F'), 'Eb': ('Eb', 'G', 'Bb')}
def tones(ch, lo, hi):                              # chord tones (MIDI) inside [lo, hi]
    pcs = {PC[n] for n in CH[ch]}
    return [m for m in range(lo, hi + 1) if m % 12 in pcs]
def root(ch, lo):                                   # lowest root at/above lo (MIDI)
    r = PC[CH[ch][0]]
    m = lo
    while m % 12 != r: m += 1
    return m
def shift(line, octs):                              # transpose a line string by octaves
    return re.sub(r'([A-G][#b]?)(\d)', lambda m: m.group(1) + str(int(m.group(2)) + octs), line)

# main motif (octave-4 reference); Phrygian Eb in bar 6, dominant C# in bars 2/7
THEME = ('D4:1.5 F4:.5 E4:1 D4:1 | C#4:1 D4:1 E4:1 A3:1 | Bb3:1.5 A3:.5 G3:1 Bb3:1 | A3:3 r:1 | '
         'D4:1.5 F4:.5 G4:1 A4:1 | Bb4:1.5 A4:.5 G4:1 Eb4:1 | D4:1 F4:1 E4:1 C#4:1 | D4:4')
TH_HARM = ['Dm', 'A', 'Gm', 'A', 'Dm', 'Eb', ('Bb', 'A'), 'Dm']
def harm_slots(start_bar, harm):
    out = []
    for i, h in enumerate(harm):
        if isinstance(h, tuple):
            out += [(bar(start_bar + i), h[0], 2), (bar(start_bar + i, 2), h[1], 2)]
        else:
            out.append((bar(start_bar + i), h, B))
    return out
TIMP = {'Dm': 'D2', 'A': 'A2', 'Gm': 'G2', 'Bb': 'D2', 'Eb': 'Eb2'}

# =============================================================== A. intro (1-6): bells in the ash
s.hit('tamtam', bar(1), dyn='mp')
s.note('contrabassoon', bar(1), 'D1', 24, dyn='pp', dyn_end='p')
s.note('basses', bar(1), 'D2', 24, dyn='pp', dyn_end='p')
s.note('celli', bar(1), 'A2', 24, dyn='pp', dyn_end='p', art='trem')
s.chord('violas', bar(1), ['A3', 'Bb3'], 16, dyn='ppp', dyn_end='p', art='trem')       # semitone shimmer
s.note('violas', bar(5), 'A3', 8, dyn='p', dyn_end='pp', art='trem')
s.note('violins1', bar(1), 'D6', 24, dyn='ppp', dyn_end='pp')
s.note('violins2', bar(3), 'A5', 16, dyn='ppp', dyn_end='pp')
for m in (1, 3, 5):
    s.hit('chimes', bar(m), 'D4', dyn='mp')
    s.hit('chimes', bar(m, 2), 'A3', dyn='p')
s.chord('choir_male', bar(3), ['D3', 'A3'], 8, dyn='pp', dyn_end='mp')
s.chord('choir_male', bar(5), ['Bb2', 'F3'], 4, dyn='mp')
s.chord('choir_male', bar(6), ['A2', 'E3'], 4, dyn='mp', dyn_end='p')
s.line('horns', bar(5), 'D4:1.5 F4:.5 E4:1 D4:1 | C#4:2 A3:2', dyn='p', legato=True)
s.roll('timpani', bar(6), 4, 'A2', dyn='pp', dyn_end='mp')

# =============================================================== B. theme in the deep (7-14)
s.line('choir_male', bar(7), shift(THEME, -1), dyn='mp', legato=True, gain=1)
s.line('celli', bar(7), shift(THEME, -1), dyn='p', legato=True)
s.line('bassoons', bar(7), shift(THEME, -1), dyn='p', legato=True)
for t, ch, d in harm_slots(7, TH_HARM):
    s.note('basses', t, root(ch, 31), d, dyn='mp')                           # G1..F#2
    s.note('contrabassoon', t, root(ch, 31), d, dyn='p')
    s.chord('violas', t, tones(ch, 57, 66)[:2], d, dyn='p', art='trem')
    s.chord('violins2', t, tones(ch, 62, 72)[:2], d, dyn='p', art='trem')
    s.chord('horns', t, tones(ch, 50, 60)[:2], d, dyn='pp', dyn_end='p')
s.line('violins1', bar(11), 'A5:4 | Bb5:4 | F5:2 E5:2 | D5:4', dyn='pp', legato=True)
s.hit('timpani', bar(7), 'D2', dyn='mf'); s.hit('timpani', bar(11), 'D2', dyn='mp')
s.hit('tamtam', bar(7), dyn='p')
s.hit('chimes', bar(7), 'D4', dyn='p'); s.hit('chimes', bar(11), 'D4', dyn='p')

# =============================================================== C. build (15-22): the march of the hollow
BUILD = ['Dm', 'Dm', 'Bb', 'Bb', 'Gm', 'Gm', 'Eb', 'A']
LV = ['mp', 'mp', 'mf', 'mf', 'mf', 'f', 'f', 'f']
UP = {'mp': 'mf', 'mf': 'f', 'f': 'ff'}
OST = [0, 0, 12, 0, 0, 12, 1, 0]                    # 8ths: root, octave, Phrygian b2
for i, ch in enumerate(BUILD):
    m = 15 + i; lv = LV[i]
    rc = root(ch, 43)                               # celli root G2..F#3
    for k, iv in enumerate(OST):
        acc = UP[lv] if k in (0, 3) else lv
        s.note('celli', bar(m, k * .5), rc + iv, .45, dyn=acc, art='staccato', voices=4)
        s.note('basses', bar(m, k * .5), rc - 12 + (iv if iv != 12 else 0), .45, dyn=acc, art='staccato', voices=4)
    s.chord('violas', bar(m), tones(ch, 57, 66)[:2], B, dyn=lv, art='trem')
    s.hit('timpani', bar(m), TIMP[ch], dyn=lv)
    if i >= 4:
        s.hit('timpani', bar(m, 2.5), TIMP[ch], dyn='mf'); s.hit('bass_drum', bar(m), dyn='mf')
# rising string line
for (m, n1, n2, d, a, b_) in [(15, 'D5', 'A4', 8, 'p', 'mp'), (17, 'F5', 'D5', 8, 'mp', 'mf'),
                              (19, 'Bb5', 'D5', 8, 'mf', 'f'), (21, 'Bb5', 'G5', 4, 'f', 'f'), (22, 'C#6', 'E5', 4, 'f', 'ff')]:
    s.note('violins1', bar(m), n1, d, dyn=a, dyn_end=b_, art='trem')
    s.note('violins2', bar(m), n2, d, dyn=a, dyn_end=b_, art='trem')
# horn calls on the motif head
for m, call in [(15, 'D4:1.5 F4:.5 E4:1 D4:1'), (17, 'D4:1.5 F4:.5 E4:1 D4:1'),
                (19, 'G4:1.5 Bb4:.5 A4:1 G4:1'), (21, 'Eb4:1.5 G4:.5 F4:1 Eb4:1')]:
    s.line('horns', bar(m), call, dyn='mf' if m < 19 else 'f', legato=True)
    ch = BUILD[m - 15]
    s.chord('horns', bar(m + 1), tones(ch, 55, 67)[:2], B, dyn='mf', dyn_end='f')
for i, ch in enumerate(BUILD):
    m = 15 + i
    s.chord('trombones', bar(m), [root(ch, 38), root(ch, 38) + 7], B, dyn='p' if i < 4 else 'mf', dyn_end='mf' if i < 4 else 'f')
    if i >= 2:
        s.chord('choir_male', bar(m), [root(ch, 43), root(ch, 43) + 7], B, dyn='mp' if i < 5 else 'mf', dyn_end='f' if i >= 5 else None)
    if i >= 4:
        s.note('tuba', bar(m), root(ch, 31), B, dyn='mf')
s.chord('choir_female', bar(19), ['Bb4', 'D5'], 8, dyn='p', dyn_end='mf')
s.chord('choir_female', bar(21), ['G4', 'Eb5'], 4, dyn='mf', dyn_end='f')
s.chord('choir_female', bar(22), ['C#5', 'E5'], 4, dyn='f', dyn_end='ff')
s.chord('trumpets', bar(22), ['A4', 'C#5', 'E5'], 4, dyn='mp', dyn_end='f')
s.roll('timpani', bar(22), 4, 'A2', dyn='mf', dyn_end='ff')
s.roll('sus_cymbal', bar(22), 4, dyn='pp', dyn_end='f')

# =============================================================== D. climax (23-30): the throne awakens
s.line('trumpets', bar(23), THEME, dyn='f', legato=True)
s.line('horns', bar(23), shift(THEME, -1), dyn='f', legato=True, gain=2)
s.line('violins1', bar(23), shift(THEME, 1), dyn='f', legato=True)
s.line('violins2', bar(23), THEME, dyn='f', legato=True)
s.line('choir_female', bar(23), shift(THEME, 1), dyn='mf', legato=True)
s.line('choir_male', bar(23), shift(THEME, -1), dyn='f', legato=True)
CL = ['f'] * 8
for t, ch, d in harm_slots(23, TH_HARM):
    r1 = root(ch, 31)
    s.note('basses', t, r1, d, dyn='f'); s.note('tuba', t, r1, d, dyn='f'); s.note('contrabassoon', t, r1, d, dyn='mf')
    s.chord('trombones', t, [r1 + 12, r1 + 19], d, dyn='f')
    s.chord('violas', t, tones(ch, 57, 66)[:2], d, dyn='f', art='trem')
    s.hit('timpani', t, TIMP[ch], dyn='f')
    rc = root(ch, 43)
    for k in range(int(d * 2)):
        iv = OST[k % 8]
        s.note('celli', t + k * .5, rc + iv, .45, dyn='ff' if k % 4 == 0 else 'f', art='staccato', voices=4)
for m in range(23, 31):
    s.hit('bass_drum', bar(m), dyn='f' if m in (23, 27) else 'mf')
    s.hit('timpani', bar(m, 2), TIMP[TH_HARM[m - 23] if isinstance(TH_HARM[m - 23], str) else TH_HARM[m - 23][1]], dyn='mf')
s.hit('cymbals', bar(23), dyn='ff'); s.hit('tamtam', bar(23), dyn='f')
s.hit('cymbals', bar(27), dyn='f')
s.roll('timpani', bar(30, 2), 2, 'A2', dyn='mf', dyn_end='ff')
s.chord('horns', bar(30), ['D3', 'A3'], 4, dyn='f', dyn_end='ff')

# =============================================================== E. aftermath (31-35): last ember
s.hit('timpani', bar(31), 'D2', dyn='ff'); s.hit('bass_drum', bar(31), dyn='f'); s.hit('tamtam', bar(31), dyn='f')
s.note('basses', bar(31), 'D2', 20, dyn='f', dyn_end='pp')
s.note('contrabassoon', bar(31), 'D1', 20, dyn='mf', dyn_end='pp')
s.chord('trombones', bar(31), ['D2', 'A2'], 4, dyn='f', dyn_end='pp')
s.hit('chimes', bar(31), 'D4', dyn='mf'); s.hit('chimes', bar(33), 'D4', dyn='p'); s.hit('chimes', bar(33, 2), 'A3', dyn='pp')
s.line('cello_solo', bar(32), 'D4:1.5 F4:.5 E4:1 D4:1 | C#4:2 D4:2', dyn='p', legato=True, gain=2)
s.note('violins1', bar(32), 'D6', 16, dyn='ppp', dyn_end='pp', art='trem')
s.note('violins2', bar(32), 'A5', 16, dyn='ppp', dyn_end='pp', art='trem')
s.chord('choir_male', bar(33), ['D3', 'F3', 'A3'], 12, dyn='pp', dyn_end='ppp')
s.chord('violas', bar(34), ['D4', 'F4'], 8, dyn='pp', dyn_end='ppp')

if __name__ == '__main__':
    s.render(sys.argv[1] if len(sys.argv) > 1 else 'ashen_throne.wav', tail=6.0, workers=2)
