# TEST STAND-IN for scripts/cert_invariants.py and scripts/health_check.py (tests only; the made-up files do not carry the
# tables the real two read). It prints what the real script prints, line for line in the parts block P7 reads
# (cert_invariants.py :268-286; health_check.py :298-305, :154-158), in the mode named by <its folder>/<kind>.mode.
# usage: copied as cert.py and health.py (the file name says which); <name>.py <db> [flags]
import os
import sys

kind = os.path.basename(__file__)[:-3]
here = os.path.dirname(os.path.abspath(__file__))


def mode():
    p = os.path.join(here, kind + ".mode")
    return open(p).read().strip() if os.path.exists(p) else "ok"


m = mode()
if kind == "cert":
    if m == "pyc":   # a cache folder appears in the checkout during the run (the block must say CHECK)
        os.makedirs(os.path.join(os.path.expanduser("~"), "bible-db", "scripts", "__pycache__"), exist_ok=True)
    names = ["1 row pins", "2 split flip", "3 em-dash", "4 corrections", "5 feed manifest", "6 backup freshness", "7 person/place binding"]
    red = {"fail4": "4 corrections", "fail6": "6 backup freshness"}.get(m)
    print("== cert_invariants on %s (read-only) ==" % sys.argv[1])
    for n in names:
        if n == red:
            print("  [FAIL] %s" % n)
            print("         - planted failure")
        else:
            print("  [OK  ] %s" % n)
        if n == "4 corrections":
            print("           . spent by lane-3: %d (declared 1)" % (2 if m == "spent2" else 1))
    cp = os.path.join(here, "cert.count")
    k = int(open(cp).read()) + 1 if os.path.exists(cp) else 1
    open(cp, "w").write(str(k))
    if m == "locked1" and k == 1:
        print("sqlite3.OperationalError: database is locked")
        sys.exit(1)
    failed = 1 if red else 0
    print("\n%s (%d/7 green)" % ("CERTIFIED STATE HOLDS" if not failed else "%d CHECK(S) FAILED" % failed, 7 - failed))
    sys.exit(1 if failed else 0)

cp = os.path.join(here, "health.count")
k = int(open(cp).read()) + 1 if os.path.exists(cp) else 1
open(cp, "w").write(str(k))
flags = [a for a in sys.argv[2:]]
locked = m == "locked" or (m == "locked1" and k == 1)
lines = ["=== bible.db health check: %s ===" % sys.argv[1], "", "  (flags: %s)" % " ".join(flags)]
if locked:
    lines.append("  [ERR ] bare (unprefixed) strongs_base  [INVARIANT]: -   (database is locked)")
else:
    lines.append("  [OK  ] bare (unprefixed) strongs_base  [INVARIANT]: 0")
short = 3873 if m == "floor" else 0
lines.append("  [%s] abp_surface rows BELOW floor 395014  [fill or a backfill missing?]: %d   (shortfall vs floor; 3873 = the 10/25 fill is missing "
             "(restore_surface_fill.py); other = backfill_abp_surface.py + backfill_pn_surface.py + build_abp_translit.py)"
             % ("WARN" if short else "OK  ", short))
if m == "warn":
    lines.append("  [WARN] exact-duplicate word rows: 2")
warns = (1 if short else 0) + (1 if m == "warn" else 0)
lines += ["", "  %d warning(s), %d error(s)." % (warns, 1 if locked else 0)]
print("\n" + "\n".join(lines) + "\n")
