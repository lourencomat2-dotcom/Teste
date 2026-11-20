// Cenário de sitcom: texturas pintadas em canvas (no Blender eram nós ou cores lisas) e luz de estúdio.
// Cada material do GLB é reconhecido pelo nome (ver motor/cena3d.py, função sala()).
import * as THREE from 'three';

const clamp = (v, a, b) => Math.min(b, Math.max(a, v));
const lin = (r, g, b) => new THREE.Color().setRGB(r / 255, g / 255, b / 255, THREE.SRGBColorSpace);
let semente = 11; const rnd = () => (semente = (semente * 16807) % 2147483647) / 2147483647;
const rgb = (c, k = 1, a = 1) => `rgba(${c.map(v => clamp(Math.round(v * k), 0, 255)).join(',')},${a})`;

export function tela(w, h, desenha) {
  const c = document.createElement('canvas'); c.width = w; c.height = h; desenha(c.getContext('2d'), w, h);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.wrapS = t.wrapT = THREE.RepeatWrapping;
  t.anisotropy = 8; return t;
}
function manchas(g, w, h, n, cores, r0, r1, alfa) {
  for (let i = 0; i < n; i++) {
    g.fillStyle = rgb(cores[Math.floor(rnd() * cores.length)], 1, alfa * rnd());
    const r = r0 + rnd() * (r1 - r0); g.beginPath(); g.ellipse(rnd() * w, rnd() * h, r, r * (0.6 + rnd() * 0.8), rnd() * 3, 0, 7); g.fill();
  }
}

// ------------------------------------------------------------------ texturas que se repetem (metros por textura)
// ladrilho hidráulico 30 cm, tons suaves (a textura tem 2 x 2 ladrilhos): círculos nas quinas + losango no meio
const LADRILHO = tela(512, 512, (g, w) => {
  const s = w / 2, base = [240, 232, 214], terra = [204, 140, 112], verde = [112, 146, 142];
  for (let i = 0; i < 2; i++) for (let j = 0; j < 2; j++) {
    const x0 = i * s, y0 = j * s;
    g.fillStyle = rgb(base); g.fillRect(x0, y0, s, s);
    g.save(); g.beginPath(); g.rect(x0, y0, s, s); g.clip();
    for (const [cx, cy] of [[x0, y0], [x0 + s, y0], [x0, y0 + s], [x0 + s, y0 + s]]) {
      g.fillStyle = rgb(terra); g.beginPath(); g.arc(cx, cy, s * 0.34, 0, 7); g.fill();
      g.fillStyle = rgb(base); g.beginPath(); g.arc(cx, cy, s * 0.27, 0, 7); g.fill();
      g.fillStyle = rgb(verde); g.beginPath(); g.arc(cx, cy, s * 0.09, 0, 7); g.fill();
    }
    g.restore();
    const cx = x0 + s / 2, cy = y0 + s / 2, d = s * 0.14;
    g.fillStyle = rgb(verde); g.beginPath(); g.moveTo(cx, cy - d); g.lineTo(cx + d, cy); g.lineTo(cx, cy + d); g.lineTo(cx - d, cy); g.fill();
    g.strokeStyle = rgb([206, 196, 176]); g.lineWidth = 3; g.strokeRect(x0 + 1.5, y0 + 1.5, s - 3, s - 3);
  }
  manchas(g, w, w, 500, [[255, 250, 240], [120, 90, 70]], 2, 14, 0.05);
});
LADRILHO.userData.metros = [0.6, 0.6];
const PAREDE = tela(1024, 1024, (g, w, h) => {      // amarelo-manteiga com leve textura de pintura
  g.fillStyle = rgb([247, 224, 158]); g.fillRect(0, 0, w, h);
  manchas(g, w, h, 3200, [[240, 212, 142], [252, 234, 178]], 3, 16, 0.12);
});
PAREDE.userData.metros = [2.5, 2.5];
const LAMBRI = tela(512, 64, (g, w, h) => {          // ripas de 15 cm, brancas
  const n = 4, s = w / n;
  for (let i = 0; i < n; i++) {
    g.fillStyle = rgb(i % 2 ? [250, 246, 236] : [245, 240, 228]); g.fillRect(i * s, 0, s, h);
    const gr = g.createLinearGradient(i * s, 0, i * s + s, 0);
    gr.addColorStop(0, 'rgba(255,255,255,0.3)'); gr.addColorStop(0.5, 'rgba(255,255,255,0)'); gr.addColorStop(1, 'rgba(0,0,0,0.05)');
    g.fillStyle = gr; g.fillRect(i * s, 0, s, h);
    g.fillStyle = rgb([206, 196, 176]); g.fillRect(i * s, 0, 6, h);
  }
});
LAMBRI.userData.metros = [0.6, 0.6];
const AZULEJO = tela(512, 512, (g, w) => {           // azulejo: decorado azul intercalado com branco liso, 15 cm
  const s = w / 2, azul = [64, 104, 172];
  for (let i = 0; i < 2; i++) for (let j = 0; j < 2; j++) {
    const x0 = i * s, y0 = j * s, cx = x0 + s / 2, cy = y0 + s / 2;
    g.fillStyle = rgb([246, 247, 250]); g.fillRect(x0, y0, s, s);
    if ((i + j) % 2 === 0) {
      g.strokeStyle = rgb(azul); g.lineWidth = s * 0.025; g.beginPath(); g.arc(cx, cy, s * 0.28, 0, 7); g.stroke();
      g.fillStyle = rgb(azul);
      for (let k = 0; k < 4; k++) {
        const a = k * Math.PI / 2;
        g.beginPath(); g.ellipse(cx + Math.cos(a) * s * 0.13, cy + Math.sin(a) * s * 0.13, s * 0.1, s * 0.045, a, 0, 7); g.fill();
      }
      g.beginPath(); g.arc(cx, cy, s * 0.045, 0, 7); g.fill();
    } else {
      g.fillStyle = rgb(azul, 1, 0.8);
      for (const [qx, qy] of [[x0, y0], [x0 + s, y0], [x0, y0 + s], [x0 + s, y0 + s]]) { g.beginPath(); g.arc(qx, qy, s * 0.07, 0, 7); g.fill(); }
    }
    g.strokeStyle = rgb([214, 218, 226]); g.lineWidth = 4; g.strokeRect(x0 + 2, y0 + 2, s - 4, s - 4);
  }
});
AZULEJO.userData.metros = [0.3, 0.3];
const XADREZ = tela(256, 256, (g, w) => {            // toalha xadrez vermelha e branca
  g.fillStyle = rgb([252, 250, 246]); g.fillRect(0, 0, w, w);
  const n = 8, s = w / n;
  for (let k = 0; k < n; k += 2) {
    g.fillStyle = rgb([214, 52, 52], 1, 0.55); g.fillRect(k * s, 0, s, w); g.fillRect(0, k * s, w, s);
  }
  manchas(g, w, w, 300, [[255, 255, 255], [120, 30, 30]], 1, 4, 0.08);
});
XADREZ.userData.metros = [0.2, 0.2];
const PAPEL_CORREDOR = tela(512, 512, (g, w) => {   // papel de parede listrado do corredor
  g.fillStyle = rgb([196, 214, 222]); g.fillRect(0, 0, w, w);
  for (let k = 0; k < 8; k++) { g.fillStyle = rgb([222, 234, 238]); g.fillRect(k * w / 8, 0, w / 16, w); g.fillStyle = rgb([170, 192, 204]); g.fillRect(k * w / 8 + w / 16, 0, 2, w); }
});
PAPEL_CORREDOR.userData.metros = [0.6, 0.6];
function madeira(c0, c1, c2) {
  return tela(1024, 1024, (g, w, h) => {
    g.fillStyle = rgb(c0); g.fillRect(0, 0, w, h);
    for (let i = 0; i < 260; i++) {
      g.strokeStyle = rgb(rnd() < 0.5 ? c1 : c2, 1, 0.35 * rnd()); g.lineWidth = 1 + rnd() * 5;
      const y = rnd() * h; g.beginPath(); g.moveTo(0, y);
      g.bezierCurveTo(w * 0.3, y + (rnd() - 0.5) * 20, w * 0.7, y + (rnd() - 0.5) * 20, w, y); g.stroke();
    }
  });
}
const MADEIRA = madeira([149, 103, 71], [136, 92, 62], [168, 120, 84]); MADEIRA.userData.metros = [1.2, 1.2];
const MADEIRA_CLARA = madeira([190, 142, 98], [172, 124, 84], [206, 160, 116]); MADEIRA_CLARA.userData.metros = [1.0, 1.0];

// ------------------------------------------------------------------ pinturas (decalques: 0..1 na face)
const QUADRO_PAISAGEM = tela(900, 650, (g, w, h) => {      // praia com morro, sol e barquinho
  let gr = g.createLinearGradient(0, 0, 0, h * 0.55); gr.addColorStop(0, rgb([120, 186, 232])); gr.addColorStop(1, rgb([255, 214, 160]));
  g.fillStyle = gr; g.fillRect(0, 0, w, h);
  g.fillStyle = rgb([255, 236, 150]); g.beginPath(); g.arc(w * 0.72, h * 0.3, h * 0.09, 0, 7); g.fill();
  g.fillStyle = rgb([92, 150, 96]); g.beginPath(); g.moveTo(0, h * 0.6); g.quadraticCurveTo(w * 0.18, h * 0.18, w * 0.38, h * 0.6); g.fill();
  g.fillStyle = rgb([70, 128, 84]); g.beginPath(); g.moveTo(w * 0.22, h * 0.6); g.quadraticCurveTo(w * 0.32, h * 0.36, w * 0.5, h * 0.6); g.fill();
  gr = g.createLinearGradient(0, h * 0.55, 0, h * 0.8); gr.addColorStop(0, rgb([60, 146, 186])); gr.addColorStop(1, rgb([110, 190, 210]));
  g.fillStyle = gr; g.fillRect(0, h * 0.58, w, h * 0.24);
  g.fillStyle = rgb([240, 214, 160]); g.beginPath(); g.moveTo(0, h); g.lineTo(0, h * 0.8); g.quadraticCurveTo(w * 0.5, h * 0.74, w, h * 0.82); g.lineTo(w, h); g.fill();
  g.fillStyle = rgb([250, 250, 246]); g.beginPath(); g.moveTo(w * 0.6, h * 0.66); g.lineTo(w * 0.66, h * 0.66); g.lineTo(w * 0.63, h * 0.48); g.fill();
  g.fillStyle = rgb([150, 80, 60]); g.fillRect(w * 0.58, h * 0.66, w * 0.1, h * 0.025);
  g.strokeStyle = rgb([96, 70, 50]); g.lineWidth = 9; g.beginPath(); g.moveTo(w * 0.86, h * 0.95); g.quadraticCurveTo(w * 0.83, h * 0.7, w * 0.88, h * 0.52); g.stroke();
  g.fillStyle = rgb([60, 130, 70]);
  for (const a of [-2.6, -2.0, -1.2, -0.5, 0.1]) { g.beginPath(); g.ellipse(w * 0.88 + Math.cos(a) * 46, h * 0.52 + Math.sin(a) * 22, 52, 12, a, 0, 7); g.fill(); }
  manchas(g, w, h, 900, [[255, 255, 255], [60, 40, 30]], 2, 9, 0.05);
});
const QUADRO_FLORES = tela(700, 500, (g, w, h) => {        // natureza-morta: vaso com flores
  g.fillStyle = rgb([214, 168, 96]); g.fillRect(0, 0, w, h);
  manchas(g, w, h, 600, [[230, 190, 120], [190, 140, 80]], 8, 30, 0.12);
  g.fillStyle = rgb([120, 80, 60]); g.fillRect(0, h * 0.78, w, h * 0.22);
  g.fillStyle = rgb([60, 96, 150]); g.beginPath(); g.ellipse(w / 2, h * 0.68, w * 0.09, h * 0.14, 0, 0, 7); g.fill();
  g.fillRect(w / 2 - w * 0.04, h * 0.48, w * 0.08, h * 0.1);
  const cores = [[230, 70, 80], [250, 200, 70], [250, 250, 245], [220, 110, 160], [240, 140, 60]];
  for (let k = 0; k < 9; k++) {
    const a = -Math.PI / 2 + (k - 4) * 0.28, r = h * (0.25 + 0.06 * (k % 3));
    const fx = w / 2 + Math.cos(a) * r, fy = h * 0.5 + Math.sin(a) * r;
    g.strokeStyle = rgb([70, 120, 70]); g.lineWidth = 4; g.beginPath(); g.moveTo(w / 2, h * 0.5); g.lineTo(fx, fy); g.stroke();
    g.fillStyle = rgb(cores[k % cores.length]); g.beginPath(); g.arc(fx, fy, h * 0.055, 0, 7); g.fill();
    g.fillStyle = rgb([250, 230, 120]); g.beginPath(); g.arc(fx, fy, h * 0.018, 0, 7); g.fill();
  }
});
const CALENDARIO = tela(300, 420, (g, w, h) => {
  g.fillStyle = rgb([252, 252, 248]); g.fillRect(0, 0, w, h);
  let gr = g.createLinearGradient(0, 0, 0, h * 0.42); gr.addColorStop(0, rgb([120, 190, 236])); gr.addColorStop(1, rgb([200, 230, 246]));
  g.fillStyle = gr; g.fillRect(10, 10, w - 20, h * 0.42);
  g.fillStyle = rgb([70, 150, 190]); g.fillRect(10, h * 0.3, w - 20, h * 0.08);
  g.fillStyle = rgb([240, 214, 160]); g.fillRect(10, h * 0.37, w - 20, h * 0.06);
  g.fillStyle = rgb([210, 60, 60]); g.fillRect(10, h * 0.45, w - 20, h * 0.08);
  g.fillStyle = 'white'; g.font = 'bold 30px sans-serif'; g.textAlign = 'center'; g.fillText('NOVEMBRO', w / 2, h * 0.515);
  g.fillStyle = rgb([60, 60, 60]); g.font = 'bold 17px sans-serif';
  for (let d = 1; d <= 30; d++) {
    const k = d + 6 - 1, c = k % 7, l = Math.floor(k / 7);
    g.fillStyle = c === 0 ? rgb([210, 60, 60]) : rgb([60, 60, 60]);
    g.fillText(String(d), 28 + c * ((w - 50) / 6), h * 0.6 + l * h * 0.075);
  }
});
const VISTA = tela(2800, 1600, (g, w, h) => {              // vista da janela: céu, prédios e árvores (centro = janela)
  let gr = g.createLinearGradient(0, 0, 0, h * 0.55); gr.addColorStop(0, rgb([96, 160, 226])); gr.addColorStop(1, rgb([214, 232, 246]));
  g.fillStyle = gr; g.fillRect(0, 0, w, h);
  for (let k = 0; k < 14; k++) {                                         // nuvens
    const cx = rnd() * w, cy = h * (0.1 + rnd() * 0.25), r = 30 + rnd() * 60;
    g.fillStyle = 'rgba(255,255,255,0.85)';
    for (let j = 0; j < 5; j++) { g.beginPath(); g.ellipse(cx + (j - 2) * r * 0.7, cy + Math.sin(j) * r * 0.15, r, r * 0.55, 0, 0, 7); g.fill(); }
  }
  const hor = h * 0.5;
  const fileira = (n, yb, hmin, hmax, cores, janelas, larg) => {
    let x = -rnd() * 80;
    while (x < w) {
      const bw = larg * (0.7 + rnd() * 0.8), bh = hmin + rnd() * (hmax - hmin), c = cores[Math.floor(rnd() * cores.length)];
      g.fillStyle = rgb(c); g.fillRect(x, yb - bh, bw, bh);
      g.fillStyle = rgb(c, 0.85); g.fillRect(x + bw * 0.85, yb - bh, bw * 0.15, bh);
      if (janelas) for (let yy = yb - bh + 16; yy < yb - 18; yy += 26) for (let xx = x + 10; xx < x + bw * 0.82 - 12; xx += 22) {
        g.fillStyle = rnd() < 0.15 ? rgb([255, 236, 170]) : rgb([150, 186, 214]); g.fillRect(xx, yy, 12, 14);
      }
      x += bw + 6 + rnd() * 20;
    }
  };
  fileira(0, hor + 40, 140, 300, [[190, 206, 222], [176, 196, 214], [204, 214, 226]], false, 120);
  fileira(0, hor + 150, 180, 360, [[236, 196, 170], [240, 226, 196], [196, 222, 206], [226, 208, 226], [244, 214, 160]], true, 150);
  g.fillStyle = rgb([150, 150, 150]); g.fillRect(0, hor + 150, w, h - hor - 150);
  for (let k = 0; k < 40; k++) {                                         // copas de árvores na frente
    const cx = rnd() * w, cy = hor + 150 + rnd() * 60, r = 40 + rnd() * 70;
    g.fillStyle = rgb(rnd() < 0.5 ? [70, 136, 76] : [94, 160, 92]); g.beginPath(); g.arc(cx, cy, r, 0, 7); g.fill();
  }
});

// ------------------------------------------------------------------ mapeamentos
export function uvCaixa(mesh, metros) {          // como as "Object coords" do Blender, no espaço do mundo
  const geo = mesh.geometry, p = geo.attributes.position, n = geo.attributes.normal, m = mesh.matrixWorld;
  const nm = new THREE.Matrix3().getNormalMatrix(m); const uv = new Float32Array(p.count * 2);
  const v = new THREE.Vector3(), nn = new THREE.Vector3();
  for (let i = 0; i < p.count; i++) {
    v.fromBufferAttribute(p, i).applyMatrix4(m); nn.fromBufferAttribute(n, i).applyMatrix3(nm);
    const ax = Math.abs(nn.x), ay = Math.abs(nn.y), az = Math.abs(nn.z); let a, b;
    if (ay >= ax && ay >= az) { a = v.x; b = v.z; } else if (az >= ax) { a = v.x; b = v.y; } else { a = v.z; b = v.y; }
    uv[2 * i] = a / metros[0]; uv[2 * i + 1] = b / metros[1];
  }
  geo.setAttribute('uv', new THREE.BufferAttribute(uv, 2));
}
export function uvDecal(mesh) {                  // plano: 0..1 na largura (da esquerda para a direita de quem olha) e altura
  const geo = mesh.geometry, p = geo.attributes.position, m = mesh.matrixWorld;
  const nrm = new THREE.Vector3(); const nm = new THREE.Matrix3().getNormalMatrix(m);
  nrm.fromBufferAttribute(geo.attributes.normal, 0).applyMatrix3(nm).normalize();
  const up = new THREE.Vector3(0, 1, 0), dir = nrm.clone().negate().cross(up).normalize();
  const pts = []; const v = new THREE.Vector3();
  for (let i = 0; i < p.count; i++) { v.fromBufferAttribute(p, i).applyMatrix4(m); pts.push([v.dot(dir), v.y]); }
  const u0 = Math.min(...pts.map(q => q[0])), u1 = Math.max(...pts.map(q => q[0]));
  const v0 = Math.min(...pts.map(q => q[1])), v1 = Math.max(...pts.map(q => q[1]));
  const uv = new Float32Array(p.count * 2);
  pts.forEach((q, i) => { uv[2 * i] = (q[0] - u0) / (u1 - u0 || 1); uv[2 * i + 1] = (q[1] - v0) / (v1 - v0 || 1); });
  geo.setAttribute('uv', new THREE.BufferAttribute(uv, 2));
}

// nome do material no GLB -> material do three.js; devolve true se tratou
export function vestir(m, nome) {
  const caixa = (tx, op = {}) => { m.material = new THREE.MeshStandardMaterial({ map: tx, roughness: 0.6, ...op }); uvCaixa(m, tx.userData.metros); return true; };
  const decal = (tx, op = {}) => {
    const t = tx.clone(); t.wrapS = t.wrapT = THREE.ClampToEdgeWrapping; t.needsUpdate = true;
    m.material = new THREE.MeshStandardMaterial({ map: t, roughness: 0.55, ...op }); uvDecal(m); return true;
  };
  switch (nome) {
    case 'piso': m.castShadow = false; return caixa(LADRILHO, { roughness: 0.32, envMapIntensity: 1.2 });
    case 'parede': return caixa(PAREDE, { roughness: 0.9 });
    case 'azulejo': return caixa(LAMBRI, { roughness: 0.35 });
    case 'azulejo_dec': return caixa(AZULEJO, { roughness: 0.12, envMapIntensity: 1.3 });
    case 'armario': return caixa(MADEIRA, { roughness: 0.5 });
    case 'mesa': return caixa(MADEIRA_CLARA, { roughness: 0.45 });
    case 'piso_corredor': return caixa(MADEIRA, { roughness: 0.4 });
    case 'toalha': return caixa(XADREZ, { roughness: 0.85, side: THREE.DoubleSide });
    case 'corredor': return caixa(PAPEL_CORREDOR, { roughness: 0.9 });
    case 'pintura1': return decal(QUADRO_PAISAGEM, { roughness: 0.6 });
    case 'pintura2': return decal(QUADRO_FLORES, { roughness: 0.6 });
    case 'calendario': return decal(CALENDARIO, { roughness: 0.8 });
    case 'ceu': m.castShadow = false; m.receiveShadow = false;
      { const t = VISTA.clone(); t.wrapS = t.wrapT = THREE.ClampToEdgeWrapping; t.needsUpdate = true;
        m.material = new THREE.MeshBasicMaterial({ map: t }); uvDecal(m); } return true;
    case 'lampada': m.castShadow = false; m.material = new THREE.MeshBasicMaterial({ color: lin(255, 246, 220) }); return true;
    case 'abajur': m.material = new THREE.MeshStandardMaterial({ color: lin(250, 232, 196), emissive: lin(255, 214, 150), emissiveIntensity: 0.9, side: THREE.DoubleSide }); return true;
    case 'teto': m.castShadow = false; return false;
  }
  return false;
}

// ------------------------------------------------------------------ luz de estúdio de sitcom (clara, suave, sem sombra dura)
export function luzes(scene, B, lampadaPos) {
  const L = {};
  L.hemi = new THREE.HemisphereLight(lin(242, 244, 250), lin(176, 146, 116), 1.25); scene.add(L.hemi);
  L.chave = new THREE.DirectionalLight(lin(255, 240, 220), 1.9);
  L.chave.position.copy(B(-2.6, -4.2, 3.4)); L.chave.target.position.copy(B(0, 0, 1.0));
  L.chave.castShadow = true; L.chave.shadow.mapSize.set(2048, 2048); L.chave.shadow.radius = 10;
  L.chave.shadow.bias = -0.0004; L.chave.shadow.normalBias = 0.02;
  Object.assign(L.chave.shadow.camera, { left: -6.5, right: 6.5, top: 4.5, bottom: -2.5, near: 0.5, far: 16 });
  scene.add(L.chave, L.chave.target);
  L.preenche = new THREE.DirectionalLight(lin(222, 236, 255), 0.9);
  L.preenche.position.copy(B(3.4, -3.6, 2.2)); L.preenche.target.position.copy(B(0.5, 0, 1)); scene.add(L.preenche, L.preenche.target);
  L.plateia = new THREE.DirectionalLight(lin(255, 246, 236), 0.55);           // luz frontal "da plateia"
  L.plateia.position.copy(B(0, -7, 1.8)); L.plateia.target.position.copy(B(0, 0, 1.2)); scene.add(L.plateia, L.plateia.target);
  L.recorte = new THREE.DirectionalLight(lin(255, 214, 168), 1.0);
  L.recorte.position.copy(B(0.4, 1.2, 2.7)); L.recorte.target.position.copy(B(0.4, -0.5, 1.2)); scene.add(L.recorte, L.recorte.target);
  L.lampada = new THREE.PointLight(lin(255, 226, 170), 1.8, 5, 1.6); L.lampada.position.copy(lampadaPos); scene.add(L.lampada);
  L.corredor = new THREE.PointLight(lin(255, 210, 150), 2.6, 4.5, 1.4); L.corredor.position.copy(B(2.1, 2.8, 2.3)); scene.add(L.corredor);
  return L;
}
