#!/usr/bin/env python3
"""
build_proof.py — generate the self-contained Didache ch1 proof page.

Reads the hand-tagged words (didache_ch1_tagged.json) + the public-domain
English (Roberts-Donaldson, below) and writes didache_ch1_proof.html showing
each verse as: readable English on top, clickable interlinear chips beneath —
the way the real Library pairs a translation with the word-study layer.
"""
import json
from pathlib import Path

HERE = Path(__file__).parent
words = json.loads((HERE / "didache_ch1_tagged.json").read_text(encoding="utf-8"))

# Roberts-Donaldson, public domain, split to match the Greek verses.
ENGLISH = {
 "0.1": "The teaching of the Lord to the Gentiles by the twelve apostles.",
 "1.1": "There are two ways, one of life and one of death, but a great difference "
        "between the two ways.",
 "1.2": "The way of life, then, is this: First, you shall love God who made you; "
        "second, love your neighbor as yourself, and do not do to another what you "
        "would not want done to you.",
 "1.3": "And of these sayings the teaching is this: Bless those who curse you, and "
        "pray for your enemies, and fast for those who persecute you. For what reward "
        "is there for loving those who love you? Do not the Gentiles do the same? But "
        "love those who hate you, and you shall not have an enemy.",
 "1.4": "Abstain from fleshly and worldly lusts. If someone strikes your right cheek, "
        "turn to him the other also, and you shall be perfect. If someone impresses you "
        "for one mile, go with him two. If someone takes your cloak, give him also your "
        "coat. If someone takes from you what is yours, ask it not back, for indeed you "
        "are not able.",
 "1.5": "Give to every one who asks you, and ask it not back; for the Father wills that "
        "to all should be given of our own blessings. Happy is he who gives according to "
        "the commandment, for he is guiltless. Woe to him who receives; for if one "
        "receives who has need, he is guiltless; but he who receives not having need "
        "shall pay the penalty, why he received and for what. And coming into "
        "confinement, he shall be examined concerning the things which he has done, and "
        "he shall not escape from there until he pays back the last penny.",
 "1.6": "And also concerning this, it has been said: Let your alms sweat in your hands, "
        "until you know to whom you should give.",
}

# group tokens by verse, preserving order
verses = {}
for w in words:
    verses.setdefault(w["ref"], []).append(w)

hit = sum(1 for w in words if w.get("strongs"))
stats = f"{len(words)} words &middot; {hit} matched Strong&rsquo;s &middot; {len(words)-hit} no-Strong&rsquo;s"

blocks = []
for ref, toks in verses.items():
    eng = ENGLISH.get(ref, "")
    chips = []
    for i, w in enumerate(toks):
        miss = not w.get("strongs")
        gid = f"{ref}-{i}"
        chips.append(
            f'<div class="chip{" miss" if miss else ""}" '
            f'data-gk="{w["greek"]}" data-lem="{w["lemma"]}" '
            f'data-sg="{w.get("strongs") or ""}" data-en="{w["gloss"]}">'
            f'<span class="gk">{w["greek"]}</span>'
            f'<span class="en">{w["gloss"]}</span>'
            f'<span class="sg">{w.get("strongs") or "—"}</span></div>'
        )
    label = "Title" if ref == "0.1" else ref
    blocks.append(
        f'<div class="verse"><div class="vref">{label}</div>'
        f'<div class="vbody"><p class="eng">{eng}</p>'
        f'<div class="chips">{"".join(chips)}</div></div></div>'
    )

HTML = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Didache 1 — reading + interlinear</title>
<style>
 :root{{ --ink:#221e18; --ink-2:#4a4338; --paper:#faf7f1; --line:#e3ddd0;
        --gold:#b8860b; --gold-bg:#fff7e0; --miss:#b04a3a; }}
 *{{ box-sizing:border-box; }}
 body{{ margin:0; background:var(--paper); color:var(--ink);
       font:16px/1.6 Georgia, serif; }}
 .wrap{{ max-width:900px; margin:0 auto; padding:28px 22px 90px; }}
 h1{{ font-size:22px; margin:0 0 2px; }}
 .sub{{ color:var(--ink-2); font-size:13px; margin:0 0 6px; font-family:system-ui,sans-serif; }}
 .stats{{ color:var(--ink-2); font-size:12px; margin:0 0 18px; font-family:system-ui,sans-serif; }}
 .bar{{ display:flex; gap:8px; margin:0 0 22px; font-family:system-ui,sans-serif; }}
 .bar button{{ border:1px solid var(--line); background:#fff; color:var(--ink);
       padding:6px 14px; border-radius:6px; cursor:pointer; font-size:13px; }}
 .bar button.on{{ background:var(--ink); color:#fff; border-color:var(--ink); }}

 .verse{{ display:flex; gap:14px; padding:14px 0; border-top:1px solid var(--line); }}
 .vref{{ flex:0 0 38px; color:var(--gold); font-family:system-ui,sans-serif;
        font-size:12px; padding-top:3px; }}
 .vbody{{ flex:1 1 auto; }}
 .eng{{ margin:0 0 10px; font-size:18px; line-height:1.7; }}
 .chips{{ display:flex; flex-wrap:wrap; gap:5px; }}
 .chip{{ border:1px solid var(--line); border-radius:7px; background:#fff;
        padding:4px 8px 5px; text-align:center; cursor:pointer; min-width:40px; }}
 .chip:hover{{ border-color:var(--gold); background:var(--gold-bg); }}
 .chip .gk{{ font-size:16px; display:block; }}
 .chip .en{{ font-size:10px; color:var(--ink-2); display:block; font-family:system-ui,sans-serif; }}
 .chip .sg{{ font-size:9px; color:var(--gold); display:block; font-family:system-ui,sans-serif; }}
 .chip.miss .sg{{ color:var(--miss); }}

 /* mode toggles via body class */
 body.reading .chips{{ display:none; }}
 body.reading .eng{{ font-size:19px; }}
 body.chipsonly .eng{{ display:none; }}

 #det{{ position:fixed; right:0; top:0; height:100%; width:280px; background:#fff;
       border-left:1px solid var(--line); padding:22px 20px; transform:translateX(100%);
       transition:transform .15s; font-family:system-ui,sans-serif; }}
 #det.show{{ transform:none; }}
 #det .gk{{ font:26px Georgia, serif; }}
 #det .lem{{ color:var(--ink-2); margin:2px 0 14px; }}
 #det .row{{ display:flex; justify-content:space-between; padding:7px 0;
       border-top:1px solid var(--line); font-size:14px; }}
 #det .row span:first-child{{ color:var(--ink-2); }}
 #det .sgval{{ color:var(--gold); font-weight:600; }}
 #det .sgval.miss{{ color:var(--miss); }}
 #det .x{{ position:absolute; top:12px; right:14px; cursor:pointer; color:var(--ink-2); }}
</style></head><body class="parallel">
<div class="wrap">
 <h1>Didache 1 — the Two Ways</h1>
 <p class="sub">English = Roberts-Donaldson (public domain) &middot; Greek = corrected Lake text
    (Tauber, CC&#8209;BY&#8209;SA) &middot; click any Greek word.</p>
 <p class="stats">{stats}</p>
 <div class="bar">
   <button data-mode="reading" onclick="setMode('reading')">Reading</button>
   <button data-mode="parallel" class="on" onclick="setMode('parallel')">English + interlinear</button>
   <button data-mode="chipsonly" onclick="setMode('chipsonly')">Interlinear only</button>
 </div>
 {"".join(blocks)}
</div>
<div id="det">
 <span class="x" onclick="hide()">&times;</span>
 <div class="gk" id="dGk"></div><div class="lem" id="dLem"></div>
 <div class="row"><span>Strong&rsquo;s</span><span class="sgval" id="dSg"></span></div>
 <div class="row"><span>Meaning</span><span id="dEn"></span></div>
 <div class="row"><span>Dictionary form</span><span id="dLem2"></span></div>
</div>
<script>
 function setMode(m){{ document.body.className=m;
   document.querySelectorAll('.bar button').forEach(b=>
     b.classList.toggle('on', b.dataset.mode===m)); }}
 document.querySelectorAll('.chip').forEach(c=>c.onclick=()=>{{
   const d=c.dataset, miss=!d.sg;
   dGk.textContent=d.gk; dLem.textContent=d.lem+' (dictionary form)';
   dSg.textContent=d.sg||'no Strong\\u2019s'; dSg.className='sgval'+(miss?' miss':'');
   dEn.textContent=d.en; dLem2.textContent=d.lem;
   document.getElementById('det').classList.add('show');
 }});
 function hide(){{ document.getElementById('det').classList.remove('show'); }}
</script></body></html>"""

out = HERE / "didache_ch1_proof.html"
out.write_text(HTML, encoding="utf-8")
print(f"wrote {out}  ({len(words)} words, {hit} tagged)")
