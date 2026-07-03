#!/usr/bin/env python3
"""
dump_lexica_packet.py — READ-ONLY. Print the audit-packet material for a set of built lexica_def
entries: senses (glance headlines), LXX-provenance senses, gloss notes (the freight flags),
coverage_audit (uncited collocations/renderings, thin/circular senses), fork, and the citation-gate
result. Feeds the hand-written rollout audit packet. Touches nothing (mode=ro).

  workon bible-env
  python scripts/dump_lexica_packet.py                 # the Batch One 26
  python scripts/dump_lexica_packet.py G3056 G5207      # specific words
"""
import json, os, sqlite3, sys

BATCH1 = ["G5207","G2036","G4160","G3004","G1093","G935","G2250","G1096","G1325","G3624",
          "G2992","G5495","G1492","G444","G435","G3962","G2064","G4172","G2980","G2983",
          "G191","G3056","G4198","G4383","G3686","G1135"]


def main():
    args = [a.upper() for a in sys.argv[1:]]
    targets = args or BATCH1
    db = os.path.expanduser("~/bible-db/bible.db")
    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    for sid in targets:
        r = conn.execute("SELECT def_json FROM lexica_def WHERE strongs=?", (sid,)).fetchone()
        if not r:
            print(f"\n### {sid} — NOT BUILT\n")
            continue
        e = json.loads(r["def_json"])
        a = e.get("audit") or {}
        print(f"\n### {sid}  {e.get('lemma','')} ({e.get('translit','')})")
        if e.get("pinned_core"):
            print(f"  PINNED CORE: {e['pinned_core']}")
        prov = e.get("sense_prov") or []
        for i, h in enumerate(e.get("sense_headlines", []), 1):
            lxx = " [LXX]" if (i - 1 < len(prov) and prov[i - 1].get("lxx")) else ""
            print(f"  {i}. {h}{lxx}")
        if e.get("range"):
            print(f"  RANGE: {e['range']}")
        if e.get("gloss_notes"):
            print(f"  GLOSS NOTES (freight flags):\n     {e['gloss_notes']}")
        cov = e.get("coverage_audit") or {}
        cu = [c for c in cov.get("collocations", []) if not c.get("cited")]
        ru = [x for x in cov.get("renderings", []) if not x.get("cited") and x.get("count", 0) >= 10]
        thin = cov.get("thin_senses", [])
        if cu:
            print("  UNCITED COLLOCATIONS: " + ", ".join(f"{c['translit']}({c['verses']}v)" for c in cu))
        if ru:
            print("  UNCITED RENDERINGS: " + ", ".join(f"'{x['gloss']}'({x['count']})" for x in ru))
        if thin:
            print("  THIN/CIRCULAR SENSES: " + ", ".join(
                f"#{t['sense']}{'(circular)' if t.get('self_only') else ''}" for t in thin))
        if e.get("fork"):
            print("  FORK: contested (register entry present)")
        gate = f"{a.get('pass','?')}/{a.get('total','?')}"
        extra = []
        if a.get("dangling"): extra.append("dangling=" + ",".join(a["dangling"]))
        if a.get("noncanon"): extra.append("noncanon=" + ",".join(a["noncanon"]))
        print(f"  GATE: {gate} pass" + (("  [" + "; ".join(extra) + "]") if extra else ""))
    conn.close()


if __name__ == "__main__":
    main()
