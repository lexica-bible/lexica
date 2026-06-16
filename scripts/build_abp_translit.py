#!/usr/bin/env python3
"""
build_abp_translit.py — fill abp_surface.translit by romanizing each printed
ABP Greek form, matching the lexicon headword style (keeps accents; eta->e-macron,
omega->o-macron, chi->ch, theta->th, phi->ph, rough breathing->h).

ABP forms carry accents but NO breathing marks, so the rough-breathing 'h' is
read from the word's dictionary form (lexicon.lemma) and added to vowel-initial
forms (and word-initial rho is always rough -> rh). Reads words/lexicon/
abp_surface; writes ONLY abp_surface.translit.

  python3 build_abp_translit.py bible.db --dry-run   # show samples, write nothing
  python3 build_abp_translit.py bible.db             # fill the column

Re-run after any words/abp_surface rebuild that shifts positions (like
build_abp_surface.py) — it keys on verse_id+position.
"""
import sqlite3
import sys
import unicodedata

# Combining marks, by codepoint, so the source stays plain ASCII (no invisible bytes).
MAC = chr(0x0304)            # combining macron, for eta and omega
ACUTE = chr(0x0301)          # Latin acute
CIRC = chr(0x0302)           # Latin circumflex
TONOS = chr(0x0301)          # Greek acute (tonos / oxia)
PERISP = chr(0x0342)         # Greek circumflex (perispomeni)
VARIA = chr(0x0300)          # Greek grave (varia)
ROUGH = chr(0x0314)          # rough breathing (dasia) — lives in the lemma

LETTER = {
  'α': 'a', 'β': 'b', 'γ': 'g', 'δ': 'd', 'ε': 'e',
  'ζ': 'z', 'η': 'e' + MAC, 'θ': 'th', 'ι': 'i', 'κ': 'k',
  'λ': 'l', 'μ': 'm', 'ν': 'n', 'ξ': 'x', 'ο': 'o',
  'π': 'p', 'ρ': 'r', 'σ': 's', 'ς': 's', 'τ': 't',
  'υ': 'y', 'φ': 'ph', 'χ': 'ch', 'ψ': 'ps', 'ω': 'o' + MAC,
}
ACC = {TONOS: ACUTE, VARIA: ACUTE, PERISP: CIRC}     # grave folded to acute for an isolated form
VOWELS = set('αεηιουω')
DIPH_FIRST = 'αεηο'          # an upsilon after one of these is 'u' (au/eu/euu/ou)
NASAL_NEXT = 'γκχξ'          # a gamma before one of these is 'n'


def rough_breathing(lemma):
    return ROUGH in unicodedata.normalize('NFD', lemma or '')


def romanize(form, lemma):
    units = []                                       # base letters, each with its accent marks
    for ch in unicodedata.normalize('NFD', form):
        if unicodedata.category(ch) == 'Mn':
            if units:
                units[-1][1].append(ch)              # accent/breathing/subscript on prev letter
        else:
            units.append([ch, []])
    out = []
    for i, (ch, marks) in enumerate(units):
        low = ch.lower()
        prev = units[i - 1][0].lower() if i else ''
        nxt = units[i + 1][0].lower() if i + 1 < len(units) else ''
        if low == 'υ' and prev in DIPH_FIRST:   # diphthong: au / eu / euu / ou
            lat = 'u'
        elif low == 'ρ' and i == 0:             # word-initial rho is always rough -> rh
            lat = 'rh'
        elif low == 'γ' and nxt in NASAL_NEXT:  # gamma-nasal: gamma-gamma -> ng
            lat = 'n'
        else:
            lat = LETTER.get(low, low)
        if ch.isupper():
            lat = lat[:1].upper() + lat[1:]
        lat += ''.join(ACC[m] for m in marks if m in ACC)   # keep accent; breathing/subscript dropped
        out.append(lat)
    roman = ''.join(out)
    if units and units[0][0].lower() in VOWELS and rough_breathing(lemma):
        roman = 'h' + roman                          # rough-breathing 'h', from the lemma
    return unicodedata.normalize('NFC', roman)


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: build_abp_translit.py <db> [--dry-run]")
    db, dry = sys.argv[1], '--dry-run' in sys.argv
    con = sqlite3.connect(db)
    cur = con.cursor()
    rows = cur.execute("""
        SELECT s.verse_id, s.position, s.form, COALESCE(l.lemma, '')
        FROM abp_surface s
        JOIN words w        ON w.verse_id = s.verse_id AND w.position = s.position
        LEFT JOIN lexicon l ON l.strongs_g = w.strongs_base
        WHERE s.form IS NOT NULL AND s.form <> ''
    """).fetchall()
    updates = [(romanize(f, lem), vid, pos) for (vid, pos, f, lem) in rows]
    if dry:
        for (vid, pos, f, lem), (r, *_) in list(zip(rows, updates))[:40]:
            print(f"{f:<16} {lem:<12} -> {r}")
        print(f"\n[dry-run] {len(updates)} forms would be filled; nothing written.")
        return
    cur.executemany("UPDATE abp_surface SET translit=? WHERE verse_id=? AND position=?", updates)
    con.commit()
    print(f"Filled {len(updates)} romanizations into abp_surface.translit.")


if __name__ == '__main__':
    main()
