// Deterministische Screenshots für den UI-Polish-Loop.
//
//   node shoot.mjs <config.json> <ausgabeordner> [--holdout] [--only <regex>]
//
// Benötigt playwright-core (npm i playwright-core) und einen lokalen Chrome.
// Ohne --holdout werden Ansichten mit "holdout": true übersprungen, mit
// --holdout zusätzlich aufgenommen.
//
// Beispielkonfiguration (docs/design-review/shots.config.json):
// {
//   "baseUrl": "http://localhost:5173",
//   "fixedTime": "today@10:40",            // oder ISO-Zeitpunkt; hält Jetzt-Linien stabil
//   "timezone": "Europe/Berlin",
//   "locale": "de-DE",
//   "deviceScaleFactor": 2,
//   "settleMs": 1200,
//   "hideSelectors": ["[data-testpanel]"],  // Entwicklerpanels ausblenden
//   "viewports": { "desktop": [1440, 900], "mobile": [390, 844], "tablet": [1024, 768] },
//   "shots": [
//     { "name": "f01-uebersicht", "path": "/dashboard?demo=filiale", "viewport": "desktop" },
//     { "name": "f02-kalender", "path": "/dashboard/calendar?demo=filiale", "viewport": "desktop", "fullPage": false },
//     { "name": "m-k01-entdecken-2", "path": "/customer?demo=kunde", "viewport": "mobile", "scrollTo": "h2:nth-of-type(2)" },
//     { "name": "h01-uebersicht-1024", "path": "/dashboard?demo=filiale", "viewport": "tablet", "holdout": true }
//   ]
// }
import fs from 'node:fs'
import { chromium } from 'playwright-core'

const args = process.argv.slice(2)
const [configPath, out] = args
if (!configPath || !out) {
  console.error('Aufruf: node shoot.mjs <config.json> <ausgabeordner> [--holdout] [--only <regex>]')
  process.exit(2)
}
const mitHoldout = args.includes('--holdout')
const onlyIndex = args.indexOf('--only')
const only = onlyIndex > -1 ? new RegExp(args[onlyIndex + 1]) : null
const cfg = JSON.parse(fs.readFileSync(configPath, 'utf8'))
fs.mkdirSync(out, { recursive: true })

function festeZeit(wert) {
  if (!wert) return null
  const heute = /^today@(\d{2}):(\d{2})$/.exec(wert)
  if (!heute) return new Date(wert)
  const d = new Date()
  d.setHours(Number(heute[1]), Number(heute[2]), 0, 0)
  return d
}

const zeit = festeZeit(cfg.fixedTime)
const browser = await chromium.launch({ channel: cfg.channel ?? 'chrome', headless: true })
let fehler = 0
for (const shot of cfg.shots) {
  if (shot.holdout && !mitHoldout) continue
  if (only && !only.test(shot.name)) continue
  const [width, height] = cfg.viewports[shot.viewport]
  const ctx = await browser.newContext({
    viewport: { width, height },
    deviceScaleFactor: cfg.deviceScaleFactor ?? 2,
    locale: cfg.locale,
    timezoneId: cfg.timezone,
  })
  const page = await ctx.newPage()
  if (zeit) await page.clock.setFixedTime(zeit)
  try {
    await page.goto(`${cfg.baseUrl}${shot.path}`, { waitUntil: 'networkidle' })
  } catch (e) {
    console.error(`${shot.name}: Laden fehlgeschlagen (${e.message})`)
    fehler++
  }
  await page.waitForTimeout(cfg.settleMs ?? 1200)
  if (cfg.hideSelectors?.length) {
    await page.addStyleTag({ content: `${cfg.hideSelectors.join(',')}{display:none!important}` })
  }
  if (shot.scrollTo) {
    await page.evaluate(selektor => {
      const el = document.querySelector(selektor)
      const kopf = document.querySelector('header')?.getBoundingClientRect().height ?? 0
      if (el) window.scrollTo(0, el.getBoundingClientRect().top + window.scrollY - kopf - 24)
    }, shot.scrollTo)
  }
  await page.waitForTimeout(300)
  const datei = `${out}/${shot.name}.png`
  await page.screenshot({ path: datei, fullPage: shot.fullPage ?? !shot.scrollTo })
  console.log(datei)
  await ctx.close()
}
await browser.close()
process.exit(fehler ? 1 : 0)
