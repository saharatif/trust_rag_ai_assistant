import puppeteer from 'puppeteer';

const BASE = 'http://localhost:5174';
const OUT  = new URL('.', import.meta.url).pathname;

const pages = [
  { name: 'chat',    path: '/'       },
  { name: 'ingest',  path: '/ingest' },
  { name: 'review',  path: '/review' },
];

const browser = await puppeteer.launch({ args: ['--no-sandbox'] });
const page    = await browser.newPage();
await page.setViewport({ width: 1400, height: 900 });

for (const { name, path } of pages) {
  await page.goto(`${BASE}${path}`, { waitUntil: 'networkidle0', timeout: 15000 });
  await page.screenshot({ path: `${OUT}${name}.png`, fullPage: false });
  console.log(`✓ ${name}.png`);
}

await browser.close();
