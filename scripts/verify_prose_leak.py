#!/usr/bin/env python3
"""verify_prose_leak.py — READ-ONLY S9 (f) gate check.

Confirms load_abp_prose's regen changed EXACTLY the banked verses in
cert_prose_leak_diff.json — each live-BEFORE -> new-AFTER, and nothing else.

Dash-neutral: before comparing, we canonicalise the em-dash '—' to '--'. Live's
prose already went through fix_emdash at its last build (so it holds '—'), but the
fresh regen emits raw '--' because fix_emdash is a LATER tail step that has not run
on the copy yet. Without this, ~2,300 dash-only NON-changes would swamp the real
diff and hide the handful of banked verses. The banked verses carry no dashes, so
the canonicalisation cannot mask any of them.

Usage:  python3 scripts/verify_prose_leak.py            # from ~/bible-db
Exit:   0 = exactly the banked set changed, all exact; 1 = otherwise.
"""
import json, sqlite3, sys

LIVE, NEW, BANK = "bible.db", "bible.db.new", "cert_prose_leak_diff.json"


def norm(t):
    return (t or "").replace("—", "--")


def load(db):
    c = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    d = {(b, ch, v): norm(t) for b, ch, v, t in
         c.execute("SELECT book, chapter, verse, text FROM verses")}
    c.close()
    return d


def parse(ref):
    book, cv = ref.rsplit(" ", 1)
    ch, v = cv.split(":")
    return (book, int(ch), int(v))


live, new = load(LIVE), load(NEW)
bank = json.load(open(BANK, encoding="utf-8"))
bankmap = {parse(e["ref"]): e for e in bank}

changed = {k for k in live if live.get(k) != new.get(k)}
print(f"banked verses: {len(bank)}   verses changed by regen (dash-neutral): {len(changed)}")

ok = True
extra = changed - set(bankmap)
missing = set(bankmap) - changed
if extra:
    ok = False
    print(f"\n!! {len(extra)} UNEXPECTED changed verse(s):")
    for k in sorted(extra)[:20]:
        print(f"   {k}: {live.get(k)!r}\n      -> {new.get(k)!r}")
if missing:
    ok = False
    print(f"\n!! {len(missing)} banked verse(s) did NOT change: {sorted(missing)}")
for k, e in sorted(bankmap.items()):
    nt, lt = new.get(k), live.get(k)
    if nt != norm(e["after"]) or lt != norm(e["before"]):
        ok = False
        print(f"\n!! {e['ref']} MISMATCH")
        if lt != norm(e["before"]):
            print(f"   live!=before\n     live {lt!r}\n     bank {e['before']!r}")
        if nt != norm(e["after"]):
            print(f"   new !=after\n     new  {nt!r}\n     bank {e['after']!r}")

print("\n" + (f"PASS — regen changed exactly the {len(bank)} banked verses, all exact."
              if ok else "FAIL — see !! lines above."))
sys.exit(0 if ok else 1)
