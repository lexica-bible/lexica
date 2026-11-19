# C4 row-by-row account (11/19, CC; v2 after the reviewer's ESCALATE on v1, §9.201). READ-ONLY, local copies only.
#   RUN  = the scp copy of PA's step6_audit_20261119/ (c4_phrase_built.out, c4_phrase_src.out) - outside the repo, not committed
#   WC   = STEP4-DELTA2 words_cells.tsv = the local 11/15 delta less its two Joh 19:18 @10 lines (sha printed; expect 86e44c58...dafc)
#   FEED = the frozen app-edition feed, local copy (sha printed; expect cert_manifest.json :273-276, 7bd77385...cf63)
# Every figure the record states about the 173 / 88 is printed by THIS script in the SUMMARY at the end of its output file.
# Writes the account straight to docs/handoffs/drafts/STEP6AUD_C4_account_20261119.txt and prints that file's sha256.
import ast, collections, hashlib, io, os, re, sys

REPO = r"C:\Users\JP\projects\bible-db"
RUN = r"C:\Users\JP\edition_upgrade_runs\pa\step6_audit_20261119"
WC11 = r"C:\Users\JP\edition_upgrade_runs\pa\step4_delta_20261115\delta\words_cells.tsv"
FEED = os.path.join(REPO, "abp_app_html", "abp_app_slots_italic.tsv")
OUT = os.path.join(REPO, "docs", "handoffs", "drafts", "STEP6AUD_C4_account_20261119.txt")
sys.path.insert(0, os.path.join(REPO, "scripts"))
from build_abp_surface import _norm          # the build's pronoun fold: every pronoun number -> '1473' (build_abp_surface.py :90-95)

ROW = re.compile(r"^      (\S+ \d+:\d+)\s*\| (\S+)\s*\| (.+?)\s*\| (.+?)\s*\| orphan\[([+-]\d)\]=(\S*)$")


def section(path, name):
    """The rows of one dump section (FLAGGED or NO-EVIDENCE), with their line numbers."""
    out, on = [], False
    for n, ln in enumerate(io.open(path, encoding="utf-8", newline="").read().split("\n"), 1):
        if ln.startswith("  --- "):
            on = ln.startswith("  --- " + name + " ")
            continue
        if on and ln.strip():
            m = ROW.match(ln)
            assert m, ln
            ref, host, head, gloss, d, orph = m.groups()
            out.append(dict(n=n, ref=ref, host=host, head=ast.literal_eval(head), gloss=ast.literal_eval(gloss),
                            d=int(d), orph=orph, line=ln.strip()))
    return out


raw = io.open(WC11, encoding="utf-8", newline="").read().split("\n")
keep = [ln for ln in raw if not ln.startswith("Joh\t19\t18\t10\t")]
assert len(raw) - len(keep) == 2
SHA_WC = hashlib.sha256("\n".join(keep).encode("utf-8")).hexdigest()
SHA_FEED = hashlib.sha256(open(FEED, "rb").read()).hexdigest()
cells = collections.defaultdict(dict)          # ref -> pos -> (src, built) english
for ln in keep[1:]:
    if ln:
        f = ln.split("\t")
        if f[4] == "english":
            cells["%s %s:%s" % (f[0], f[1], f[2])][int(f[3])] = (ast.literal_eval(f[5]), ast.literal_eval(f[6]))

A2B = ast.literal_eval(re.search(r"APP_TO_ABBREV = (\{.*?\n\})", io.open(os.path.join(REPO, "scripts", "audit_abp_app_vs_surface.py"),
                       encoding="utf-8").read(), re.S).group(1))
feed = collections.defaultdict(list)
for i, ln in enumerate(io.open(FEED, encoding="utf-8").read().split("\n")):
    if i and ln:
        f = ln.split("\t")
        feed["%s %s:%s" % (A2B[f[0]], f[1], f[2])].append((f[3], f[4], f[6]))

B = section(RUN + r"\c4_phrase_built.out", "FLAGGED")
S = section(RUN + r"\c4_phrase_src.out", "FLAGGED")
NEB = section(RUN + r"\c4_phrase_built.out", "NO-EVIDENCE")
cb, cs = collections.Counter(r["line"] for r in B), collections.Counter(r["line"] for r in S)
nb, ns = cb - cs, cs - cb                      # whole printed lines as multisets, as the check program did
NEW, GONE = [], []
for r in B:
    if nb[r["line"]] > 0:
        NEW.append(r); nb[r["line"]] -= 1
for r in S:
    if ns[r["line"]] > 0:
        GONE.append(r); ns[r["line"]] -= 1


def blank(v):
    return (v or "").strip() == ""


def num(sb):
    return _norm(sb.lstrip("GH").split(".")[0])


def wnorm(s):
    s = (s or "").replace("--", "\u2014").replace(" -", " \u2014")
    s = re.sub(r"[\[\]]", "", s)
    s = re.sub(r"(^|\s)\d+(?=\S)", r"\1", s)
    return " ".join(s.split())


def shift(ref, k):
    b, cv = ref.rsplit(" ", 1)
    c, v = cv.split(":")
    return "%s %s:%d" % (b, c, int(v) + k)


def rests_on(r, k):
    """k = 1: a new row (built side); k = 0: a cleared row (src side). Returns (kind, host_pos, orphan_pos, lines)."""
    vc = cells.get(r["ref"], {})
    side = "built" if k == 1 else "src"
    hosts = [p for p, v in vc.items() if v[k] == r["gloss"]]
    L = []
    if len(hosts) > 1:
        L.append("      (gloss matches %d changed cells: %s)" % (len(hosts), hosts))
    if hosts:
        hp = hosts[0]; op = hp + r["d"]
        L.append("      host    pos %-3d english %r -> %r" % (hp, vc[hp][0], vc[hp][1]))
        if op in vc:
            L.append("      orphan  pos %-3d english %r -> %r" % (op, vc[op][0], vc[op][1]))
            kind = "host+orphan"
        else:
            L.append("      orphan  pos %-3d english unchanged in the delta; blank on %s by the audit's rule 4, so blank on both" % (op, side))
            kind = "host"
        return kind, hp, op, L
    # host cell unchanged: the row can rest only on its orphan cell (blank on this side, filled on the other) whose host
    # position (orphan - d) has no english change
    cand = [p for p, v in vc.items() if blank(v[k]) and not blank(v[1 - k]) and (p - r["d"]) not in vc]
    L.append("      english cells changed in the verse: %s" % sorted(vc))
    for p in cand:
        L.append("      orphan  pos %-3d english %r -> %r  (host pos %d has no english change in the delta; its value is not in the "
                 "delta - the only english cell changed in the verse is this one)" % (p, vc[p][0], vc[p][1], p - r["d"])
                 if len(vc) == 1 else
                 "      orphan  pos %-3d english %r -> %r  (host pos %d has no english change in the delta)" % (p, vc[p][0], vc[p][1], p - r["d"]))
    if len(cand) == 1:
        return "orphan", cand[0] - r["d"], cand[0], L
    L.append("      RESTS ON NO CELL" if not cand else "      AMBIGUOUS: %d candidate orphan cells" % len(cand))
    return "none", None, None, L


def feed_slot(r):
    h, o = num(r["host"]), num(r["orph"])
    for k, tag in ((0, "same reference"), (1, "app's next verse"), (-1, "app's previous verse")):
        ref = shift(r["ref"], k)
        for s in feed.get(ref, []):
            n = [_norm(x.split(".")[0]) for x in s[1].split("-")]
            if h in n and o in n:
                g = "gloss = the flagged gloss" if wnorm(s[2]) == wnorm(r["gloss"]) else "gloss differs"
                return tag, "joined", "%s slot %s %s %r (%s; %s)" % (ref, s[0], s[1], s[2], tag, g)
    return "none", "separate", "%s: NO slot holding both %s and %s (+/- 1 verse)" % (r["ref"], h, o)


key = lambda r: (r["ref"], r["host"], r["head"])
gk = collections.Counter(key(r) for r in GONE)
nk = collections.Counter(key(r) for r in NEW)
out = ["# C4 account v2 (CC, 11/19). Inputs: STEP4-DELTA2 words_cells sha256 %s; feed sha256 %s." % (SHA_WC, SHA_FEED),
       "# built FLAGGED %d, src FLAGGED %d; newly flagged %d, newly cleared %d (whole printed lines, as the check program)." % (len(B), len(S), len(NEW), len(GONE)),
       "# Each row: the dump line (file:line); the STEP4-DELTA2 english cell(s) it rests on (src -> built); the feed slot holding both",
       "# Strong's numbers (pronoun numbers folded by build_abp_surface._norm); for a cleared row, where it sits on built.", "",
       "# NEWLY FLAGGED on built (not on src)"]
T = collections.Counter()
for r in NEW:
    kind, hp, op, L = rests_on(r, 1)
    cp = "counterpart (a cleared row: same verse / host / head)" if gk[key(r)] else "no counterpart"
    ft, fj, fl = feed_slot(r)
    out += ["c4_phrase_built.out:%d  %s" % (r["n"], r["line"])] + L + ["      %s" % cp, "      feed: " + fl]
    T[("new", kind)] += 1; T[("new", kind, cp.split(" (")[0])] += 1; T[("new feed", ft, fj)] += 1; T[("new host", r["host"])] += 1
out += ["", "# NEWLY CLEARED on built (flagged on src only)"]
for r in GONE:
    kind, hp, op, L = rests_on(r, 0)
    ft, fj, fl = feed_slot(r)
    # where the SAME slot sits on built: the host cell's built english (from the delta) looked up in built's two lists
    bg = cells.get(r["ref"], {}).get(hp, (None, None))[1] if hp is not None else None
    fl2 = [x for x in B if x["ref"] == r["ref"] and x["host"] == r["host"] and x["gloss"] == bg]
    ne = [x for x in NEB if x["ref"] == r["ref"] and x["host"] == r["host"] and x["gloss"] == bg]
    if fl2 and nk[key(r)] and any(x["head"] == r["head"] for x in fl2):
        where = "re-flagged on built, same head, new wording: " + "; ".join("built.out:%d %r" % (x["n"], x["gloss"]) for x in fl2)
    elif fl2:
        where = "flagged on built under a new head: " + "; ".join("built.out:%d %r head %r" % (x["n"], x["gloss"], x["head"]) for x in fl2)
    elif ne:
        where = "under NO-EVIDENCE on built: " + "; ".join("built.out:%d %r" % (x["n"], x["gloss"]) for x in ne)
    else:
        where = "in neither built list (built english at the host slot: %r)" % (bg,)
    out += ["c4_phrase_src.out:%d  %s" % (r["n"], r["line"])] + L + ["      on built: " + where, "      feed: " + fl]
    T[("cleared", kind)] += 1; T[("cleared feed", ft, fj)] += 1; T[("cleared on built", where.split(":")[0])] += 1
nc_new = sum(1 for r in NEW if not gk[key(r)]); nc_gone = sum(1 for r in GONE if not nk[key(r)])
out += ["", "# SUMMARY (every figure the record states, counted here)"]
for k in sorted(T, key=str):
    out.append("#   %4d  %s" % (T[k], " | ".join(k)))
out.append("#   net: new with no counterpart %d - cleared with no counterpart %d = %+d (built FLAGGED %d - src %d = %+d)"
           % (nc_new, nc_gone, nc_new - nc_gone, len(B), len(S), len(B) - len(S)))
text = "\n".join(out) + "\n"
io.open(OUT, "w", encoding="utf-8", newline="\n").write(text)
print("wrote %s (%d lines) sha256 %s" % (OUT, text.count("\n"), hashlib.sha256(text.encode("utf-8")).hexdigest()))
print("STEP4-DELTA2 words_cells %s | feed %s" % (SHA_WC, SHA_FEED))
print("\n".join(l for l in out if l.startswith("#   ")))
