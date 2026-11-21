// Mede candidatos a "idle" (parado) da CMU e aponta o melhor trecho para a sitcom.
//   node tempo_real/escolher_idle.mjs <pasta com os .bvh> [duração da janela em s, padrão 10]
// Para cada arquivo, procura a janela (passo de 0,5 s) com tronco e cabeça mais retos, mãos caídas
// ao lado do corpo e sem sair do lugar. Mede no mesmo leitor de BVH da cena (three.js), em relação à
// T-pose do quadro 0 (a conversão de 2010 põe uma T-pose de frente para +z no quadro 0).
// Medidas (pior valor na janela):
//   tronco: ângulo entre quadril->pescoço e a vertical
//   cabeça: inclinação lateral (linha dos olhos x horizontal) desde a T-pose
//   mãos:   altura do punho abaixo do quadril (m, na escala do Beto); < 0,10 = mão no bolso/cintura/braço cruzado
//   desvio: quanto o quadril anda no chão (m); balanço: movimento típico da cabeça (cm)
//   emenda: diferença de pose entre o começo e o fim da janela (graus; pequeno = repete sem pulo)
import fs from 'fs'; import path from 'path'; import * as THREE from 'three';
import { BVHLoader } from 'three/addons/loaders/BVHLoader.js';

const pasta = process.argv[2] || 'mocap', JANELA = +(process.argv[3] || 10), FPS = 30, QUADRIL_BETO = 0.947;
const Y = new THREE.Vector3(0, 1, 0), graus = r => r * 180 / Math.PI;
const linhas = [];
for (const arq of fs.readdirSync(pasta).filter(f => f.endsWith('.bvh')).sort()) {
  const { skeleton, clip } = new BVHLoader().parse(fs.readFileSync(path.join(pasta, arq), 'utf8'));
  const g = new THREE.Group(); g.add(skeleton.bones[0]);
  const mixer = new THREE.AnimationMixer(g), acao = mixer.clipAction(clip); acao.play();
  const b = Object.fromEntries(skeleton.bones.map(x => [x.name, x]));
  const P = n => b[n].getWorldPosition(new THREE.Vector3()), Q = n => b[n].getWorldQuaternion(new THREE.Quaternion());
  const em = t => { acao.time = t; mixer.update(0); g.updateMatrixWorld(true); };
  em(0); const ref = Q('Head'), h0 = P('Hips').y, esc = QUADRIL_BETO / h0;
  const ossos = ['LowerBack', 'Spine', 'Spine1', 'Neck', 'Neck1', 'Head', 'LeftArm', 'RightArm', 'LeftForeArm', 'RightForeArm', 'LeftUpLeg', 'RightUpLeg'];
  const quadros = [];
  for (let t = 0.5; t <= clip.duration; t += 1 / FPS) {         // pula a T-pose do começo
    em(t);
    const hip = P('Hips'), dT = P('Neck').sub(hip).normalize(), tronco = graus(dT.angleTo(Y));
    // lado x frente do tronco, no referencial para onde o quadril aponta
    const fq = new THREE.Vector3(0, 0, 1).applyQuaternion(Q('Hips')).setY(0).normalize(), lq = new THREE.Vector3().crossVectors(Y, fq);
    const lateral = Math.abs(graus(Math.atan2(dT.dot(lq), dT.y))), frente = graus(Math.atan2(dT.dot(fq), dT.y));
    const olhos = new THREE.Vector3(1, 0, 0).applyQuaternion(Q('Head').multiply(ref.clone().invert()));
    const maos = Math.min(hip.y - P('LeftHand').y, hip.y - P('RightHand').y) * esc;
    quadros.push({ t, tronco, lateral, frente, cabeca: Math.abs(graus(Math.asin(THREE.MathUtils.clamp(olhos.y, -1, 1)))), maos,
                   chao: new THREE.Vector2(hip.x, hip.z).multiplyScalar(esc), topo: P('Head').multiplyScalar(esc),
                   rot: ossos.map(n => b[n].quaternion.clone()) });
  }
  const n = Math.min(quadros.length, Math.round(JANELA * FPS));
  let melhor = null;
  for (let i = 0; i + n <= quadros.length; i += FPS / 2) {
    const w = quadros.slice(i, i + n), max = k => Math.max(...w.map(q => q[k]));
    const desvio = Math.max(...w.map(q => q.chao.distanceTo(w[0].chao)));
    const media = w.reduce((s, q) => s.add(q.topo), new THREE.Vector3()).divideScalar(w.length);
    const balanco = 100 * Math.sqrt(w.reduce((s, q) => s + q.topo.distanceToSquared(media), 0) / w.length);
    const emenda = graus(w[0].rot.reduce((s, q, k) => s + q.angleTo(w[w.length - 1].rot[k]), 0) / ossos.length);
    const r = { arq, t0: w[0].t, t1: w[w.length - 1].t, tronco: max('tronco'), cabeca: max('cabeca'), lateral: max('lateral'),
                frenteMin: Math.min(...w.map(q => q.frente)), frenteMax: max('frente'),
                maos: Math.min(...w.map(q => q.maos)), desvio, balanco, emenda };
    // nota: o que mais pesa é tronco/cabeça tortos; mão fora do lugar e sair do lugar desclassificam
    r.nota = Math.max(r.tronco, r.cabeca) + (r.maos < 0.10 ? 50 : 0) + (r.desvio > 0.15 ? 50 : 0) + 0.2 * r.emenda;
    if (!melhor || r.nota < melhor.nota) melhor = r;
  }
  linhas.push({ ...melhor, dur: clip.duration });
}
const f = (x, d = 1) => x.toFixed(d).replace('.', ',');
console.log(`janela de ${JANELA} s · aprovado = tronco < 8°, cabeça < 8°, mãos > 0,10 m abaixo do quadril, desvio < 0,15 m`);
console.log('arquivo      dur    trecho          tronco (lado; frente)       cabeça  mãos  desvio balanço emenda');
for (const r of linhas.sort((a, b) => a.nota - b.nota)) {
  const ok = r.tronco < 8 && r.cabeca < 8 && r.maos > 0.10 && r.desvio < 0.15;
  console.log(`${r.arq.padEnd(12)} ${f(r.dur).padStart(5)}s  ${f(r.t0).padStart(5)}–${f(r.t1).padEnd(5)}s  ${f(r.tronco).padStart(5)}° (${f(r.lateral).padStart(4)}°; ${f(r.frenteMin).padStart(5)} a ${f(r.frenteMax).padStart(4)}°) ${f(r.cabeca).padStart(5)}°  ${f(r.maos, 2)}  ${f(r.desvio, 2)}  ${f(r.balanco).padStart(5)}cm ${f(r.emenda).padStart(5)}° ${ok ? 'APROVADO' : ''}`);
}
