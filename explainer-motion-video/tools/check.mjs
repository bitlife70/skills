// node tools/check.mjs verify|stills|all '[["D1",8.5],...]' [outdir]     (run from the project root; env SRC=src PAGE=index.html ONLY=D1,D2)
import fs from 'fs'; import path from 'path'; import { openPage } from './_server.mjs';
const root = path.resolve(process.env.SRC || 'src'); const { pg, close } = await openPage(root, 8771, process.env.PAGE || 'index.html');
const mode = process.argv[2] || 'verify';
if (mode === 'verify' || mode === 'all') {
  const only = process.env.ONLY ? process.env.ONLY.split(',') : null;
  const issues = await pg.evaluate(o => window.verifyAll(0.25, o || undefined), only);
  console.log(issues.length ? issues.join('\n') : 'VERIFY OK');
}
if (mode === 'stills' || mode === 'all') {
  const shots = JSON.parse(process.argv[3] || '[]'); const out = process.argv[4] || '_stills'; fs.mkdirSync(out, { recursive: true });
  for (const [id, t] of shots) { const d = await pg.evaluate(([id, t]) => window.still(id, t), [id, t]); fs.writeFileSync(`${out}/${id}_${t}.png`, Buffer.from(d.split(',')[1], 'base64')); }
  console.log('stills', shots.length, '→', out);
}
await close();
