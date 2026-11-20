// Geladeira Dividida — versão em tempo real (three.js) da abertura fria.
// Mesmos modelos (exportados do Blender por motor/exportar_glb.py), mesmas cores, vozes e rostos
// (motor/tempo_real.py). Aqui o movimento é de verdade: câmera passeando, cabeças virando, Beto andando.
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { GTAOPass } from 'three/addons/postprocessing/GTAOPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';

const CAPTURA = new URLSearchParams(location.search).has('captura');
if (CAPTURA) document.body.classList.add('captura');
const W = 1920, H = 1080;
const B = (x, y, z) => new THREE.Vector3(x, z, -y);          // Blender (z para cima) -> three (y para cima)
const lin = (r, g, b) => new THREE.Color().setRGB(r / 255, g / 255, b / 255, THREE.SRGBColorSpace);
const clamp = (v, a, b) => Math.min(b, Math.max(a, v));
const ease = u => { u = clamp(u, 0, 1); return u * u * (3 - 2 * u); };
const lerp = (a, b, u) => a + (b - a) * u;

// ------------------------------------------------------------------ renderizador
const palco = document.getElementById('palco');
const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: CAPTURA });
renderer.setPixelRatio(1);
renderer.setSize(W, H, false);
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 0.95;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
palco.prepend(renderer.domElement);

const scene = new THREE.Scene();
scene.background = lin(200, 214, 230);
const pmrem = new THREE.PMREMGenerator(renderer);
scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
scene.environmentIntensity = 0.32;

const camera = new THREE.PerspectiveCamera(27, W / H, 0.05, 80);
const lente = mm => THREE.MathUtils.radToDeg(2 * Math.atan(10.125 / mm));   // sensor 36 mm, 16:9

// luzes (as mesmas posições do Blender: chave, preenchimento, recorte, sol pela janela, lâmpada)
const hemi = new THREE.HemisphereLight(lin(232, 238, 248), lin(150, 110, 84), 0.9); scene.add(hemi);
const chave = new THREE.DirectionalLight(lin(255, 237, 214), 2.3);
chave.position.copy(B(-2.6, -4.2, 3.4)); chave.target.position.copy(B(0, 0, 1.0));
chave.castShadow = true; chave.shadow.mapSize.set(2048, 2048); chave.shadow.radius = 6; chave.shadow.bias = -0.0004;
chave.shadow.normalBias = 0.02;
Object.assign(chave.shadow.camera, { left: -5, right: 5, top: 4, bottom: -2, near: 0.5, far: 14 });
scene.add(chave, chave.target);
const preenche = new THREE.DirectionalLight(lin(219, 234, 255), 0.7);
preenche.position.copy(B(3.4, -3.6, 2.2)); preenche.target.position.copy(B(0.5, 0, 1)); scene.add(preenche, preenche.target);
const recorte = new THREE.DirectionalLight(lin(255, 214, 168), 1.1);
recorte.position.copy(B(0.4, 1.2, 2.7)); recorte.target.position.copy(B(0.4, -0.5, 1.2)); scene.add(recorte, recorte.target);
const lampada = new THREE.PointLight(lin(255, 226, 170), 1.6, 5, 1.6);
lampada.position.copy(B(0.05, 0.6, 2.0)); scene.add(lampada);

// ------------------------------------------------------------------ texturas procedurais (as do Blender eram nós)
function tela(w, h, desenha) {
  const c = document.createElement('canvas'); c.width = w; c.height = h; desenha(c.getContext('2d'), w, h);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.wrapS = t.wrapT = THREE.RepeatWrapping;
  t.anisotropy = 8; return t;
}
let semente = 7; const rnd = () => (semente = (semente * 16807) % 2147483647) / 2147483647;
const rgb = (c, k = 1) => `rgb(${c.map(v => clamp(Math.round(v * k), 0, 255)).join(',')})`;
function ruido(g, w, h, n, cor0, cor1, esticaX = 1, esticaY = 1, alfa = 0.08) {
  for (let i = 0; i < n; i++) {
    const c = rnd() < 0.5 ? cor0 : cor1; g.fillStyle = rgb(c); g.globalAlpha = alfa * rnd();
    const x = rnd() * w, y = rnd() * h, r = 2 + rnd() * 10;
    g.beginPath(); g.ellipse(x, y, r * esticaX, r * esticaY, 0, 0, 7); g.fill();
  }
  g.globalAlpha = 1;
}
// piso: tábuas 1,3 m x 0,2 m, deslocamento 0,37 (textura = 2,6 m x 1,0 m)
const TX_PISO = tela(2048, 788, (g, w, h) => {
  const c1 = [178, 122, 86], c2 = [160, 104, 72], arg = [96, 60, 42];
  g.fillStyle = rgb(arg); g.fillRect(0, 0, w, h);
  const lh = h / 5, bw = w / 2;
  for (let r = 0; r < 5; r++) {
    const off = ((r * 0.37) % 1) * bw;
    for (let k = -1; k < 3; k++) {
      const x = off + k * bw; g.fillStyle = rgb(rnd() < 0.5 ? c1 : c2, 0.95 + rnd() * 0.1);
      g.fillRect(x + 2, r * lh + 2, bw - 4, lh - 4);
      for (let s = 0; s < 26; s++) {     // veios
        g.strokeStyle = rgb(c2, 0.82); g.globalAlpha = 0.18 * rnd(); g.lineWidth = 1 + rnd() * 3; g.beginPath();
        const y = r * lh + 6 + rnd() * (lh - 12); g.moveTo(x, y);
        g.bezierCurveTo(x + bw * 0.3, y + (rnd() - 0.5) * 8, x + bw * 0.6, y + (rnd() - 0.5) * 8, x + bw, y + (rnd() - 0.5) * 6); g.stroke();
      }
      g.globalAlpha = 1;
    }
  }
});
TX_PISO.userData.metros = [2.6, 1.0];
// "azulejo": no Blender, a textura de tijolo usa só X e Y do objeto; na face da parede (Y constante)
// vira ripas verticais de 0,15 m com frisos de 8 mm (lambri). Reproduz isso.
const TX_AZUL = tela(512, 64, (g, w, h) => {
  const n = 4, s = w / n, friso = Math.max(3, Math.round(0.008 / 0.6 * w));
  for (let i = 0; i < n; i++) {
    g.fillStyle = rgb(i % 2 ? [240, 220, 190] : [234, 212, 180]); g.fillRect(i * s, 0, s, h);
    const gr = g.createLinearGradient(i * s, 0, i * s + s, 0);     // leve relevo da ripa
    gr.addColorStop(0, 'rgba(255,255,255,0.18)'); gr.addColorStop(0.5, 'rgba(255,255,255,0)'); gr.addColorStop(1, 'rgba(0,0,0,0.06)');
    g.fillStyle = gr; g.fillRect(i * s, 0, s, h);
    g.fillStyle = rgb([210, 186, 152]); g.fillRect(i * s, 0, friso, h);
    g.fillStyle = 'rgba(80,60,40,0.18)'; g.fillRect(i * s + friso, 0, 2, h);
  }
});
TX_AZUL.userData.metros = [0.6, 0.6];  // 4 ripas por textura
const TX_PAREDE = tela(1024, 1024, (g, w, h) => {
  g.fillStyle = rgb([242, 224, 196]); g.fillRect(0, 0, w, h); ruido(g, w, h, 3000, [236, 216, 186], [250, 236, 210], 4, 4, 0.12);
});
TX_PAREDE.userData.metros = [2.5, 2.5];
const TX_MADEIRA = tela(1024, 1024, (g, w, h) => {
  g.fillStyle = rgb([149, 103, 71]); g.fillRect(0, 0, w, h);
  for (let i = 0; i < 260; i++) {
    g.strokeStyle = rgb(rnd() < 0.5 ? [136, 92, 62] : [168, 120, 84]); g.globalAlpha = 0.35 * rnd(); g.lineWidth = 1 + rnd() * 5;
    const y = rnd() * h; g.beginPath(); g.moveTo(0, y);
    g.bezierCurveTo(w * 0.3, y + (rnd() - 0.5) * 20, w * 0.7, y + (rnd() - 0.5) * 20, w, y); g.stroke();
  }
  g.globalAlpha = 1;
});
TX_MADEIRA.userData.metros = [1.2, 1.2];

// coordenadas de textura "de caixa" (como as Object coords do Blender), no espaço do mundo
function uvCaixa(mesh, metros) {
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

const CONTORNO = new THREE.MeshBasicMaterial({ color: lin(48, 32, 30), side: THREE.BackSide });
function contorno(mesh, esp = 0.009) {
  const g = mesh.geometry.clone(); g.deleteAttribute('uv');
  const p = g.attributes.position, n = g.attributes.normal;
  // normal média por posição (evita rachaduras nas costuras)
  const mapa = new Map(), chave = i => `${p.getX(i).toFixed(4)},${p.getY(i).toFixed(4)},${p.getZ(i).toFixed(4)}`;
  for (let i = 0; i < p.count; i++) {
    const k = chave(i); const a = mapa.get(k) || [0, 0, 0];
    a[0] += n.getX(i); a[1] += n.getY(i); a[2] += n.getZ(i); mapa.set(k, a);
  }
  const s = mesh.scale; // escala do objeto (esferas achatadas): compensa para manter espessura em metros
  for (let i = 0; i < p.count; i++) {
    const a = mapa.get(chave(i)); const l = Math.hypot(...a) || 1;
    p.setXYZ(i, p.getX(i) + a[0] / l * esp / s.x, p.getY(i) + a[1] / l * esp / s.y, p.getZ(i) + a[2] / l * esp / s.z);
  }
  const o = new THREE.Mesh(g, CONTORNO); o.castShadow = false; o.receiveShadow = false; mesh.add(o); return o;
}

// ------------------------------------------------------------------ dados (linha do tempo, rostos, legendas)
const DADOS = './dados/';
const linha = await (await fetch(DADOS + 'linha.json')).json();
const FPS = linha.fps, DUR = linha.dur, R_CAB = 0.233;
const texLoader = new THREE.TextureLoader();
const carregaTex = url => new Promise(ok => texLoader.load(url, t => { t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8; ok(t); }));
const nomesRostos = [...new Set(linha.quadros.flatMap(q => Object.values(q).map(v => v.rosto)))];
const ROSTOS = Object.fromEntries(await Promise.all(nomesRostos.map(async n => [n, await carregaTex(DADOS + 'rostos/' + n)])));
const TX_GOTA = await carregaTex(DADOS + 'gota.png');

// ------------------------------------------------------------------ cena do Blender
const gltf = await new GLTFLoader().loadAsync('./cena.glb');
scene.add(gltf.scene);
gltf.scene.updateMatrixWorld(true);
const PERS = { clara: { x: -1.0, dz: 0 }, beto: { x: 0.75, dz: 0 }, neide: { x: 1.95, dz: -0.09 } };
const quemDe = nome => (nome.match(/_(clara|beto|neide)(_repouso)?$/) || [])[1];
const partes = { clara: [], beto: [], neide: [] };
const objetos = [...gltf.scene.children];
for (const ob of objetos) {
  const quem = quemDe(ob.name);
  const malhas = []; ob.traverse(m => { if (m.isMesh) malhas.push(m); });
  for (const m of malhas) {
    const mn = m.material.name.split('.')[0];
    m.castShadow = !['ceu', 'predios', 'lampada', 'teto'].includes(mn) && ob.name !== 'teto';
    m.receiveShadow = true;
    if (mn === 'piso') { m.material = new THREE.MeshStandardMaterial({ map: TX_PISO, roughness: 0.42, envMapIntensity: 1.4 }); uvCaixa(m, TX_PISO.userData.metros); m.castShadow = false; }
    else if (mn === 'azulejo') { m.material = new THREE.MeshStandardMaterial({ map: TX_AZUL, roughness: 0.3 }); uvCaixa(m, TX_AZUL.userData.metros); }
    else if (mn === 'parede') { m.material = new THREE.MeshStandardMaterial({ map: TX_PAREDE, roughness: 0.9 }); uvCaixa(m, TX_PAREDE.userData.metros); }
    else if (mn === 'armario') { m.material = new THREE.MeshStandardMaterial({ map: TX_MADEIRA, roughness: 0.5 }); uvCaixa(m, TX_MADEIRA.userData.metros); }
    else if (mn === 'ceu') {
      m.material = new THREE.MeshBasicMaterial({ map: tela(16, 256, (g, w, h) => { const gr = g.createLinearGradient(0, h, 0, 0);
        gr.addColorStop(0.0, 'rgb(222,238,250)'); gr.addColorStop(0.3, 'rgb(222,238,250)'); gr.addColorStop(0.75, 'rgb(86,156,228)'); gr.addColorStop(1, 'rgb(86,156,228)');
        g.fillStyle = gr; g.fillRect(0, 0, w, h); }) });
      const geo = m.geometry, p = geo.attributes.position; const uv = new Float32Array(p.count * 2);
      const ys = []; const v = new THREE.Vector3();
      for (let i = 0; i < p.count; i++) ys.push(v.fromBufferAttribute(p, i).applyMatrix4(m.matrixWorld).y);
      const y0 = Math.min(...ys), y1 = Math.max(...ys);
      for (let i = 0; i < p.count; i++) { uv[2 * i] = 0.5; uv[2 * i + 1] = (ys[i] - y0) / (y1 - y0 || 1); }
      geo.setAttribute('uv', new THREE.BufferAttribute(uv, 2));
    }
    else if (mn === 'predios') m.material = new THREE.MeshBasicMaterial({ color: lin(150, 176, 206) });
    else if (mn === 'lampada') m.material = new THREE.MeshBasicMaterial({ color: lin(255, 246, 220) });
    else if (m.material.isMeshStandardMaterial) {
      const nome = mn;
      if (/^(pele|roupa|calca|cabelo|sapato|meia)/.test(nome)) m.material.envMapIntensity = 0.6;
      if (nome.startsWith('roupa') || nome.startsWith('calca')) { m.material.roughness = 0.8; m.material.sheen = 0; }
    }
    if (quem && !/estrela|gola|botao/.test(ob.name)) contorno(m);
  }
  if (quem) partes[quem].push(ob);
}

// ------------------------------------------------------------------ esqueleto simples de cada personagem
// raiz (pés) > quadril > pernas | tronco > braços, cabeça (com o rosto)
function pivo(pai, pos) { const g = new THREE.Group(); g.position.copy(pos); pai.updateMatrixWorld(true);
  pai.add(g); g.position.copy(pai.worldToLocal(pos.clone())); g.updateMatrixWorld(true); return g; }
const RIG = {};
for (const [quem, cfg] of Object.entries(PERS)) {
  const { x, dz } = cfg; const raiz = new THREE.Group(); raiz.position.copy(B(x, 0, 0)); scene.add(raiz); raiz.updateMatrixWorld(true);
  const corpo = pivo(raiz, B(x, 0, 0.45));             // sobe e desce (respiração, passo)
  const tronco = pivo(corpo, B(x, 0, 0.5 + dz));
  const cabeca = pivo(tronco, B(x, 0, 0.98 + dz));
  const pernas = {}, bracos = {};
  for (const s of [-1, 1]) {
    pernas[s] = pivo(raiz, B(x + s * 0.075, 0, 0.42));
    bracos[s] = pivo(tronco, B(x + s * 0.25, 0, 0.87 + dz));
  }
  for (const ob of partes[quem]) {
    const n = ob.name; let alvo = tronco;
    if (/^(perna|sapato)/.test(n)) alvo = pernas[n.includes('-1') ? -1 : 1];
    else if (/^(braco|mao)/.test(n)) alvo = bracos[n.includes('-1') ? -1 : 1];
    else if (/^(cabeca|orelha|nariz|cabelo|coque|lateral)/.test(n)) alvo = cabeca;
    else if (/^saia/.test(n)) alvo = corpo;
    alvo.attach(ob);
  }
  // rosto: calota esférica com o desenho projetado de frente (como a troca de textura dos jogos)
  const centro = B(x, 0, 1.2 + dz); const cl = cabeca.worldToLocal(centro.clone());
  const geo = new THREE.SphereGeometry(R_CAB * 1.008, 96, 64).toNonIndexed();
  const p = geo.attributes.position; const uv = new Float32Array(p.count * 2); const manter = [];
  const kpx = (68 * linha.kf) / linha.n;                // raio da cabeça em fração da textura
  for (let i = 0; i < p.count; i += 3) {
    const zc = (p.getZ(i) + p.getZ(i + 1) + p.getZ(i + 2)) / 3;
    if (zc < R_CAB * 0.18) continue;
    for (let j = 0; j < 3; j++) { manter.push(p.getX(i + j), p.getY(i + j), p.getZ(i + j) * 0.94);
      uv.set([0.5 + p.getX(i + j) / R_CAB * kpx, 0.5 + p.getY(i + j) / R_CAB * kpx], (manter.length / 3 - 1) * 2); }
  }
  const g2 = new THREE.BufferGeometry(); g2.setAttribute('position', new THREE.Float32BufferAttribute(manter, 3));
  g2.setAttribute('uv', new THREE.BufferAttribute(uv.slice(0, manter.length / 3 * 2), 2)); g2.computeVertexNormals();
  const matRosto = new THREE.MeshStandardMaterial({ transparent: true, roughness: 0.55, depthWrite: false,
    polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -2 });
  const rosto = new THREE.Mesh(g2, matRosto); rosto.position.copy(cl); rosto.renderOrder = 2; rosto.receiveShadow = true; cabeca.add(rosto);
  const gota = new THREE.Mesh(new THREE.PlaneGeometry(24 / 68 * R_CAB, 36 / 68 * R_CAB),
    new THREE.MeshBasicMaterial({ map: TX_GOTA, transparent: true, depthWrite: false }));
  gota.position.copy(cl).add(new THREE.Vector3(74 / 68 * R_CAB, 24 / 68 * R_CAB, R_CAB * 0.55)); gota.rotation.y = 0.5; cabeca.add(gota);
  RIG[quem] = { raiz, corpo, tronco, cabeca, pernas, bracos, rosto, gota, x, dz,
                olhar: { yaw: 0, pitch: 0, vy: 0, vp: 0 }, giro: { v: 0, a: 0 }, gesto: {} };
}
// a Dona Neide não está nesta cena
RIG.neide.raiz.visible = false;

// ------------------------------------------------------------------ direção da cena
// Beto vem do balcão até o lugar dele enquanto a Clara pergunta (passos a cada 0,32 s, como no Blender)
const CAMINHO = linha.caminhada || { t0: 0.0, t1: 2.5, de: [2.85, 0.3], ate: [0.75, 0.0] };
const VIRADA = { clara: 0.42, beto: -0.42 };          // "cheat" de sitcom: meio de frente para a câmera, meio para o outro
function posicaoBeto(t) {
  const { t0, t1, de, ate } = CAMINHO; const u = clamp((t - t0) / (t1 - t0), 0, 1);
  const k = u - Math.sin(2 * Math.PI * u) / (2 * Math.PI);    // acelera e freia
  return { x: lerp(de[0], ate[0], k), y: lerp(de[1], ate[1], k), andando: t > t0 && t < t1, u };
}
const cabecaMundo = quem => RIG[quem].cabeca.localToWorld(new THREE.Vector3(0, 0.22, 0));
function alvoOlhar(quem, t, q) {
  const outro = quem === 'clara' ? 'beto' : 'clara';
  const ex = q[quem].ex;
  if (quem === 'beto') {
    const leg = linha.legendas.find(l => t >= l.fala0 - 0.2 && t < l.fala1 + 0.6);
    if (leg && /lâmpada/i.test(leg.texto) && t > leg.fala0 + 0.55) return B(0.62, -0.35, 2.9);          // olha para cima, para a lâmpada
    if (ex === 'nervoso' && Math.sin(t * 2.3) > 0.55) return B(1.6, -2.5, 1.0);                         // desvia o olhar
    if (posicaoBeto(t).andando) { const p = posicaoBeto(t + 0.4); return B(p.x - 0.9, -0.6, 1.15); }
  }
  return cabecaMundo(outro);
}

const tmp = new THREE.Vector3();
function mola(st, alvo, dt, k = 60, c = 13) { const a = k * (alvo - st.v) - c * st.a; st.a += a * dt; st.v += st.a * dt; return st.v; }

let tAnterior = 0;
function animar(t, dt) {
  const f = clamp(Math.round(t * FPS), 0, linha.quadros.length - 1); const q = linha.quadros[f];
  for (const quem of ['clara', 'beto']) {
    const R = RIG[quem]; const info = q[quem];
    R.rosto.material.map = ROSTOS[info.rosto]; R.rosto.material.needsUpdate = R.rosto.material.userData.ult !== info.rosto;
    R.rosto.material.userData.ult = info.rosto;
    R.gota.visible = info.ex === 'nervoso';
    // posição e direção do corpo
    let andando = false, fase = 0, yawCorpo = VIRADA[quem];
    if (quem === 'beto') {
      const p = posicaoBeto(t); andando = p.andando;
      R.raiz.position.copy(B(p.x, p.y, 0));
      const viz = posicaoBeto(t + 0.05); const dx = viz.x - p.x, dy = viz.y - p.y;
      if (Math.hypot(dx, dy) > 1e-4) yawCorpo = Math.atan2(dx, dy * -1) ;
      fase = (t - CAMINHO.t0) / 0.64 * Math.PI * 2;
    }
    const giro = mola(R.giro, yawCorpo, dt, 40, 12);
    R.raiz.rotation.y = giro;
    // passo: pernas, braços e balanço
    const peso = andando ? 1 : 0; R.passo = lerp(R.passo || 0, peso, clamp(dt * 8, 0, 1));
    const sw = Math.sin(fase) * 0.45 * R.passo;
    R.pernas[-1].rotation.x = sw; R.pernas[1].rotation.x = -sw;
    R.corpo.position.y = R.corpo.userData.y0 ??= R.corpo.position.y;
    R.corpo.position.y = R.corpo.userData.y0 + Math.abs(Math.cos(fase)) * 0.025 * R.passo - 0.012 * R.passo
      + Math.sin(t * 2.2 + quem.length) * 0.004;
    R.tronco.rotation.z = Math.sin(fase) * 0.04 * R.passo;
    R.tronco.rotation.x = 0.06 * R.passo;
    // gestos (mesma lógica de poses da versão Blender, agora articulados)
    const g = info.g, pose = info.pose;
    const lado = quem === 'clara' ? 1 : -1;        // lado do braço que aponta para o outro
    let bx = { '-1': [-sw * 0.8, 0], '1': [sw * 0.8, 0] };   // [rot x, rot z]
    if (pose === 'aponta') bx[lado] = [-1.15 * g, lado * 0.35 * g];
    if (pose === 'ombros') { bx[-1] = [-0.35 * g, -0.55 * g]; bx[1] = [-0.35 * g, 0.55 * g]; }
    if (pose === 'cintura') { bx[-1] = [0.1 * g, -0.5 * g]; bx[1] = [0.1 * g, 0.5 * g]; }
    for (const s of [-1, 1]) {
      const [rx, rz] = bx[s]; const st = R.gesto[s] ??= { x: { v: 0, a: 0 }, z: { v: 0, a: 0 } };
      R.bracos[s].rotation.x = mola(st.x, rx, dt, 90, 15); R.bracos[s].rotation.z = mola(st.z, rz + s * 0.04, dt, 90, 15);
    }
    R.tronco.position.y = (R.tronco.userData.y0 ??= R.tronco.position.y) + (pose === 'ombros' ? 0.02 * g : 0);
    // cabeça vira para quem fala (em relação ao corpo), com mola
    const alvo = alvoOlhar(quem, t, q); const piv = R.cabeca.getWorldPosition(tmp.set(0, 0, 0)).clone();
    const d = alvo.clone().sub(piv.add(new THREE.Vector3(0, 0.22, 0)));
    d.applyAxisAngle(new THREE.Vector3(0, 1, 0), -R.raiz.rotation.y);
    const yaw = clamp(Math.atan2(d.x, d.z), -1.15, 1.15), pitch = clamp(Math.atan2(d.y, Math.hypot(d.x, d.z)), -0.5, 0.55);
    const ol = R.olhar; ol.y ??= { v: 0, a: 0 }; ol.p ??= { v: 0, a: 0 };
    const vy = mola(ol.y, yaw, dt, 70, 14), vp = mola(ol.p, pitch, dt, 70, 14);
    let tilt = 0, nod = 0;
    if (info.ex === 'suspeita') tilt = 0.12;
    if (info.ex === 'nervoso') tilt = Math.sin(t * 9) * 0.035;
    if (info.vol) nod = info.vol * 0.06 * Math.sin(t * 13);
    R.cabeca.rotation.set(-vp * 0.85 + nod, vy * 0.85, tilt * lado, 'YXZ');
  }
}

// ------------------------------------------------------------------ câmera passeando
// mesmos cortes da versão Blender (para comparar), mas cada plano tem movimento
const H_BETO = () => cabecaMundo('beto'), H_CLARA = () => cabecaMundo('clara');
const PLANOS = [
  { t0: 0, t1: 3.1, f: (u, t) => {           // grua: começa no balcão acompanhando o Beto e abre para o plano geral
      const e = ease(u);
      const pos = new THREE.Vector3().lerpVectors(B(3.3, -2.0, 1.75), B(-0.15, -5.2, 1.3), e);
      const alvo = new THREE.Vector3().lerpVectors(B(2.2, 0.3, 1.0), B(-0.12, 0.6, 1.0), ease(u * 1.15));
      return { pos, alvo, mm: lerp(30, 40, e) }; } },
  { t0: 3.1, t1: 4.1, f: u => ({ pos: B(-1.58 + 0.06 * u, -0.62, 1.44), alvo: H_BETO().add(B(0, 0, -0.06)), mm: 40 }) },     // por cima do ombro da Clara
  { t0: 4.1, t1: 6.11, f: u => ({ pos: B(1.34 - 0.08 * u, -0.62, 1.44), alvo: H_CLARA().add(B(0, 0, -0.06)), mm: 40 }) },   // por cima do ombro do Beto
  { t0: 6.11, t1: 7.66, f: u => ({ pos: B(0.4 + 0.08 * u, -1.95 + 0.25 * ease(u), 1.3), alvo: H_BETO().add(B(0, 0, -0.05)), mm: 45 }) },
  { t0: 7.66, t1: 9.59, f: u => ({ pos: B(-0.65 - 0.08 * u, -1.95 + 0.25 * ease(u), 1.32), alvo: H_CLARA().add(B(0, 0, -0.05)), mm: 45 }) },
  { t0: 9.59, t1: 99, f: (u, t) => {          // Beto culpa a lâmpada: a câmera sobe junto e depois abre na risada
      const a = ease((t - 10.3) / 1.0), b = ease((t - 11.3) / 1.7);
      const perto = B(0.35, -1.75, 1.32), longe = B(-0.1, -4.2, 1.45);
      const pos = new THREE.Vector3().lerpVectors(perto, longe, b);
      const alvoB = H_BETO().add(B(0, 0, -0.05)), alvoL = B(0.05, 0.6, 2.05), alvoG = B(-0.1, 0.4, 1.15);
      let alvo = alvoB.clone().lerp(alvoL, a * (1 - b) * 0.42); alvo.lerp(alvoG, b);
      return { pos, alvo, mm: lerp(36, 34, b) }; } },
];
function posicionarCamera(t) {
  const p = PLANOS.find(p => t >= p.t0 && t < p.t1) || PLANOS.at(-1);
  const u = clamp((t - p.t0) / (Math.min(p.t1, DUR) - p.t0), 0, 1); const r = p.f(u, t);
  camera.position.copy(r.pos); camera.lookAt(r.alvo); camera.fov = lente(r.mm); camera.updateProjectionMatrix();
}

// ------------------------------------------------------------------ pós-processamento (oclusão de ambiente)
const composer = new EffectComposer(renderer);
composer.setPixelRatio(1); composer.setSize(W, H);
composer.addPass(new RenderPass(scene, camera));
const ao = new GTAOPass(scene, camera, W, H);
ao.updateGtaoMaterial({ radius: 0.35, distanceExponent: 1.5, thickness: 1.0, scale: 1.0, samples: 12 });
ao.blendIntensity = 0.75;
composer.addPass(ao);
composer.addPass(new OutputPass());

// ------------------------------------------------------------------ legenda
const legDiv = document.getElementById('legenda'); const legImgs = {};
for (const l of linha.legendas) { const im = new Image(); im.src = DADOS + 'legendas/' + l.img; legImgs[l.img] = im; }
await Promise.all(Object.values(legImgs).map(im => im.decode()));
let legAtual = null;
function legenda(t) {
  const l = linha.legendas.find(l => t >= l.t0 && t < l.t1); const nome = l ? l.img : null;
  if (nome === legAtual) return; legAtual = nome; legDiv.innerHTML = '';
  if (l) { const im = legImgs[nome]; im.style.width = (im.naturalWidth / W * 100) + '%'; legDiv.appendChild(im); }
}
function ajustarLegenda() { legDiv.style.width = palco.clientWidth + 'px'; legDiv.style.display = 'flex'; legDiv.style.justifyContent = 'center'; }
ajustarLegenda(); addEventListener('resize', ajustarLegenda);

// ------------------------------------------------------------------ quadro
function quadro(t, dt) { animar(t, dt); scene.updateMatrixWorld(true); posicionarCamera(t); legenda(t); composer.render(); }

// captura: o Node chama window.renderizar(f) quadro a quadro (tempo fixo, resultado determinístico)
let fAnterior = -1;
window.renderizar = async f => {
  if (f !== fAnterior + 1) { fAnterior = -1; for (const R of Object.values(RIG)) { R.olhar = {}; R.giro = { v: 0, a: 0 }; R.gesto = {}; } }
  const dt = 1 / FPS;
  // as molas começam já no lugar
  if (f === 0) for (let k = 0; k < 60; k++) animar(0, dt);
  quadro(f / FPS, dt); fAnterior = f;
  return true;
};
window.simular = f => { if (f === 0) for (let k = 0; k < 60; k++) animar(0, 1 / FPS); animar(f / FPS, 1 / FPS); fAnterior = f; };
window.DUR = DUR; window.FPS = FPS; window.pronto = true;

if (!CAPTURA) {
  const audio = new Audio(DADOS + 'audio.wav'); const btn = document.getElementById('play');
  for (let k = 0; k < 60; k++) animar(0, 1 / FPS);
  quadro(0, 1 / FPS);
  btn.onclick = () => { btn.style.display = 'none'; audio.currentTime = 0; audio.play(); };
  audio.onended = () => { btn.textContent = '↻ tocar de novo'; btn.style.display = 'flex'; };
  let ult = performance.now();
  renderer.setAnimationLoop(() => {
    const agora = performance.now(); const dt = Math.min(0.05, (agora - ult) / 1000); ult = agora;
    if (!audio.paused) quadro(audio.currentTime, dt);
  });
}
