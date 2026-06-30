// ============================================================
// WORD STUDY DATA  (original synthesis — not authoritative)
// Verse markup (shared with Library):
//   [ ]            word-order bracket group
//   ^N             superscript word-order number
//   *word*         supplied / italic word
//   {Eng|Strong}   clickable lemma  (target lemma highlights when active)
// ============================================================

// canon order index (for sorting distribution + grouping)
const CANON_ORDER = [
  "Genesis","Exodus","Leviticus","Numbers","Deuteronomy","Joshua","Judges","Ruth",
  "1 Samuel","2 Samuel","1 Kings","2 Kings","1 Chronicles","2 Chronicles","Ezra",
  "Nehemiah","Esther","Job","Psalms","Proverbs","Ecclesiastes","Song of Solomon",
  "Isaiah","Jeremiah","Lamentations","Ezekiel","Daniel","Hosea","Joel","Amos",
  "Obadiah","Jonah","Micah","Nahum","Habakkuk","Zephaniah","Haggai","Zechariah","Malachi",
  "Matthew","Mark","Luke","John","Acts","Romans","1 Corinthians","2 Corinthians",
  "Galatians","Ephesians","Philippians","Colossians","1 Thessalonians","2 Thessalonians",
  "1 Timothy","2 Timothy","Titus","Philemon","Hebrews","James","1 Peter","2 Peter",
  "1 John","2 John","3 John","Jude","Revelation",
];
const TESTAMENT = (book) => (CANON_ORDER.indexOf(book) >= 39 ? "NT" : "OT");

// ============================================================
// LEMMA DICTIONARY
// ============================================================
const LEMMAS = {
  G4151: {
    strongs: "G4151", script: "greek", word: "πνεῦμα", translit: "pneûma",
    morph: "Noun · neuter", type: "Common noun", occ: 677, root: "from πνέω (G4154) — to breathe, to blow",
    lsjShort: "A movement of air; the wind; breath of the mouth or nostrils; the vital principle by which the body is animated; spirit.",
    lsjFull: "πνεῦμα, ατος, τό: (1) air in motion, wind, blast; (2) the breath of life, that which animates the body; (3) a spirit or simple essence, devoid of grosser matter, possessed of the power of knowing, desiring, deciding, and acting; (4) of the Holy Spirit, the third person of the Godhead, the immanent presence of God acting upon and within creation.",
    abp: [["spirit", 564], ["wind", 43], ["spirits", 37], ["breath", 29], ["winds", 2], ["harvest", 1]],
    kjv: [["spirit", 255], ["ghost", 91], ["spirits", 32], ["also", 1], ["itself", 1], ["life", 1], ["spiritual", 1], ["wind", 1]],
    related: [
      { s: "G4154", word: "πνέω", translit: "pnéō", gloss: "to breathe, blow" },
      { s: "G4152", word: "πνευματικός", translit: "pneumatikós", gloss: "spiritual" },
      { s: "G4157", word: "πνοή", translit: "pnoḗ", gloss: "breath, wind" },
      { s: "G5590", word: "ψυχή", translit: "psychḗ", gloss: "soul, life" },
    ],
    distribution: [
      ["Acts",70],["1 Corinthians",41],["Isaiah",40],["Ezekiel",38],["Luke",38],["Romans",35],
      ["Psalms",31],["John",24],["Revelation",24],["Mark",23],["Ecclesiastes",21],["Job",21],
      ["Matthew",19],["Galatians",18],["2 Corinthians",17],["1 Samuel",15],["Ephesians",15],
      ["Numbers",14],["1 John",13],["1 Kings",12],["Daniel",12],["Hebrews",12],["Judges",10],
      ["1 Peter",9],["2 Chronicles",9],["Genesis",7],["Zechariah",7],["Exodus",6],["Jeremiah",6],
      ["1 Thessalonians",5],["2 Kings",5],["1 Chronicles",4],["1 Timothy",4],["Haggai",4],["Hosea",4],
    ],
    verses: ["Joh4-24","Rom8-16","1Co2-11","Gal5-22","Eze37-9","Joh3-8","Act2-4","Psa51-11"],
  },

  G4102: {
    strongs: "G4102", script: "greek", word: "πίστις", translit: "pístis",
    morph: "Noun · feminine", type: "Common noun", occ: 243, root: "from πείθω (G3982) — to persuade, to be persuaded",
    lsjShort: "Conviction of the truth of anything; in the NT, a conviction respecting one's relationship to God, with the included idea of trust and holy fervor.",
    lsjFull: "πίστις, εως, ἡ: (1) conviction of the truth of anything, belief; in the NT of a conviction or belief respecting man's relationship to God and divine things; (2) fidelity, faithfulness, the character of one who can be relied on; (3) objectively, that which is believed, the body of faith or doctrine; (4) the persuasion or assurance by which one cleaves to Christ as the ground of salvation.",
    abp: [["belief", 142], ["faith", 88], ["trust", 7], ["assurance", 3], ["fidelity", 2], ["the faith", 1]],
    kjv: [["faith", 239], ["assurance", 1], ["belief", 1], ["fidelity", 1], ["them that believe", 1]],
    related: [
      { s: "G3982", word: "πείθω", translit: "peíthō", gloss: "to persuade" },
      { s: "G4100", word: "πιστεύω", translit: "pisteúō", gloss: "to believe, entrust" },
      { s: "G4103", word: "πιστός", translit: "pistós", gloss: "faithful, believing" },
      { s: "G571", word: "ἄπιστος", translit: "ápistos", gloss: "unbelieving" },
    ],
    distribution: [
      ["Romans",40],["Hebrews",32],["Galatians",22],["1 Corinthians",7],["2 Corinthians",7],
      ["Ephesians",8],["1 Timothy",19],["2 Timothy",8],["James",16],["1 Thessalonians",8],
      ["2 Thessalonians",5],["Colossians",5],["Philippians",5],["Titus",6],["Acts",15],
      ["Luke",11],["Matthew",8],["Mark",5],["1 Peter",5],["Revelation",4],["Philemon",2],
    ],
    verses: ["Rom3-22","Rom1-17","Gal2-20","Heb11-1","1Co13-13","Eph2-8","Rom10-17","1Th3-2"],
  },

  G26: {
    strongs: "G26", script: "greek", word: "ἀγάπη", translit: "agápē",
    morph: "Noun · feminine", type: "Common noun", occ: 116, root: "from ἀγαπάω (G25) — to love, regard with affection",
    lsjShort: "Self-giving, covenantal regard for the other — not contingent upon merit or reciprocation. Used of God's love and of the disposition demanded of believers.",
    lsjFull: "ἀγάπη, ης, ἡ: (1) affection, good-will, love, benevolence; (2) of the love feasts; distinct from φιλία (affection) and ἔρως (desire). In NT usage: a volitional, principled benevolence, self-giving and covenantal, expressing the very character of God toward humanity.",
    abp: [["love", 105], ["charity", 9], ["love feast", 1], ["dear", 1]],
    kjv: [["love", 86], ["charity", 27], ["dear", 1], ["charitably", 1], ["feast of charity", 1]],
    related: [
      { s: "G25", word: "ἀγαπάω", translit: "agapáō", gloss: "to love" },
      { s: "G27", word: "ἀγαπητός", translit: "agapētós", gloss: "beloved" },
      { s: "G5360", word: "φιλαδελφία", translit: "philadelphía", gloss: "brotherly love" },
    ],
    distribution: [
      ["1 Corinthians",14],["1 John",18],["Ephesians",10],["2 Corinthians",9],["Romans",8],
      ["Philippians",4],["Colossians",5],["1 Thessalonians",5],["2 Thessalonians",3],["Galatians",3],
      ["John",7],["Jude",3],["Revelation",2],["2 Peter",1],["Philemon",2],
    ],
    verses: ["1Co13-13","1Co13-4","Joh15-13","Rom5-8","Eph2-4","1Jo4-8","Gal5-22"],
  },

  G1680: {
    strongs: "G1680", script: "greek", word: "ἐλπίς", translit: "elpís",
    morph: "Noun · feminine", type: "Common noun", occ: 53, root: "from a primary ἔλπω — to anticipate, usually with pleasure",
    lsjShort: "Expectation of good, hope; in the Christian sense, joyful and confident expectation of eternal salvation grounded in the promises of God.",
    lsjFull: "ἐλπίς, ίδος, ἡ: (1) expectation, whether of good or of evil; (2) in the NT, almost always of the expectation of good, hope; (3) joyful and confident expectation of eternal salvation; (4) by metonymy, the author of hope, or the object on which hope is fixed.",
    abp: [["hope", 51], ["faith", 1], ["expectation", 1]],
    kjv: [["hope", 53]],
    related: [
      { s: "G1679", word: "ἐλπίζω", translit: "elpízō", gloss: "to hope, expect" },
      { s: "G4102", word: "πίστις", translit: "pístis", gloss: "faith" },
    ],
    distribution: [
      ["Romans",13],["1 Corinthians",4],["2 Corinthians",3],["Colossians",4],["Ephesians",3],
      ["1 Thessalonians",4],["2 Thessalonians",1],["Titus",3],["Hebrews",5],["1 Peter",3],["Acts",8],
    ],
    verses: ["Rom15-13","1Co13-13","Rom5-5","Heb11-1","1Th1-3","Tit2-13"],
  },

  H7307: {
    strongs: "H7307", script: "hebrew", word: "רוּחַ", translit: "rûwach",
    morph: "Noun · feminine", type: "Common noun", occ: 378, root: "from רוּחַ (H7306) — to blow, breathe",
    lsjShort: "Wind, breath, mind, spirit; the animating principle, and the Spirit of God moving over creation.",
    lsjFull: "רוּחַ: (1) wind, by resemblance breath, i.e. a sensible (or even violent) exhalation; (2) figuratively, life, anger, unsubstantiality; (3) by extension, a region of the sky; (4) spirit, but only of a rational being, including its expression and functions; (5) the Spirit of God.",
    abp: [["spirit", 232], ["wind", 90], ["breath", 27], ["winds", 5], ["side", 6], ["mind", 5]],
    kjv: [["Spirit", 76], ["wind", 92], ["spirit", 127], ["breath", 27], ["side", 6], ["mind", 5]],
    related: [
      { s: "H7306", word: "רוּחַ", translit: "rûwach", gloss: "to breathe, perceive" },
      { s: "H5397", word: "נְשָׁמָה", translit: "neshâmâh", gloss: "breath" },
      { s: "G4151", word: "πνεῦμα", translit: "pneûma", gloss: "spirit (LXX)" },
    ],
    distribution: [
      ["Ezekiel",52],["Isaiah",51],["Psalms",39],["Job",31],["Ecclesiastes",24],["Genesis",13],
      ["Numbers",10],["Proverbs",18],["Jeremiah",18],["Zechariah",8],["Exodus",6],["Judges",7],
      ["1 Samuel",9],["1 Kings",11],["Daniel",10],["2 Chronicles",8],["Hosea",4],["Habakkuk",1],
    ],
    verses: ["Gen1-2","Eze37-9","Psa51-11","Isa11-2","Job33-4"],
  },

  H5397: {
    strongs: "H5397", script: "hebrew", word: "נְשָׁמָה", translit: "neshâmâh",
    morph: "Noun · feminine", type: "Common noun", occ: 24, root: "from נָשַׁם (H5395) — to blow away, pant",
    lsjShort: "A puff, i.e. wind, vital breath, divine inspiration, intellect, or an animal.",
    lsjFull: "נְשָׁמָה: (1) a puff, i.e. wind, angry or vital breath; (2) divine inspiration; (3) intellect; (4) by implication, an animal. The breath which God breathed into the nostrils of man, making him a living soul.",
    abp: [["breath", 12], ["blast", 3], ["spirit", 2], ["souls", 2], ["inspiration", 1]],
    kjv: [["breath", 17], ["blast", 3], ["spirit", 2], ["souls", 1], ["inspiration", 1]],
    related: [
      { s: "H5395", word: "נָשַׁם", translit: "nâsham", gloss: "to pant, blow" },
      { s: "H7307", word: "רוּחַ", translit: "rûwach", gloss: "spirit, wind" },
    ],
    distribution: [
      ["Job",6],["Genesis",2],["Deuteronomy",2],["Joshua",4],["Isaiah",3],["Psalms",1],
      ["1 Kings",1],["2 Samuel",1],["Proverbs",1],["Daniel",1],["Job ",1],
    ],
    verses: ["Gen2-7","Job33-4"],
  },
};

// ============================================================
// VERSE POOL  (ABP English w/ study markup + KJV plain)
// ============================================================
const VERSES = {
  "Joh4-24":  { book: "John", ab: "Joh", ch: 4, v: 24, abp: "[^2a spirit ^1God] *is*; and the ones worshiping him, in {spirit|G4151} and truth must worship.", kjv: "God is a Spirit: and they that worship him must worship him in spirit and in truth." },
  "Rom8-16":  { book: "Romans", ab: "Rom", ch: 8, v: 16, abp: "[^3itself ^1The ^2{spirit|G4151}] bears witness together with our {spirit|G4151}, that we are children of God.", kjv: "The Spirit itself beareth witness with our spirit, that we are the children of God:" },
  "1Co2-11":  { book: "1 Corinthians", ab: "1Co", ch: 2, v: 11, abp: "For who of men knows the things of the man, except the {spirit|G4151} of the man, the one in him?", kjv: "For what man knoweth the things of a man, save the spirit of man which is in him?" },
  "Gal5-22":  { book: "Galatians", ab: "Gal", ch: 5, v: 22, abp: "But the fruit of the {spirit|G4151} is {love|G26}, joy, peace, long-suffering, kindness, goodness, {belief|G4102},", kjv: "But the fruit of the Spirit is love, joy, peace, longsuffering, gentleness, goodness, faith," },
  "Eze37-9":  { book: "Ezekiel", ab: "Eze", ch: 37, v: 9, abp: "And he said to me, Prophesy unto the {spirit|H7307}; prophesy, O son of man, and say to the {spirit|H7307}, Come from the four {winds|H7307}.", kjv: "Then said he unto me, Prophesy unto the wind, prophesy, son of man, and say to the wind, Come from the four winds, O breath." },
  "Joh3-8":   { book: "John", ab: "Joh", ch: 3, v: 8, abp: "The {wind|G4151} [^2where ^3it wills ^1blows], and [^2its sound ^1you hear], but you do not know from where it comes.", kjv: "The wind bloweth where it listeth, and thou hearest the sound thereof, but canst not tell whence it cometh." },
  "Act2-4":   { book: "Acts", ab: "Act", ch: 2, v: 4, abp: "And they were [^2filled ^1all] of {spirit|G4151} holy, and began to speak other languages.", kjv: "And they were all filled with the Holy Ghost, and began to speak with other tongues." },
  "Psa51-11": { book: "Psalms", ab: "Psa", ch: 51, v: 11, abp: "You should not cast me from your presence; and [^4{spirit|H7307} ^3holy ^1your ^2do not take] from me.", kjv: "Cast me not away from thy presence; and take not thy holy spirit from me." },

  "Rom3-22":  { book: "Romans", ab: "Rom", ch: 3, v: 22, abp: "And the righteousness of God is through the {belief|G4102} of Jesus Christ unto all and upon all the ones believing.", kjv: "Even the righteousness of God which is by faith of Jesus Christ unto all and upon all them that believe:" },
  "Rom1-17":  { book: "Romans", ab: "Rom", ch: 1, v: 17, abp: "For the righteousness of God in it is revealed from {belief|G4102} unto {belief|G4102}, as it has been written, And the just [^2by ^3belief ^1shall live].", kjv: "For therein is the righteousness of God revealed from faith to faith: as it is written, The just shall live by faith." },
  "Gal2-20":  { book: "Galatians", ab: "Gal", ch: 2, v: 20, abp: "[^3I live ^1And ^2no longer], [^2lives ^1but ^4in ^5me ^3Christ]; and what I now live in flesh, [^2in ^3{belief|G4102} ^1I live] of the son of God.", kjv: "I am crucified with Christ: nevertheless I live; yet not I, but Christ liveth in me: and the life which I now live in the flesh I live by the faith of the Son of God." },
  "Heb11-1":  { book: "Hebrews", ab: "Heb", ch: 11, v: 1, abp: "And is {belief|G4102} [^3of things being hoped ^1the ^2support], a proof of things not seen.", kjv: "Now faith is the substance of things hoped for, the evidence of things not seen." },
  "1Co13-13": { book: "1 Corinthians", ab: "1Co", ch: 13, v: 13, abp: "And now abides {belief|G4102}, {hope|G1680}, {love|G26}, these three; [^2the greater ^1but] of these is {love|G26}.", kjv: "And now abideth faith, hope, charity, these three; but the greatest of these is charity." },
  "Eph2-8":   { book: "Ephesians", ab: "Eph", ch: 2, v: 8, abp: "For by favor you are being delivered through {belief|G4102}, and this not of you — [^2of God ^1*it is* the gift];", kjv: "For by grace are ye saved through faith; and that not of yourselves: it is the gift of God:" },
  "Rom10-17": { book: "Romans", ab: "Rom", ch: 10, v: 17, abp: "So then the {belief|G4102} comes by report, and the report through a saying of God.", kjv: "So then faith cometh by hearing, and hearing by the word of God." },
  "1Th3-2":   { book: "1 Thessalonians", ab: "1Th", ch: 3, v: 2, abp: "And we sent forth Timothy our brother and servant of God, to support you and to comfort you concerning [^2{belief|G4102} ^1your];", kjv: "And sent Timothy, our brother, and minister of God, to establish you, and to comfort you concerning your faith:" },
  "1Co13-4":  { book: "1 Corinthians", ab: "1Co", ch: 13, v: 4, abp: "{Love|G26} is leniant, is kind; {love|G26} is not jealous; [^2{love|G26} ^1does not act rashly], is not inflated,", kjv: "Charity suffereth long, and is kind; charity envieth not; charity vaunteth not itself, is not puffed up," },
  "Joh15-13": { book: "John", ab: "Joh", ch: 15, v: 13, abp: "Greater [^2than this ^1{love|G26}] no one has, that any [^2his life ^1should place] for his friends.", kjv: "Greater love hath no man than this, that a man lay down his life for his friends." },
  "Rom5-8":   { book: "Romans", ab: "Rom", ch: 5, v: 8, abp: "[^3commends ^1And ^2his own {love|G26}] to us God, for *we* still [^2sinners ^1being], Christ died for us.", kjv: "But God commendeth his love toward us, in that, while we were yet sinners, Christ died for us." },
  "Eph2-4":   { book: "Ephesians", ab: "Eph", ch: 2, v: 4, abp: "But God being rich in mercy, on account of [^2much ^1his] {love|G26} in which he loved us,", kjv: "But God, who is rich in mercy, for his great love wherewith he loved us," },
  "1Jo4-8":   { book: "1 John", ab: "1Jo", ch: 4, v: 8, abp: "The one not loving knew not God, for God is {love|G26}.", kjv: "He that loveth not knoweth not God; for God is love." },
  "Rom15-13": { book: "Romans", ab: "Rom", ch: 15, v: 13, abp: "And the God of {hope|G1680} fill you with all joy and peace in believing, for you to abound in the {hope|G1680} by the power of {spirit|G4151} holy.", kjv: "Now the God of hope fill you with all joy and peace in believing, that ye may abound in hope, through the power of the Holy Ghost." },
  "Rom5-5":   { book: "Romans", ab: "Rom", ch: 5, v: 5, abp: "And the {hope|G1680} does not put to shame, because the {love|G26} of God has been poured out in our hearts through {spirit|G4151} holy.", kjv: "And hope maketh not ashamed; because the love of God is shed abroad in our hearts by the Holy Ghost." },
  "1Th1-3":   { book: "1 Thessalonians", ab: "1Th", ch: 1, v: 3, abp: "Unceasingly remembering your work of {belief|G4102}, and the toil of {love|G26}, and the endurance of {hope|G1680} of our Lord Jesus Christ,", kjv: "Remembering without ceasing your work of faith, and labour of love, and patience of hope in our Lord Jesus Christ," },
  "Tit2-13":  { book: "Titus", ab: "Tit", ch: 2, v: 13, abp: "waiting for the blessed {hope|G1680} and revelation of the glory of the great God and our deliverer Jesus Christ;", kjv: "Looking for that blessed hope, and the glorious appearing of the great God and our Saviour Jesus Christ;" },
  "Gen1-2":   { book: "Genesis", ab: "Gen", ch: 1, v: 2, abp: "And the {spirit|H7307} of God was carried upon the water.", kjv: "And the Spirit of God moved upon the face of the waters." },
  "Isa11-2":  { book: "Isaiah", ab: "Isa", ch: 11, v: 2, abp: "And [^4shall rest ^5upon ^6him ^1*the* ^2{spirit|H7307} ^3of God], a {spirit|H7307} of wisdom and understanding.", kjv: "And the spirit of the LORD shall rest upon him, the spirit of wisdom and understanding," },
  "Job33-4":  { book: "Job", ab: "Job", ch: 33, v: 4, abp: "[^2{spirit|H7307} ^1*The* divine] is the one making me, and the {breath|H5397} of *the* Almighty teaches me.", kjv: "The Spirit of God hath made me, and the breath of the Almighty hath given me life." },
  "Gen2-7":   { book: "Genesis", ab: "Gen", ch: 2, v: 7, abp: "And God formed the man — dust from the earth, and breathed into his face a {breath|H5397} of life, and [^3became ^1the ^2man] into [^2soul ^1a living].", kjv: "And the LORD God formed man of the dust of the ground, and breathed into his nostrils the breath of life; and man became a living soul." },
};

// ============================================================
// ENGLISH GLOSS INDEX  (gloss → matching lemmas, ordered)
// ============================================================
const GLOSS_INDEX = {
  spirit: ["G4151", "H7307", "H5397"],
  breath: ["H5397", "H7307", "G4151"],
  wind:   ["G4151", "H7307"],
  faith:  ["G4102"],
  belief: ["G4102"],
  love:   ["G26"],
  charity:["G26"],
  hope:   ["G1680"],
};

// ============================================================
// CORPUS SYNTHESES  (canned AI answers)
// ============================================================
const CORPUS = {
  "faith in paul's letters": {
    q: "faith in paul's letters",
    lead: "G4102",
    cited: ["G4102", "G26", "G1680"],
    total: 134,
    text: "Pístis (G4102) in Paul's letters denotes trust, confidence, and reliance on God or Christ — the foundational concept of Pauline theology. The word spans both the abstract noun “faith” and the concrete sense of “that which is believed” (the faith, the gospel). In Romans, pístis appears 40 times, anchoring Paul's argument that justification comes through faith apart from works of the law (Rom 3:28, 4:5). In 1 Corinthians 13 it ranks among the three abiding virtues alongside agápē (love) and elpís (hope). Galatians 2:16 and 3:22–26 establish faith as the means of receiving the Spirit and becoming children of God; Ephesians 2:8–9 declares salvation by grace through faith, not works. The semantic range holds both the act of believing and the content of belief — Paul uses pístis for both personal trust in Christ and the apostolic deposit of doctrine.",
    primary: ["1Th3-2", "1Co13-13", "Eph2-8", "Rom10-17", "Gal2-20", "Rom1-17"],
    additional: ["Rom3-22", "Heb11-1", "1Th1-3"],
  },
};

// per-word corpus prompt (lemma mode → seeds a question)
function corpusForLemma(strongs) {
  const lex = LEMMAS[strongs];
  if (!lex) return null;
  return {
    q: `the meaning of ${lex.translit} across Scripture`,
    lead: strongs,
    cited: [strongs, ...(lex.related || []).filter((r) => LEMMAS[r.s]).slice(0, 2).map((r) => r.s)],
    total: lex.occ,
    text: `${cap(lex.translit)} (${lex.strongs}) — ${lex.lsjShort} It occurs ${lex.occ} times in the corpus, concentrated in ${lex.distribution.slice(0,3).map((d)=>d[0]).join(", ")}. ${lex.abp[0] ? `The dominant rendering is “${lex.abp[0][0]}” (${lex.abp[0][1]}×), with secondary senses of ${lex.abp.slice(1,3).map((a)=>`“${a[0]}”`).join(" and ")} shading the word toward its fuller semantic field.` : ""}`,
    primary: lex.verses.slice(0, 6),
    additional: lex.verses.slice(6),
  };
}
function cap(s) { return s.charAt(0).toUpperCase() + s.slice(1); }

// suggested follow-up questions (lemma mode)
function suggestionsFor(strongs) {
  const lex = LEMMAS[strongs];
  if (!lex) return [];
  return [
    `How does ${lex.translit} differ from its synonyms?`,
    `Where is ${lex.translit} most concentrated?`,
    `Trace ${lex.translit} from the OT to the NT`,
  ];
}

// ============================================================
// WORD-SCOPED AI ANSWER  (overlay synthesis)
// Returns { q, text, cited:[strongs], citedVerses:[verseId] }
// text uses inline tokens: [[ref:ID]] clickable verse · [[lem:S]] clickable lemma
// citedVerses are always a subset of the studied word's occurrences
// (the center list is the evidence — no verse list lives in the overlay).
// ============================================================
function lemmaAnswer(strongs, question) {
  const lex = LEMMAS[strongs];
  if (!lex) return null;
  const q = (question || "").toLowerCase();
  const tr = lex.translit;
  const cap1 = cap(tr);
  const V = lex.verses.filter((id) => VERSES[id]);
  const gloss = lex.abp[0] ? lex.abp[0][0] : "the word";
  const rel = (lex.related || []).filter((r) => LEMMAS[r.s]);
  const otV = V.filter((id) => TESTAMENT(VERSES[id].book) === "OT");
  const ntV = V.filter((id) => TESTAMENT(VERSES[id].book) === "NT");
  const ref = (id) => (id ? `[[ref:${id}]]` : "");
  const lem = (s) => `[[lem:${s}]]`;
  const top = lex.distribution.slice().sort((a, b) => b[1] - a[1]).slice(0, 3);
  const uniq = (a) => a.filter((x, i) => x && a.indexOf(x) === i);

  let kind = "general";
  if (/differ|synonym|versus|\bvs\b|distinct|compare|nuance|same as/.test(q)) kind = "synonyms";
  else if (/concentrat|most|where.*(found|appear|occur)|distribut|frequen|common|cluster/.test(q)) kind = "concentration";
  else if (/trace|\bot\b|\bnt\b|old.*(new|test)|new.*old|develop|history|origin|journey|across the canon/.test(q)) kind = "trace";

  let text, cited, citedV;

  if (kind === "synonyms") {
    const syn = rel.slice(0, 2);
    text =
      `${cap1} (${lex.strongs}) carries the sense of ${lex.abp.slice(0, 2).map((a) => `“${a[0]}”`).join(" and ")}, ` +
      `but it shares the field with ${syn.map((r) => `${lem(r.s)} (${r.gloss})`).join(" and ") || "its cognates"}. ` +
      `The distinction is real: where ${syn[0] ? syn[0].translit : "its kin"} leans toward the plainer physical sense, ${tr} keeps the active, animating charge. ` +
      `Read ${ref(V[0])} against ${ref(V[1])} — both turn on ${tr}, yet the register shifts from ${gloss} to ${lex.abp[1] ? `“${lex.abp[1][0]}”` : "its fuller theological sense"}. ` +
      `${ref(V[2])} sharpens the line further.`;
    cited = [lex.strongs, ...syn.map((r) => r.s)];
    citedV = [V[0], V[1], V[2]];
  } else if (kind === "concentration") {
    const inTop = V.find((id) => VERSES[id].book === top[0][0]) || V[0];
    text =
      `${cap1} occurs ${lex.occ}× across the canon, but the weight is uneven. ` +
      `The heaviest concentrations fall in ${top.map((d) => `${d[0]} (${d[1]})`).join(", ")} — ` +
      `together a third of all occurrences. In ${top[0][0]} the word drives whole arguments; see ${ref(inTop)}. ` +
      `Elsewhere it thins to a handful of charged appearances, like ${ref(V[V.length - 1])}.`;
    cited = [lex.strongs];
    citedV = [inTop, V[V.length - 1]];
  } else if (kind === "trace") {
    text =
      `In the Hebrew Scriptures ${tr} opens as ${lex.abp.slice(0, 2).map((a) => `“${a[0]}”`).join(" and ")}` +
      `${otV[0] ? ` — ${ref(otV[0])}${otV[1] ? `, then ${ref(otV[1])}` : ""}` : ", a breath moving over the deep"}. ` +
      `By the New Testament the word has gathered its full theological charge: ` +
      `${ntV[0] ? ref(ntV[0]) : ""}${ntV[1] ? ` and ${ref(ntV[1])}` : ""} read it as the personal, indwelling ${gloss}. ` +
      `The arc runs unbroken from ${otV[0] ? `${VERSES[otV[0]].ab} ${VERSES[otV[0]].ch}` : "creation"} ` +
      `to ${ntV[0] ? `${VERSES[ntV[0]].ab} ${VERSES[ntV[0]].ch}` : "Pentecost"}, the same ${tr} at both ends.`;
    cited = [lex.strongs, ...rel.slice(0, 1).map((r) => r.s)];
    citedV = [...otV.slice(0, 2), ...ntV.slice(0, 2)];
  } else {
    text =
      `${cap1} (${lex.strongs}) — ${lex.lsjShort} ` +
      `It occurs ${lex.occ}× in the corpus, concentrated in ${top.map((d) => d[0]).join(", ")}. ` +
      `Representative passages: ${uniq(V.slice(0, 3)).map(ref).join(", ")}. ` +
      `The dominant rendering is “${lex.abp[0][0]}” (${lex.abp[0][1]}×), with ${lex.abp.slice(1, 3).map((a) => `“${a[0]}”`).join(" and ")} shading its semantic field.`;
    cited = [lex.strongs, ...rel.slice(0, 2).map((r) => r.s)];
    citedV = V.slice(0, 3);
  }

  return { q: question, text, cited: uniq(cited), citedVerses: uniq(citedV) };
}
