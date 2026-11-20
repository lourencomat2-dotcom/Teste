// Renderiza a cena three.js quadro a quadro (sem GPU: Chromium + SwiftShader) e junta com o áudio.
//   node tempo_real/capturar.js [saida.mp4] [quadros...]   (com números: salva só esses quadros em PNG)
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const http = require('http'), fs = require('fs'), path = require('path');
const DIR = __dirname;
const TIPOS = { '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json', '.png': 'image/png', '.glb': 'model/gltf-binary', '.wav': 'audio/wav' };
const srv = http.createServer((q, r) => {
  const p = path.join(DIR, decodeURIComponent(q.url.split('?')[0]));
  if (!p.startsWith(DIR) || !fs.existsSync(p) || fs.statSync(p).isDirectory()) { r.writeHead(404); return r.end(); }
  r.writeHead(200, { 'Content-Type': TIPOS[path.extname(p)] || 'application/octet-stream' }); fs.createReadStream(p).pipe(r);
}).listen(0);
(async () => {
  const saida = process.argv[2] || path.join(DIR, '..', 'saida', 'abertura_threejs.mp4');
  const so = process.argv.slice(3).map(Number);
  const b = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const pg = await b.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
  pg.on('console', m => console.log('[pág]', m.text())); pg.on('pageerror', e => console.log('[erro]', e.message));
  await pg.goto(`http://localhost:${srv.address().port}/index.html?captura${process.env.PARAMS || ''}`);
  await pg.waitForFunction('window.pronto === true', null, { timeout: 90000 });
  const { DUR, FPS } = await pg.evaluate(() => ({ DUR: window.DUR, FPS: window.FPS }));
  const n = Math.floor(DUR * FPS);
  const t0 = Date.now();
  if (so.length) {
    for (let f = 0; f <= Math.max(...so); f++) {
      if (!so.includes(f)) { await pg.evaluate(f => window.simular(f), f); continue; }
      await pg.evaluate(f => window.renderizar(f), f);
      { await pg.screenshot({ path: path.join(path.dirname(saida), `rt_${f}.png`) }); console.log('quadro', f); }
    }
  } else {
    fs.mkdirSync(path.dirname(saida), { recursive: true });
    const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-i', '-',
      '-i', path.join(DIR, 'dados', 'audio.wav'), '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-preset', 'medium', '-crf', '18',
      '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-shortest', saida], { stdio: ['pipe', 'inherit', 'inherit'] });
    for (let f = 0; f < n; f++) {
      await pg.evaluate(f => window.renderizar(f), f);
      const img = await pg.screenshot({ type: 'jpeg', quality: 95 });
      if (!ff.stdin.write(img)) await new Promise(ok => ff.stdin.once('drain', ok));
      if (f % 30 === 0) console.log(`quadro ${f}/${n} · ${((Date.now() - t0) / 1000 / (f + 1)).toFixed(2)} s/quadro`);
    }
    ff.stdin.end(); await new Promise(ok => ff.on('close', ok));
    console.log('pronto:', saida);
  }
  await b.close(); srv.close();
})();
