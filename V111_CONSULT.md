# V11.1 one-time PA consult — banked bytes (2026-07-12)

Read-only consult per DESIGN_v11_acceptance.md fixture rule. Source: the four surviving
draw files on PA (`~/bible-db/draws/G*.json` — each holds the word's LAST draw, d2;
d1 raws overwritten, the known draw-cache-history loss). Two artifacts, both JP-run,
pasted verbatim into the session and copied here byte-for-byte:

1. **Warn reproduction** (`~/v111_warns.txt`): production `probe2_names` (p2wl:v1,
   imported from scripts/build_lexica_def.py, never a copy) re-run against the four
   surviving raws with live verses.text lookups. 43 warns, 0 notrun.
2. **Context extraction** (`~/v111_ctx.txt`): 120/160-char context around selected
   warned tokens in the raws.

## Artifact 1 — probe-2 warns, verbatim

```
==== G1390 (11 warns, 0 notrun)
  named subject "Jehoshaphat" absent from cited text(s) 2Ch 21:3 — adjudicate (misattribution class)
  named subject "Nebuchadnezzar" absent from cited text(s) Dan 2:6 — adjudicate (misattribution class)
  named subject "Belshazzar" absent from cited text(s) Dan 5:17 — adjudicate (misattribution class)
  named subject "Israel" absent from cited text(s) 1Ki 13:7 — adjudicate (misattribution class)
  named subject "Korah" absent from cited text(s) 2Ch 31:14 — adjudicate (misattribution class)
  named subject "Hiram" absent from cited text(s) 2Ch 2:10 — adjudicate (misattribution class)
  named subject "Paul" absent from cited text(s) Php 4:17 — adjudicate (misattribution class)
  named subject "Levitical" absent from cited text(s) Num 3:9 — adjudicate (misattribution class)
  named subject "Aaron" absent from cited text(s) Num 18:11 — adjudicate (misattribution class)
  named subject "Votive" absent from cited text(s) Lev 23:38 — adjudicate (misattribution class)
  named subject "English" absent from cited text(s) Num 28:2 — adjudicate (misattribution class)
==== G227 (8 warns, 0 notrun)
  named subject "Jesus" absent from cited text(s) Joh 4:18 — adjudicate (misattribution class)
  named subject "Samaritan" absent from cited text(s) Joh 4:18 — adjudicate (misattribution class)
  named subject "Peter" absent from cited text(s) Act 12:9 — adjudicate (misattribution class)
  named subject "Beloved" absent from cited text(s) Joh 21:24, Gen 41:32 — adjudicate (misattribution class)
  named subject "Egypt" absent from cited text(s) Joh 21:24, Gen 41:32 — adjudicate (misattribution class)
  named subject "Johannine" absent from cited text(s) Joh 5:31, Joh 5:32, Joh 8:13, Joh 8:14, Joh 8:16, Joh 8:17, Joh 3:33, 3Jn 1:12, 3Jn 1:12 — adjudicate (misattribution class)
  named subject "Jesus" absent from cited text(s) Neh 7:2, Mar 12:14, Mat 22:16, Mar 12:14, Mat 22:16 — adjudicate (misattribution class)
  named subject "Paul" absent from cited text(s) Joh 7:18, Rom 3:4, 2Co 6:8, 1Pe 5:12, 1Jn 2:27 — adjudicate (misattribution class)
==== G162 (13 warns, 0 notrun)
  named subject "Active" absent from cited text(s) Job 1:15 — adjudicate (misattribution class)
  named subject "Sabean" absent from cited text(s) Job 1:15 — adjudicate (misattribution class)
  named subject "Amalekites" absent from cited text(s) 1Sa 30:5 — adjudicate (misattribution class)
  named subject "Amalekite" absent from cited text(s) 1Sa 30:3 — adjudicate (misattribution class)
  named subject "Shechem" absent from cited text(s) Gen 34:29 — adjudicate (misattribution class)
  named subject "Reubenites" absent from cited text(s) 1Ch 5:21 — adjudicate (misattribution class)
  named subject "Elisha" absent from cited text(s) 2Ki 6:22 — adjudicate (misattribution class)
  named subject "Israelites" absent from cited text(s) Jer 50:33 — adjudicate (misattribution class)
  named subject "Judahites" absent from cited text(s) Jer 50:33 — adjudicate (misattribution class)
  named subject "Edom" absent from cited text(s) Oba 1:11 — adjudicate (misattribution class)
  named subject "Solomon" absent from cited text(s) 1Ki 8:50 — adjudicate (misattribution class)
  named subject "Solomon" absent from cited text(s) 2Ch 6:36 — adjudicate (misattribution class)
  named subject "None" absent from cited text(s) 2Ti 3:6 — adjudicate (misattribution class)
==== G236 (11 warns, 0 notrun)
  named subject "Putting" absent from cited text(s) Gen 35:2 — adjudicate (misattribution class)
  named subject "Jehoiachin" absent from cited text(s) Jer 52:33 — adjudicate (misattribution class)
  named subject "Trading" absent from cited text(s) Gen 31:7 — adjudicate (misattribution class)
  named subject "Laban" absent from cited text(s) Gen 31:7 — adjudicate (misattribution class)
  named subject "Israelites" absent from cited text(s) Isa 24:5 — adjudicate (misattribution class)
  named subject "Altering" absent from cited text(s) Ezr 6:11, Ezr 6:12, Act 6:14 — adjudicate (misattribution class)
  named subject "Stephen" absent from cited text(s) Ezr 6:11, Ezr 6:12, Act 6:14 — adjudicate (misattribution class)
  named subject "Altering" absent from cited text(s) Gal 4:20 — adjudicate (misattribution class)
  named subject "Paul" absent from cited text(s) Gal 4:20 — adjudicate (misattribution class)
  named subject "Nebuchadnezzar" absent from cited text(s) Dan 4:16 — adjudicate (misattribution class)
  named subject "Applying" absent from cited text(s) Isa 24:5, Neh 9:26, Rom 1:23 — adjudicate (misattribution class)
```

## Artifact 2 — raw-card context around warned tokens, verbatim (Python repr)

```
==== G1390
'Aaron\'s house (Num 18:11); "from all your gifts you shall remove a cut-away portion to the LORD" (Num 18:29).\n\nSub-use: Votive and voluntary sanctuary offerings — "besides the Sabbaths of the LORD, and besides your gifts, and besides all your vows, and besides all your voluntary offeri'
---
'than what the contexts show — in Num 28:2 the word governs ritual offerings brought to God on feast days, a setting the English "presents" does not capture. The gloss "gift" renders adequately across both senses but obscures the distinction the contexts draw between an ordinary interper'
---
'r is the cultic or sanctuary setting and the language of sanctification, vowing, or approaching.\n\nSub-use: Priestly and Levitical portions set apart for sacred service — the Levites themselves are given to Aaron "for a gift being given" (Num 3:9); they are taken "as a gift being given to '
---
' from the nations (2Ch 32:23); the king of Israel offers "a gift!" as hospitality-payment to the man of God (1Ki 13:7); Korah oversees the distribution of "gifts" (2Ch 31:14); provisions supplied to Hiram\'s workers are given "as gifts" (2Ch 2:10).\n\nSub-use: Land, inheritance, or porti'
---
'ty-payment to the man of God (1Ki 13:7); Korah oversees the distribution of "gifts" (2Ch 31:14); provisions supplied to Hiram\'s workers are given "as gifts" (2Ch 2:10).\n\nSub-use: Land, inheritance, or portion assigned as an allocated share — Joseph does not acquire the priests\' land b'
---
==== G227
'Standing or holding as valid — testimony or judgment meets the standard of legitimate, receivable witness**\n\nIn several Johannine passages the word addresses not merely whether a claim fits the facts but whether it qualifies as admissible, authoritative witness. The question is juridical:'
---
'his testimony is true; and that one knows that he speaks true" (Joh 19:35). At Joh 21:24 the community vouches that the Beloved Disciple\'s witness "is true." The dream-doubling in Egypt means "the saying by God will be true" (Gen 41:32). The investigation prescribed in Deu 13:14 is to c'
---
'e" (Joh 19:35). At Joh 21:24 the community vouches that the Beloved Disciple\'s witness "is true." The dream-doubling in Egypt means "the saying by God will be true" (Gen 41:32). The investigation prescribed in Deu 13:14 is to confirm "if the word be clearly true that this abomination '
---
'what actually happened — the word predicates that a statement about a past or present event holds up against the facts. Jesus tells the Samaritan woman "this truly you have said" after she denied having a husband (Joh 4:18). Peter, emerging from the prison, recognizes that what the an'
---
'er it qualifies as admissible, authoritative witness. The question is juridical: does this testimony count? At Joh 5:31 Jesus says "if I testify concerning myself, my testimony is not true" — the issue is whether solo self-testimony satisfies legal requirements. At Joh 5:32 he immedia'
---
'nother\'s corroborating word does qualify. Joh 8:13 has the Pharisees object "your testimony is not valid"; Joh 8:14 has Jesus assert "my testimony is valid; for I know from what place I came"; Joh 8:16 extends it: "my judgment is valid, because I am not alone"; Joh 8:17 grounds the po'
---
' is commended as "a true man" — his reliability is the reason for his appointment. Mar 12:14 and Mat 22:16 both address Jesus with "we know that you are true" (Mar 12:14; Mat 22:16), explaining this as meaning he does not play to persons but teaches God\'s way honestly — his character '
---
' true, and every man a liar" — God\'s nature is contrasted with human fallibility as a guarantee of his word. In 2Co 6:8 Paul places himself "as deluded, and yet true" — he is reliable though misjudged. In 1Pe 5:12 the characterization moves to an assertion: "attesting this to be the '
---
==== G162
' foreign army, a raiding party, or an individual captor; the taken are removed to another land or held as prisoners.\n\n- Active (the agent captures): Sabean raiders "fell upon and captured" Job\'s livestock servants (Job 1:15); similarly Chaldeans "captured" camels and killed servants (J'
---
'ing as a full noun phrase, which the translation\'s surrounding wording ("the ones capturing") actually reflects well.\n- None of the supplied occurrences attests any sense of purely intellectual or spiritual "captivating" independent of the control-and-removal image; 2Ti 3:6 is the cl'
---
'y, or an individual captor; the taken are removed to another land or held as prisoners.\n\n- Active (the agent captures): Sabean raiders "fell upon and captured" Job\'s livestock servants (Job 1:15); similarly Chaldeans "captured" camels and killed servants (Job 1:17); the Syrians "captur'
---
'ase ("the ones capturing") that identifies the enemy power holding captives, without describing a fresh act of seizure. Solomon is urged to "appoint them for compassions before the ones capturing them" (1Ki 8:50); God similarly "gave them over for compassions before all the ones having '
---
'ing shall be captives" (Isa 14:2); "For there the ones capturing us asked …" (Psa 137:3); in the conditional framing of Solomon\'s prayer, "the ones capturing shall take them captive into a land far or near" (2Ch 6:36, both the agent-noun "ones capturing" and the finite "shall take them '
---
' "return the captivity which you captured from your brethren" (2Ch 28:11); "Because of their capturing the captivity of Solomon, to close them up in Edom" (Amo 1:6).\n\n---\n\n**2. Taking something abstract — using the same seizing-and-carrying-off image on a non-physical object**\n\nTwo occu'
---
==== G236
'ing constructions; the object being replaced ranges from physical garments to covenantal law to divine glory.\n\nSub-use: Putting on different clothes or marking a change of personal circumstance by swapping garments. Jacob\'s household is told to "cleanse and change your robes" (Gen 35:2)'
---
'tle for cattle. Lev 27:27 and Lev 27:33 extend the rule to unclean animals and tithed livestock respectively.\n\nSub-use: Trading one thing for another in a transaction framed as substitution rather than purchase. Laban "bartered my wage for the ten lambs" (Gen 31:7); every firstborn donk'
---
'resentation of an image" (Rom 1:23); they "changed their glory into a representation of a calf" (Psa 106:20).\n\nSub-use: Altering an existing decree, custom, or institution. Ezra 6:11 threatens the man "who ever changes this word"; Ezra 6:12 prays God will "eradicate every king … who shou'
---
'cusation against Stephen is that Jesus "will … change the customs which Moses delivered up to us" (Act 6:14).\n\nSub-use: Altering the tone or manner of speech rather than exchanging objects. Paul wishes "to change my voice; for I am perplexed as to you" (Gal 4:20) — he wants to shift his '
---
'exchange occurrences in Lev 27 do not require; the Lev 27 verses are regulatory substitutions, not market transactions. Applying "barter" to Neh 9:26 and Rom 1:23 (which this translation also does) is defensible in that both describe exchanging one thing for a worse one, but the commerci'
---
'e every king … who should stretch out his hand to change and remove from view the house of God"; the accusation against Stephen is that Jesus "will … change the customs which Moses delivered up to us" (Act 6:14).\n\nSub-use: Altering the tone or manner of speech rather than exchanging obj'
---
'he leopard her colors" — transformation of inborn physical nature used as a figure for moral impossibility (Jer 13:23). Nebuchadnezzar\'s heart "shall be changed from the ones of men, and the heart of a wild beast shall be given to him; and seven times shall change over him" (Dan 4:16); the sam'
---
```

## Provenance limits (honest scope)

- These are the d2 (surviving) draws only. The d1 raws are overwritten; classes named
  in the ticket bank but not reproduced here (Earthly, Also, Similarly, Cosmic,
  Renewed, Sets, Greek, Peoples) have NO surviving bytes — same structural shape as
  the reproduced classes, fixtures for them (if any) must be labeled reconstructions.
- Warn lines in artifact 1 were REGENERATED today with the production detector at
  p2wl:v1 against the surviving raws — they are real detector output on real card
  bytes, not the run session's console lines (those were never written to disk).
