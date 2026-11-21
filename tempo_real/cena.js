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
import * as CEN from './cenario.js';
import * as LOC from './locomocao.js';

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

// luz de estúdio de sitcom (cenario.js); a lâmpada fica em cima da mesa
const LUZ = CEN.luzes(scene, B, B(0.05, 0.95, 2.0));

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
    m.castShadow = !['ceu', 'lampada', 'teto'].includes(mn) && ob.name !== 'teto';
    m.receiveShadow = true;
    if (CEN.vestir(m, mn)) { /* textura pintada do cenário */ }
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

// ------------------------------------------------------------------ versão realista (MakeHuman), com ?humanos
// O corpo de massinha fica escondido e serve de "marionete": a mesma direção (caminho, olhar, gestos)
// é copiada para os ossos do personagem realista; o rosto vira expressões 3D (morphs).
const HUMANOS = new URLSearchParams(location.search).has('humanos');
const HUM = {};
if (HUMANOS) {
  const { carregarHumano } = await import('./humano.js');
  for (const quem of ['clara', 'beto']) {
    const h = await carregarHumano('./humanos/', quem); HUM[quem] = h; const R = RIG[quem];
    R.raiz.add(h.raiz);
    R.corpo.visible = false; R.pernas[-1].visible = false; R.pernas[1].visible = false;
    h.raiz.traverse(o => { if (o.isBone) o.userData.p0 = o.position.clone(); });
    // pose A do MakeHuman -> braços caídos (ângulo medido no próprio esqueleto)
    const a = h.osso['upperarm01.L'].getWorldPosition(new THREE.Vector3()), b = h.osso['lowerarm01.L'].getWorldPosition(new THREE.Vector3());
    h.bracoRepouso = Math.atan2(Math.abs(b.x - a.x), a.y - b.y) - 0.1;
    // o MakeHuman vem com o antebraço dobrado para a frente: endireita (fica ~15% da dobra, natural)
    h.qCotovelo = {};
    for (const lado of ['L', 'R']) {
      const p = n => h.osso[n + '.' + lado].getWorldPosition(new THREE.Vector3());
      const dBraco = p('lowerarm01').sub(p('upperarm01')).normalize(), dAnte = p('wrist').sub(p('lowerarm01')).normalize();
      h.qCotovelo[lado] = new THREE.Quaternion().setFromUnitVectors(dAnte, dBraco.clone().lerp(dAnte, 0.15).normalize());
    }
    h.morph = {};
  }
}
// versão com mocap real (CMU), com ?humanos&mocap: caminhada e idle capturados; o IK só trava os pés
const MOCAP = HUMANOS && new URLSearchParams(location.search).has('mocap');
const SEM_OLHAR = new URLSearchParams(location.search).has('semolhar');
const CABECA_CMU = new URLSearchParams(location.search).has('cabecacmu');   // diagnóstico: cabeça copiada da CMU (antes)
let MOC = null, MOCS = null;
let GES = null;
if (MOCAP) {
  MOC = await import('./mocap.js'); MOCS = await MOC.preparar(HUM, { cabeca: CABECA_CMU ? 'cmu' : 'olhar' });
  GES = await import('./gestos.js'); for (const h of Object.values(HUM)) GES.preparar(h);
}
// rosto 3D: expressões do roteiro -> unidades de expressão do MakeHuman
const EXPR = {
  neutro: {},
  suspeita: { 'eyebrows-left-down': 0.75, 'eyebrows-right-up': 0.25, 'eye-left-slit': 0.55, 'eye-right-slit': 0.35, 'mouth-compression': 0.35 },
  seca: { 'eye-left-slit': 0.6, 'eye-right-slit': 0.6, 'mouth-compression': 0.25, 'mouth-depression': 0.15 },
  inocente: { 'eyebrows-left-up': 0.55, 'eyebrows-right-up': 0.55, 'eyebrows-left-inner-up': 0.45, 'eyebrows-right-inner-up': 0.45, 'mouth-corner-puller': 0.3 },
  nervoso: { 'eyebrows-left-inner-up': 0.9, 'eyebrows-right-inner-up': 0.9, 'mouth-retraction': 0.45, 'eyebrows-left-up': 0.2, 'eyebrows-right-up': 0.2 },
  feliz: { 'mouth-corner-puller': 0.75, 'eyebrows-left-up': 0.2, 'eyebrows-right-up': 0.2 },
  brava: { 'eyebrows-left-down': 0.85, 'eyebrows-right-down': 0.85, 'mouth-depression': 0.45, 'mouth-compression': 0.3 },
  surpresa: { 'eyebrows-left-up': 0.95, 'eyebrows-right-up': 0.95, 'mouth-open': 0.25 },
};
const EIXO_X = new THREE.Vector3(1, 0, 0);
const BOCA = { fechada: {}, pequena: { 'mouth-open': 0.22 }, aberta: { 'mouth-open': 0.55 },
               larga: { 'mouth-open': 0.3, 'mouth-retraction': 0.35 }, redonda: { 'mouth-open': 0.3, 'mouth-pursing': 0.55 } };
// pés plantados: onde está cada pé no chão (mundo) e para onde aponta
function chaoDoPe(quem, lado, t) {
  if (quem === 'beto') {
    const e = LOC.pe(PASSOS, lado, t - CAMINHO.t0, PERF);
    const k = e.d / DIST, c = B(lerp(P0[0], P1[0], k), lerp(P0[1], P1[1], k), 0);
    const lat = (lado === 'L' ? 1 : -1) * 0.105;                 // lado esquerdo do corpo = +x local
    c.x += Math.cos(e.yaw) * lat; c.z -= Math.sin(e.yaw) * lat; c.y += e.alto;
    return { c, yaw: e.yaw, incl: e.incl, e };
  }
  const R = RIG[quem], yaw = R.raiz.rotation.y, c = R.raiz.position.clone(), lat = (lado === 'L' ? 1 : -1) * 0.12;
  c.x += Math.cos(yaw) * lat; c.z -= Math.sin(yaw) * lat;
  return { c, yaw, incl: 0, e: { apoio: true } };
}
function aplicarHumano(quem, R, info, t, dt, fase, rotCabeca, olharResto) {
  if (MOCAP) return aplicarMocap(quem, R, info, t, dt, rotCabeca, olharResto);
  const h = HUM[quem], o = h.osso, passo = R.passo || 0;
  const pL = chaoDoPe(quem, 'L', t), pR = chaoDoPe(quem, 'R', t);
  // quadril: desce com os dois pés no chão, sobe no meio do passo, balança para o lado do pé de apoio
  let bob = 0, ginga = 0;
  const noAr = !pL.e.apoio ? pL.e : (!pR.e.apoio ? pR.e : null);
  if (noAr) { bob = 0.016 * Math.sin(Math.PI * noAr.u) - 0.012; ginga = (!pL.e.apoio ? -1 : 1) * 0.02 * Math.sin(Math.PI * noAr.u); }
  else if (quem === 'beto' && t > CAMINHO.t0 && t < CAMINHO.t1) bob = -0.012;
  const resp = Math.sin(t * 2.2 + quem.length) * 0.003;                  // respiração / peso
  o.root.position.set(o.root.userData.p0.x + ginga, o.root.userData.p0.y + bob + resp, o.root.userData.p0.z);
  const frente = new THREE.Vector3(Math.sin(R.raiz.rotation.y), 0, Math.cos(R.raiz.rotation.y));
  // passada: braços em oposição às pernas, tronco torce um pouco ao contrário do quadril
  const dif = clamp(pL.c.clone().sub(pR.c).dot(frente) / 0.6, -1, 1) * passo;
  o.root.rotation.y = 0.08 * dif; o.spine02.rotation.y = -0.12 * dif;
  o.spine03.rotation.set(0.05 * passo, 0, -ginga * 1.5);
  h.balanco = { L: 0.32 * dif, R: -0.32 * dif };
  h.raiz.updateMatrixWorld(true);
  LOC.perna(h, 'L', pL.c, pL.yaw, pL.incl, frente); LOC.perna(h, 'R', pR.c, pR.yaw, pR.incl, frente);
  // braços: repouso + gestos da marionete; cotovelo conforme o gesto
  const cot = { aponta: -0.15, ombros: 0.75, cintura: 1.4 }[info.pose] ?? 0;
  for (const [s, lado] of [[1, 'L'], [-1, 'R']]) {
    const br = R.bracos[s];
    const andar = R.passo || 0;
    o['upperarm01.' + lado].rotation.set(br.rotation.x * 0.85 * (1 - andar) + (h.balanco?.[lado] || 0), 0,
                                         -s * h.bracoRepouso + (br.rotation.z - s * 0.04) * 0.6);
    for (let dd = 2; dd <= 5; dd++) for (let k = 1; k <= 3; k++) {          // dedos relaxados (o MakeHuman vem de mão aberta)
      const f = o[`finger${dd}-${k}.${lado}`]; if (f) f.rotation.z = -s * (k === 1 ? 0.18 : 0.32);
    }
    const st = (h.cot ??= {})[lado] ??= { v: 0, a: 0 };
    const dobra = mola(st, 0.2 + 0.12 * Math.abs(h.balanco?.[lado] || 0) / 0.32 + cot * info.g, dt, 80, 14);
    o['lowerarm01.' + lado].quaternion.setFromAxisAngle(EIXO_X, -dobra).multiply(h.qCotovelo[lado]);
  }
  o['clavicle.L'].rotation.z = o['clavicle.R'].rotation.z = 0;
  if (info.pose === 'ombros') { o['clavicle.L'].rotation.z = 0.12 * info.g; o['clavicle.R'].rotation.z = -0.12 * info.g; }
  // pescoço e cabeça dividem a rotação; os olhos completam o que a cabeça ainda não virou
  const [rx, ry, rz] = rotCabeca;
  o.neck02.rotation.set(rx * 0.35, ry * 0.35, rz * 0.35, 'YXZ'); o.head.rotation.set(rx * 0.65, ry * 0.65, rz * 0.65, 'YXZ');
  for (const s of ['L', 'R']) o['eye.' + s]?.rotation.set(-clamp(olharResto[1], -0.3, 0.3), clamp(olharResto[0], -0.45, 0.45), 0);
  // rosto
  const alvo = { ...EXPR[info.ex] };
  const vol = clamp(info.vol / 0.8, 0, 1);
  for (const [k, v] of Object.entries(BOCA[info.forma] || {})) alvo[k] = Math.max(alvo[k] || 0, v * (0.6 + 0.4 * vol));
  if (info.pisca) alvo['eye-left-closure'] = alvo['eye-right-closure'] = 1;
  for (const k of new Set([...Object.keys(alvo), ...Object.keys(h.morph)])) {
    const v0 = h.morph[k] || 0, v1 = alvo[k] || 0;
    const vel = /closure/.test(k) ? 0.8 : /mouth-open|pursing|retraction/.test(k) ? 0.7 : 0.18;   // piscar e boca rápidos
    h.morph[k] = v0 + (v1 - v0) * clamp(vel * dt * 30, 0, 1); h.expressao(k, h.morph[k]);
  }
}

// ------------------------------------------------------------------ modo mocap
const T_ANDAR = 0;                                        // a caminhada capturada começa junto com a cena
function caminhoMocap() {                                 // começo/fim no mundo para terminar na marca do Beto
  if (caminhoMocap.c) return caminhoMocap.c;
  const w = MOCS.beto.andar, fim = B(CAMINHO.ate[0], CAMINHO.ate[1], 0), ini0 = B(CAMINHO.de[0], CAMINHO.de[1], 0);
  const yaw = Math.atan2(fim.x - ini0.x, fim.z - ini0.z);
  const d = new THREE.Vector3(w.rFim.x - w.r0.x, 0, w.rFim.z - w.r0.z).applyAxisAngle(new THREE.Vector3(0, 1, 0), yaw);
  return (caminhoMocap.c = { yaw, fim, inicio: fim.clone().sub(d), dur: w.dur });
}
function aplicarMocap(quem, R, info, t, dt, rotCabeca, olharResto) {
  const h = HUM[quem], o = h.osso;
  MOC.pose(MOCS, quem, t, { tAndar: T_ANDAR });
  if (quem === 'beto' && t - T_ANDAR >= MOCS.beto.andar.dur) {              // depois de chegar: âncora na marca
    o.root.position.x -= MOCS.beto.andar.rFim.x; o.root.position.z -= MOCS.beto.andar.rFim.z;
  }
  for (const [s, lado] of [[1, 'L'], [-1, 'R']]) for (let dd = 2; dd <= 5; dd++) for (let k = 1; k <= 3; k++) {
    const f = o[`finger${dd}-${k}.${lado}`]; if (f) f.rotation.z = -s * (k === 1 ? 0.18 : 0.32);   // dedos relaxados
  }
  // gestos de fala no espaço do mundo (gestos.js): alvos para mão, cotovelo e palma no referencial do tronco
  // do mocap. O peso tem mola, como os braços da marionete (sem ela a mão chegava a andar 23 cm num quadro).
  const st = (R.gesto.h ??= { v: 0, a: 0, pose: null });
  if (info.pose) st.pose = info.pose;
  const g = clamp(mola(st, info.pose ? info.g : 0, dt, 90, 15), 0, 1);
  const outro = quem === 'clara' ? 'beto' : 'clara';
  GES.aplicar(h, st.pose, g, { lado: quem === 'clara' ? 'L' : 'R', alvo: cabecaMundo(outro).add(new THREE.Vector3(0, -0.25, 0)) });
  // pescoço e cabeça: nivelados e guiados só pelo olhar (mocap.js, olhar); ?semolhar desliga o olhar
  MOC.olhar(MOCS, quem, SEM_OLHAR ? [0, 0, 0] : rotCabeca);
  for (const s of ['L', 'R']) o['eye.' + s]?.rotation.set(-clamp(olharResto[1], -0.3, 0.3), clamp(olharResto[0], -0.45, 0.45), 0);
  rostoHumano(h, info, dt);
  // pés: trava no chão; no fim o Beto dá dois passinhos para virar para a Clara
  const frente = new THREE.Vector3(Math.sin(R.raiz.rotation.y), 0, Math.cos(R.raiz.rotation.y));
  let troca = null;
  if (quem === 'beto') {
    const cm = caminhoMocap(), tA = T_ANDAR + cm.dur + 0.15;
    if (t >= tA) {
      const est = (aplicarMocap.passos ??= {});
      troca = {};
      [['L', tA, 1], ['R', tA + 0.24, -1]].forEach(([lado, t0, s]) => {
        if (t < t0) return;
        est[lado] ??= (MOCS.beto.pes[lado].trava || o['foot.' + lado].getWorldPosition(new THREE.Vector3()).setY(0)).clone();
        const novo = cm.fim.clone().add(new THREE.Vector3(s * 0.11, 0, 0).applyAxisAngle(new THREE.Vector3(0, 1, 0), VIRADA.beto));
        const u = clamp((t - t0) / 0.32, 0, 1), e = u * u * (3 - 2 * u);
        troca[lado] = est[lado].clone().lerp(novo, e); troca[lado + 'Alto'] = 0.04 * Math.sin(Math.PI * u);
      });
    }
  }
  h.raiz.updateMatrixWorld(true);
  MOC.travarPes(MOCS, quem, dt, LOC, frente, troca);
}
function rostoHumano(h, info, dt) {
  const alvo = { ...EXPR[info.ex] };
  const vol = clamp(info.vol / 0.8, 0, 1);
  for (const [k, v] of Object.entries(BOCA[info.forma] || {})) alvo[k] = Math.max(alvo[k] || 0, v * (0.6 + 0.4 * vol));
  if (info.pisca) alvo['eye-left-closure'] = alvo['eye-right-closure'] = 1;
  for (const k of new Set([...Object.keys(alvo), ...Object.keys(h.morph)])) {
    const v0 = h.morph[k] || 0, v1 = alvo[k] || 0;
    const vel = /closure/.test(k) ? 0.8 : /mouth-open|pursing|retraction/.test(k) ? 0.7 : 0.18;
    h.morph[k] = v0 + (v1 - v0) * clamp(vel * dt * 30, 0, 1); h.expressao(k, h.morph[k]);
  }
}

// ------------------------------------------------------------------ direção da cena
// Beto vem do balcão até o lugar dele enquanto a Clara pergunta (passos a cada 0,32 s, como no Blender)
const CAMINHO = linha.caminhada || { t0: 0.0, t1: 2.5, de: [2.85, 0.3], ate: [0.75, 0.0] };
const VIRADA = { clara: 0.42, beto: -0.42 };          // "cheat" de sitcom: meio de frente para a câmera, meio para o outro
// caminhada com velocidade de gente (~1,1 m/s): acelera, anda e freia; pegadas planejadas (locomocao.js)
const P0 = CAMINHO.de, P1 = CAMINHO.ate, DIST = Math.hypot(P1[0] - P0[0], P1[1] - P0[1]);
const PERF = LOC.perfil(DIST, CAMINHO.t1 - CAMINHO.t0);
const PASSOS = LOC.planejar({ D: DIST, T: CAMINHO.t1 - CAMINHO.t0, yawAnda: Math.atan2(P1[0] - P0[0], P0[1] - P1[1]),
                              yawFim: VIRADA.beto, perf: PERF });
function posicaoBeto(t) {
  const { t0, t1 } = CAMINHO;
  // versões realistas: velocidade em trapézio (casa com as pegadas planejadas). Versão estilizada: a curva
  // aprovada em 20/11 (acelera e freia), que é dela; a troca de 21/11 tinha vazado para ela sem pedido.
  const u = clamp((t - t0) / (t1 - t0), 0, 1);
  const k = HUMANOS ? PERF.s(t - t0) / DIST : u - Math.sin(2 * Math.PI * u) / (2 * Math.PI);
  return { x: lerp(P0[0], P1[0], k), y: lerp(P0[1], P1[1], k), andando: t > t0 && t < t1, u: HUMANOS ? k : u };
}
const cabecaMundo = quem => HUMANOS ? HUM[quem].osso.head.localToWorld(new THREE.Vector3(0, 0.07, 0.06))
                                    : RIG[quem].cabeca.localToWorld(new THREE.Vector3(0, 0.22, 0));
function alvoOlhar(quem, t, q) {
  const outro = quem === 'clara' ? 'beto' : 'clara';
  const ex = q[quem].ex;
  if (quem === 'beto') {
    const leg = linha.legendas.find(l => t >= l.fala0 - 0.2 && t < l.fala1 + 0.6);
    if (leg && /lâmpada/i.test(leg.texto) && t > leg.fala0 + 0.55) return B(0.62, -0.35, 2.9);          // olha para cima, para a lâmpada
    if (ex === 'nervoso' && Math.sin(t * 2.3) > 0.55) return B(1.6, -2.5, HUMANOS ? 1.35 : 1.0);         // desvia o olhar
    if (MOCAP && t - T_ANDAR < caminhoMocap().dur - 0.6) {
      const cm = caminhoMocap(); return cabecaMundo('beto').add(new THREE.Vector3(Math.sin(cm.yaw), -0.15, Math.cos(cm.yaw)).multiplyScalar(3));
    }
    if (!MOCAP && posicaoBeto(t).andando) { const p = posicaoBeto(t + 0.4); return B(p.x - 0.9, -0.6, HUMANOS ? 1.55 : 1.15); }
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
    if (MOCAP && quem === 'beto') {
      const cm = caminhoMocap(), fim = t - T_ANDAR >= cm.dur;
      R.raiz.position.copy(fim ? cm.fim : cm.inicio);
      if (!fim) { R.giro.v = cm.yaw; R.giro.a = 0; yawCorpo = cm.yaw; }
    } else if (quem === 'beto') {
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
    const alvo = alvoOlhar(quem, t, q);
    const d = alvo.clone().sub(cabecaMundo(quem));
    d.applyAxisAngle(new THREE.Vector3(0, 1, 0), -R.raiz.rotation.y);
    const yaw = clamp(Math.atan2(d.x, d.z), -1.15, 1.15), pitch = clamp(Math.atan2(d.y, Math.hypot(d.x, d.z)), -0.5, 0.55);
    const ol = R.olhar; ol.y ??= { v: 0, a: 0 }; ol.p ??= { v: 0, a: 0 };
    const vy = mola(ol.y, yaw, dt, 70, 14), vp = mola(ol.p, pitch, dt, 70, 14);
    let tilt = 0, nod = 0;
    if (info.ex === 'suspeita') tilt = 0.12;
    if (info.ex === 'nervoso') tilt = Math.sin(t * 9) * 0.035;
    if (info.vol) nod = info.vol * 0.06 * Math.sin(t * 13);
    R.cabeca.rotation.set(-vp * 0.85 + nod, vy * 0.85, tilt * lado, 'YXZ');
    if (HUMANOS) aplicarHumano(quem, R, info, t, dt, fase, [-vp * 0.85 + nod, vy * 0.85, tilt * lado], [yaw - vy * 0.85, pitch - vp * 0.85]);
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
      const alvoB = H_BETO().add(B(0, 0, -0.05)), alvoL = B(0.05, 0.95, 2.05), alvoG = B(-0.1, 0.4, 1.15);
      let alvo = alvoB.clone().lerp(alvoL, a * (1 - b) * 0.42); alvo.lerp(alvoG, b);
      return { pos, alvo, mm: lerp(36, 34, b) }; } },
];
const CAM_DEBUG = new URLSearchParams(location.search).get('cam')?.split(',').map(Number);
function posicionarCamera(t) {
  if (CAM_DEBUG) {
    const [x, y, z, ax, ay, az, mm] = CAM_DEBUG; camera.position.copy(B(x, y, z)); camera.lookAt(B(ax, ay, az));
    camera.fov = lente(mm || 35); camera.updateProjectionMatrix(); return;
  }
  const p = PLANOS.find(p => t >= p.t0 && t < p.t1) || PLANOS.at(-1);
  const u = clamp((t - p.t0) / (Math.min(p.t1, DUR) - p.t0), 0, 1); const r = p.f(u, t);
  if (HUMANOS) {   // personagens realistas são mais altos (1,60 m e 1,78 m): câmera sobe junto
    const i = PLANOS.indexOf(p);
    r.pos.y += [0.15, 0.3, 0.3, 0.32, 0.26, 0.3][i];
    if (i >= 1 && i <= 4) r.mm *= 1.3;                     // closes mais fechados (rostos menores que os de massinha)
    if (i === 0) r.alvo.y += 0.25;
    if (i === 5) r.alvo.y += 0.25 * ease((t - 11.3) / 1.7);
  }
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
const SEM_LEGENDA = new URLSearchParams(location.search).has('semlegenda');   // vídeo limpo (para pós-produção/IA)
function legenda(t) {
  if (SEM_LEGENDA) return;
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
