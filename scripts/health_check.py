#!/usr/bin/env python3
"""
health_check.py — READ-ONLY data-quality scan for bible.db.

Runs a battery of sanity checks over words / lexicon / bdb / metaV and prints a
report. Never writes. Run it anytime, especially after a words rebuild or import.
Each check is OK (0 / informational) or WARN (non-zero where zero is expected).

Usage:
  python3 scripts/health_check.py bible.db
  python3 scripts/health_check.py bible.db --email                 # mail the report
  python3 scripts/health_check.py bible.db --email --only-warn     # mail only if not clean
  python3 scripts/health_check.py bible.db --email --email-to=you@example.com

The email path is for a nightly PythonAnywhere scheduled task. SMTP creds + the
recipient (OWNER_EMAIL) come from a repo-root .env (a cron run has no WSGI env), or
pass --email-to=. See mailer.py.
"""
import os
import sqlite3
import sys

DB = next((a for a in sys.argv[1:] if not a.startswith("--")), "bible.db")
EMAIL = "--email" in sys.argv
ONLY_WARN = "--only-warn" in sys.argv
EMAIL_TO = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--email-to=")), None)
conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row

results = []


def check(label, sql, args=(), expect_zero=True, note=""):
    try:
        n = conn.execute(sql, args).fetchone()[0]
    except Exception as e:
        results.append(("ERR ", label, "-", str(e)[:60]))
        return
    status = "OK  " if (n == 0 or not expect_zero) else "WARN"
    results.append((status, label, n, note))


# ── words integrity ──────────────────────────────────────────────────────────
check("bare (unprefixed) strongs_base  [INVARIANT]",
      "SELECT count(*) FROM words WHERE strongs_base GLOB '[0-9]*'")

check("exact-duplicate word rows",
      """SELECT COALESCE(sum(c-1),0) FROM (
           SELECT count(*) c FROM words GROUP BY verse_id, position,
             COALESCE(strongs_base,''), COALESCE(english,''),
             COALESCE(greek_pos,-1), COALESCE(bracket_id,-1) HAVING c>1)""")

check("same (verse,position) with DIFFERENT data  [misalignment]",
      """SELECT count(*) FROM (
           SELECT verse_id, position FROM words
           GROUP BY verse_id, position
           HAVING count(DISTINCT COALESCE(strongs_base,'')||'|'||COALESCE(english,'')) > 1)""")

check("fragmented (non-contiguous) brackets",
      """SELECT count(*) FROM (
           SELECT verse_id,bracket_id FROM words WHERE bracket_id IS NOT NULL
           GROUP BY verse_id,bracket_id
           HAVING (max(position)-min(position)+1)!=count(*))""")

check("bracketed words missing greek_pos (+gloss)",
      """SELECT count(*) FROM words WHERE bracket_id IS NOT NULL
         AND greek_pos IS NULL AND english IS NOT NULL AND english!=''""")

check("non-bracket words carrying greek_pos  [cosmetic]",
      """SELECT count(*) FROM words WHERE bracket_id IS NULL
         AND greek_pos IS NOT NULL AND english IS NOT NULL AND english!=''""",
      expect_zero=False, note="harmless; prose ignores greek_pos for these")

check("PN placeholder ('*') missing is_pn flag",
      "SELECT count(*) FROM words WHERE strongs_base='*' AND COALESCE(is_pn,0)=0")

check("english with leftover bracket chars [ or ]",
      "SELECT count(*) FROM words WHERE english LIKE '%[%' OR english LIKE '%]%'")

check("english starting with a stray digit  [parse leak]",
      # Rev 13:18 is exempt: ABP renders the number of the beast (666) as the Greek
      # numeral split into the words "600", "60", "6" — legit content, not a parse leak.
      """SELECT count(*) FROM words WHERE english GLOB '[0-9]*'
           AND verse_id NOT IN (
             SELECT id FROM verses WHERE book='Rev' AND chapter=13 AND verse=18)""")

# ── strongs range / lexicon coverage ─────────────────────────────────────────
# NOTE: proper nouns excluded — TIPNR assigns valid EXTENDED numbers (G9xxx/H9xxx)
# to names not in classic Strong's. Only non-PN out-of-range numbers are bad.
check("G-number out of range (>5624), non-PN  [bad Greek strongs]",
      """SELECT count(*) FROM words WHERE strongs_base LIKE 'G%'
         AND CAST(substr(strongs_base,2) AS INT) > 5624
         AND COALESCE(is_pn,0)=0 AND COALESCE(strongs,'')!='*'""")

check("H-number out of range (>8674), non-PN  [bad Hebrew strongs]",
      """SELECT count(*) FROM words WHERE strongs_base LIKE 'H%'
         AND CAST(substr(strongs_base,2) AS INT) > 8674
         AND COALESCE(is_pn,0)=0 AND COALESCE(strongs,'')!='*'""")

check("proper-noun EXTENDED strongs (TIPNR G9xxx/H9xxx)  [expected]",
      """SELECT count(*) FROM words
         WHERE (COALESCE(is_pn,0)=1 OR strongs='*')
         AND ((strongs_base LIKE 'G%' AND CAST(substr(strongs_base,2) AS INT) > 5624)
           OR (strongs_base LIKE 'H%' AND CAST(substr(strongs_base,2) AS INT) > 8674))""",
      expect_zero=False, note="legit STEPBible extended numbers for names")

check("distinct G-bases with NO lexicon gloss",
      """SELECT count(*) FROM (SELECT DISTINCT strongs_base FROM words
           WHERE strongs_base LIKE 'G%')
         WHERE substr(strongs_base,2) NOT IN (SELECT strongs FROM lexicon)""",
      expect_zero=False, note="some legit: LXX-only / dotted-variant bases")

check("distinct H-bases with NO bdb entry",
      """SELECT count(*) FROM (SELECT DISTINCT strongs_base FROM words
           WHERE strongs_base LIKE 'H%')
         WHERE strongs_base NOT IN (SELECT strongs_id FROM bdb)""",
      expect_zero=False)

# ── verses ───────────────────────────────────────────────────────────────────
check("verses with zero words  [parse failure]",
      """SELECT count(*) FROM verses v
         WHERE NOT EXISTS (SELECT 1 FROM words w WHERE w.verse_id=v.id)""",
      expect_zero=False)

# ── print report ─────────────────────────────────────────────────────────────
report_lines = [f"=== bible.db health check: {DB} ===", ""]
for status, label, count, note in results:
    line = f"  [{status}] {label}: {count}"
    if note:
        line += f"   ({note})"
    report_lines.append(line)
warns = sum(1 for s, *_ in results if s == "WARN")
errs = sum(1 for s, *_ in results if s == "ERR ")
report_lines += ["", f"  {warns} warning(s), {errs} error(s)."]
report_text = "\n".join(report_lines)
print("\n" + report_text + "\n")

# ── person/place overlap (metaV) — informational ─────────────────────────────
print("=== person/place name overlap (metaV) ===")
try:
    both = conn.execute(
        """SELECT DISTINCT p.name FROM metav_people p
           JOIN metav_places pl ON pl.name = p.name COLLATE NOCASE
           ORDER BY p.name"""
    ).fetchall()
    print(f"  names that are BOTH a person and a place: {len(both)}")
    if both:
        print("  sample:", ", ".join(r[0] for r in both[:25]))
    # of those overlaps, how many can be disambiguated by the place's strongs_g
    placed = conn.execute(
        """SELECT count(DISTINCT p.name) FROM metav_people p
           JOIN metav_places pl ON pl.name = p.name COLLATE NOCASE
           WHERE pl.strongs_g IS NOT NULL AND pl.strongs_g != ''"""
    ).fetchone()[0]
    print(f"  ...of which the PLACE carries a strongs_g (disambiguable): {placed}")
except Exception as e:
    print("  (metaV overlap query failed:", str(e)[:80], ")")
conn.close()

# ── optional email (for a nightly PythonAnywhere scheduled task) ──────────────
if EMAIL:
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if root not in sys.path:
        sys.path.insert(0, root)
    try:
        from dotenv import load_dotenv
        load_dotenv(os.path.join(root, ".env"))   # a cron run has no WSGI env
    except Exception:
        pass
    from mailer import send_email, mail_configured
    to = EMAIL_TO or os.environ.get("OWNER_EMAIL") or os.environ.get("ESV_OWNER_EMAIL")
    if not to:
        print("  [email] no recipient — pass --email-to=you@example.com or set OWNER_EMAIL")
    elif ONLY_WARN and warns == 0 and errs == 0:
        print("  [email] all clear — not sending (--only-warn)")
    elif not mail_configured():
        print("  [email] SMTP not configured (set SMTP_* in .env / WSGI) — not sending")
    else:
        status = "all clear" if (warns == 0 and errs == 0) else f"{warns} warning(s), {errs} error(s)"
        sent = send_email(to, f"Lexica health check — {status}", report_text)
        print(f"  [email] {'sent to ' + to if sent else 'send FAILED (see log)'}")
