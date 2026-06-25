#!/usr/bin/env python3
"""Structural / function-word entries for the word card — a NEW entry type, beside the
verse-grounded Lexica dictionary.

A few words don't carry their meaning internally; they're grammatical machinery whose
value is set by what flanks them. Verse-grounding MISLOCATES them — it reads the meaning
off the surrounding words and reports it as a sense of the target. The copula εἰμί is the
first case: it links a subject to a predicate and asserts only that link — identity, class,
quality, and representation are all set by the PREDICATE, never by the verb. So instead of a
sense list, the card states the verb's FUNCTION, flags that it's underspecified, and shows
the construction TYPES it appears in (patterns, not senses).

CLOSED CLASS, hand-authored, served directly — no model, no PA data build. Same spirit as
the _LSJ_OVERRIDES register: edit here, ship on a normal code deploy. Provenance tag =
GRAMMAR, kept distinct from LEXICA/LSJ/MM because "this is the copula's grammatical
function" is a different KIND of claim than "this sense is attested in usage".

INHERITANCE: the explanation is written ONCE, on the lemma (G1510). ABP tags every
conjugated form with a dotted number (G1510.2.3 = present indicative 3rd sg, "is"); all
~7,800 of them resolve to this one entry and display their own PARSE — never a generated
entry of their own. The ABP dot on εἰμί is pure morphology (first slot = tense/mood, second
= person+number), verified against abp_texts; see memory project_dotted_strongs_lemma.
"""
import copy

# --- εἰμί dotted-number -> parse: the verified decode (all 25 codes seen in abp_texts) -------
# First slot = tense/mood; second slot (finite indicatives only) = person + number.
_MOOD = {
    "1": "present infinitive", "2": "present", "3": "present subjunctive",
    "4": "present optative", "5": "present imperative", "6": "present participle",
    "7": "imperfect", "8": "future", "9": "future infinitive", "10": "future participle",
}
_PERSON = {"1": "1st sg", "2": "2nd sg", "3": "3rd sg", "4": "1st pl", "5": "2nd pl", "6": "3rd pl"}
_FINITE = ("2", "7", "8")  # the moods ABP gives a person slot

# Plain English for the finite indicative forms, by (mood, person).
_FINITE_GLOSS = {
    ("2", "1"): "I am", ("2", "2"): "you are", ("2", "3"): "is",
    ("2", "4"): "we are", ("2", "5"): "you are", ("2", "6"): "are",
    ("7", "1"): "I was", ("7", "2"): "you were", ("7", "3"): "was",
    ("7", "4"): "we were", ("7", "5"): "you were", ("7", "6"): "were",
    ("8", "1"): "I will be", ("8", "2"): "you will be", ("8", "3"): "will be",
    ("8", "4"): "we will be", ("8", "5"): "you will be", ("8", "6"): "will be",
}
# Plain English for the non-finite / non-indicative moods (no person slot).
_MOOD_GLOSS = {
    "1": "to be", "3": "(that it) be", "4": "might be", "5": "be!",
    "6": "being", "9": "to be (about to be)", "10": "that which will be",
}


def eimi_form(strongs):
    """Decode a dotted εἰμί number ('G1510.2.3') into {parse, gloss}, or None for the bare
    lemma / an unrecognized code."""
    slots = strongs.replace("G", "").split(".")[1:]   # drop the '1510'
    if not slots:
        return None
    mood = slots[0]
    label = _MOOD.get(mood)
    if not label:
        return None
    person = slots[1] if len(slots) > 1 else None
    if mood in _FINITE and person in _PERSON:
        return {"parse": f"{label}, {_PERSON[person]}", "gloss": _FINITE_GLOSS.get((mood, person), "")}
    return {"parse": label, "gloss": _MOOD_GLOSS.get(mood, "")}


# --- The hand-authored structural entries (keyed by BASE number) -----------------------------
_STRUCTURAL = {
    "G1510": {
        "kind": "structural",
        "strongs": "G1510",
        "lemma": "εἰμί",
        "forms": "eimi",          # which form-decoder its dotted numbers use
        "function": "εἰμί is the copula — the linking verb. In this use it joins a subject to a "
                    "predicate (“A is B”) and asserts only the connection; what the connection "
                    "MEANS is supplied by the predicate, not by the verb.",
        "scope": "This card covers the linking use. εἰμί also has an absolute use, where the verb "
                 "itself is the predicate and asserts existence or presence — “I am the one being” "
                 "(Exodus 3:14), “in the beginning was the word” (John 1:1). There the meaning "
                 "is IN the verb; that is a distinct use, not the linking one described here.",
        "scope_contested": "John 8:58 (“before Abraham existed, I am”) is the disputed case — "
                           "whether that “I am” is the absolute self-naming that echoes Exodus "
                           "3:14 and Isaiah 43:10, or a thinner statement of existence, is itself "
                           "contested. Flagged here, not settled.",
        "underspecified": "In the linking use the verb does not say what KIND of connection — the "
                          "predicate sets it. The one grammatical tell is the article on the "
                          "predicate: with it the predicate tends to identify (“you are THE Christ”), "
                          "without it to classify or describe (“I am A Pharisee”, “God is love”) — "
                          "and even that only narrows it; the complement’s meaning settles the rest. "
                          "Any reading that leans on “is” itself to force a relation — strict "
                          "identity, say — is loading the copula with more than it carries.",
        "relation_lead": "There is really one construction — subject + “is” + predicate. The "
                         "article on the predicate makes the only grammatical cut: with it → "
                         "identity or representation; without it → class or quality. Which one "
                         "inside each pair is set by the complement’s meaning, not the verb.",
        "relations": [
            {"type": "Identity",
             "note": "predicate takes the article; subject and predicate are the same",
             "ref": "Matthew 16:16", "text": "you are the Christ"},
            {"type": "Representation",
             "note": "predicate takes the article; it stands for the subject",
             "ref": "Matthew 13:38", "text": "the field is the world"},
            {"type": "Class",
             "note": "no article; the subject is one of a category",
             "ref": "Acts 23:6", "text": "I am a Pharisee"},
            {"type": "Quality",
             "note": "no article; it describes the subject’s nature",
             "ref": "1 John 4:8", "text": "God is love"},
        ],
        "relation_tail": "Inside each pair the shape is identical — the article does not separate "
                         "identity from representation, or class from quality; only the "
                         "complement’s meaning does. The verb settles none of it.",
        "crossref": {
            "ref": "Matthew 26:26",
            "note": "At “this is my body” (Matthew 26:26; Luke 22:19) the same copula is read "
                    "as both identity and representation — and it is doubly open there, since "
                    "“this” (the demonstrative) is underspecified too. The verb settles neither.",
        },
        "provenance": "GRAMMAR",
    },
    # PREPOSITION (proof of the case-row card — one card per lemma, case-relations as internal rows;
    # "cut by form" survives as the card's structure, the routing stays one card). diá takes gen +
    # acc with distinct relations. No dot inheritance (prepositions are bare-tagged); no form stamp.
    "G1223": {
        "kind": "structural",
        "strongs": "G1223",
        "lemma": "διά",
        "function": "διά is a preposition — it marks how its object relates to the rest of the "
                    "clause. Which relation it marks is fixed by the CASE of that object — "
                    "ordinarily visible in the form of what follows.",
        "relation_label": "The object’s case makes the cut",
        "relation_lead": "Same word, two relations — set by the case of what follows, not by διά:",
        "relations": [
            {"case": "gen", "type": "+ genitive",
             "note": "through; by means of — the channel or intermediary something passes through "
                     "(not the ultimate doer — that is ὑπό+gen)",
             "ref": "Matthew 1:22", "text": "spoken by the Lord through the prophet"},
            {"case": "acc", "type": "+ accusative",
             "note": "because of; for the sake of — the reason or cause",
             "ref": "Mark 2:27", "text": "the Sabbath on account of man exists"},
        ],
        "straddle": "Frozen into a fixed phrase, or fused onto a verb as a διά- compound, διά stops "
                    "marking a live relation — that use belongs to the word’s plain meaning, not here.",
        "provenance": "GRAMMAR",
    },

    # ---- MULTI-CASE prepositions: case-rows (the form-cut), one card per lemma ----
    "G2596": {
        "kind": "structural", "strongs": "G2596", "lemma": "κατά",
        "function": "κατά is a preposition — which relation it marks is fixed by the CASE of its "
                    "object, ordinarily visible in the form of what follows.",
        "relation_label": "The object’s case makes the cut",
        "relation_lead": "Same word, two relations — set by the case of what follows, not by κατά:",
        "relations": [
            {"case": "gen", "type": "+ genitive",
             "note": "against — hostile opposition (also, spatially, ‘down from’)",
             "ref": "Matthew 12:30", "text": "the one not being with me is against me"},
            {"case": "acc", "type": "+ accusative", "note": "according to; along; throughout",
             "ref": "1 Corinthians 15:3", "text": "Christ died … according to the scriptures"},
        ],
        "straddle": "Fused into a compound verb (a κατα- verb), κατά stops marking a live relation — "
                    "that use is the word’s plain meaning, not here.",
        "provenance": "GRAMMAR",
    },
    "G3326": {
        "kind": "structural", "strongs": "G3326", "lemma": "μετά",
        "function": "μετά is a preposition — which relation it marks is fixed by the CASE of its "
                    "object, ordinarily visible in the form of what follows.",
        "relation_label": "The object’s case makes the cut",
        "relation_lead": "Same word, two relations — set by the case of what follows, not by μετά:",
        "relations": [
            {"case": "gen", "type": "+ genitive", "note": "with — accompaniment, in company with",
             "ref": "Matthew 1:23", "text": "God with us"},
            {"case": "acc", "type": "+ accusative", "note": "after — later in time or order",
             "ref": "Matthew 17:1", "text": "after six days"},
        ],
        "straddle": "Fused into a compound verb (a μετα- verb, often ‘change’), μετά stops marking a "
                    "live relation — that use is the word’s plain meaning, not here.",
        "provenance": "GRAMMAR",
    },
    "G4012": {
        "kind": "structural", "strongs": "G4012", "lemma": "περί",
        "function": "περί is a preposition — which relation it marks is fixed by the CASE of its "
                    "object, ordinarily visible in the form of what follows.",
        "relation_label": "The object’s case makes the cut",
        "relation_lead": "Same word, two relations — set by the case of what follows, not by περί:",
        "relations": [
            {"case": "gen", "type": "+ genitive", "note": "concerning; about — the topic in view",
             "ref": "John 1:22", "text": "what say you concerning yourself?"},
            {"case": "acc", "type": "+ accusative", "note": "around — encircling a place or person",
             "ref": "Mark 3:34", "text": "the ones sitting around him"},
        ],
        "straddle": "Fused into a compound verb (a περι- verb, often ‘around’), περί stops marking a "
                    "live relation — that use is the word’s plain meaning, not here.",
        "provenance": "GRAMMAR",
    },
    "G5228": {
        "kind": "structural", "strongs": "G5228", "lemma": "ὑπέρ",
        "function": "ὑπέρ is a preposition — which relation it marks is fixed by the CASE of its "
                    "object, ordinarily visible in the form of what follows.",
        "relation_label": "The object’s case makes the cut",
        "relation_lead": "Same word, two relations — set by the case of what follows, not by ὑπέρ:",
        "relations": [
            {"case": "gen", "type": "+ genitive", "note": "for; on behalf of — to someone’s benefit",
             "ref": "Romans 5:8", "text": "Christ died for us"},
            {"case": "acc", "type": "+ accusative", "note": "above; beyond — surpassing",
             "ref": "Philippians 2:9", "text": "the name above every name"},
        ],
        "straddle": "Fused into a compound verb (a ὑπερ- verb, ‘over/excess’), ὑπέρ stops marking a "
                    "live relation — that use is the word’s plain meaning, not here.",
        "provenance": "GRAMMAR",
    },
    "G5259": {
        "kind": "structural", "strongs": "G5259", "lemma": "ὑπό",
        "function": "ὑπό is a preposition — which relation it marks is fixed by the CASE of its "
                    "object, ordinarily visible in the form of what follows.",
        "relation_label": "The object’s case makes the cut",
        "relation_lead": "Same word, two relations — set by the case of what follows, not by ὑπό:",
        "relations": [
            {"case": "gen", "type": "+ genitive",
             "note": "by — the doer/agent (the ultimate cause, esp. of a passive verb)",
             "ref": "Matthew 4:1", "text": "to be tested by the devil"},
            {"case": "acc", "type": "+ accusative", "note": "under — place or subjection",
             "ref": "Matthew 8:8", "text": "you should enter under my roof"},
        ],
        "straddle": "Fused into a compound verb (a ὑπο- verb, ‘under’), ὑπό stops marking a live "
                    "relation — that use is the word’s plain meaning, not here.",
        "provenance": "GRAMMAR",
    },
    "G1909": {
        "kind": "structural", "strongs": "G1909", "lemma": "ἐπί",
        "function": "ἐπί is a preposition — which relation it marks is fixed by the CASE of its "
                    "object (it takes all three), ordinarily visible in the form of what follows.",
        "relation_label": "The object’s case makes the cut",
        "relation_lead": "Same word, three relations — set by the case of what follows, not by ἐπί:",
        "relations": [
            {"case": "gen", "type": "+ genitive", "note": "on, upon (at rest); in the time of",
             "ref": "Matthew 6:10", "text": "as in heaven also upon the earth"},
            {"case": "dat", "type": "+ dative", "note": "on, at; on the basis of (ground, occasion)",
             "ref": "Matthew 4:4", "text": "not by bread alone shall a man live"},
            {"case": "acc", "type": "+ accusative", "note": "onto, over, against (motion, extent)",
             "ref": "Matthew 5:15", "text": "put it … upon the lamp-stand"},
        ],
        "straddle": "Fused into a compound verb (an ἐπι- verb), ἐπί stops marking a live relation — "
                    "that use is the word’s plain meaning, not here.",
        "provenance": "GRAMMAR",
    },
    "G3844": {
        "kind": "structural", "strongs": "G3844", "lemma": "παρά",
        "function": "παρά is a preposition — which relation it marks is fixed by the CASE of its "
                    "object (it takes all three), ordinarily visible in the form of what follows.",
        "relation_label": "The object’s case makes the cut",
        "relation_lead": "Same word, three relations — set by the case of what follows, not by παρά:",
        "relations": [
            {"case": "gen", "type": "+ genitive", "note": "from — a person as the source",
             "ref": "John 16:27", "text": "I have come forth from God"},
            {"case": "dat", "type": "+ dative", "note": "with, beside — in someone’s presence",
             "ref": "John 17:5", "text": "the glory which I had … with you"},
            {"case": "acc", "type": "+ accusative", "note": "alongside; contrary to; than (comparison)",
             "ref": "Matthew 13:1", "text": "he sat down by the sea"},
        ],
        "straddle": "Fused into a compound verb (a παρα- verb), παρά stops marking a live relation — "
                    "that use is the word’s plain meaning, not here.",
        "provenance": "GRAMMAR",
    },

    # ---- SINGLE-CASE prepositions: one case, so no form-cut — one card, range filled by context ----
    "G1722": {
        "kind": "structural", "strongs": "G1722", "lemma": "ἐν",
        "function": "ἐν is a preposition (with the dative). It sets its object as the surrounding "
                    "setting; which shade — place, sphere, time, or means — is filled by context, "
                    "since ἐν works with a single case.",
        "relation_label": "What it marks (one case — context, not case, fills the range)",
        "relations": [
            {"type": "in; among; by; at",
             "note": "location, sphere, time, or instrument — context picks which",
             "ref": "John 1:1", "text": "in the beginning"},
        ],
        "straddle": "Frozen in a fixed phrase (ἐν Χριστῷ, ‘in Christ’) or fused into an ἐν- compound, "
                    "ἐν stops marking a live relation — that use is the word’s plain meaning, not here.",
        "provenance": "GRAMMAR",
    },
    "G1519": {
        "kind": "structural", "strongs": "G1519", "lemma": "εἰς",
        "function": "εἰς is a preposition (with the accusative). It marks the goal or direction "
                    "its object stands as; the shade — into, to, for, against — is filled by context.",
        "relation_label": "What it marks (one case — context fills the range)",
        "relations": [
            {"type": "into; to; for", "note": "goal, direction, or purpose",
             "ref": "Matthew 2:1", "text": "magi from the east came unto Jerusalem"},
        ],
        "straddle": "Fused into an εἰς- compound verb, εἰς stops marking a live relation — that use "
                    "is the word’s plain meaning, not here.",
        "provenance": "GRAMMAR",
    },
    "G1537": {
        "kind": "structural", "strongs": "G1537", "lemma": "ἐκ",
        "function": "ἐκ is a preposition (with the genitive). It marks its object as the source or "
                    "origin something comes out of; the shade is filled by context.",
        "relation_label": "What it marks (one case — context fills the range)",
        "relations": [
            {"type": "out of; from", "note": "source, origin, or cause",
             "ref": "John 1:13", "text": "from God were born"},
        ],
        "straddle": "Fused into an ἐκ-/ἐξ- compound verb, ἐκ stops marking a live relation — that "
                    "use is the word’s plain meaning, not here.",
        "provenance": "GRAMMAR",
    },
    "G575": {
        "kind": "structural", "strongs": "G575", "lemma": "ἀπό",
        "function": "ἀπό is a preposition (with the genitive). It marks separation or departure "
                    "from its object; the shade is filled by context.",
        "relation_label": "What it marks (one case — context fills the range)",
        "relations": [
            {"type": "from; away from", "note": "separation, distance, or source",
             "ref": "Matthew 1:21", "text": "he shall deliver his people from their sins"},
        ],
        "straddle": "Fused into an ἀπο- compound verb, ἀπό stops marking a live relation — that use "
                    "is the word’s plain meaning, not here.",
        "provenance": "GRAMMAR",
    },
    "G4253": {
        "kind": "structural", "strongs": "G4253", "lemma": "πρό",
        "function": "πρό is a preposition (with the genitive). It marks its object as what comes "
                    "before — in time, place, or rank; the shade is filled by context.",
        "relation_label": "What it marks (one case — context fills the range)",
        "relations": [
            {"type": "before", "note": "earlier in time, in front in place, or ahead in rank",
             "ref": "John 17:5", "text": "before the world being in existence"},
        ],
        "straddle": "Fused into a προ- compound verb, πρό stops marking a live relation — that use "
                    "is the word’s plain meaning, not here.",
        "provenance": "GRAMMAR",
    },
    "G4862": {
        "kind": "structural", "strongs": "G4862", "lemma": "σύν",
        "function": "σύν is a preposition (with the dative). It marks association — its object "
                    "together with the subject; the shade is filled by context.",
        "relation_label": "What it marks (one case — context fills the range)",
        "relations": [
            {"type": "with; together with", "note": "association, accompaniment",
             "ref": "Philippians 1:23", "text": "to be with Christ"},
        ],
        "straddle": "Fused into a συν- compound verb, σύν stops marking a live relation — that use "
                    "is the word’s plain meaning, not here.",
        "provenance": "GRAMMAR",
    },
    # ἀντί is a CONTESTED-FORK preposition (like a loaded content word): at Mat 20:28 "a ransom
    # ἀντὶ many", substitution ("instead of") vs representation ("on behalf of") is live theological
    # ground. The lex-talionis exemplar below is the clean substitution case — KEEP it; any future
    # 2nd exemplar / highlight that reaches Mat 20:28 must SURFACE that fork, never quietly resolve it.
    "G473": {
        "kind": "structural", "strongs": "G473", "lemma": "ἀντί",
        "function": "ἀντί is a preposition (with the genitive). It marks exchange or substitution — "
                    "one thing in the place of another; the shade is filled by context.",
        "relation_label": "What it marks (one case — context fills the range)",
        "relations": [
            {"type": "instead of; in place of; for", "note": "exchange, substitution, equivalence",
             "ref": "Matthew 5:38", "text": "an eye for an eye"},
        ],
        "straddle": "Fused into an ἀντι- compound (often ‘against/opposite’), ἀντί stops marking a "
                    "live relation — that use is the word’s plain meaning, not here.",
        "provenance": "GRAMMAR",
    },
    "G303": {
        "kind": "structural", "strongs": "G303", "lemma": "ἀνά",
        "function": "ἀνά is a rare preposition (with the accusative). On its own it marks "
                    "distribution — ‘so much each’. (Its common phrase ἀνὰ μέσον ‘in the midst of’ "
                    "is a fixed expression ABP tags as its own number, G303.1 — a frozen idiom, the "
                    "word’s plain meaning, not this relation.)",
        "relation_label": "What it marks (one case — context fills the range)",
        "relations": [
            {"type": "each (distributive)", "note": "so much apiece",
             "ref": "Matthew 20:9", "text": "they received each a denarius"},
        ],
        "straddle": "In ἀνὰ μέσον (‘in the midst’) and ἀνα- compound verbs, ἀνά stops marking this "
                    "distributive relation — that use is the word’s plain meaning, not here.",
        "provenance": "GRAMMAR",
    },
    "G4314": {
        "kind": "structural", "strongs": "G4314", "lemma": "πρός",
        "function": "πρός is a preposition (in the NT, with the accusative). It marks direction "
                    "toward, or relationship with, its object; the shade is filled by context. "
                    "(Rare +dative ‘at/near’ and +genitive uses to confirm at build time.)",
        "relation_label": "What it marks (one case — context fills the range)",
        "relations": [
            {"type": "to; toward; with", "note": "motion toward, or relationship/address",
             "ref": "John 1:1", "text": "the word was with God"},
        ],
        "straddle": "Fused into a προς- compound verb, πρός stops marking a live relation — that use "
                    "is the word’s plain meaning, not here.",
        "provenance": "GRAMMAR",
    },
}

_FORM_DECODERS = {"eimi": eimi_form}


# --- Dotted IDIOMS: the CONTENT side of a structural word's straddle --------------------------
# ABP gives a frozen phrase its OWN dotted number parked on a preposition's base — ἀνὰ μέσον is
# G303.1 (336×), the set phrase "in the midst of, between", parked on the preposition ἀνά (G303).
# That phrase is NOT ἀνά's grammatical card; it's a fixed expression with a plain meaning. So it
# routes to a one-line CONTENT note (kind "idiom"), never the structural relation card: click the
# phrase and you get what it MEANS, not the distributive use of the bare preposition.
# CLOSED SET — verified 2026-06-25 across the whole ABP corpus: ἀνὰ μέσον is the ONLY genuine
# frozen idiom of a structural word. Every OTHER dotted child of a structural number is a different
# word ABP parked at "nearest Strong's + dot" (G303.2 "stairs", G235.1 "barter", G3588.2 "oboli",
# …); those are NOT declared here and fall through to their own existing word entry. Keyed by the
# FULL dotted number, G-prefixed.
_IDIOMS = {
    "G303.1": {
        "phrase": "ἀνὰ μέσον",
        "note": "A fixed phrase meaning “in the midst of, between.” ἀνά here is frozen into a set "
                "expression — its plain meaning, not the distributive use of the bare preposition.",
    },
}


def structural_entry(strongs):
    """Return the ready-to-serve card for a normalized Strong's number, or None to fall through to
    the normal word entry. THREE exits through one gate:
      • a declared dotted IDIOM (ἀνὰ μέσον, G303.1) -> a one-line CONTENT note (kind "idiom");
      • the bare structural lemma (G1510, G303, …) OR a decodable FORM-child of it (eimi's dotted
        conjugates G1510.2.3 -> a parse stamp) -> the structural card;
      • any OTHER dotted child (a different word ABP parked at "nearest Strong's + dot", e.g.
        G303.2 "stairs") -> None, so it lands on its OWN content entry instead of borrowing this
        word's structural card. This gate keeps every future batch card seam-free: a parked number
        can never inherit the card just because its base became structural.
    """
    # 1) Declared idiom — the content side of a straddle. Checked FIRST so the phrase never inherits
    #    its base preposition's grammatical card.
    idiom = _IDIOMS.get(strongs)
    if idiom:
        return dict(idiom, kind="idiom", strongs=strongs)

    base = strongs.split(".")[0]
    spec = _STRUCTURAL.get(base)
    if not spec:
        return None

    # 2) A dotted child of a structural word earns the structural card ONLY if it decodes to a real
    #    grammatical FORM (eimi's conjugations). Otherwise it is a different parked word, not this
    #    lemma — fall through (None) to its own entry (abp_ext / dotted_lexicon).
    if "." in strongs:
        decoder = _FORM_DECODERS.get(spec.get("forms"))
        form = decoder(strongs) if decoder else None
        if not form:
            return None
        entry = copy.deepcopy(spec)
        entry["form"] = form
        entry.pop("forms", None)
        return entry

    # 3) The bare structural lemma.
    entry = copy.deepcopy(spec)
    entry.pop("forms", None)       # internal routing field, not for the browser
    return entry
