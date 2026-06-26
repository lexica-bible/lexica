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

    # ---- CONJUNCTIONS ----
    # TYPOLOGY card (no form selects the sense — context does, so ONE card with the senses listed
    # under one finding; the eimi pattern, NOT a card per sense). ὅτι's three jobs — content,
    # reason, quotation-frame — are ALL the same function (a subordinator introducing a clause);
    # they are not separate functions. So unlike eimi (whose existential use is a DIFFERENT
    # function the copula card scopes itself away from), ὅτι's finding covers all three, and the
    # glance pointer points INTO the typology (flagging recitative, the easy-to-miss member),
    # never OUT to something the card doesn't cover. Exemplars are verbatim ABP, verified — the
    # recitative (John 1:32) survives only because ABP is literal; the first-person “I saw” proves
    # it's a quote, not reported content.
    "G3754": {
        "kind": "structural",
        "strongs": "G3754",
        "lemma": "ὅτι",
        "function": "ὅτι is a subordinating conjunction — it introduces a clause and links it to "
                    "the word that governs it, but it does not itself fix what that clause DOES. "
                    "Whether the clause gives the content of a verb of saying or knowing (“that …”), "
                    "gives a reason (“because …”), or frames direct speech as a quotation is set by "
                    "the governing verb and the context, not by ὅτι.",
        "glance": "The one to watch is the recitative: before direct speech ὅτι is an untranslated "
                  "quotation mark that smooth English drops —",
        "relation_label": "What the ὅτι-clause does — context makes the cut, not ὅτι",
        "relation_lead": "Same word, three jobs — told apart by the governing verb and context:",
        "relations": [
            {"type": "that (content)",
             "note": "the clause is the CONTENT of a verb of knowing, saying, or perceiving",
             "ref": "John 3:2",
             "text": "we know that from God you have come as a teacher"},
            {"type": "because (reason)",
             "note": "the clause gives the GROUND or reason for what was just said",
             "ref": "1 John 2:13",
             "text": "I write to you, fathers, because you have known the one from the beginning"},
            {"type": "quotation (recitative)",
             "note": "the clause IS direct speech — ὅτι frames it like opening quote marks, left "
                     "untranslated in smooth English; the comma and the shift into first-person "
                     "speech are the tell",
             "ref": "John 1:32",
             "text": "saying that, I saw the spirit descending as a dove from out of heaven"},
        ],
        "provenance": "GRAMMAR",
    },

    # TYPOLOGY card — ὡς, four context-set relations (no form selects them). Glance points INTO
    # the list, flagging the approximation use (ὡς + a number = “about”), the one a reader who
    # knows ὡς only as “like” would miss.
    "G5613": {
        "kind": "structural",
        "strongs": "G5613",
        "lemma": "ὡς",
        "function": "ὡς is a connector whose relation is set by what flanks it — it can mark a "
                    "comparison (“as, like”), a point in time (“when, while”), an approximation "
                    "before a number (“about”), or reported content (“how, that”). The context "
                    "picks which; ὡς itself does not.",
        "glance": "The surprising one is ὡς before a number — there it means “about, "
                  "approximately,” not “like” —",
        "relation_label": "What ὡς marks — context makes the cut, not ὡς",
        "relation_lead": "Same word, four relations — set by the flanking words:",
        "relations": [
            {"type": "as; like (comparison)",
             "note": "measures one thing against another",
             "ref": "Matthew 22:39",
             "text": "you shall love your neighbor as yourself"},
            {"type": "when; while (time)",
             "note": "fixes the clause at a point in time",
             "ref": "John 19:33",
             "text": "when they saw him already having died, they did not break his legs"},
            {"type": "about (with a number)",
             "note": "rounds a figure — approximately",
             "ref": "Acts 13:18",
             "text": "about forty years time he bore with them in the wilderness"},
            {"type": "how; that (content)",
             "note": "introduces reported content, much like ὅτι",
             "ref": "Romans 1:9",
             "text": "how continually I make mention of you"},
        ],
        "provenance": "GRAMMAR",
    },

    # TYPOLOGY card — εἰ. Glance flags the oath-negative, the use a smooth translation deletes:
    # in a Hebraic oath εἰ (“if”) is a strong NO. ABP keeps it literal (“Shall they … no”), so the
    # construction survives only here — verbatim ABP, not a paraphrase.
    "G1487": {
        "kind": "structural",
        "strongs": "G1487",
        "lemma": "εἰ",
        "function": "εἰ supposes a case — ordinarily a real or granted one (“if …”). What that "
                    "supposing DOES is set by context: it can frame a plain condition, pose an "
                    "indirect question (“whether …”), or, inside a Hebraic oath, stand as a strong "
                    "negative. εἰ marks the supposition; the context settles its force.",
        "glance": "The one to watch is the oath-negative — inside an oath εἰ (“if”) is a strong "
                  "NO, not a real condition —",
        "relation_label": "What εἰ supposes — context makes the cut, not εἰ",
        "relation_lead": "Same word, three forces — set by context:",
        "relations": [
            {"type": "if (condition)",
             "note": "supposes a case as real or granted",
             "ref": "Matthew 4:3",
             "text": "If you are son of God, speak that these stones should become bread loaves"},
            {"type": "whether (indirect question)",
             "note": "supposes both sides of a question being weighed",
             "ref": "Acts 26:23",
             "text": "whether the Christ is susceptible of suffering"},
            {"type": "oath-negative (surely not)",
             "note": "in a Hebraic oath, “if” is a strong NO — ABP keeps the construction literal, "
                     "as a question answered “no”",
             "ref": "Hebrews 3:11",
             "text": "I swore by an oath in my wrath, Shall they enter into my rest, no."},
        ],
        "provenance": "GRAMMAR",
    },

    # SINGLE-USE card — ἐάν is connective-grade (one relation), but its finding is worth stating:
    # it is the subjunctive twin of εἰ. No glance split (no deep layer) — renders flat.
    "G1437": {
        "kind": "structural",
        "strongs": "G1437",
        "lemma": "ἐάν",
        "function": "ἐάν is the conditional conjunction for a supposed or potential case — “if, in "
                    "the event that; whenever.” It is the hypothetical twin of εἰ: where εἰ "
                    "supposes a case as real or granted, ἐάν supposes one that may or may not come "
                    "about, and its verb takes the “should / may” form to show it.",
        "relation_label": "What ἐάν marks (one use — the verb’s “should” form is the tell)",
        "relations": [
            {"type": "if; whenever (potential)",
             "note": "supposes a case that may or may not come about",
             "ref": "1 John 1:9",
             "text": "If we should acknowledge our sins, he is trustworthy and just"},
        ],
        "provenance": "GRAMMAR",
    },

    # ---- ἵνα: PURPOSE conjunction carrying a flagged GRAMMATICAL debate (NOT a fork) ----
    # Single-function like ἐάν above (one job — purpose), but it SPLITS glance/full because a
    # contested-grammar flag sits below the finding. The flag rides scope_contested (the generalized
    # "contested-case flag" StructuralBody splits on — eimi's John 8:58 field) + a glance pointer; it
    # is NOT a sense row and NOT a fork. The debate: whether ἵνα ever marks pure RESULT (the "ekbatic
    # ἵνα") instead of purpose — a question about the PARTICLE's grammatical range.
    #   STRUCTURAL-WORD CONTEST RULE (ἵνα = the worked example): a structural word whose GRAMMAR is
    #   settled but whose APPLICATION is doctrinally contested at specific verses does NOT get a
    #   fairness-gate fork. Those forks are for CONTENT words whose senses are contested between
    #   reading-communities (dikaioō: forensic / infused / covenant). A structural word's senses are
    #   not the contested thing — what's contested is WHICH settled sense applies in a given verse, a
    #   passage-level question, not a lexical one. So the card stays grammatically honest, and the
    #   loaded verses point OUT to an argument graph where the doctrinal contest is mapped (the lexeme
    #   is innocent; the passage is contested). This is distinct from a content fork, where the
    #   lexeme's OWN senses fork (dikaioō -> salvation_how).
    #   The hardening verses (Mark 4:12, Matt 13:13ff, John 12:40) are exactly where which-sense-
    #   applies becomes the doctrinal fight, so per the structural-exemplar rule they CANNOT be the
    #   teaching verse. The exemplar is therefore a PLAIN purpose ἵνα (Mark 3:14 — mundane, no
    #   predestination weight), verbatim ABP, tag-verified G2443, bracket-clean.
    #   DEFERRED: the hardening graph + the verse-pointer do NOT exist yet (nothing to point to), so
    #   NO fork, NO fairness-gate entry, NO pointer is wired here — just the structural card; the
    #   pointer gets added later, when the graph is built. Telic twin of ὅπως (G3704, below). No
    #   dotted children in the corpus (scanned).
    "G2443": {
        "kind": "structural",
        "strongs": "G2443",
        "lemma": "ἵνα",
        "function": "ἵνα marks purpose — it ties a clause to an action as its aim or goal "
                    "(“in order that, so that”). The ἵνα-clause says what the action is FOR; its verb "
                    "stands in the “should / may” (subjunctive) form.",
        "glance": "There is one debated grammatical point — whether ἵνα can ever mark pure result "
                  "(an outcome that follows) rather than purpose (an aim intended) —",
        "scope_contested": "Whether ἵνα ever marks pure result — an outcome that simply followed, not "
                           "an aim that was intended — is a debated point of Koine grammar. Some read "
                           "a “result (ekbatic) ἵνα” where a clause looks more like a consequence than "
                           "a goal; others hold that ἵνα always keeps its purpose force. It is a "
                           "grammatical question about the particle’s range — flagged here, not "
                           "settled, and not a doctrinal one.",
        "relation_label": "What ἵνα marks",
        "relations": [
            {"type": "purpose (aim, goal)",
             "note": "marks what an action is for — “in order that”",
             "ref": "Mark 3:14", "text": "he appointed twelve that they might be with him"},
        ],
        "provenance": "GRAMMAR",
    },

    # ---- PLAIN CONNECTIVES ----
    # One job each, force set by context — no internal typology, no glance split (flat cards).
    # “καί is καί”: the and/also/even flip is one connective, not separate senses.
    "G2532": {
        "kind": "structural", "strongs": "G2532", "lemma": "καί",
        "function": "καί is the basic connecting word — it ties together words, phrases, and "
                    "clauses. Its English flips with context (and / also / even), but that is one "
                    "connective doing one job, not a set of separate meanings.",
        "relation_label": "What it does (force set by context, not a sense cut)",
        "relations": [
            {"type": "and; also; even", "note": "joins items, adds (“also”), or heightens (“even”)",
             "ref": "John 1:1", "text": "and the word was with God"},
        ],
        "provenance": "GRAMMAR",
    },
    "G1161": {
        "kind": "structural", "strongs": "G1161", "lemma": "δέ",
        "function": "δέ is the mild connective — it carries the account forward, often with a "
                    "light turn. Context sets whether it reads as “and” (continuing) or “but” "
                    "(turning); the step it marks is gentle either way.",
        "relation_label": "What it does (force set by context)",
        "relations": [
            {"type": "and; but (mild)", "note": "continues, or lightly contrasts, what precedes",
             "ref": "Matthew 4:4", "text": "And responding he said"},
        ],
        "provenance": "GRAMMAR",
    },
    "G1063": {
        "kind": "structural", "strongs": "G1063", "lemma": "γάρ",
        "function": "γάρ looks back — it gives the ground or explanation for what was just said "
                    "(“for, because”). It never opens its clause (it sits second in the Greek), so "
                    "it always points to the statement before it.",
        "relation_label": "What it does (force set by context)",
        "relations": [
            {"type": "for (explains, grounds)", "note": "gives the reason or basis for what precedes",
             "ref": "Matthew 6:34", "text": "for tomorrow shall be anxious for the things of itself"},
        ],
        "provenance": "GRAMMAR",
    },
    "G3767": {
        "kind": "structural", "strongs": "G3767", "lemma": "οὖν",
        "function": "οὖν draws an inference — it ties what follows to what came before as its "
                    "consequence (“therefore, then”). In narrative it can simply resume the thread "
                    "(“so, then”); context sets which.",
        "relation_label": "What it does (force set by context)",
        "relations": [
            {"type": "therefore; then", "note": "draws a conclusion, or resumes the account",
             "ref": "Matthew 1:17", "text": "All then the generations from Abraham unto David"},
        ],
        "provenance": "GRAMMAR",
    },
    "G235": {
        "kind": "structural", "strongs": "G235", "lemma": "ἀλλά",
        "function": "ἀλλά is the strong adversative — it sets what follows AGAINST what precedes "
                    "(“but, rather”). Heavier than δέ: it does not merely turn the thread, it "
                    "opposes or corrects.",
        "relation_label": "What it does (force set by context)",
        "relations": [
            {"type": "but; rather", "note": "marks a strong contrast or correction",
             "ref": "Matthew 4:4", "text": "but by every word coming forth by the mouth of God"},
        ],
        "provenance": "GRAMMAR",
    },
    "G3303": {
        "kind": "structural", "strongs": "G3303", "lemma": "μέν",
        "function": "μέν sets up a balance — it flags one side (“on one hand; indeed”) with a "
                    "following δέ answering it (“on the other”). It points forward to that pairing; "
                    "context supplies the answering clause.",
        "relation_label": "What it does (force set by context)",
        "relations": [
            {"type": "indeed; on one hand", "note": "flags one half of a μέν … δέ pairing",
             "ref": "Acts 11:16",
             "text": "John indeed immersed in water, but you shall be immersed in holy spirit"},
        ],
        "provenance": "GRAMMAR",
    },
    "G5620": {
        "kind": "structural", "strongs": "G5620", "lemma": "ὥστε",
        "function": "ὥστε marks a result — it ties what follows to what precedes as its outcome "
                    "(“so that, so then, therefore”). It points back to the cause and states what "
                    "came of it.",
        "relation_label": "What it does (force set by context)",
        "relations": [
            {"type": "so that; so (result)", "note": "states the outcome of what precedes",
             "ref": "Mark 2:12", "text": "so that all were amazed, and glorified God"},
        ],
        "provenance": "GRAMMAR",
    },
    "G3753": {
        "kind": "structural", "strongs": "G3753", "lemma": "ὅτε",
        "function": "ὅτε is the plain temporal connective — it fixes a clause at a point in time "
                    "(“when”). Where ὡς-as-“when” is one job among several, ὅτε does only this.",
        "relation_label": "What it does (force set by context)",
        "relations": [
            {"type": "when", "note": "marks the time at which something happens",
             "ref": "Matthew 7:28", "text": "when Jesus completed these words"},
        ],
        "provenance": "GRAMMAR",
    },
    "G3704": {
        "kind": "structural", "strongs": "G3704", "lemma": "ὅπως",
        "function": "ὅπως marks purpose — it ties a clause to an aim (“so that, in order that”). "
                    "Close in force to ἵνα; context supplies the goal in view.",
        "relation_label": "What it does (force set by context)",
        "relations": [
            {"type": "so that; in order that", "note": "marks the aim or goal",
             "ref": "Matthew 2:8", "text": "so that I also having come should do obeisance to him"},
        ],
        "provenance": "GRAMMAR",
    },
    "G1352": {
        "kind": "structural", "strongs": "G1352", "lemma": "διό",
        "function": "διό draws a conclusion — it ties what follows to what precedes as the thing "
                    "that follows from it (“therefore, wherefore”). A tight inferential link: “for "
                    "this reason.”",
        "relation_label": "What it does (force set by context)",
        "relations": [
            {"type": "therefore; wherefore", "note": "draws a conclusion from what precedes",
             "ref": "2 Corinthians 4:13", "text": "I trusted, therefore I spoke"},
        ],
        "provenance": "GRAMMAR",
    },
    "G2228": {
        "kind": "structural", "strongs": "G2228", "lemma": "ἤ",
        "function": "ἤ sets alternatives — it offers a choice between options (“or”), and in a "
                    "comparison it marks the thing compared against (“than”). Context picks which.",
        "relation_label": "What it does (force set by context)",
        "relations": [
            {"type": "or; than", "note": "marks an alternative, or the standard in a comparison",
             "ref": "Matthew 12:25",
             "text": "every city or house being portioned out against itself"},
        ],
        "provenance": "GRAMMAR",
    },
    "G5037": {
        "kind": "structural", "strongs": "G5037", "lemma": "τε",
        "function": "τε is the close-binding connective — a lighter “and” that ties items into a "
                    "single set, often paired (“both … and”). Tighter than καί: it groups things "
                    "as belonging together.",
        "relation_label": "What it does (force set by context)",
        "relations": [
            {"type": "and; both … and", "note": "binds items closely into one group",
             "ref": "Acts 8:38", "text": "both Philip and the eunuch"},
        ],
        "provenance": "GRAMMAR",
    },

    # ---- PARTICLES ----
    # ἄν — the modal / contingency particle. The particle analog of εἰμί: a pure FUNCTION word with
    # no English of its own, whose deep layer is an UNDERSPECIFICATION finding worth stating (the
    # verb's form alone doesn't settle whether its action is actual or merely supposed — ἄν is what
    # tips it). ONE structural use, NO sense typology. The glance/full split turns on that finding,
    # so the split is gated on data.glance + data.underspecified (NOT data.scope — ἄν has no
    # separate-use boundary the way the copula does, so its glance points INTO the finding, like the
    # conjunction cards, never OUT). underspecified_label is authored ("...contingency", not the
    # copula's "...relation"). Exemplars woven into the finding are verbatim ABP, verified vs local
    # abp_texts: Acts 2:21 (generalizing relative + subjunctive) + 1 John 2:19 (contrary-to-fact, ἄν
    # in the unreal apodosis). G302 has no dotted children (scanned) — nothing to route.
    "G302": {
        "kind": "structural",
        "strongs": "G302",
        "lemma": "ἄν",
        "function": "ἄν is a modal particle — it carries no English word of its own. It marks the "
                    "verb’s action as contingent: potential, conditional, or generalized, rather "
                    "than a flat statement of fact. What KIND of contingency is set by the verb’s "
                    "form and the construction around it, not by ἄν itself.",
        "glance": "There is a deeper point — the verb’s form alone doesn’t settle whether its "
                  "action is meant as real or merely supposed; ἄν is what tips it —",
        "underspecified_label": "The verb alone doesn’t settle the contingency",
        "underspecified": "By itself the verb’s form does not say whether its action is meant as "
                          "actual or as merely supposed — ἄν is the tell that tips it toward "
                          "contingent, and it has no separate word: it folds into the construction. "
                          "On a relative or temporal word, with the verb in its “should / may” "
                          "form, it makes the clause open-ended — “all who ever should call upon "
                          "the name of the Lord shall be delivered” (Acts 2:21), where “who” "
                          "becomes “whoever.” In the result-half of an unfulfilled condition it "
                          "marks what would have been but was not — “if they were of us, they would "
                          "have remained with us” (1 John 2:19). Take ἄν away and “whoever” narrows "
                          "to a definite “who,” and “would have remained” flattens to a plain "
                          "“remained”: the contingency rides on the particle, not the verb.",
        "provenance": "GRAMMAR",
    },
    # δή + γε — emphatic/discourse particles, one finding each (flat). Postpositive/enclitic, so the
    # γάρ-at-Mat-1:21 failure mode applies: each exemplar was tag-verified to carry the base lemma
    # on the quoted English word (both render "indeed", which ABP also uses for μέν G3303 — so the
    # SPECIFIC "indeed" was confirmed G1211 / G1065, not μέν). Dotted children G1211.1 ("strikes")
    # and G1065.1 ("troop") are parked different-words — they fall through the gate, not carded.
    "G1211": {
        "kind": "structural", "strongs": "G1211", "lemma": "δή",
        "function": "δή is an emphatic particle — it lends insistence or immediacy, most often "
                    "pressing a command home: “now, then, by all means; indeed.” It adds urgency to "
                    "what is said; it does not change what the words mean.",
        "relation_label": "What it does (force set by context)",
        "relations": [
            {"type": "indeed; now; then (urging)",
             "note": "presses a command, or underlines a statement",
             "ref": "Acts 13:2", "text": "Separate indeed to me Barnabas and Saul"},
        ],
        "provenance": "GRAMMAR",
    },
    "G1065": {
        "kind": "structural", "strongs": "G1065", "lemma": "γε",
        "function": "γε is an intensive particle — it singles out and emphasizes the word it "
                    "attaches to: “indeed, even, at least, in fact.” It adds focus or force to that "
                    "one word; context sets whether the shade is emphatic (“indeed”) or limiting "
                    "(“at least”).",
        "relation_label": "What it does (force set by context)",
        "relations": [
            {"type": "indeed; even; at least",
             "note": "emphasizes or restricts the word it attaches to",
             "ref": "Romans 8:32", "text": "The one who indeed his own son spared not"},
        ],
        "provenance": "GRAMMAR",
    },

    # ---- NEGATIVES ----
    # THE MECHANISM CUT: Greek has TWO negatives, split by what they scope — οὐ (G3756) negates a
    # flat assertion of fact (goes with the indicative); μή (G3361) negates everything that is NOT a
    # flat assertion (commands, purposes, wishes, suppositions, participles + questions slanted
    # toward "no"). TWO entries (distinct lexemes, "cut by form"), each stating its half and naming
    # the other. Both render as English "not", so each exemplar is picked so the CONSTRUCTION is
    # visible (Face-1 of the exemplar rule), verbatim + tag-verified vs local abp_texts. ABP does
    # NOT render the μή-question's "no"-slant visibly (Joh 4:12/8:53 read neutral), so that use is
    # named in the finding, not shown as a row. The compounds οὐδέ/μηδέ/οὔτε/μήτε/οὐχί inherit this
    # base split. Neither base has dotted children (scanned). BOTH cards carry a cross-ref to
    # Matthew 5:17 — the cleanest minimal pair in the corpus, where μή ("you should not think") and
    # οὐ ("I came not") sit in one sentence with the choice visible and motivated; it self-
    # demonstrates the cut without breaking the per-word model (eimi's Last-Supper-crossref move).
    # The cross-ref does NOT split οὐ (it stays flat) — a lone crossref no longer triggers hasMore.
    "G3756": {
        "kind": "structural", "strongs": "G3756", "lemma": "οὐ",
        "function": "οὐ is the factual negative. It denies a statement of fact and pairs with the "
                    "indicative — the mood that asserts what is or is not the case. Greek splits "
                    "“not” into two words by what is being denied, and οὐ takes the factual half: a "
                    "flat “this is not so.” (Everything that is not a flat assertion — commands, "
                    "purposes, suppositions — takes its counterpart μή.)",
        "relation_label": "What it negates",
        "relations": [
            {"type": "a statement of fact",
             "note": "denies what is or is not the case; pairs with the indicative",
             "ref": "Matthew 5:17", "text": "I came not to depose, but to fulfill"},
        ],
        "crossref": {
            "ref": "Matthew 5:17",
            "note": "Both negatives appear together at Matthew 5:17 — μή on the forbidden thought "
                    "(“you should not think”), οὐ on the flat denial (“I came not to depose”). The "
                    "choice of negative is visible and motivated in one sentence.",
        },
        "provenance": "GRAMMAR",
    },
    # μή — typology card (the ὅτι shape: several jobs told apart by context, ONE card). Glance flags
    # "lest" (the easy-to-miss member: a negative that is a whole subordinator, not a pre-posed
    # "not") and points INTO the list. The three rows span the non-indicative moods — command
    # (imperative), purpose (subjunctive), wish (optative) — all verbatim ABP, tag-verified G3361.
    "G3361": {
        "kind": "structural", "strongs": "G3361", "lemma": "μή",
        "function": "μή is the other negative. Where οὐ denies a fact, μή negates everything that "
                    "is not a flat assertion — a command, a purpose, a wish, a supposition — and it "
                    "pairs with the non-indicative moods, the realm of will and possibility. It "
                    "also slants a question toward the answer “no.” The English word is still just "
                    "“not”; which negative Greek reaches for tells you what KIND of thing is being "
                    "denied. (For a plain denial of fact, Greek uses οὐ.)",
        "glance": "The one to watch is “lest” — there μή is not a pre-posed “not” but a whole word, "
                  "heading off an outcome to be guarded against —",
        "relation_label": "What μή negates — context picks which, not μή",
        "relation_lead": "Same word, several jobs — each negating something other than a flat fact:",
        "relations": [
            {"type": "a command (prohibition)",
             "note": "with an imperative or a “should” verb — “do not …”",
             "ref": "Matthew 10:31", "text": "Do not then fear!"},
            {"type": "a purpose, guarded against (“lest”)",
             "note": "heads off a feared or unwanted outcome",
             "ref": "1 Corinthians 10:12", "text": "take heed lest he should fall!"},
            {"type": "a wish, rejected (“may it not be!”)",
             "note": "negates a wish or supposed possibility — Paul’s emphatic refusal",
             "ref": "Romans 6:2", "text": "May it not be."},
        ],
        "crossref": {
            "ref": "Matthew 5:17",
            "note": "Both negatives appear together at Matthew 5:17 — μή on the forbidden thought "
                    "(“you should not think”), οὐ on the flat denial (“I came not to depose”). The "
                    "choice of negative is visible and motivated in one sentence.",
        },
        "provenance": "GRAMMAR",
    },
    # COMPOUND negatives — each inherits the base cut: the οὐ-family (οὐδέ/οὔτε/οὐχί) negates fact
    # (indicative); the μή-family (μηδέ/μήτε) negates the non-factual (commands, oaths, suppositions).
    # Each card names its base and its twin so the family reads as one mechanism. Flat one-finding
    # cards; exemplars verbatim + tag-verified. None has dotted children (scanned).
    "G3761": {
        "kind": "structural", "strongs": "G3761", "lemma": "οὐδέ",
        "function": "οὐδέ is the factual negative οὐ joined with δέ — “and not, not even, neither.” "
                    "Like its base οὐ it denies a matter of fact (it goes with the indicative), and "
                    "it adds to or caps the denial (“not even …”). Its non-factual twin, used in "
                    "commands and the like, is μηδέ.",
        "relation_label": "What it does",
        "relations": [
            {"type": "not even; and not; neither",
             "note": "denies a fact, adding to or capping it",
             "ref": "Matthew 6:29",
             "text": "not even Solomon in all his glory was clothed as one of these"},
        ],
        "provenance": "GRAMMAR",
    },
    "G3366": {
        "kind": "structural", "strongs": "G3366", "lemma": "μηδέ",
        "function": "μηδέ is the non-factual negative μή joined with δέ — “and not, not even, nor.” "
                    "Like its base μή it negates within a command, purpose, or supposition rather "
                    "than a flat fact, carrying the prohibition on to a further item (“do not …, "
                    "nor …”). Its factual twin is οὐδέ.",
        "relation_label": "What it does",
        "relations": [
            {"type": "nor; and not; not even",
             "note": "extends a prohibition or non-factual negation to a further item",
             "ref": "1 John 2:15", "text": "Do not love the world, nor the things in the world!"},
        ],
        "provenance": "GRAMMAR",
    },
    "G3777": {
        "kind": "structural", "strongs": "G3777", "lemma": "οὔτε",
        "function": "οὔτε is the factual negative οὐ joined with τε — the correlative “neither … "
                    "nor.” Like its base οὐ it denies matters of fact (with the indicative), "
                    "pairing two or more denials into one series. Its non-factual twin is μήτε.",
        "relation_label": "What it does",
        "relations": [
            {"type": "neither … nor",
             "note": "denies two or more things together, as facts",
             "ref": "Matthew 22:30", "text": "neither they marry, nor give in marriage"},
        ],
        "provenance": "GRAMMAR",
    },
    "G3383": {
        "kind": "structural", "strongs": "G3383", "lemma": "μήτε",
        "function": "μήτε is the non-factual negative μή joined with τε — the correlative “neither "
                    "… nor.” Like its base μή it negates within commands, oaths, and suppositions "
                    "rather than flat facts, joining the items into one series. Its factual twin is "
                    "οὔτε.",
        "relation_label": "What it does",
        "relations": [
            {"type": "neither … nor",
             "note": "joins two or more items under one prohibition or non-factual negation",
             "ref": "Matthew 5:34", "text": "Do not swear by an oath wholly; nor on the heaven"},
        ],
        "provenance": "GRAMMAR",
    },
    "G3780": {
        "kind": "structural", "strongs": "G3780", "lemma": "οὐχί",
        "function": "οὐχί is the strengthened form of the factual negative οὐ — an emphatic “not at "
                    "all; no indeed.” It denies a fact with extra force, and often heads a question "
                    "that expects the answer “yes” (“Is it not …?”). It has no μή-side twin — it is "
                    "simply οὐ, intensified.",
        "relation_label": "What it does",
        "relations": [
            {"type": "no!; not at all (emphatic)",
             "note": "an emphatic denial; also heads a question slanted toward “yes”",
             "ref": "Luke 13:3", "text": "No, I say to you"},
        ],
        "provenance": "GRAMMAR",
    },

    # ---- THE ARTICLE ----
    # ὁ — the definite article. STRUCTURAL USE ONLY (definite marker + substantivizer; it also bears
    # case/gender/number). Like ἄν it carries an underspecification finding worth stating (Greek's
    # article is NOT a one-to-one "the"), so it splits glance/full (data.glance + data.underspecified;
    # NOT data.scope — its glance points INTO the finding, not OUT to a separate use). The standalone
    # PRONOMINAL use (ὁ δέ "and he"; ὁ μέν … ὁ δέ "the one … the other") resolves at the REFERENT, not
    # the noun — flagged in the straddle as handled separately, DEFERRED to step b (the demonstrative/
    # pronoun card); not built here. Dotted children G3588.1 ("sharp points", Job 41:30) + G3588.2
    # ("oboli", 7×) are parked different-words — they fall through the gate (no "forms" key), not carded.
    "G3588": {
        "kind": "structural", "strongs": "G3588", "lemma": "ὁ",
        "function": "ὁ is the definite article. It marks its noun as definite — a particular, "
                    "identifiable one — and it carries the case, gender, and number that show how "
                    "the noun fits the sentence. It also works as a substantivizer: set in front of "
                    "an adjective, a participle, or a whole phrase, it turns that into a noun — “the "
                    "poor,” “the one who believes.”",
        "glance": "Greek’s article is not a one-to-one match for English “the” — its presence or "
                  "absence carries weight English often can’t show, and translators add or drop "
                  "“the” freely —",
        "underspecified_label": "Greek’s article is not English “the”",
        "underspecified": "Greek uses and omits the article on principles English does not share — "
                          "it can stand with abstract nouns, with proper names, even in front of a "
                          "whole clause, and it is regularly left untranslated, or supplied where "
                          "Greek has none. So its presence is not simply “the,” nor its absence "
                          "“a”: what the article is doing — marking a definite noun, turning a word "
                          "into a noun, or just carrying the grammatical case — is read off the "
                          "construction, not off an English equivalent. Mapped straight onto “the,” "
                          "it gets both over- and under-read.",
        "relation_label": "What the article does — context picks which",
        "relation_lead": "One word, two jobs (besides carrying case, gender, and number):",
        "relations": [
            {"type": "definite marker",
             "note": "marks the noun as a particular, identifiable one",
             "ref": "Matthew 16:16", "text": "You are the Christ"},
            {"type": "substantivizer",
             "note": "turns a participle, adjective, or phrase into a noun — its most distinctive "
                     "job, and the one English can least do one-to-one",
             "ref": "John 11:25", "text": "The one believing in me"},
        ],
        "straddle": "Standing alone, without a noun, ὁ can work as a pronoun — “ὁ δέ” (“and he, but "
                    "he”), or “ὁ μέν … ὁ δέ” (“the one … the other”). There it points at someone "
                    "already in view rather than marking a noun, so its meaning resolves at the "
                    "referent, not here — that use is handled separately.",
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
        # Hand-authored header, displayed VERBATIM — the card hero must NOT source the lemma +
        # romanization from the dotted_lexicon row (its base-neighbour lemma μέσος + the ABP
        # romanization converter mangle a two-word idiom into "ἀνάμέσος / anámésos"). The translit
        # follows the converter's own scheme (grave folded to acute) so it matches every other card.
        "translit": "aná méson",
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
