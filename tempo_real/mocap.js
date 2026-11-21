// Mocap real (CMU Motion Capture Database, BVH) aplicado ao esqueleto do MakeHuman.
// - SkeletonUtils.retargetClip copia a rotação "no mundo" de cada osso da CMU para o osso correspondente;
//   como as poses de repouso diferem (CMU em T, MakeHuman em A), cada osso recebe um ajuste (localOffsets)
//   que leva a direção de repouso do MakeHuman até a da CMU.
// - A translação do quadril vira "root motion" controlada aqui (para encaixar no caminho da cena).
// - O IK de locomocao.js só trava os pés no chão quando o mocap diz que o pé está apoiado.
// Dados: tempo_real/mocap/*.bvh (base da CMU, livre para uso inclusive comercial; conversão BVH de Bruce Hahne).
import * as THREE from 'three';
import { BVHLoader } from 'three/addons/loaders/BVHLoader.js';
import * as SkeletonUtils from 'three/addons/utils/SkeletonUtils.js';

const Y = new THREE.Vector3(0, 1, 0);
const clamp = (v, a, b) => Math.min(b, Math.max(a, v));
const suave = u => { u = clamp(u, 0, 1); return u * u * (3 - 2 * u); };

// osso do MakeHuman -> osso da CMU
export const MAPA = (() => {
  const m = { root: 'Hips', spine05: 'LowerBack', spine04: 'LowerBack', spine03: 'Spine', spine02: 'Spine', spine01: 'Spine1',
              neck01: 'Neck', neck02: 'Neck1', neck03: 'Neck1', head: 'Head' };
  for (const [s, S] of [['L', 'Left'], ['R', 'Right']]) Object.assign(m, {
    [`clavicle.${s}`]: `${S}Shoulder`, [`upperarm01.${s}`]: `${S}Arm`, [`upperarm02.${s}`]: `${S}Arm`,
    [`lowerarm01.${s}`]: `${S}ForeArm`, [`lowerarm02.${s}`]: `${S}ForeArm`, [`wrist.${s}`]: `${S}Hand`,
    [`upperleg01.${s}`]: `${S}UpLeg`, [`upperleg02.${s}`]: `${S}UpLeg`, [`lowerleg01.${s}`]: `${S}Leg`,
    [`lowerleg02.${s}`]: `${S}Leg`, [`foot.${s}`]: `${S}Foot` });
  return m;
})();
// direção de repouso: segmentos inteiros (coxa = quadril->joelho etc.), não os ossinhos intermediários
const SEGMENTO = { upperleg01: ['upperleg01', 'lowerleg01'], upperleg02: ['upperleg01', 'lowerleg01'],
  lowerleg01: ['lowerleg01', 'foot'], lowerleg02: ['lowerleg01', 'foot'], foot: ['foot', 'toe3-1'],
  upperarm01: ['upperarm01', 'lowerarm01'], upperarm02: ['upperarm01', 'lowerarm01'],
  lowerarm01: ['lowerarm01', 'wrist'], lowerarm02: ['lowerarm01', 'wrist'], wrist: ['wrist', 'finger3-1'] };
function direcaoAlvo(meta, nome) {
  if (nome === 'root') return null;
  const o = Object.fromEntries(meta.ossos.map(x => [x.nome, x]));
  const [base, lado] = nome.split('.'), suf = lado ? '.' + lado : '';
  const [a, b] = SEGMENTO[base] ? [o[SEGMENTO[base][0] + suf].cabeca, o[SEGMENTO[base][1] + suf].cabeca] : [o[nome].cabeca, o[nome].cauda];
  if (!a || !b) return null;
  return new THREE.Vector3(b[0] - a[0], b[1] - a[1], b[2] - a[2]).normalize();
}
const FILHO_PREFERIDO = { Spine1: 'Neck', Neck1: 'Head', LeftHand: 'LeftFingerBase', RightHand: 'RightFingerBase', Hips: null };
function direcaoFonte(osso) {
  if (osso.name === 'Hips') return null;
  const filho = osso.children.find(c => c.name === FILHO_PREFERIDO[osso.name]) || osso.children[0];
  return filho && filho.position.lengthSq() > 1e-8 ? filho.position.clone().normalize() : null;
}

// base ortonormal de um osso: eixo 1 = direção; eixo 2 = "frente" do personagem (+z) tirada a componente do eixo 1
function base(d) {
  const ref = Math.abs(d.z) > 0.9 ? new THREE.Vector3(0, -1, 0) : new THREE.Vector3(0, 0, 1);   // pé aponta para a frente: usa "baixo"
  const e2 = ref.addScaledVector(d, -ref.dot(d)).normalize(), e3 = new THREE.Vector3().crossVectors(d, e2);
  return new THREE.Matrix4().makeBasis(d, e2, e3);
}
function alinharOsso(dT, dS) {                 // rotação que leva a base do MakeHuman até a base da CMU
  const m = base(dS).multiply(base(dT).transpose());
  return new THREE.Quaternion().setFromRotationMatrix(m);
}

export async function carregar(url) { return new BVHLoader().loadAsync(url); }

// retarget de um trecho [t0, t1] (segundos da CMU) para o personagem h; alinha a direção para +z
export function retargetar(h, bvh, { trecho, alinhar = 'deslocamento', fps = 30 }) {
  const { skeleton, clip } = bvh;
  const raiz = skeleton.bones[0];
  const grupo = raiz.parent?.isGroup ? raiz.parent : new THREE.Group(); if (!raiz.parent) grupo.add(raiz);
  const trilha = n => clip.tracks.find(t => t.name === n);
  const amostra = (n, tempo) => trilha(n).createInterpolant(new Float32Array(trilha(n).getValueSize())).evaluate(tempo).slice();
  const p0 = new THREE.Vector3().fromArray(amostra('Hips.position', trecho[0]));
  let rumo;
  if (alinhar === 'deslocamento') {
    const p1 = new THREE.Vector3().fromArray(amostra('Hips.position', trecho[1])); rumo = Math.atan2(p1.x - p0.x, p1.z - p0.z);
  } else {                                     // parado: para onde o quadril aponta
    const q = new THREE.Quaternion().fromArray(amostra('Hips.quaternion', trecho[0]));
    const f = new THREE.Vector3(0, 0, 1).applyQuaternion(q); rumo = Math.atan2(f.x, f.z);
  }
  grupo.rotation.set(0, -rumo, 0);
  const p0r = p0.clone().applyAxisAngle(Y, -rumo); grupo.position.set(-p0r.x, 0, -p0r.z);
  grupo.updateMatrixWorld(true);
  // ajustes de pose (T-pose do quadro 0 da CMU x pose A do MakeHuman). A conversão 2010 coloca uma T-pose de
  // frente para +z no quadro 0; a "pose zero" dos offsets não é ereta. Para cada osso:
  //   offset = inverso(rotação do osso da CMU no quadro 0) x (gira a direção do MakeHuman até a direção da CMU no quadro 0)
  const porNome = Object.fromEntries(skeleton.bones.map(b => [b.name, b]));
  const gRot = grupo.rotation.y, gPos = grupo.position.clone();
  grupo.rotation.set(0, 0, 0); grupo.position.set(0, 0, 0);
  for (const tr of clip.tracks) {
    const [nome, prop] = tr.name.split('.'); const b = porNome[nome]; if (!b) continue;
    const v = tr.createInterpolant(new Float32Array(tr.getValueSize())).evaluate(0);
    if (prop === 'quaternion') b.quaternion.fromArray(v); else if (prop === 'position') b.position.fromArray(v);
  }
  grupo.updateMatrixWorld(true);
  const localOffsets = {};
  for (const [alvo, fonte] of Object.entries(MAPA)) {
    const b = porNome[fonte]; if (!b) continue;
    const qRef = b.getWorldQuaternion(new THREE.Quaternion());
    let A = new THREE.Quaternion();
    const dT = direcaoAlvo(h.meta, alvo);
    const filho = fonte === 'Hips' ? null : (b.children.find(c => c.name === FILHO_PREFERIDO[fonte]) || b.children[0]);
    if (dT && filho) {
      const dS = filho.getWorldPosition(new THREE.Vector3()).sub(b.getWorldPosition(new THREE.Vector3()));
      // alinha o osso inteiro (direção + "lado da frente"), não só a direção: assim o cotovelo e o joelho
      // dobram no mesmo plano da pessoa capturada (sem a torção que juntava as mãos na frente do corpo)
      if (dS.lengthSq() > 1e-8) A = alinharOsso(dT, dS.normalize());
    }
    localOffsets[alvo] = new THREE.Matrix4().makeRotationFromQuaternion(qRef.invert().multiply(A));
  }
  grupo.rotation.set(0, gRot, 0); grupo.position.copy(gPos); grupo.updateMatrixWorld(true);
  const escala = h.osso.root.userData.p0.y / p0.y;           // altura do quadril do personagem / da pessoa capturada
  // o retarget trabalha com o personagem na origem: solta-o da marionete por um instante
  const pai = h.raiz.parent, pos = h.raiz.position.clone(), rot = h.raiz.quaternion.clone();
  pai?.remove(h.raiz); h.raiz.position.set(0, 0, 0); h.raiz.quaternion.identity(); h.raiz.updateMatrixWorld(true);
  const alvoMalha = h.malhas[0];
  const novo = SkeletonUtils.retargetClip(alvoMalha, skeleton, clip, { names: MAPA, hip: 'Hips', scale: escala, localOffsets, trim: trecho, fps });
  alvoMalha.skeleton.pose();
  pai?.add(h.raiz); h.raiz.position.copy(pos); h.raiz.quaternion.copy(rot); h.raiz.updateMatrixWorld(true);
  // a translação do quadril sai do clipe e vira dado (root motion)
  const iPos = novo.tracks.findIndex(t => t.name === '.bones[root].position');
  const raizTrilha = novo.tracks.splice(iPos, 1)[0];
  return { clip: novo, raiz: raizTrilha, dur: novo.duration, escala, rumo };
}
function amostrar(trilha, tempo) {
  return new THREE.Vector3().fromArray(trilha.createInterpolant(new Float32Array(3)).evaluate(clamp(tempo, 0, trilha.times[trilha.times.length - 1])));
}

// ------------------------------------------------------------------ montagem na cena
// beto: caminhada (16_34 "slow walk, stop": entra andando e para) + idle (113_21 "Standing Still"); clara: idle.
// (a 133_11 "Walk Stop Walk" foi descartada: a pessoa capturada anda curvada, 25–38° para a frente)
export async function preparar(HUM, { pasta = './mocap/' } = {}) {
  const andar = await carregar(pasta + '16_34.bvh');
  const parado = await carregar(pasta + '113_21.bvh');
  const M = {};
  for (const quem of Object.keys(HUM)) {
    const h = HUM[quem], e = (M[quem] = { h });
    e.mixer = new THREE.AnimationMixer(h.malhas[0]);
    const idle = retargetar(h, parado, { trecho: quem === 'beto' ? [1.0, 11.0] : [3.0, 11.0], alinhar: 'frente' });
    e.idle = { ...idle, acao: e.mixer.clipAction(idle.clip) };
    e.idle.acao.play(); e.idle.r0 = amostrar(idle.raiz, 0);
    if (quem === 'beto') {
      const w = retargetar(h, andar, { trecho: [0.02, 2.88], alinhar: 'deslocamento' });   // quadro 0 é a T-pose
      e.andar = { ...w, acao: e.mixer.clipAction(w.clip) };
      e.andar.acao.setLoop(THREE.LoopOnce); e.andar.acao.clampWhenFinished = true; e.andar.acao.play();
      e.andar.r0 = amostrar(w.raiz, 0); e.andar.rFim = amostrar(w.raiz, w.dur);
    }
    e.pes = { L: { w: 0, trava: null, ult: null }, R: { w: 0, trava: null, ult: null } };
  }
  return M;
}

// pose do corpo no instante t (segundos da cena). tAndar: quando o clipe de caminhada começa.
export function pose(M, quem, t, { tAndar = 0, transicao = 0.5 } = {}) {
  const e = M[quem], h = e.h, o = h.osso;
  e.idle.acao.time = (t + (quem === 'clara' ? 2.3 : 0)) % e.idle.dur;
  let pAndar = 0, raiz;
  const ri = amostrar(e.idle.raiz, e.idle.acao.time).sub(e.idle.r0);       // balanço do idle (pequeno)
  if (e.andar) {
    const tau = t - tAndar; e.andar.acao.time = clamp(tau, 0, e.andar.dur);
    pAndar = 1 - suave((tau - (e.andar.dur - transicao)) / transicao);
    const ra = amostrar(e.andar.raiz, e.andar.acao.time);
    if (tau < e.andar.dur) raiz = ra.clone().lerp(new THREE.Vector3(e.andar.rFim.x + ri.x, e.idle.r0.y + ri.y, e.andar.rFim.z + ri.z), 1 - pAndar);
    else raiz = new THREE.Vector3(e.andar.rFim.x + ri.x, e.idle.r0.y + ri.y, e.andar.rFim.z + ri.z);
  } else raiz = new THREE.Vector3(ri.x, e.idle.r0.y + ri.y, ri.z);
  e.idle.acao.setEffectiveWeight(1 - pAndar); e.andar?.acao.setEffectiveWeight(pAndar);
  e.mixer.update(0);
  o.root.position.copy(raiz);
  return { andando: pAndar > 0.5, pAndar };
}

// trava os pés: quando o pé está perto do chão e quase parado no mocap, ele fica preso onde pousou
const _v = new THREE.Vector3(), _q = new THREE.Quaternion();
export function travarPes(M, quem, dt, LOC, frente, troca = null) {
  const e = M[quem], h = e.h, o = h.osso;
  h.raiz.updateMatrixWorld(true);
  for (const lado of ['L', 'R']) {
    const p = e.pes[lado], pe = o['foot.' + lado];
    const ank = pe.getWorldPosition(new THREE.Vector3());
    const vel = p.ult ? Math.hypot(ank.x - p.ult.x, ank.z - p.ult.z) / Math.max(dt, 1e-3) : 0;
    p.ult = ank.clone();
    const noChao = ank.y < 0.074 + 0.035 && vel < 0.45;
    if (noChao && !p.trava) p.trava = new THREE.Vector3(ank.x, 0, ank.z);
    if (!noChao && p.trava && (vel > 0.7 || ank.y > 0.074 + 0.06)) p.trava = null;
    if (troca?.[lado]) p.trava = troca[lado];                     // passinho de ajuste (virar no fim)
    p.w = clamp(p.w + (p.trava ? dt / 0.06 : -dt / 0.1), 0, 1);
    if (p.w <= 0 || !p.trava) continue;
    // guarda a pose do mocap, aplica o IK e mistura
    const ossos = ['upperleg01.' + lado, 'lowerleg01.' + lado, 'foot.' + lado].map(n => o[n]);
    const antes = ossos.map(b => b.quaternion.clone());
    const qPe = pe.getWorldQuaternion(_q).clone();
    const alvo = p.trava.clone(); if (troca?.[lado + 'Alto']) alvo.y += troca[lado + 'Alto'];
    LOC.perna(h, lado, alvo, null, 0, frente, qPe);
    ossos.forEach((b, i) => b.quaternion.copy(antes[i].slerp(b.quaternion, p.w)));
  }
  h.raiz.updateMatrixWorld(true);
}
