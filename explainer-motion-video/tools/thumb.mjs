// node tools/thumb.mjs A B   — calls window.thumb(k) defined in src/thumb.js (loaded by src/thumb.html), saves _thumb_<k>.png (1920x1080)
// then: python3 -c "from PIL import Image; Image.open('_thumb_A.png').convert('RGB').resize((1280,720), Image.LANCZOS).save('thumb_A.jpg', quality=92)"
import fs from 'fs'; import path from 'path'; import { openPage } from './_server.mjs';
const { pg, close } = await openPage(path.resolve(process.env.SRC || 'src'), 8779, 'thumb.html');
for (const k of process.argv.slice(2).length ? process.argv.slice(2) : ['A']) { const d = await pg.evaluate(k => window.thumb(k), k); fs.writeFileSync(`_thumb_${k}.png`, Buffer.from(d.split(',')[1], 'base64')); console.log('thumb', k); }
await close();
