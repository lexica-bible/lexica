# C4 row-by-row account (11/19, CC). Read-only, local copies only:
#   RUN  = the scp copy of PA's step6_audit_20261119/ (c4_phrase_built.out, c4_phrase_src.out)
#   WC   = STEP4-DELTA2 words_cells.tsv = the local 11/15 delta less its two Joh 19:18 @10 lines (sha checked below = 86e44c58...dafc)
#   FEED = the frozen app-edition feed, local copy (sha checked below = cert_manifest.json :273-276)
# For each newly flagged row (built only) and each newly cleared row (src only): the english cells of STEP4-DELTA2 it rests on
# (the host slot's cell and / or the orphan slot's cell), and the feed slot that carries the gloss.
import ast, collections, hashlib, io, re
RUN = r"C:\Users\JP\edition_upgrade_runs\pa\step6_audit_20261119"
WC11 = r"C:\Users\JP\edition_upgrade_runs\pa\step4_delta_20261115\delta\words_cells.tsv"
FEED = r"C:\Users\JP\projects\bible-db\abp_app_html\abp_app_slots_italic.tsv"
ROW = re.compile(r"^      (\S+ \d+:\d+)\s*\| (\S+)\s*\| (.+?)\s*\| (.+?)\s*\| orphan\[([+-]\d)\]=(\S*)$")

def lines(path):
    return io.open(path, encoding="utf-8", newline="").read().split("\n")

def flagged(path):
    out, on = [], False
    for n, ln in enumerate(lines(path), 1):
        if ln.startswith("  --- FLAGGED"):
            on = True; continue
        if ln.startswith("  --- NO-EVIDENCE"):
            break
        if on and ln.strip():
            m = ROW.match(ln); assert m, ln
            ref, host, head, gloss, d, orph = m.groups()
            out.append(dict(n=n, ref=ref, host=host, head=ast.literal_eval(head), gloss=ast.literal_eval(gloss),
                            d=int(d), orph=orph, line=ln.strip()))
    return out

# STEP4-DELTA2, proved by its sha
raw = [ln for ln in io.open(WC11, encoding="utf-8", newline="").read().split("\n")]
keep = [ln for ln in raw if not ln.startswith("Joh\t19\t18\t10\t")]
assert len(raw) - len(keep) == 2
body = "\n".join(keep).encode("utf-8")
print("STEP4-DELTA2 words_cells sha256:", hashlib.sha256(body).hexdigest(), "(expect 86e44c58...dafc)")
cells = collections.defaultdict(dict)
for ln in keep[1:]:
    if not ln:
        continue
    f = ln.split("\t")
    if f[4] == "english":
        cells["%s %s:%s" % (f[0], f[1], f[2])][int(f[3])] = (ast.literal_eval(f[5]), ast.literal_eval(f[6]))
print("feed sha256:", hashlib.sha256(open(FEED, "rb").read()).hexdigest(), "(expect 7bd77385...cf63)")

B = flagged(RUN + r"\c4_phrase_built.out"); S = flagged(RUN + r"\c4_phrase_src.out")
cb = collections.Counter(r["line"] for r in B); cs = collections.Counter(r["line"] for r in S)
nb, ns = cb - cs, cs - cb
NEW, GONE = [], []
for r in B:
    if nb[r["line"]] > 0:
        NEW.append(r); nb[r["line"]] -= 1
for r in S:
    if ns[r["line"]] > 0:
        GONE.append(r); ns[r["line"]] -= 1
print("built FLAGGED %d, src FLAGGED %d; newly flagged %d, newly cleared %d" % (len(B), len(S), len(NEW), len(GONE)))

def blank(v):
    return (v or "").strip() == ""

def rests_on(r, side):
    """side 'b' = built (new rows): host cell's built value == gloss; side 'a' = src (cleared rows): host's src value == gloss."""
    vc = cells.get(r["ref"], {})
    k = 1 if side == "b" else 0
    hosts = [p for p, v in vc.items() if v[k] == r["gloss"]]
    used = []
    if len(hosts) > 1:
        # keep the host whose orphan neighbour fits (blank on this side) if that singles one out
        fit = [p for p in hosts if (p + r["d"]) not in vc or blank(vc[p + r["d"]][k])]
        hosts = fit if len(fit) == 1 else hosts
    for p in hosts[:1]:
        used.append(("host", p, vc[p]))
        if (p + r["d"]) in vc:
            used.append(("orphan", p + r["d"], vc[p + r["d"]]))
    if not hosts:
        # host cell unchanged: the row can only rest on its orphan cell changing (blank on this side, filled on the other)
        orf = [p for p, v in vc.items() if blank(v[k]) and not blank(v[1 - k])]
        for p in orf:
            used.append(("orphan*", p, vc[p]))   # * = the host cell is unchanged in the delta; the row rests on this cell only
    return hosts, used

A2B = ast.literal_eval(re.search(r"APP_TO_ABBREV = (\{.*?\n\})",
      io.open(r"C:\Users\JP\projects\bible-db\scripts\audit_abp_app_vs_surface.py", encoding="utf-8").read(), re.S).group(1))
feed = collections.defaultdict(list)
for i, ln in enumerate(io.open(FEED, encoding="utf-8").read().split("\n")):
    if i and ln:
        f = ln.split("\t"); feed["%s %s:%s" % (A2B[f[0]], f[1], f[2])].append((f[3], f[4], f[6]))
OFFSET = {"Psa 24:4": "Psa 24:5", "Psa 78:38": "Psa 78:39", "Psa 118:18": "Psa 118:19"}

def nums(sg):
    return [x.split(".")[0] for x in sg.split("-")]

def feed_slot(r):
    ref = OFFSET.get(r["ref"], r["ref"])
    h, o = r["host"].lstrip("GH").split(".")[0], r["orph"].lstrip("GH").split(".")[0]
    h = {"846": "1473"}.get(h, h)          # the build renumbers the app's 1473 for 3rd-person forms (Mar 9:18)
    for s in feed.get(ref, []):
        n = nums(s[1])
        if h in n and o in n:
            return "%s slot %s %s %r" % (ref, s[0], s[1], s[2])
    return "%s: NO slot holding both %s and %s" % (ref, h, o)

def report(rows, side, title, fname):
    out = ["# %s — %d rows; each: the dump line (file:line), then the STEP4-DELTA2 english cell(s) it rests on (src -> built)," % (title, len(rows)),
           "#   then the app-edition feed slot that holds both numbers. orphan* = the host cell is unchanged in the delta; the row rests on the orphan cell only."]
    none = []
    for r in rows:
        hosts, used = rests_on(r, side)
        out.append("%s:%d  %s" % (fname, r["n"], r["line"]))
        if not used:
            none.append(r); out.append("      RESTS ON NO CELL")
        for kind, p, (a, b) in used:
            out.append("      %-7s pos %-3d english %r -> %r" % (kind, p, a, b))
        if len(hosts) > 1:
            out.append("      (gloss matches %d positions: %s)" % (len(hosts), hosts))
        out.append("      feed: " + feed_slot(r))
    return out, none

o1, n1 = report(NEW, "b", "NEWLY FLAGGED on built (not on src)", "c4_phrase_built.out")
o2, n2 = report(GONE, "a", "NEWLY CLEARED on built (flagged on src only)", "c4_phrase_src.out")
io.open(r"C:\Users\JP\AppData\Local\Temp\claude\375bfdbef9aafd6e\2c800d5c-aa55-4d34-b144-23d87cfc5ca6\scratchpad\s6\c4rows.txt",
        "w", encoding="utf-8", newline="\n").write("\n".join(o1 + [""] + o2) + "\n")
print("new rows resting on no cell:", [r["line"] for r in n1])
print("cleared rows resting on no cell:", [r["line"] for r in n2])
amb = sum(1 for l in o1 + o2 if "gloss matches" in l); print("rows whose gloss matched more than one changed cell:", amb)
nof = sum(1 for l in o1 + o2 if "NO slot holding" in l); print("rows with no feed slot holding both numbers:", nof)
q = sum(1 for l in o1 + o2 if "orphan*" in l); print("rows resting only on an orphan cell (host unchanged):", q)
