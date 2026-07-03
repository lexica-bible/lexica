#!/usr/bin/env python3
"""contested_register.py — THE CONTESTED-WORD FAIRNESS GATE register (the ONE copy).

The hand-authored fork register: a word in here is, by MEMBERSHIP ALONE, read more than one
way, and its Lexica entry carries the fork block (core + the live readings, each named with
its tradition). No model, no detector. Extracted from scripts/build_lexica_def.py 2026-07-01
so the build, the serving route (views_lexica.py — the serve-time fork backstop + the G5485
alias), and the trial/agreement rigs all read ONE copy — the stale duplicate in
trial_lexica_def.py is gone. Repo root (like structural.py / corpus_panel.py) so both the
app and the scripts/ tools can import it.

DATA: charis is tagged G5484 in ABP (not the textbook G5485 stub) — keyed under G5484 + alias.
"""
from collections import OrderedDict

CONTESTED = OrderedDict([
    ("G1344", {
        "lemma": "dikaioō", "gloss": "justify",
        # contest_verses (piece B, self_only check): the disputed locus the fork's readings fight
        # over. dikaioō's contest is chapter-granular — the register names "James 2", so a
        # faith-works sense that never reaches outside that chapter (Romans 4, Gen 15:6, Habakkuk)
        # is circular in exactly the sense we mean. Chapter form "Jas 2" matches any verse in it.
        "contest_verses": ["Jas 2"],
        # Seam index (chat design): why they diverge + whether the LEAD sense flips when the two
        # priors are swapped (the "different-lead" filter — computed values from the 2026-06-25 run).
        "divergence_type": "content", "lead_flip": True,
        # FRAME-LEAK (agreement run 2026-06-25): the model's senses pre-pick a fork frame draw to
        # draw, so the neutral hand-authored core below is PINNED as the definition's lead
        # (entry.pinned_core) and the model's framed senses are demoted to attested uses beneath it.
        # The contest itself lives in the fork. Only the three frame-statable-as-definition leakers
        # carry this; sarx/ekklesia layer their freight on a plain sense and gate-ship without it.
        "pin_core": True,
        "core": "to deem, treat, or pronounce just; to set right, hold to be in the right",
        "frames": [
            ("forensic / imputed", "Reformation",
             "a legal verdict — righteous status declared, not moral change"),
            ("transformative / infused", "Catholic / Trent",
             "actually made righteous; the -oō verb as factitive (James 2)"),
            ("covenant-membership", "New Perspective",
             "declarative, but about who belongs to God's people — not imputed moral righteousness"),
        ],
        "note": "forensic and covenant-membership share the declarative mechanism; "
                "they split on content, not declare-vs-make",
        "graph_ref": "salvation_how:def_dikaioo_forensic|def_dikaioo_infused|def_dikaioo_demonstrate",
    }),
    ("G166", {
        "lemma": "aionios", "gloss": "eternal / age-long",
        "divergence_type": "loaded", "lead_flip": True,
        "pin_core": True,   # frame-leak — neutral core pinned as the lead (see G1344)
        "core": "pertaining to an age; long-lasting, ancient",
        "frames": [
            ("unending duration", "—", "everlasting, without end"),
            ("of-the-coming-age / qualitative", "inaugurated-eschatology",
             "belonging to the age to come; a quality of life, not only its length"),
        ],
        "graph_ref": None,
    }),
    ("G5484", {
        "lemma": "charis", "gloss": "favor / grace",
        "divergence_type": "loaded", "lead_flip": True,
        "aliases": ["G5485"],
        "pin_core": True,   # frame-leak — neutral core pinned as the lead (see G1344)
        "core": "favor, goodwill, gift",
        "frames": [
            ("unmerited favor by faith", "Reformed",
             "God's gracious disposition, received by faith"),
            ("infused grace", "sacramental", "a quality imparted by a rite"),
        ],
        "graph_ref": "baptism_who:def_grace_infused|obj_grace_charis",
    }),
    ("G4561", {
        "lemma": "sarx", "gloss": "flesh",
        "divergence_type": "loaded", "lead_flip": False,
        "core": "body, human being, mortal nature",
        "frames": [
            ("embodied humanity", "—", "the physical/human, morally neutral"),
            ("sin-principle", "—",
             "the disposition opposed to the Spirit; NIV 'sinful nature' — itself a contested gloss"),
        ],
        "graph_ref": None,
    }),
    ("G1577", {
        "lemma": "ekklesia", "gloss": "assembly / church",
        "divergence_type": "loaded", "lead_flip": True,
        "core": "an assembly; a convened gathering or congregation",
        "etymology_note": "ek-kaleō, 'called out' — etymologizing gloss, not a sense felt in "
                          "usage; flag, don't seat in core",
        "frames": [
            ("local congregation", "—", "a particular gathered body in a place"),
            ("universal body of believers", "invisible-church",
             "all believers across time; visible institution not implied"),
            ("institutional Church", "hierarchical / sacramental",
             "the visible, structured Church as an entity"),
        ],
        "graph_ref": None,
    }),
    ("G4151", {
        "lemma": "pneuma", "gloss": "spirit / breath / wind",
        "divergence_type": "referent", "lead_flip": False,
        # FRAME-LEAK: the model leads with "the Holy Spirit, third person of the Trinity"; pin the
        # neutral range so the divine-Spirit reading (person / mode / power) lives in the fork, not
        # the lead. Tightened to a one-line gloss (not a six-way sense list) after JP's chat check —
        # the engine's generated senses carry the detail below under "Attested uses".
        "pin_core": True,
        "core": "breath, wind, or the immaterial spirit — of a person, a spirit-being, or God",
        "frames": [
            ("divine person", "Nicene / Trinitarian",
             "the Holy Spirit as a distinct person of the Godhead — who acts, speaks, and can be "
             "grieved (Acts 13:2; Eph 4:30)"),
            ("a mode of the one God", "modalist / Oneness / Sabellian",
             "not a distinct person but God himself in his spiritual activity — fully divine, not a "
             "third alongside Father and Son"),
            ("God's active power and presence", "non-Trinitarian / Unitarian",
             "God's own outreaching breath, presence, and power at work — not a distinct person, "
             "paralleled with 'the power of the Most High' (Luke 1:35)"),
        ],
        "note": "the fork touches ONLY the divine-Spirit use; the wind, breath, life, inner-spirit, "
                "and spirit-being senses are uncontested",
        "graph_ref": None,
    }),
    ("G2316", {
        "lemma": "theos", "gloss": "God / god",
        # contest_verses (piece B, self_only check): the three disputed loci — John 1:1c (the deity
        # fork below), Exo 22:28 (the magistrates referent, flagged in core), and Psa 82 (the
        # superhuman-'gods' reading, senses 3/4). Psa 82 is CHAPTER-level: the disputed passage is
        # the whole psalm — sense 3 cites 82:8, sense 4 cites 82:1/6 — so a per-verse list would
        # miss part of it (like dikaioō's "Jas 2"). It is the FOUNDING case for the circular check:
        # sense 3 rested on Psa 82 alone until Deu 32:8 (and 1Sa 28:13) were added as INDEPENDENT
        # support from OTHER passages. Those are deliberately NOT here — corroboration from outside
        # the disputed psalm is exactly what keeps the fixed sense 3 from reading circular.
        "contest_verses": ["Joh 1:1", "Exo 22:28", "Psa 82"],
        "divergence_type": "referent", "lead_flip": False,
        # The model's Sense 1 closes by reading John 1:1c as settled identity ("the word ... identifies
        # the Logos both as with this being and as being this being"). That one sentence is pulled from
        # the raw (fix_lexica_raw.py) and the contest moves here. The fork is NARROW: it touches the
        # anarthrous predicate in John 1:1c (θεὸς ἦν ὁ λόγος) ONLY — every other use (creator, lesser/
        # fabricated gods, human magistrates) is uncontested and stays in the senses. No pin_core: once
        # the verdict sentence is cut, Sense 1 leads neutral on its own (the sarx/ekklesia pattern).
        "core": "the one sovereign creator — named, invoked, prayed to, spoken of as acting in "
                "history; in the plural or of foreign cult, lesser or fabricated 'gods'; of "
                "figures set in authority (Exo 22:28), the referent there contested",
        "frames": [
            ("shared divine nature", "Nicene / Trinitarian",
             "the anarthrous predicate ascribes God's own nature to the Word — 'what God was, the "
             "Word was also' (Harner's qualitative reading): divine in kind, a distinct person from "
             "ho theos (the Father)"),
            ("identity", "modalist / Oneness / Sabellian",
             "the Word is the one God himself — the clause read as fully convertible, no distinction "
             "of persons"),
            ("a divine being, subordinate", "Arian / non-Trinitarian",
             "'the Word was a god' — the anarthrous predicate read as indefinite: a divine being "
             "lesser than and distinct from ho theos"),
        ],
        "note": "the qualitative reading is Harner's, not Colwell's — Colwell's Rule only says a "
                "DEFINITE preverbal predicate tends to drop the article, which says nothing about "
                "whether the anarthrous theos here is definite. The apologetic Colwell-inversion "
                "('the dropped article proves the Word is God') is exactly what this fork "
                "neutralizes, so no frame rests on it. The fork touches John 1:1c only.",
        "graph_ref": None,
    }),
    ("G2962", {
        "lemma": "kyrios", "gloss": "lord / master",
        # contest_verses (piece B, self_only check): the title-transfer set the note already names —
        # a YHWH text or the "one Lord" confession applied to Jesus. A sense resting only on these
        # is circular; ordinary kyrios use reaches far past them.
        "contest_verses": ["Rom 10:13", "Heb 1:10", "Php 2:9-11", "Jud 1:4"],
        "divergence_type": "referent", "lead_flip": False,
        # Scope like pneuma: the SENSE isn't contested — "lord, master," applied both to the God of
        # Israel and to Jesus, is plainly attested and stays in the core. What's contested is the
        # IMPLICATION when a NT writer takes a text that named YHWH (or the exclusive "one Lord"
        # confession) and applies the same lemma to Jesus. The fork is bounded to that title-transfer
        # citation set ONLY; ordinary kyrios — God, Jesus, or a human master — never fires it.
        "core": "lord, master — the holder of sovereign or practical authority: the God of Israel, "
                "the Lord Jesus, or a human owner/ruler over others",
        "frames": [
            ("shared divine identity", "Nicene / Trinitarian",
             "applying a YHWH text to Jesus identifies him with the one Lord — the divine name "
             "carried across (Rom 10:13; Heb 1:10)"),
            ("delegated lordship", "non-Trinitarian / Unitarian",
             "the title is bestowed on the man Jesus by God — 'God has made him Lord' (Phil 2:9-11) "
             "— an appointed sovereignty, not the uncreated name"),
            ("the one Lord, manifested", "modalist / Oneness",
             "no distinction of persons: the one Lord named in the OT is the same Lord present in "
             "Jesus (Jude 1:4)"),
        ],
        "note": "the fork touches ONLY the title-transfer cases — where a YHWH text or the exclusive "
                "'one Lord' confession is applied to Jesus (Rom 10:13, Heb 1:10, Phil 2:9-11, "
                "Jude 1:4). It does not fire on ordinary uses of kyrios for God, for Jesus, or for a "
                "human master.",
        "graph_ref": None,
    }),
])

# membership index: every Strong's number (primary + aliases) -> its entry
CONTESTED_BY_SID = {}
for _sid, _e in CONTESTED.items():
    CONTESTED_BY_SID[_sid] = _e
    for _a in _e.get("aliases", []):
        CONTESTED_BY_SID[_a] = _e

# Plain split-lemma aliases — a Strong's number the dictionary + KJV/BSB treat as a headword
# but ABP tags ~zero occurrences under, because they live on a neighbouring number that is the
# SAME lexeme. Verified read-only vs ABP 2026-07-02 (audit_alias_gap.py review). The fold makes
# Ask-corpus retrieval / counting / highlighting key on the number ABP actually uses. These are
# NOT contested words (no fork, no register entry) — just a corpus-tagging split, so they seed the
# same serve-time map without going through CONTESTED.
#   suspect -> canonical (the number ABP tags)
SPLIT_LEMMA_ALIASES = {
    "G40":   "G39",    # hagios "holy" -> ABP tags the whole holy family (adj + saints + holies) on G39
    "G1672": "G1673",  # Hellen "a Greek" -> ABP's Greek(s) ethnonym number
    "G3398": "G3397",  # mikros "small" -> the small family (the neuter form's number)
    "G3570": "G3568",  # nyni "now" (emphatic) -> nyn G3568
    "G3063": "G3062",  # loipon "the rest/finally" -> the loipos family G3062
    "G3480": "G3478",  # Nazoraios "Nazarene" -> ABP merges person + place on G3478
    "G3479": "G3478",  # Nazarenos "Nazarene" -> same
    "G2411": "G2413",  # hieron "temple" -> ABP tags the temple noun on hieros G2413
    "G1432": "G1431",  # dorean "freely" (adv. acc.) -> the dorea "gift" number G1431
}

# Alias-pool provenance notes — where the destination number's ABP rows are NOT a pure pool of the
# aliased lexeme, so the definition engine stays honest about what it's drawing from. The alias is
# still correct (the bulk is the same word); this just flags the minority the engine should not
# silently fold into the headword sense.
SPLIT_LEMMA_ALIAS_NOTES = {
    # Keep counts SOFT in user-facing copy — a hard number goes stale silently when the pool shifts.
    "G2413": "Pool mixes the temple noun (hieron) with a handful of genuine 'sacred/consecrated' "
             "adjective (hieros) rows — the alias is right for temple, but a few rows are the true adjective.",
}

# Serve-time alias map, derived from the same "aliases" fields (never write a pair twice), plus
# the plain split-lemma pairs above.
# Charis: {"G5485": "G5484"} — ABP tags charis on G5484 (the form charin), so that's the number
# the Lexica entry was built under; KJV/BSB tag the textbook G5485. A word card asking for
# G5485 gets the G5484 row served (views_lexica.py). An alias must never name a word that has
# its own structural.py card — the serving route resolves structural FIRST to keep that safe.
LEXICA_ALIASES = {alias: sid for sid, e in CONTESTED.items() for alias in e.get("aliases", [])}
LEXICA_ALIASES.update(SPLIT_LEMMA_ALIASES)   # + the plain split-lemma pairs


def alias_note_for(requested):
    """The numbering-crosswalk descriptor for an aliased Strong's number, or None.

    `requested` is the number the reader arrived on (G-prefixed). Worded by direction:
      to_abp   — a standard number that folds onto the ABP number (asked G2411 → served G2413):
                 the card shows "· ABP: G2413".
      from_abp — the ABP/served number itself (asked G2413 directly): the card shows
                 "· standard: G2411" plus any pool caveat.
    Pure lookup over LEXICA_ALIASES + SPLIT_LEMMA_ALIAS_NOTES — the ONE place the crosswalk is
    computed, so every serving route (word card, word-study profile) words it identically.
    """
    served = LEXICA_ALIASES.get(requested, requested)
    if requested != served:
        return {"direction": "to_abp", "abp": served, "standard": [requested], "caveat": ""}
    std = sorted(k for k, v in LEXICA_ALIASES.items() if v == served)
    caveat = SPLIT_LEMMA_ALIAS_NOTES.get(served, "")
    if std or caveat:
        return {"direction": "from_abp", "abp": served, "standard": std, "caveat": caveat}
    return None
