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
                 "itself is the predicate and asserts existence or presence — “I am the One who "
                 "is” (Exodus 3:14), “in the beginning was the Word” (John 1:1). There the meaning "
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
}

_FORM_DECODERS = {"eimi": eimi_form}


def structural_entry(strongs):
    """Return the ready-to-serve structural card for a normalized Strong's number (e.g.
    'G1510.2.3' or 'G1510'), with a per-form parse stamp when a dotted conjugate was clicked,
    or None if this base has no structural entry."""
    base = strongs.split(".")[0]
    spec = _STRUCTURAL.get(base)
    if not spec:
        return None
    entry = copy.deepcopy(spec)
    decoder = _FORM_DECODERS.get(spec.get("forms"))
    if decoder and "." in strongs:
        form = decoder(strongs)
        if form:
            entry["form"] = form
    entry.pop("forms", None)       # internal routing field, not for the browser
    return entry
