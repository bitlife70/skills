// node tools/render.mjs      env: SRC=src PAGE=index.html OUT=_scenes ONLY=D1,D2 P=<worker number for port>
// Renders each scene to OUT/<id>.mp4 (30fps, x264 veryfast crf18). Existing files are skipped → delete only changed scenes to re-render.
import fs from 'fs'; import path from 'path'; import { spawn } from 'child_process'; import { openPage } from './_server.mjs';
const root = path.resolve(process.env.SRC || 'src'), out = path.resolve(process.env.OUT || '_scenes'); fs.mkdirSync(out, { recursive: true });
const { pg, close } = await openPage(root, 8800 + Number(process.env.P || 0), process.env.PAGE || 'index.html');
const scenes = await pg.evaluate(() => window.SC.map(s => [s.id, s.dur]));
const want = (process.env.ONLY || '').split(',').filter(Boolean);
for (const [id, dur] of scenes) {
  if (want.length && !want.includes(id)) continue;
  const fn = `${out}/${id}.mp4`; if (fs.existsSync(fn)) { console.log('skip', id); continue; }
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', '30', '-c:v', 'mjpeg', '-i', '-', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', '-pix_fmt', 'yuv420p', fn + '.tmp.mp4']);
  const N = Math.round(dur * 30); const t0 = Date.now();
  for (let f = 0; f < N; f++) {
    const d = await pg.evaluate(([id, t]) => { const s = window.SC.find(x => x.id === id); drawScene(s, t); return document.getElementById('c').toDataURL('image/jpeg', .92); }, [id, f / 30]);
    const buf = Buffer.from(d.slice(d.indexOf(',') + 1), 'base64'); if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
  }
  ff.stdin.end(); await new Promise(r => ff.on('close', r)); fs.renameSync(fn + '.tmp.mp4', fn);
  console.log('scene', id, N, ((Date.now() - t0) / 1000).toFixed(0) + 's');
}
await close(); console.log('DONE');
