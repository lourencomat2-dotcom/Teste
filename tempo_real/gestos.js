// Gestos de fala no espaço do mundo (versão com mocap, ?humanos&mocap).
// Cada gesto é um alvo no referencial do tronco do mocap: onde fica o punho, para onde aponta o cotovelo
// e para onde vira a palma. Um IK de duas articulações (braço e antebraço, como o das pernas) gira os ossos
// até lá. A mistura com o mocap é feita nos alvos, não nas rotações locais: a mão anda em linha reta da
// pose do mocap até o gesto. Antes, misturar rotações locais (pensadas para a marionete) dava braços
// esticados no "não sei" e poses intermediárias estranhas.
//   preparar(h)                      uma vez por personagem (medidas do braço e da palma no repouso)
//   aplicar(h, pose, g, { lado, alvo })   depois do mocap e antes de travar os pés; pose: aponta | ombros | cintura
import * as THREE from 'three';

const clamp = (v, a, b) => Math.min(b, Math.max(a, v));
const SINAL = { L: 1, R: -1 };                 // +x = lado esquerdo do personagem
const IDENT = new THREE.Quaternion();

// base ortonormal: eixo 1 = d; eixo 2 = parte de v perpendicular a d
function base(d, v) {
  const e1 = d.clone().normalize(), e2 = v.clone().addScaledVector(e1, -v.dot(e1)).normalize();
  return new THREE.Matrix4().makeBasis(e1, e2, new THREE.Vector3().crossVectors(e1, e2));
}
// rotação no mundo que leva o par de repouso (d0, v0) até (d, v)
const alinhar = (d0, v0, d, v) => new THREE.Quaternion().setFromRotationMatrix(base(d, v).multiply(base(d0, v0).transpose()));
const P = (h, n) => h.osso[n].getWorldPosition(new THREE.Vector3());
const Qm = (b) => b.getWorldQuaternion(new THREE.Quaternion());
const repouso = (h, n) => new THREE.Vector3(...h.meta.ossos.find(o => o.nome === n).cabeca);
// no repouso todo osso tem rotação identidade no mundo: direções de repouso valem também no referencial local

export function preparar(h) {
  h.gestos = {};
  for (const s of ['L', 'R']) {
    const S = repouso(h, 'upperarm01.' + s), E = repouso(h, 'lowerarm01.' + s), W = repouso(h, 'wrist.' + s);
    const u0 = E.clone().sub(S).normalize(), f0 = W.clone().sub(E).normalize();
    const n0 = new THREE.Vector3().crossVectors(u0, f0).normalize();          // normal do plano do cotovelo
    // palma: perpendicular à mão e à linha dos nós dos dedos; no repouso (pose A) ela olha para o corpo
    const mao = repouso(h, 'finger3-1.' + s).sub(W), nos = repouso(h, 'finger5-1.' + s).sub(repouso(h, 'finger2-1.' + s));
    const p0 = new THREE.Vector3().crossVectors(mao, nos).normalize();
    if (p0.x * SINAL[s] > 0) p0.negate();
    p0.addScaledVector(f0, -p0.dot(f0)).normalize();
    h.gestos[s] = { a: S.distanceTo(E), b: E.distanceTo(W), u0, f0, n0, p0 };
  }
}

// dedos: dobra de cada falange (radianos) por dedo [indicador, médio, anelar, mínimo]; padrão = relaxado
const RELAXADO = k => (k === 1 ? 0.18 : 0.32);
const DEDOS = {
  aponta: (d, k) => (d === 2 ? 0.02 : k === 1 ? 0.95 : 1.15),       // indicador esticado, os outros fechados
  ombros: (d, k) => (k === 1 ? 0.08 : 0.14),                        // mão aberta
  cintura: (d, k) => (k === 1 ? 0.3 : 0.4),
};

// alvos do gesto no mundo, a partir do ombro S, do tronco (eixos X, Y, Z) e do quadril
function alvos(h, pose, s, S, T, Qd, alvo) {
  const sg = SINAL[s], { X, Y, Z } = T;
  const v = (x, y, z, E = T) => E.X.clone().multiplyScalar(x).addScaledVector(E.Y, y).addScaledVector(E.Z, z);
  if (pose === 'ombros') {                     // "não sei": cotovelos junto do corpo, antebraços para fora, palmas para cima
    return { W: S.clone().add(v(sg * 0.17, -0.24, 0.26)), polo: v(sg * 0.35, -1, -0.45), palma: v(sg * 0.3, 1, 0), clavicula: 0.12 };
  }
  if (pose === 'aponta') {                     // braço quase esticado na direção do outro, palma para baixo
    const dir = alvo ? alvo.clone().sub(S).normalize() : v(sg * 0.3, 0, 1).normalize();
    return { W: S.clone().addScaledVector(dir, 0.5), polo: v(sg * 0.4, -1, 0), palma: v(-sg * 0.4, -1, 0), clavicula: 0 };
  }
  if (pose === 'cintura') {                    // mãos na cintura: punho na lateral do quadril, cotovelo para fora e para trás
    const R = P(h, 'root');
    return { W: R.add(v(sg * 0.205, 0.08, 0.06, Qd)), polo: v(sg, 0.1, -0.5, Qd), palma: v(-sg, 0, 0, Qd), clavicula: 0 };
  }
  return null;
}
const eixos = q => ({ X: new THREE.Vector3(1, 0, 0).applyQuaternion(q), Y: new THREE.Vector3(0, 1, 0).applyQuaternion(q), Z: new THREE.Vector3(0, 0, 1).applyQuaternion(q) });

export function aplicar(h, pose, g, { lado = 'R', alvo = null } = {}) {
  if (!pose || !DEDOS[pose] || g < 1e-3) return;
  g = clamp(g, 0, 1);
  const o = h.osso;
  h.raiz.updateMatrixWorld(true);
  const T = eixos(Qm(o.spine01)), Qd = eixos(Qm(o.root));
  for (const s of pose === 'aponta' ? [lado] : ['L', 'R']) {
    const R = h.gestos[s], sg = SINAL[s];
    const up1 = o['upperarm01.' + s], up2 = o['upperarm02.' + s], lo1 = o['lowerarm01.' + s], lo2 = o['lowerarm02.' + s];
    // 1) o que o mocap está fazendo agora (ponto de partida da mistura)
    const Sm = P(h, 'upperarm01.' + s), Em = P(h, 'lowerarm01.' + s), Wm = P(h, 'wrist.' + s);
    const em = Wm.clone().sub(Sm).normalize(), cot = Em.clone().sub(Sm);
    cot.addScaledVector(em, -cot.dot(em));
    const poloM = cot.lengthSq() > 1e-6 ? cot.normalize() : T.Y.clone().negate();
    const palmaM = R.p0.clone().applyQuaternion(Qm(lo2));
    const U2m = up2.quaternion.clone(), L2m = lo2.quaternion.clone();
    // 2) ombro: neutro (e sobe no "não sei")
    const A = alvos(h, pose, s, Sm, T, Qd, alvo);
    const qCla = new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0, 0, 1), sg * A.clavicula);
    o['clavicle.' + s].quaternion.slerp(qCla, g);
    h.raiz.updateMatrixWorld(true);
    const S = P(h, 'upperarm01.' + s);
    const G = alvos(h, pose, s, S, T, Qd, alvo);
    // 3) alvos misturados
    let W = Wm.clone().lerp(G.W, g);
    const polo = poloM.clone().lerp(G.polo.normalize(), g).normalize();
    const palma = palmaM.clone().lerp(G.palma.normalize(), g).normalize();
    // 4) IK de duas articulações (cotovelo no plano do polo)
    const { a, b } = R, e = W.clone().sub(S).normalize();
    const d = clamp(S.distanceTo(W), Math.abs(a - b) + 1e-3, (a + b) * 0.999);
    W = S.clone().addScaledVector(e, d);
    const pp = polo.clone().addScaledVector(e, -polo.dot(e)).normalize();
    const x = (a * a - b * b + d * d) / (2 * d), hh = Math.sqrt(Math.max(0, a * a - x * x));
    const E = S.clone().addScaledVector(e, x).addScaledVector(pp, hh);
    const u = E.clone().sub(S).normalize(), f = W.clone().sub(E).normalize();
    const n = new THREE.Vector3().crossVectors(u, f);
    const qU = alinhar(R.u0, R.n0, u, n.lengthSq() > 1e-6 ? n.normalize() : new THREE.Vector3().crossVectors(u, pp));
    const qF = alinhar(R.f0, R.p0, f, palma);
    // 5) rotações locais: a torção do braço e a do antebraço continuam divididas entre os dois ossos
    up2.quaternion.copy(U2m).slerp(IDENT, g);
    up1.quaternion.copy(Qm(up1.parent).invert().multiply(qU).multiply(up2.quaternion.clone().invert()));
    h.raiz.updateMatrixWorld(true);
    const rel = Qm(up2).invert().multiply(qF);                                  // antebraço em relação ao braço
    const ax = R.f0, tw = new THREE.Quaternion(ax.x * (rel.x * ax.x + rel.y * ax.y + rel.z * ax.z),
      ax.y * (rel.x * ax.x + rel.y * ax.y + rel.z * ax.z), ax.z * (rel.x * ax.x + rel.y * ax.y + rel.z * ax.z), rel.w).normalize();
    lo2.quaternion.copy(L2m).slerp(new THREE.Quaternion().slerp(tw, 0.5), g);   // metade da torção no lowerarm02
    lo1.quaternion.copy(rel).multiply(lo2.quaternion.clone().invert());
    o['wrist.' + s].quaternion.slerp(IDENT, g);                                 // mão alinhada com o antebraço
    // 6) dedos
    for (let dd = 2; dd <= 5; dd++) for (let k = 1; k <= 3; k++) {
      const fa = o[`finger${dd}-${k}.${s}`]; if (fa) fa.rotation.z = -sg * (RELAXADO(k) + (DEDOS[pose](dd, k) - RELAXADO(k)) * g);
    }
    h.raiz.updateMatrixWorld(true);
  }
}
