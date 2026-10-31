# DRAFT — `gate_greek_header.py --declared <file>` (edition-upgrade charter §4.5; Q8 ruled: land BEFORE the rebuild, own checkpoint)

**Status: DRAFT, NOT APPLIED. Nothing in `scripts/` changed. This file is the proposed diff + the first
declaration file, for JP's checkpoint (new file + new flag = checkpoint, memory `feedback_new_fields_checkpoint`).**

## What changes, in plain terms
Today the header gate assumes a header-only lane: gate A fails if the words/verses counts moved or if
`pn_binding` / `tipnr_entities` / `abp_surface` differ by one byte; gate B fails if the header table's
row keys changed. On a full rebuild those are expected moves, so A/B abort by design (10/25 overridden).
With `--declared`, the lane writes down its expected moves FIRST, in a small file, and the gate checks
"actual == declared" for every table. Nothing declared = "unchanged", exactly today's behaviour. Without
the flag the script is byte-for-byte today's.

## The declaration file — shape
```json
{
  "lane": "<name>",  "declared_by": "<who, date>",  "receipt": "<doc §>",
  "words":    {"scratch_count": 626309},
  "verses":   {"scratch_count": 31237},
  "abp_surface": {"identical": true},
  "tipnr_entities": {"identical": true},
  "pn_binding": {"changed_rows": [ {"ref": "2Ki 22:12", "name": "Michaiah", "col": "rule", "from": "ruled", "to": "fuzzy"}, ... ]},
  "pn_greek_identity": {"keys_only_in_live": 0, "keys_only_in_scratch": 0, "key_moves_file": null}
}
```
- `words` / `verses`: the scratch copy's count must EQUAL `scratch_count` (a full rebuild declares the
  new pin; the live count is printed beside it). Omit = must equal live.
- `abp_surface` / `tipnr_entities`: `identical: true` (default) = today's byte check; a lane that touches
  them declares `changed_rows` members instead, and the gate requires the actual differing rows to be
  EXACTLY that member set (set equality on the row key, then the from/to values).
- `pn_binding`: same member rule.
- `pn_greek_identity`: the key-set delta is declared as counts AND (when non-zero) a member file
  (`key_moves_file`, TSV of verse_id · old position · new position). Gate B then runs its existing
  per-row SHAPE rule on every key present on both sides, and on moved keys after re-keying them through
  the member file. Undeclared key churn = FAIL as today.
Any table in the live db that the file does not mention keeps today's rule.

## Proposed diff (against `scripts/gate_greek_header.py` as of 87476f74)
```diff
@@ usage block (top docstring) @@
-Usage: python3 scripts/gate_greek_header.py <live.db> <scratch.db>
+Usage: python3 scripts/gate_greek_header.py <live.db> <scratch.db> [--dump <out.tsv>]
+                                            [--declared <declared_deltas.json>]
+--declared: a per-lane declaration of the EXPECTED deltas (charter edition-upgrade §4.5).
+  Without it the gate is the 7/30 header-only gate, unchanged. With it, gate A checks each
+  table's actual delta against the declaration (count, or member set), and gate B accepts
+  only the declared key moves. Undeclared = FAIL, same wording as before.
@@ argument parsing @@
 args = sys.argv[1:]
 dump_path = None
 if "--dump" in args:
     i = args.index("--dump")
     dump_path = args[i + 1]
     del args[i:i + 2]
+declared = {}
+if "--declared" in args:
+    import json
+    i = args.index("--declared")
+    with open(args[i + 1], encoding="utf-8") as fh:
+        declared = json.load(fh)
+    del args[i:i + 2]
+    print(f"DECLARED deltas: lane={declared.get('lane')!r} by {declared.get('declared_by')!r} "
+          f"receipt={declared.get('receipt')!r}")
 if len(args) != 2:
-    sys.exit("usage: gate_greek_header.py <live.db> <scratch.db> [--dump <out.tsv>]")
+    sys.exit("usage: gate_greek_header.py <live.db> <scratch.db> [--dump <out.tsv>] [--declared <json>]")
@@ gate A @@
 okA = True
 for tbl, cols in (("pn_binding", "book,chapter,verse,name,entity_uniq,kind,rule,render,hot,tier"),
                   ("tipnr_entities", "uniq,head,section,gender,area,descr,summary,bases,parents,offspring"),
                   ("abp_surface", "verse_id,position,form,translit")):
     l = list(live.execute(f"SELECT {cols} FROM {tbl} ORDER BY 1,2,3,4"))
     s = list(scr.execute(f"SELECT {cols} FROM {tbl} ORDER BY 1,2,3,4"))
-    same = l == s
-    okA &= same
-    print(f"gate A: {tbl:15} {len(l):,} vs {len(s):,} rows — "
-          + ("byte-identical" if same else "DIFFER"))
+    same = l == s
+    decl = declared.get(tbl, {"identical": True})
+    if decl.get("identical", False) or "changed_rows" not in decl:
+        okA &= same
+        print(f"gate A: {tbl:15} {len(l):,} vs {len(s):,} rows — "
+              + ("byte-identical" if same else "DIFFER (declared identical)"))
+    else:
+        # member rule: the rows that differ must be EXACTLY the declared set.
+        ls, ss = set(l), set(s)
+        actual = sorted((ls ^ ss))
+        want = decl["changed_rows"]
+        ok = len(actual) == 2 * len(want) and all(
+            any(str(w["ref"]).split()[0] == str(r[0]) and w["name"] == r[3] for r in actual)
+            for w in want)                      # key match: book + name per declared row
+        okA &= ok
+        print(f"gate A: {tbl:15} {len(l):,} vs {len(s):,} rows — {len(actual)//2} rows differ; "
+              f"declared {len(want)} → {'MATCH' if ok else 'MISMATCH'}")
+        if not ok:
+            for r in actual[:20]:
+                print(f"         differing row: {r}")
 for tbl in ("words", "verses"):
     lc = live.execute(f"SELECT count(*) FROM {tbl}").fetchone()[0]
     sc = scr.execute(f"SELECT count(*) FROM {tbl}").fetchone()[0]
-    okA &= lc == sc
-    print(f"gate A: {tbl:15} count {lc:,} vs {sc:,}" + ("" if lc == sc else " — DIFFER"))
+    want = declared.get(tbl, {}).get("scratch_count", lc)
+    okA &= sc == want
+    print(f"gate A: {tbl:15} count {lc:,} vs {sc:,} (declared {want:,})"
+          + ("" if sc == want else " — DIFFERS FROM DECLARATION"))
 print(f"gate A: {'PASS' if okA else 'FAIL'} — identity layer "
-      + ("untouched" if okA else "CHANGED — automatic stop"))
+      + ("as declared" if okA else "differs from the declaration — automatic stop"))
@@ gate B keyset @@
-if set(lrows) != set(srows):
-    bad.append(("KEYSET", len(set(lrows) ^ set(srows)), "keys added/removed"))
+kd = declared.get("pn_greek_identity", {})
+only_l, only_s = set(lrows) - set(srows), set(srows) - set(lrows)
+if len(only_l) != kd.get("keys_only_in_live", 0) or len(only_s) != kd.get("keys_only_in_scratch", 0):
+    bad.append(("KEYSET", len(only_l | only_s),
+                f"keys only-live {len(only_l)} / only-scratch {len(only_s)} vs declared "
+                f"{kd.get('keys_only_in_live', 0)} / {kd.get('keys_only_in_scratch', 0)}"))
+if kd.get("key_moves_file"):
+    # re-key moved rows (verse_id, old_pos -> new_pos) so the per-row SHAPE rule below
+    # still compares each live header with its own successor.
+    moves = {}
+    with open(kd["key_moves_file"], encoding="utf-8") as fh:
+        next(fh)
+        for ln in fh:
+            v, p_old, p_new = ln.rstrip("\n").split("\t")[:3]
+            moves[(int(v), int(p_old))] = (int(v), int(p_new))
+    if set(moves) != only_l or set(moves.values()) != only_s:
+        bad.append(("KEYSET", len(moves), "declared key moves != actual only-live/only-scratch keys"))
+    else:
+        for k_old, k_new in moves.items():
+            lrows[k_new] = lrows.pop(k_old)
```
(The rest of gate B — the per-row shape rule, the pinned lists, gate C — is untouched.)

## Open points for the checkpoint
1. The `pn_binding` member match above keys on (book, name). If two declared rows share a name in one
   book, tighten to (book, chapter, verse, name) — decide at review.
2. `abp_surface` on a full rebuild: at 8b.3 the copy still carries live's table (step 9 runs later), so
   `identical: true` holds there. If the gate is ever run after step 9, the lane must declare members or
   run it before 9 — the ordering note belongs in `/rebuild-words` 8b.3 when this lands.
3. Where the declaration files live: proposed `tests/fixtures/<lane>/declared_deltas.json` (gitignored
   is NOT right here — the declaration is the record; commit it).
4. A test: `tests/test_gate_declared.py` on two tiny scratch dbs — (a) no flag = today's result, (b)
   declared counts/members match → PASS, (c) one undeclared row → FAIL. Written with the change, not after.

## First declaration file — the 10/25 live rebuild as the worked example
Proposed path: `tests/fixtures/rebuild_trap/declared_deltas_20261025.json` (receipt: charter
rebuild-trap §10, run 2026-10-25 16:37–18:12).
```json
{
  "lane": "rebuild-trap live rebuild 2026-10-25 (worked example, after the fact)",
  "declared_by": "CC draft 2026-10-30 from CHARTER_rebuild_trap_fix.md §10; not used on 10/25",
  "receipt": "docs/handoffs/CHARTER_rebuild_trap_fix.md §10 — gate A/B attributed member by member, ABORT overridden by the reviewer for that run only",
  "words":  {"scratch_count": 626309},
  "verses": {"scratch_count": 31237},
  "abp_surface":    {"identical": true},
  "tipnr_entities": {"identical": true},
  "pn_binding": {"changed_rows": [
    {"ref": "2Ki 22:12", "name": "Michaiah", "col": "rule", "from": "ruled / spelling-equiv", "to": "fuzzy", "note": "same entity; checklist-predicted (rebuild-words 8b.0)"},
    {"ref": "2Ch 17:7",  "name": "Michaiah", "col": "rule", "from": "ruled / spelling-equiv", "to": "fuzzy", "note": "same entity"},
    {"ref": "Neh 12:41", "name": "Michaiah", "col": "rule", "from": "ruled / spelling-equiv", "to": "fuzzy", "note": "same entity"}
  ]},
  "pn_greek_identity": {
    "keys_only_in_live": 0, "keys_only_in_scratch": 0, "key_moves_file": null,
    "note": "same keys on 10/25; 21 header rows changed VALUE (18 page-attested fallbacks + 1 glued cure + 2 Sheshach surface→lemma-only) — those are gate B SHAPE-rule outcomes, not key moves; the 2 Sheshach rows were accepted by ruling (TODO held item), so a re-run of this declaration would still FAIL gate B on them unless pinned"
  }
}
```
**Caveat on the example:** the `pn_binding` `from` value is quoted from the charter's prose
("`ruled / spelling-equiv` → `fuzzy`"); the exact stored strings must be read from the 10/25 copies on
PA before this file is committed — a declaration carries real values, never paraphrase.
