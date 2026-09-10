/*
 * render_svg.js — Rendu headless de fichiers SVG en PNG via Chromium (Playwright global).
 *
 * Usage :
 *   set NPM_GLOBAL_ROOT=%CD% (ou : $env:NPM_GLOBAL_ROOT = (npm root -g).Trim())
 *   node render_svg.js --src "<dossier_svg>" --out "<dossier_sortie>" --files "a.svg,b.svg"
 *
 * Si --files est omis, tous les *.svg du dossier --src sont rendus.
 * Prérequis : `playwright` installé globalement (npm root -g) + Chromium (ms-playwright).
 */
const path = require('path');
const fs = require('fs');

function arg(name, def) {
  const i = process.argv.indexOf('--' + name);
  return i !== -1 && process.argv[i + 1] ? process.argv[i + 1] : def;
}

const SRC = arg('src');
const OUT = arg('out');
const FILES_ARG = arg('files');
const SCALE = parseInt(arg('scale', '2'), 10);

if (!SRC || !OUT) {
  console.error('ERREUR : --src et --out sont obligatoires.');
  process.exit(1);
}

const gr = process.env.NPM_GLOBAL_ROOT;
if (!gr) {
  console.error('ERREUR : variable NPM_GLOBAL_ROOT non définie (chemin de `npm root -g`).');
  process.exit(1);
}
const { chromium } = require(path.join(gr, 'playwright'));

fs.mkdirSync(OUT, { recursive: true });

const files = FILES_ARG
  ? FILES_ARG.split(',').map((f) => f.trim()).filter(Boolean)
  : fs.readdirSync(SRC).filter((f) => f.toLowerCase().endsWith('.svg'));

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ deviceScaleFactor: SCALE });
  for (const name of files) {
    const svgPath = path.join(SRC, name);
    const svg = fs.readFileSync(svgPath, 'utf8');
    await page.setContent(
      '<!DOCTYPE html><html><body style="margin:0;display:inline-block">' + svg + '</body></html>'
    );
    const el = await page.$('svg');
    if (!el) {
      console.error('SKIP (pas de <svg>) :', name);
      continue;
    }
    const outPng = path.join(OUT, path.basename(name, path.extname(name)) + '.png');
    await el.screenshot({ path: outPng });
    console.log('OK', outPng);
  }
  await browser.close();
})();
