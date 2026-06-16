#!/usr/bin/env node
/*
 * gen-icons.js — rasterize the Lexica logo into every icon the site needs.
 *
 * Source: a single square SVG (navy book + gold cross). Outputs into static/:
 *   favicon.svg           the source SVG itself (modern browsers, scalable)
 *   favicon.ico           16/32/48 multi-size, legacy + Google search result
 *   apple-touch-icon.png  180x180, iOS home-screen
 *   icon-192.png          Android / PWA manifest
 *   icon-512.png          Android / PWA manifest (splash)
 *   og.png                1200x630 social-share preview (navy + mark + wordmark)
 *
 * Run once (re-run only if the logo changes). Needs sharp + png-to-ico, which
 * are NOT permanent deps — install transiently:
 *   npm install sharp png-to-ico --no-save && node scripts/gen-icons.js [logo.svg]
 */
const fs = require("fs");
const path = require("path");
const sharp = require("sharp");
const pngToIco = require("png-to-ico").default || require("png-to-ico");

const NAVY = "#1a1a2e";
const GOLD = "#c9a84c";
const CREAM = "#f0e9d8";

const SRC = process.argv[2] || path.join(process.env.USERPROFILE || "", "Downloads", "logo.svg");
const OUT = path.join(__dirname, "..", "static");
const svgBuf = fs.readFileSync(SRC);

// Render the source SVG to a square PNG buffer at the given pixel size.
// density oversamples the vector so downscales stay crisp.
const png = (size) => sharp(svgBuf, { density: 384 }).resize(size, size).png().toBuffer();

// The two mark paths (book outline + cross), in the source viewBox coords.
const MARK = `
  <path d="M5 4.5A2.5 2.5 0 0 1 7.5 2H19v17H7.5a2.5 2.5 0 0 0 0 5H19v-3"
        stroke="${GOLD}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
  <path d="M11 8v4M13 10h-4" stroke="${GOLD}" stroke-width="1.4" stroke-linecap="round"/>`;

// The mark + wordmark lockup, laid out only RELATIVE to each other (mark left,
// "Lexica" beside it, tagline under it). We render this with a transparent
// background, auto-crop to the real ink, then drop it dead-center on the navy
// canvas — so we never have to guess text widths to center it.
const LOCKUP = `<svg width="1500" height="420" viewBox="0 0 1500 420" xmlns="http://www.w3.org/2000/svg">
  <svg x="0" y="50" width="320" height="320" viewBox="-2 -1 28 28">${MARK}</svg>
  <text x="295" y="262" font-family="Georgia, 'Times New Roman', serif" font-size="175"
        font-weight="600" fill="${CREAM}">Lexica</text>
  <text x="298" y="330" font-family="Georgia, 'Times New Roman', serif" font-size="46"
        fill="${GOLD}">Greek &amp; Hebrew Bible word study</text>
</svg>`;

(async () => {
  fs.writeFileSync(path.join(OUT, "favicon.svg"), svgBuf);

  fs.writeFileSync(path.join(OUT, "apple-touch-icon.png"), await png(180));
  fs.writeFileSync(path.join(OUT, "icon-192.png"), await png(192));
  fs.writeFileSync(path.join(OUT, "icon-512.png"), await png(512));

  const icoSizes = await Promise.all([16, 32, 48].map(png));
  fs.writeFileSync(path.join(OUT, "favicon.ico"), await pngToIco(icoSizes));

  // Render lockup, crop to the actual ink, scale to fit, center on navy.
  const lockup = await sharp(Buffer.from(LOCKUP), { density: 200 })
    .trim()
    .resize({ width: 900, fit: "inside", withoutEnlargement: false })
    .png()
    .toBuffer();
  const og = await sharp({
    create: { width: 1200, height: 630, channels: 4, background: NAVY },
  })
    .composite([{ input: lockup, gravity: "center" }])
    .png()
    .toBuffer();
  fs.writeFileSync(path.join(OUT, "og.png"), og);

  console.log("icons written to", OUT);
})().catch((e) => { console.error(e); process.exit(1); });
