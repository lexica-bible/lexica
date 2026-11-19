# STEP6AUD tests: the block AS WRITTEN with only the constants the made-up test data cannot share swapped (diff printed).
# argv: 1 block.sh  2 out path  3 a test home (for the shas)  then KEY=VALUE overrides (optional)
import hashlib, subprocess, sys
from pathlib import Path

blk, outp, H = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
over = dict(a.split("=", 1) for a in sys.argv[4:])


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


R = H / "edition_upgrade_runs"
ref = subprocess.check_output(["git", "-C", str(H / "bible-db"), "log", "-1", "--format=%h"], text=True).strip()
cdl = (H / "edition_a_count_differs.log").read_text(encoding="utf-8")
import re
m = re.search(r"COUNT-DIFFERS verses: ([\d,]+)  \(OT ([\d,]+) · NT ([\d,]+)\)", cdl)
swap = {
    "REF": ref,
    "XEL": sha(R / "step5_eligible_20261101.tsv"),
    "XWC": sha(R / "step4_delta2_20261116/delta/words_cells.tsv"),
    "XPRO": sha(R / "step5_prose_20261101.tsv"),
    "XBH": sha(H / "bible-db/bh_scrape.db"),
    "XCDM_N": str(sum(1 for _ in open(H / "count_differs_members.tsv", encoding="utf-8"))),
    "XCHK": sha(R / "step6aud_check_20261119.py"),
    "XA1": "0",
    "XT2": "100.00%",
    "XCD": m.group(1).replace(",", ""), "XCDOT": m.group(2).replace(",", ""), "XCDNT": m.group(3).replace(",", ""),
    "XSELF": '"V2 MEMBER DIFF: FAIL - word-order 0 - content-other 1 - dup-gloss 0 - Joh 14:26 clean - new on non-eligible 0 | '
             'to ruling: gone 607 - new on eligible 0 - changed ops 0 - unchanged 0"',
}
swap.update(over)
lines = blk.read_text(encoding="utf-8").split("\n")
done = set()
for i, ln in enumerate(lines):
    head = ln.split("#", 1)[0] if not ln.startswith("XSELF=") else ln
    for k, v in swap.items():
        # a constant line: KEY=... (also 'XCD=...; XCDOT=...' and 'XACT=...; XPIN=...' share a line)
        for part in [p.strip() for p in head.split(";")]:
            if part.startswith(k + "="):
                old = part if k != "XSELF" else part.split("   #", 1)[0]
                lines[i] = lines[i].replace(old, "%s=%s" % (k, v), 1)
                done.add(k)
miss = set(swap) - done
if miss:
    sys.exit("not swapped: %s" % sorted(miss))
outp.write_text("\n".join(lines), encoding="utf-8", newline="\n")
print(subprocess.run(["diff", str(blk), str(outp)], capture_output=True, text=True).stdout)
