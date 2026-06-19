// ============================================================
// ASK THE CORPUS — corpus-wide AI data (original synthesis, not authoritative)
// Answer markup tokens:
//   [[l:STRONGS]]  → clickable lemma chip (jumps to Word study)
//   [[v:ID]]       → inline clickable reference (jumps to Library reader)
// Cited verses are also rendered in full beneath the prose (inline evidence).
// ============================================================

// lemmas referenced in answers (need not be full Word-study entries)
const AC_LEMMAS = {
  G129:  { gk: "αἷμα",     tr: "haîma",    gloss: "blood",    script: "greek" },
  G1242: { gk: "διαθήκη",  tr: "diathḗkē", gloss: "covenant", script: "greek" },
  H1818: { gk: "דָּם",      tr: "dām",      gloss: "blood",    script: "hebrew" },
  H1285: { gk: "בְּרִית",   tr: "berîth",   gloss: "covenant", script: "hebrew" },
  G4521: { gk: "σάββατον", tr: "sábbaton", gloss: "Sabbath",  script: "greek" },
  H7676: { gk: "שַׁבָּת",   tr: "shabbāth", gloss: "Sabbath",  script: "hebrew" },
  H7673: { gk: "שָׁבַת",    tr: "shābath",  gloss: "to cease, rest", script: "hebrew" },
  G4442: { gk: "πῦρ",      tr: "pŷr",      gloss: "fire",     script: "greek" },
  H784:  { gk: "אֵשׁ",      tr: "ʾēsh",     gloss: "fire",     script: "hebrew" },
  G3485: { gk: "ναός",     tr: "naós",     gloss: "temple, sanctuary", script: "greek" },
  G2411: { gk: "ἱερόν",    tr: "hierón",   gloss: "temple precinct",   script: "greek" },
  H1964: { gk: "הֵיכָל",    tr: "hêykāl",   gloss: "temple, palace",    script: "hebrew" },
};

// verse pool (KJV — public domain)
const AC_VERSES = {
  "Exo24-8":  { ref: "Exodus 24:8",      book: "Exodus",      text: "And Moses took the blood, and sprinkled it on the people, and said, Behold the blood of the covenant, which the LORD hath made with you concerning all these words." },
  "Lev17-11": { ref: "Leviticus 17:11",  book: "Leviticus",   text: "For the life of the flesh is in the blood: and I have given it to you upon the altar to make an atonement for your souls: for it is the blood that maketh an atonement for the soul." },
  "Mat26-28": { ref: "Matthew 26:28",    book: "Matthew",     text: "For this is my blood of the new testament, which is shed for many for the remission of sins." },
  "Heb9-22":  { ref: "Hebrews 9:22",     book: "Hebrews",     text: "And almost all things are by the law purged with blood; and without shedding of blood is no remission." },

  "Exo20-8":  { ref: "Exodus 20:8",      book: "Exodus",      text: "Remember the sabbath day, to keep it holy. Six days shalt thou labour, and do all thy work: but the seventh day is the sabbath of the LORD thy God." },
  "Mar2-27":  { ref: "Mark 2:27",        book: "Mark",        text: "And he said unto them, The sabbath was made for man, and not man for the sabbath." },
  "Col2-16":  { ref: "Colossians 2:16",  book: "Colossians",  text: "Let no man therefore judge you in meat, or in drink, or in respect of an holyday, or of the new moon, or of the sabbath days: which are a shadow of things to come." },
  "Heb4-9":   { ref: "Hebrews 4:9",      book: "Hebrews",     text: "There remaineth therefore a rest to the people of God. For he that is entered into his rest, he also hath ceased from his own works, as God did from his." },

  "Jer23-29": { ref: "Jeremiah 23:29",   book: "Jeremiah",    text: "Is not my word like as a fire? saith the LORD; and like a hammer that breaketh the rock in pieces?" },
  "Isa6-6":   { ref: "Isaiah 6:6",       book: "Isaiah",      text: "Then flew one of the seraphims unto me, having a live coal in his hand, which he had taken with the tongs from off the altar: and he laid it upon my mouth." },
  "Mal3-2":   { ref: "Malachi 3:2",      book: "Malachi",     text: "But who may abide the day of his coming? and who shall stand when he appeareth? for he is like a refiner's fire, and like fullers' soap." },
  "Eze1-4":   { ref: "Ezekiel 1:4",      book: "Ezekiel",     text: "And I looked, and, behold, a whirlwind came out of the north, a great cloud, and a fire infolding itself, and a brightness was about it, and out of the midst thereof as the colour of amber, out of the midst of the fire." },

  "Joh2-19":  { ref: "John 2:19",        book: "John",        text: "Jesus answered and said unto them, Destroy this temple, and in three days I will raise it up. But he spake of the temple of his body." },
  "1Co3-16":  { ref: "1 Corinthians 3:16", book: "1 Corinthians", text: "Know ye not that ye are the temple of God, and that the Spirit of God dwelleth in you?" },
  "Eph2-21":  { ref: "Ephesians 2:21",   book: "Ephesians",   text: "In whom all the building fitly framed together groweth unto an holy temple in the Lord: in whom ye also are builded together for an habitation of God through the Spirit." },
  "Rev21-22": { ref: "Revelation 21:22", book: "Revelation",  text: "And I saw no temple therein: for the Lord God Almighty and the Lamb are the temple of it." },

  "Psa119-105": { ref: "Psalm 119:105",  book: "Psalms",      text: "Thy word is a lamp unto my feet, and a light unto my path." },
};

// canned corpus answers — matched loosely by keyword
const AC_ANSWERS = [
  {
    id: "blood-covenant",
    match: ["blood", "covenant", "atonement", "sacrifice"],
    q: "Where does Scripture link blood and covenant?",
    text:
      "The link between [[l:H1818]] (blood) and [[l:H1285]] (covenant) is structural, not incidental — across the canon a covenant is cut, and blood is the seal. In the Sinai ceremony Moses dashes blood on the people and names it directly: [[v:Exo24-8]]. The logic is stated in the law itself — life resides in the blood, and so blood alone makes atonement — [[v:Lev17-11]]. The New Testament does not abandon the image but fulfils it: at the table Jesus takes the cup and calls it [[l:G129]] of the new [[l:G1242]] — [[v:Mat26-28]]. Hebrews then draws the principle to its sharpest edge, that under the law cleansing comes by blood and there is no remission without its shedding — [[v:Heb9-22]]. The thread runs unbroken from altar to upper room: covenant is always ratified in blood.",
    cited: ["H1818", "H1285", "G129", "G1242"],
    verses: ["Exo24-8", "Lev17-11", "Mat26-28", "Heb9-22"],
  },
  {
    id: "sabbath",
    match: ["sabbath", "rest", "seventh day", "shabbat"],
    q: "Compare the OT and NT view of the Sabbath",
    text:
      "In the Hebrew Scriptures the [[l:H7676]] (Sabbath) is law and gift at once — rooted in the verb [[l:H7673]] (to cease) and grounded in creation: the seventh day is set apart and hallowed — [[v:Exo20-8]]. The emphasis falls on cessation as covenant sign. The Gospels reframe rather than revoke it: Jesus subordinates the day to the person it was made to serve — [[v:Mar2-27]]. Paul then treats the [[l:G4521]] as shadow, its substance found in Christ — [[v:Col2-16]]. Hebrews completes the move, reading the Sabbath forward into an eschatological rest that still remains for the people of God — [[v:Heb4-9]]. The trajectory runs from a weekly ordinance toward a rest that is a person and a promise.",
    cited: ["H7676", "H7673", "G4521"],
    verses: ["Exo20-8", "Mar2-27", "Col2-16", "Heb4-9"],
  },
  {
    id: "fire-prophets",
    match: ["fire", "prophet", "refine", "burn", "flame"],
    q: "What does fire symbolize across the prophets?",
    text:
      "Among the prophets [[l:H784]] (fire) is rarely mere destruction — it is the medium of God's presence, word, and purifying judgment. Jeremiah hears the divine word itself as fire that breaks rock — [[v:Jer23-29]]. In Isaiah's call a live coal from the altar touches the prophet's lips, fire as cleansing rather than ruin — [[v:Isa6-6]]. Ezekiel's inaugural vision wraps God's approach in a self-infolding fire and brightness — [[v:Eze1-4]]. Malachi gathers the strands into the coming day, when the Lord arrives like a refiner's fire that tests who can stand — [[v:Mal3-2]]. Across the corpus [[l:G4442]] signifies the same double action: it consumes what is false and refines what is true.",
    cited: ["H784", "G4442"],
    verses: ["Jer23-29", "Isa6-6", "Eze1-4", "Mal3-2"],
  },
  {
    id: "temple",
    match: ["temple", "sanctuary", "dwell", "presence", "tabernacle"],
    q: "How is the temple reimagined in the New Testament?",
    text:
      "The Old Testament [[l:H1964]] is a fixed place where God's presence dwells; the New Testament relocates that presence again and again. Jesus first identifies the [[l:G3485]] with his own body — destroy this temple, and in three days I will raise it — [[v:Joh2-19]]. Paul extends the image to the gathered church, then to the believer: you are the temple of God, indwelt by the Spirit — [[v:1Co3-16]] — a building growing into a holy sanctuary — [[v:Eph2-21]]. Revelation completes the arc by removing the structure entirely, for God and the Lamb are themselves the temple of the city — [[v:Rev21-22]]. The movement is from a building, to a body, to a people, to God unmediated.",
    cited: ["H1964", "G3485", "G2411"],
    verses: ["Joh2-19", "1Co3-16", "Eph2-21", "Rev21-22"],
  },
];

// the four landing-page example prompts
const AC_EXAMPLES = [
  "Where does Scripture link blood and covenant?",
  "Compare the OT and NT view of the Sabbath",
  "What does fire symbolize across the prophets?",
  "How is the temple reimagined in the New Testament?",
];

// ============================================================
// WORD-SCOPED CONTEXT — when the tab is opened from a word study link.
// Hand-tuned suggestions for well-known lemmas; everything else gets a
// sensible generic set built from the transliteration.
// ============================================================
const AC_CONTEXT = {
  G4151: [ // πνεῦμα
    "How does pneûma differ from psyché?",
    "Trace pneûma from the OT to the NT",
    "Where is pneûma most concentrated?",
    "When does it mean wind vs. spirit?",
  ],
  G26: [ // ἀγάπη
    "How does agápē differ from philía and érōs?",
    "Trace agápē from the OT chesed to the NT",
    "Where is agápē most concentrated?",
    "Is agápē a feeling or an action in Scripture?",
  ],
  G4102: [ // πίστις
    "How does pístis differ from belief as mere assent?",
    "Trace pístis from Abraham to Paul",
    "Where is pístis most concentrated?",
    "Does pístis mean faith or faithfulness?",
  ],
  G5485: [ // χάρις
    "How does cháris differ from éleos (mercy)?",
    "Trace cháris from the OT chen to the NT",
    "Where is cháris most concentrated?",
    "What is the link between cháris and gift?",
  ],
};

function acScopeSuggestions(scope) {
  if (!scope) return AC_EXAMPLES;
  if (AC_CONTEXT[scope.strongs]) return AC_CONTEXT[scope.strongs];
  const tr = scope.tr || (scope.gk || "this word");
  return [
    `How does ${tr} differ from its near-synonyms?`,
    `Trace ${tr} from the OT to the NT`,
    `Where is ${tr} most concentrated?`,
    `What semantic range does ${tr} cover?`,
  ];
}

function acAnswer(question) {
  const q = (question || "").toLowerCase();
  let best = null, bestScore = 0;
  for (const a of AC_ANSWERS) {
    const score = a.match.reduce((n, k) => n + (q.includes(k) ? 1 : 0), 0);
    if (score > bestScore) { best = a; bestScore = score; }
  }
  if (best && bestScore > 0) return { ...best, q: question };
  // graceful fallback for an unmatched question — no fabricated citations
  return {
    id: "generic",
    q: question,
    text:
      "That's a broad, corpus-wide question. In a live build this would draw a synthesis from across the canon — weighing how the theme is introduced in the Law, developed by the Prophets, and taken up in the Gospels and Epistles — and cite the Greek and Hebrew lemmas it turns on along with the passages that carry them. The prototype ships four worked examples below; try one to see the full answer shape. [[v:Psa119-105]]",
    cited: [],
    verses: ["Psa119-105"],
    generic: true,
  };
}
