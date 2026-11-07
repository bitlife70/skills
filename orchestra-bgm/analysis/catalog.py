"""Parse sample file names into (instrument, articulation, label_midi, dynamic, ensemble)."""
import os, re

PC = {'c': 0, 'c#': 1, 'db': 1, 'd': 2, 'd#': 3, 'eb': 3, 'e': 4, 'f': 5, 'f#': 6, 'gb': 6,
      'g': 7, 'g#': 8, 'ab': 8, 'a': 9, 'a#': 10, 'bb': 10, 'b': 11}
NOTE_RE = re.compile(r'(?<![a-z])([a-g](?:#|b)?)(-?\d)(?![\d])', re.I)

def note_midi(tok):
    m = NOTE_RE.search(tok)
    if not m: return None
    return 12 * (int(m.group(2)) + 1) + PC[m.group(1).lower()]

# (source, folder) -> instrument key, ensemble flag
FOLDER = {
    ('sso', '1st_Violins'): ('violins', True), ('sso', '2nd_Violins'): ('violins', True),
    ('vsco', 'Violin_Section'): ('violins', True),
    ('sso', 'Violas'): ('violas', True), ('vsco', 'Viola_Section'): ('violas', True),
    ('sso', 'Celli'): ('celli', True), ('vsco', 'Cello_Section'): ('celli', True),
    ('sso', 'Basses'): ('basses', True),
    ('sso', 'Violin'): ('violin_solo', False), ('vsco', 'Solo_Violin'): ('violin_solo', False),
    ('sso', 'Cello'): ('cello_solo', False), ('vsco', 'Solo_Contrabass'): ('contrabass_solo', False),
    ('sso', 'Flutes'): ('flutes', True), ('sso', 'Flute'): ('flute', False), ('vsco', 'Flute'): ('flute', False),
    ('sso', 'Piccolo'): ('piccolo', False),
    ('sso', 'Oboes'): ('oboes', True), ('sso', 'Oboe'): ('oboe', False), ('vsco', 'Oboe'): ('oboe', False),
    ('sso', 'Clarinets'): ('clarinets', True), ('sso', 'Clarinet'): ('clarinet', False), ('vsco', 'Clarinet'): ('clarinet', False),
    ('sso', 'Bassoons'): ('bassoons', True), ('sso', 'Bassoon'): ('bassoon', False), ('sso', 'Contrabassoon'): ('contrabassoon', False),
    ('sso', 'Horns'): ('horns', True), ('sso', 'Horn'): ('horn', False), ('vsco', 'F_Horn'): ('horn', False),
    ('sso', 'Trumpets'): ('trumpets', True), ('sso', 'Trumpet'): ('trumpet', False), ('vsco', 'Trumpet'): ('trumpet', False),
    ('sso', 'Trombones'): ('trombones', True), ('sso', 'Tenor_Trombone'): ('trombone', False), ('vsco', 'Tenor_Trombone'): ('trombone', False),
    ('sso', 'Tuba'): ('tuba', False), ('vsco', 'Tuba'): ('tuba', False),
    ('sso', 'Harp'): ('harp', False), ('vsco', 'Harp'): ('harp', False),
    ('sso', 'Chorus'): ('choir', True),
    ('vsco', 'Glock'): ('glockenspiel', False), ('vsco', 'Timpani'): ('timpani', False),
}
PERC = [  # (regex on sso/vsco percussion name, instrument, articulation, dynamic)
    (r'^timpani-roll-crsc', 'timpani', 'roll_cresc', 'mf'), (r'^timpani-roll', 'timpani', 'roll', 'mf'),
    (r'^timpani-f-', 'timpani', 'hit', 'f'), (r'^timpani-p-', 'timpani', 'hit', 'p'),
    (r'^bass_drum-f', 'bass_drum', 'hit', 'f'), (r'^bass_drum-p', 'bass_drum', 'hit', 'p'),
    (r'^BDrumNewhit_v1', 'bass_drum', 'hit', 'p'), (r'^BDrumNewhit_v3', 'bass_drum', 'hit', 'mp'),
    (r'^BDrumNewhit_v5', 'bass_drum', 'hit', 'mf'), (r'^BDrumNewhit_v7', 'bass_drum', 'hit', 'f'),
    (r'^piatti', 'cymbals', 'crash', 'f'), (r'^cymbal-crash1_ff', 'cymbals', 'crash', 'ff'),
    (r'^cymbal-crash1_mf', 'cymbals', 'crash', 'mf'), (r'^cymbal-crash1_pp', 'cymbals', 'crash', 'pp'),
    (r'^cymbal_roll', 'sus_cymbal', 'roll', 'mf'), (r'^susCymb1-cresc', 'sus_cymbal', 'roll_cresc', 'mf'),
    (r'^snare-rh', 'snare', 'hit', 'mf'), (r'^Snare2-HitSN_v1', 'snare', 'hit', 'p'),
    (r'^Snare2-HitSN_v5', 'snare', 'hit', 'mf'), (r'^Snare2-HitSN_v9', 'snare', 'hit', 'f'),
    (r'^tamtam', 'tamtam', 'hit', 'f'), (r'^gongHit_p', 'tamtam', 'hit', 'p'), (r'^gongHit_f\.', 'tamtam', 'hit', 'f'),
    (r'^gongHit_fff', 'tamtam', 'hit', 'ff'),
    (r'^glockenspiel', 'glockenspiel', 'hit', 'mf'), (r'^xylophone', 'xylophone', 'hit', 'mf'),
    (r'^chimes', 'chimes', 'hit', 'mf'), (r'^triangle-opn', 'triangle', 'hit', 'mf'), (r'^Triangle3', 'triangle', 'hit', 'mf'),
]
DYN_ORDER = ['ppp', 'pp', 'p', 'mp', 'mf', 'f', 'ff', 'fff']
DYN_VAL = {d: i / 7 for i, d in enumerate(DYN_ORDER)}   # 0..1

def articulation(name):
    n = name.lower()
    if re.search(r'piz', n): return 'pizz'
    if re.search(r'trm|trem', n): return 'trem'
    if re.search(r'stc|stac|spic', n): return 'staccato'
    return 'sus'

def dynamic(name, src):
    n = name
    m = re.search(r'-(pp|mp|mf|ff|p|f)-', n) or re.search(r'_(ppp|pp|p|mp|mf|f|ff|fff)(?:_|\.|$)', n)
    if m: return m.group(1)
    m = re.search(r'_v(\d)', n)
    if m and src == 'vsco':
        v = int(m.group(1)); return {1: 'p', 2: 'mf', 3: 'f', 4: 'ff'}.get(v, 'mf')
    return 'mf'

def parse(fname):
    src, folder, name = fname.split('__')
    base = os.path.splitext(name)[0]
    if folder == 'Percussion' or (src == 'sso' and folder == 'Percussion'):
        for rx, inst, art, dyn in PERC:
            if re.search(rx, base):
                return dict(file=fname, src=src, inst=inst, art=art, dyn=dyn, label=note_midi(base.split('-')[-1]) if inst in ('glockenspiel', 'xylophone', 'chimes') else None, ens=False)
        return None
    if (src, folder) not in FOLDER: return None
    inst, ens = FOLDER[(src, folder)]
    if 'harmon' in base or 'mute' in base or 'hrm' in base: return None   # skip muted / harmonics
    art = articulation(base)
    if inst == 'timpani': art = 'hit'
    if inst in ('harp', 'glockenspiel'): art = 'hit'
    if inst == 'choir':
        inst = 'choir_female' if 'female' in base else 'choir_male'
    # note token: last match in the name
    toks = NOTE_RE.findall(base.replace('_', ' ').replace('-', ' '))
    label = None
    if toks:
        t = toks[-1] if src == 'sso' else toks[0]
        label = 12 * (int(t[1]) + 1) + PC[t[0].lower()]
    if inst == 'timpani': label = None
    return dict(file=fname, src=src, inst=inst, art=art, dyn=dynamic(base, src), label=label, ens=ens)

def load_catalog(d='flac'):
    out = []
    for f in sorted(os.listdir(d)):
        r = parse(f)
        if r: out.append(r)
    return out

if __name__ == '__main__':
    import collections
    cat = load_catalog()
    c = collections.Counter((r['inst'], r['art'], r['dyn']) for r in cat)
    for k, v in sorted(c.items()): print(v, k)
    print(len(cat), 'missing label:', [r['file'] for r in cat if r['label'] is None and r['art'] not in ('hit', 'crash', 'roll', 'roll_cresc')][:10])
