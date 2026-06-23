#!/usr/bin/env python3
"""Build the BSB word-level tables (bsb_words + bsb_strongs) from the Berean
Bible project's Strong's-tagged translation tables.

Source: https://bereanbible.com/bsb_tables.tsv  (public domain, CC0)

One row per ORIGINAL-language word; the BSB English sits in its own column with a
separate English reading-order ("BSB Sort"). We collapse each verse's rows, in
BSB Sort order, into English word tokens carrying that row's Strong's number
(Str Heb -> H####, Str Grk -> G####; Hebrew AND Aramaic use H-numbers).

Mirrors kjv_words / kjv_strongs so views_bsb can serve BSB exactly like views_kjv:
    bsb_words(word_id, book_id, chapter, verse_num, verse_pos, word, italic, punc,
              form, form_translit)
    bsb_strongs(id, word_id, strongs_id)        strongs_id fully H/G prefixed

`form` = the original-language word AS PRINTED (the inflected Hebrew/Greek surface
form, e.g. בְּרֵאשִׁ֖ית / αὐτῷ) and `form_translit` its transliteration — both straight
from the Berean tables ("WLC / Nestle Base TR RP WH NE NA SBL" + "Translit" columns).
They feed the word-detail side card's big headword (the word as it appears in the
verse); the chip top line + interlinear stay the dictionary lemma.

The token text reproduces the BSB reading text (verified against bsb.txt: all
31,102 verses rebuild, 0 content differences). Non-text source markers are
dropped: '-' (untranslated), 'vvv' (folded into a neighbour), spaced '. . .'
(elision; a tight '...' is real and kept), HTML (footnote/paragraph tags). BSB
[added]/{idiom} words are kept and flagged italic=1 (translator-supplied, like
KJV italics).

Safe to re-run: it DROPs and rebuilds ONLY bsb_words + bsb_strongs. It never
touches words/verses/kjv_* or any other table.

Usage:
    python3 scripts/load_bsb_words.py bible.db --dry-run [path/to/bsb_tables.tsv]
        Build tokens in memory, compare to the live bsb_verses text, write NOTHING.
    python3 scripts/load_bsb_words.py bible.db [path/to/bsb_tables.tsv]
        Build + write the two tables (runs the same check at the end).
If the TSV path is omitted it is downloaded from bereanbible.com.
"""
import csv
import io
import re
import sqlite3
import sys
import urllib.request

from load_bsb import _BOOK_ID, _NAME_TO_ABBR      # reuse the same book maps

TSV_URL = "https://bereanbible.com/bsb_tables.tsv"
csv.field_size_limit(10_000_000)

# ── source-marker cleaning (proven against bsb.txt) ──────────────────────────
REFTEXT = re.compile(r"<span class=\|reftext\|>.*?</span>", re.S)   # footnote ref + its number
TAG = re.compile(r"<[^>]+>")


def _html(s):
    return TAG.sub("", REFTEXT.sub("", s))


def _markers(w):
    w = re.sub(r"\.(?:\s+\.)+", " ", w)                 # spaced ". . ." (keep tight "...")
    w = w.replace("vvv", " ")                           # untranslated marker
    w = " ".join(t for t in w.split() if t != "-")      # standalone dash
    return re.sub(r"\s+", " ", w).strip()


def _punc(s):
    s = _html(s)
    return s.replace("[’’]", "").replace("[‘‘]", "").replace("[", "").replace("]", "")


def _word(cell):
    w = _html(cell)
    added = ("[" in w) or ("{" in w)                    # BSB supplied-word marker
    w = w.replace("[", "").replace("]", "").replace("{", "").replace("}", "")
    return _markers(w), added


def parse_vid(vid):
    """'Genesis 1:1' / '1 Samuel 2:3' -> (book_id, chapter, verse) or None."""
    name, _, cv = vid.strip().rpartition(" ")
    if ":" not in cv:
        return None
    abbr = _NAME_TO_ABBR.get(name.lower())
    if not abbr:
        return None
    try:
        chap, vs = cv.split(":", 1)
        return _BOOK_ID[abbr], int(chap), int(vs)
    except (ValueError, KeyError):
        return None


def tokenize(rows, ix):
    """All source rows of one verse -> English tokens in reading order:
    [{word, italic, punc, strongs}]. ix maps a stripped column name -> position."""
    rows = sorted(rows, key=lambda r: int(r[ix["BSB Sort"]] or 0))
    toks, pre = [], ""
    # The original word AS PRINTED + its transliteration (added later for the side-card
    # headword). .get so an older/odd header without them just leaves the fields blank.
    fi = ix.get("WLC / Nestle Base TR RP WH NE NA SBL")
    ti = ix.get("Translit")
    for r in rows:
        word, added = _word(r[ix["BSB version"]].strip())
        beg = _punc(r[ix["begQ"]]).strip()
        trail = _punc(r[ix["pnc"]]) + _punc(r[ix["endQ"]]) + _punc(r[ix["End text"]])
        strh, strg = r[ix["Str Heb"]].strip(), r[ix["Str Grk"]].strip()
        sid = ("H" + strh) if strh else (("G" + strg) if strg else None)
        form = r[fi].strip() if (fi is not None and fi < len(r)) else ""
        ftr  = r[ti].strip() if (ti is not None and ti < len(r)) else ""
        # marker/empty OR punctuation-only residue (e.g. "(") -> float onto neighbours
        if not word or not any(c.isalnum() for c in word):
            pre += beg + word
            if toks:
                toks[-1]["punc"] += trail
            else:
                pre += trail
            continue
        toks.append({"word": pre + beg + word, "italic": added, "punc": trail,
                     "strongs": sid, "form": form, "form_translit": ftr})
        pre = ""
    return toks


def read_verses(src):
    """Yield (verse_id, [rows]) in file order, grouping by carried-forward VerseId.
    Stashes the column index on read_verses.ix for the caller."""
    if src:
        f = open(src, encoding="utf-8")
    else:
        print(f"Downloading {TSV_URL} ...")
        f = io.StringIO(urllib.request.urlopen(TSV_URL).read().decode("utf-8"))
    with f:
        r = csv.reader(f, delimiter="\t")
        header = next(r)
        ix = {h.strip(): i for i, h in enumerate(header)}
        read_verses.ix = ix
        cur, rows = None, []
        for row in r:
            if len(row) < len(header):
                row += [""] * (len(header) - len(row))
            vid = row[ix["VerseId"]].strip()
            if vid and cur is not None and vid != cur:
                yield cur, rows
                rows = []
            if vid:
                cur = vid
            if cur is not None:
                rows.append(row)
        if cur is not None:
            yield cur, rows


def _norm(s):
    s = re.sub(r"\s*—\s*", "—", s)
    return re.sub(r"\s+", " ", s).strip()


def build(db_path, src, dry):
    # 1) tokenize the whole TSV
    built = []          # (book_id, chapter, verse, [tokens], verse_id)
    skipped = []
    for vid, rows in read_verses(src):
        ref = parse_vid(vid)
        if not ref:
            skipped.append(vid)
            continue
        built.append((*ref, tokenize(rows, read_verses.ix), vid))
    n_tok = sum(len(t) for *_, t, _ in built)
    print(f"verses: {len(built)}   word tokens: {n_tok}   unparsed verse ids: {len(skipped)}")
    if skipped:
        print(f"  e.g. {skipped[:8]}")

    # 2) check the tokens rebuild the live bsb_verses text (the read-only gate)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    have = {}
    try:
        for row in conn.execute("SELECT book_id, chapter, verse_num, verse_text FROM bsb_verses"):
            have[(row["book_id"], row["chapter"], row["verse_num"])] = row["verse_text"]
    except sqlite3.OperationalError:
        print("WARNING: bsb_verses not found — skipping the text-rebuild check.")
    if have:
        exact = spacing = bad = 0
        samples = []
        for bid, ch, vs, toks, vid in built:
            want = have.get((bid, ch, vs))
            if want is None:
                continue
            got = " ".join((t["word"] + t["punc"]) for t in toks)
            if _norm(got) == _norm(want):
                exact += 1
            elif _norm(got).replace(" ", "") == _norm(want).replace(" ", ""):
                spacing += 1
            else:
                bad += 1
                if len(samples) < 15:
                    samples.append((vid, want, got))
        print(f"REBUILD vs bsb_verses:  exact={exact}  spacing-only={spacing}  mismatch={bad}")
        for vid, want, got in samples:
            print(f"  {vid}\n    want: {want}\n    got : {got}")
        if bad:
            print("REFUSING to write: the rebuilt text does not match bsb_verses.")
            conn.close()
            return

    if dry:
        print("dry-run: no tables written.")
        conn.close()
        return

    # 3) write the two BSB-only tables (drop+rebuild; nothing else is touched)
    conn.executescript("""
        DROP TABLE IF EXISTS bsb_words;
        DROP TABLE IF EXISTS bsb_strongs;
        CREATE TABLE bsb_words (
            word_id   INTEGER PRIMARY KEY,
            book_id   INTEGER NOT NULL,
            chapter   INTEGER NOT NULL,
            verse_num INTEGER NOT NULL,
            verse_pos INTEGER NOT NULL,
            word      TEXT,
            italic    INTEGER DEFAULT 0,
            punc      TEXT,
            form          TEXT,
            form_translit TEXT
        );
        CREATE TABLE bsb_strongs (
            id        INTEGER PRIMARY KEY,
            word_id   INTEGER NOT NULL,
            strongs_id TEXT
        );
    """)
    wid = 0
    sid_id = 0
    for bid, ch, vs, toks, _vid in built:
        for pos, t in enumerate(toks, start=1):
            wid += 1
            conn.execute(
                "INSERT INTO bsb_words (word_id, book_id, chapter, verse_num, verse_pos, word, italic, punc, form, form_translit)"
                " VALUES (?,?,?,?,?,?,?,?,?,?)",
                (wid, bid, ch, vs, pos, t["word"], 1 if t["italic"] else 0, t["punc"],
                 t.get("form", ""), t.get("form_translit", "")),
            )
            if t["strongs"]:
                sid_id += 1
                conn.execute(
                    "INSERT INTO bsb_strongs (id, word_id, strongs_id) VALUES (?,?,?)",
                    (sid_id, wid, t["strongs"]),
                )
    conn.executescript("""
        CREATE INDEX idx_bsb_words_ref ON bsb_words (book_id, chapter, verse_num);
        CREATE INDEX idx_bsb_strongs_word ON bsb_strongs (word_id);
        -- Look up by Strong's number (word study uses BSB as a source). Mirrors the
        -- kjv_strongs.strongs_id index; without it those lookups scan the whole table.
        CREATE INDEX idx_bsb_strongs_id ON bsb_strongs (strongs_id);
    """)
    conn.commit()

    # 4) report + the same prefix invariant kjv_strongs has
    books = conn.execute("SELECT COUNT(DISTINCT book_id) FROM bsb_words").fetchone()[0]
    sw = conn.execute("SELECT COUNT(*) FROM bsb_strongs").fetchone()[0]
    bare = conn.execute("SELECT COUNT(*) FROM bsb_strongs WHERE strongs_id GLOB '[0-9]*'").fetchone()[0]
    conn.close()
    print(f"WROTE bsb_words: {wid}  bsb_strongs: {sw}  across {books} books")
    print(f"strongs_id NOT H/G-prefixed (must be 0): {bare}")


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(1)
    db_path = args[0]
    dry = "--dry-run" in args
    rest = [a for a in args[1:] if a != "--dry-run"]
    src = rest[0] if rest else None
    build(db_path, src, dry)


if __name__ == "__main__":
    main()
