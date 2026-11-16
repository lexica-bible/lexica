#!/usr/bin/env python3
"""lane3_spent.py — the ONE "spent by lane-3" rule (edition upgrade DESIGN §9.152-§9.153, option B).

WHY: a words correction is applied at rebuild step 7; lane-3 (step 8b.2a, the three frozen files
below) may then rewrite the same cell by a ruled edit. On any copy after 8b.2a that cell holds
neither the correction's source value nor its corrected value, so the guarded apply would
LOUD-SKIP it and the cert check would name it, forever, though nothing is wrong. Today exactly one
active row is in that state: Heb 11:24 pos 7 english (EU-Heb11:24 corrects "Pharoah's" ->
"Pharaoh's", then fixes2 splits the cell into "daughter," + "of Pharaoh's" — §9.67's order).

THE RULE — a correction row is SPENT BY LANE-3 only when ALL THREE hold, else it stays a LOUD SKIP:
  (a) a lane-3 op sits on the row's cell: same book / chapter / verse / position, exactly ONE op
      across the three files, and the row's field is one lane-3 records an OLD value for
      (english -> old_eng, greek_pos -> old_gpos, bracket_id -> old_bid; english_head has no
      recorded old value, so an english_head row can never be spent);
  (b) the row's corrected_value = that op's OLD value for the field;
  (c) the cell's slot now holds that op's NEW values — english, english_head, greek_pos,
      bracket_id, on the op's own number (strongs_base = sbase) — the same test
      fix_lane3_star_merges.py uses for "already applied".

SHA PINS: the three files are read only when each one's sha256 equals its pin below; the shas are
printed by both users. A changed or missing file turns the rule OFF (every row is judged exactly
as before this rule existed), so a changed file can never widen it silently. Re-pin only by a
ruling.

DECLARED: the rows ruled spent (§9.153: 1 today). A row the rule matches that is NOT declared is
still a LOUD SKIP in the apply and red in the cert check — a second spent row is red until ruled.

Used by scripts/apply_abp_corrections.py and scripts/cert_invariants.py (no second copy).
"""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent

# run order of rebuild step 8b.2a (lane3_rebuild_step.FILES) -> sha256 of the committed bytes
LANE3_PINS = (
    ("lane3_star_fixes.json",  "e8942de0cf5df9b998568f70ef66042b1c968564e8fb5781526887532dd98948"),
    ("lane3_star_gapfix.json", "8c8ad0afc76468eb3f32c1c3419a0ea30d10650d5c448365dcc86d746b6d36b2"),
    ("lane3_star_fixes2.json", "e6a7efc762ff5185f4cab2983dada481955f7aab92ca417d516703182c042b22"),
)

# (book, chapter, verse, position, field) -> the ruling that declared it spent
DECLARED = {
    ("Heb", 11, 24, 7, "english"): "DESIGN §9.153 (EU-Heb11:24; lane3_star_fixes2.json op pos 7)",
}

# correction field -> (the op's OLD-value key, the op's NEW-value key)
_FIELD_KEYS = {
    "english":    ("old_eng",  "new_eng"),
    "greek_pos":  ("old_gpos", "new_gpos"),
    "bracket_id": ("old_bid",  "new_bid"),
}


def _text_eq(op_value, target):
    """op value (str / int / None) vs a correction's TEXT value — the apply's cellmatch rule:
    None equals only None; anything else compares as text."""
    if op_value is None:
        return target is None
    return str(op_value) == target


class Lane3Ops:
    """The three lane-3 files, loaded only if every sha matches its pin."""

    def __init__(self, script_dir=HERE, pins=LANE3_PINS):
        self.lines = []        # what the user prints: one line per file + the rule's state
        self.ops = {}          # (book, ch, vs, pos) -> [(file, op), ...]
        self.on = True
        loaded = []
        for name, want in pins:
            path = Path(script_dir) / name
            if not path.is_file():
                self.lines.append(f"lane-3 file {name}: MISSING (pinned {want[:12]}…)")
                self.on = False
                continue
            raw = path.read_bytes()
            got = hashlib.sha256(raw).hexdigest()
            ok = got == want
            self.lines.append(f"lane-3 file {name}: sha256 {got} "
                              f"{'= pin' if ok else '!= pin ' + want}")
            if not ok:
                self.on = False
            loaded.append((name, raw))
        if not self.on:
            self.lines.append("spent-by-lane-3 rule: OFF (a lane-3 file is missing or changed — "
                              "every row is judged as before; re-pin only by a ruling)")
            return
        for name, raw in loaded:
            d = json.loads(raw.decode("utf-8"))
            d.pop("_comment", None)
            for verse, spec in d.items():
                book, rest = verse.rsplit(" ", 1)
                ch, vs = rest.split(":")
                for op in spec["ops"]:
                    key = (book, int(ch), int(vs), int(op["pos"]))
                    self.ops.setdefault(key, []).append((name, op))
        self.lines.append(f"spent-by-lane-3 rule: ON ({sum(len(v) for v in self.ops.values())} "
                          f"op cells; declared spent rows: {len(DECLARED)})")

    def match(self, conn, c):
        """-> (file, op) when correction row `c` is spent by lane-3 under (a)+(b)+(c), else None.
        `c` needs book, chapter, verse, position, field, corrected_value."""
        if not self.on or c["field"] not in _FIELD_KEYS:
            return None
        hits = self.ops.get((c["book"], int(c["chapter"]), int(c["verse"]), int(c["position"])), [])
        if len(hits) != 1:                                   # (a) exactly one op on the cell
            return None
        name, op = hits[0]
        old_key, _ = _FIELD_KEYS[c["field"]]
        if not _text_eq(op[old_key], c["corrected_value"]):  # (b) corrected = the op's old value
            return None
        rows = conn.execute(
            """SELECT w.english, w.english_head, w.strongs_base, w.greek_pos, w.bracket_id
               FROM words w JOIN verses v ON v.id = w.verse_id
               WHERE v.book=? AND v.chapter=? AND v.verse=? AND w.position=?""",
            (c["book"], c["chapter"], c["verse"], c["position"])).fetchall()
        if len(rows) != 1:
            return None
        r = rows[0]
        if not (r[2] == op["sbase"]                          # (c) the slot holds the op's NEW values
                and (r[0] or None) == op["new_eng"]
                and (r[1] or None) == (op["new_head"] or None)
                and r[3] == op["new_gpos"] and r[4] == op["new_bid"]):
            return None
        return name, op


def declared(c):
    """The ruling that declared row `c` spent, or None."""
    return DECLARED.get((c["book"], int(c["chapter"]), int(c["verse"]), int(c["position"]),
                         c["field"]))


def describe(name, op):
    """One line naming the op a spent row matched."""
    return (f"{name} op pos {op['pos']}: old english {op['old_eng']!r} -> new english "
            f"{op['new_eng']!r} / head {op['new_head']!r} / gpos {op['new_gpos']} / "
            f"bid {op['new_bid']} on {op['sbase']}")
