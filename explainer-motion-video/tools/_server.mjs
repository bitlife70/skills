// shared: static server for the project's src/ folder + playwright page
import http from 'http'; import fs from 'fs'; import path from 'path';
import { createRequire } from 'module';
const require = createRequire(import.meta.url);
export async function loadPlaywright() {
  for (const p of [process.env.PLAYWRIGHT_PATH, '/opt/npm-tools/node_modules/playwright/index.mjs', 'playwright']) {
    if (!p) continue; try { return await import(p); } catch (e) { }
  }
  throw new Error('playwright not found — set PLAYWRIGHT_PATH');
}
export function serve(root, port) {
  return http.createServer((q, r) => { const p = path.join(root, decodeURIComponent(q.url.split('?')[0])); if (!fs.existsSync(p) || fs.statSync(p).isDirectory()) { r.writeHead(404); r.end(); return; }
    const ext = path.extname(p); r.writeHead(200, { 'Content-Type': { '.html': 'text/html', '.js': 'text/javascript', '.woff2': 'font/woff2' }[ext] || 'application/octet-stream' }); fs.createReadStream(p).pipe(r); }).listen(port);
}
export async function openPage(root, port, page) {
  const { chromium } = await loadPlaywright();
  const srv = serve(root, port); const b = await chromium.launch(); const pg = await b.newPage({ viewport: { width: 1920, height: 1080 } });
  pg.on('pageerror', e => console.log('ERR', e.message)); pg.on('console', m => { if (m.type() === 'error') console.log('CONSOLE', m.text()); });
  await pg.goto(`http://localhost:${port}/${page}`); await pg.waitForFunction(() => window.ready, null, { timeout: 30000 });
  return { pg, close: async () => { await b.close(); srv.close(); } };
}
