// Caminhada com pés plantados no chão: pegadas planejadas ao longo do caminho + IK de duas articulações.
// O pé que apoia fica parado no chão enquanto o corpo passa por cima (sem "patinar"); o outro faz o arco
// do passo, sai pela ponta e chega pelo calcanhar. Quadril sobe/desce e balança; braços em oposição.
import * as THREE from 'three';

const clamp = (v, a, b) => Math.min(b, Math.max(a, v));
const suave = u => { u = clamp(u, 0, 1); return u * u * (3 - 2 * u); };

// velocidade em trapézio: acelera em ta, anda em velocidade constante, freia em td (segundos)
export function perfil(D, T, ta = 0.55, td = 0.65) {
  const v = D / (T - ta / 2 - td / 2);
  const s = t => {
    if (t <= 0) return 0; if (t >= T) return D;
    if (t < ta) return 0.5 * v * t * t / ta;
    if (t < T - td) return 0.5 * v * ta + v * (t - ta);
    const r = T - t; return D - 0.5 * v * r * r / td;
  };
  const tempo = alvo => { let a = 0, b = T; for (let k = 0; k < 40; k++) { const m = (a + b) / 2; if (s(m) < alvo) a = m; else b = m; } return (a + b) / 2; };
  return { s, tempo, v, D, T };
}

// pegadas: distâncias ao longo do caminho em que cada pé pousa (alternando), terminando com os pés juntos
// e dois passinhos de ajuste para virar para a câmera/Clara no fim
export function planejar({ D, T, yawAnda, yawFim, perf, periodo = 0.5, swing = 0.44, frente = 0.25 }) {
  // ritmo de gente: um passo a cada ~0,5 s; cada pé pousa ~25 cm à frente do quadril e só sai do chão
  // depois que o outro pousou (sempre um pé apoiado: andar, não correr). Termina com os pés juntos.
  const passos = [], pos = { L: 0, R: 0 };
  let t = 0.45, lado = 'R', ultimoPouso = -0.05;
  while (passos.length < 20) {
    let d = Math.min(D, perf.s(t) + frente); if (d > D - 0.04) d = D;
    passos.push({ pe: lado, d, yaw: yawAnda, tSai: Math.max(-0.05, ultimoPouso + 0.04, t - swing), tPousa: t });
    pos[lado] = d; ultimoPouso = t;
    if (pos.L >= D - 1e-6 && pos.R >= D - 1e-6) break;
    lado = lado === 'R' ? 'L' : 'R'; t += periodo;
  }
  // ajuste final: cada pé dá um passinho girando para a nova direção
  const ultimo = passos[passos.length - 1].pe, outro = ultimo === 'L' ? 'R' : 'L';
  const t0 = Math.max(T, passos[passos.length - 1].tPousa) + 0.05;
  passos.push({ pe: outro, d: D, yaw: yawFim, tSai: t0, tPousa: t0 + 0.32, ajuste: true });
  passos.push({ pe: ultimo, d: D, yaw: yawFim, tSai: t0 + 0.24, tPousa: t0 + 0.56, ajuste: true });
  return passos;
}

// estado de um pé no tempo t: ponto no chão (distância no caminho), yaw, altura do arco e inclinação do pé
export function pe(passos, lado, t, perf) {
  const meus = passos.filter(p => p.pe === lado);
  let anterior = { d: 0, yaw: meus[0]?.yaw ?? 0, tPousa: -1 };
  for (const p of meus) {
    if (t < p.tSai) break;                                     // ainda não saiu: apoiado no anterior
    if (t < p.tPousa) {                                        // no ar: arco entre as pegadas
      const u = (t - p.tSai) / (p.tPousa - p.tSai), e = suave(u);
      const alto = (p.ajuste ? 0.035 : 0.07) * Math.sin(Math.PI * clamp(u * 1.1, 0, 1));
      const incl = p.ajuste ? 0 : 0.42 * Math.pow(1 - clamp(u / 0.35, 0, 1), 2) - 0.28 * Math.pow(clamp((u - 0.7) / 0.3, 0, 1), 2);
      return { d: anterior.d + (p.d - anterior.d) * e, yaw: anterior.yaw + (p.yaw - anterior.yaw) * e, alto, incl, apoio: false, u };
    }
    anterior = p;
  }
  // apoiado: no fim do apoio o calcanhar sobe (a ponta empurra) antes do próximo passo
  const prox = meus.find(p => p.tSai > t);
  let incl = 0;
  if (prox && !prox.ajuste) incl = 0.42 * suave(1 - (prox.tSai - t) / 0.18);
  if (anterior.tPousa >= 0 && !anterior.ajuste) incl -= 0.28 * Math.pow(1 - suave((t - anterior.tPousa) / 0.12), 2);  // calcanhar assentando
  return { d: anterior.d, yaw: anterior.yaw, alto: 0, incl, apoio: true };
}

// ------------------------------------------------------------------ IK de duas articulações (coxa e canela)
const _q = new THREE.Quaternion(), _qp = new THREE.Quaternion(), _v = [0, 1, 2, 3, 4, 5].map(() => new THREE.Vector3());
function girarNoMundo(osso, de, para) {
  _q.setFromUnitVectors(de, para);
  osso.parent.getWorldQuaternion(_qp);
  const pinv = _qp.clone().invert();
  osso.quaternion.copy(pinv.multiply(_q).multiply(_qp).multiply(osso.quaternion));
}
function rotacaoNoMundo(osso, qMundo) {
  osso.parent.getWorldQuaternion(_qp);
  osso.quaternion.copy(_qp.invert().multiply(qMundo));
}
const ALTURA_TORNOZELO = 0.074;
export function perna(h, lado, chao, yawPe, incl, frente, qPeMundo = null) {
  const o = h.osso, coxa = o['upperleg01.' + lado], canela = o['lowerleg01.' + lado], pe = o['foot.' + lado];
  coxa.quaternion.identity(); canela.quaternion.identity(); pe.quaternion.identity();
  h.raiz.updateMatrixWorld(true);
  const H = coxa.getWorldPosition(_v[0]), K0 = canela.getWorldPosition(_v[1]).clone(), A0 = pe.getWorldPosition(_v[2]).clone();
  const a = H.distanceTo(K0), b = K0.distanceTo(A0);
  // tornozelo sobe quando o pé inclina (gira na ponta ao sair, no calcanhar ao chegar)
  const alvo = chao.clone(); alvo.y += ALTURA_TORNOZELO + (incl > 0 ? 0.13 * Math.sin(incl) : 0.05 * Math.sin(-incl));
  let d = H.distanceTo(alvo); const dmax = (a + b) * 0.995;
  if (d > dmax) { alvo.sub(H).setLength(dmax).add(H); d = dmax; }
  const eixo = _v[3].copy(alvo).sub(H).normalize();
  const polo = frente.clone().addScaledVector(eixo, -frente.dot(eixo)).normalize();     // joelho para a frente
  const x = (a * a - b * b + d * d) / (2 * d), hh = Math.sqrt(Math.max(0, a * a - x * x));
  const K = H.clone().addScaledVector(eixo, x).addScaledVector(polo, hh);
  girarNoMundo(coxa, K0.clone().sub(H).normalize(), K.clone().sub(H).normalize());
  h.raiz.updateMatrixWorld(true);
  const K1 = canela.getWorldPosition(_v[4]).clone(), A1 = pe.getWorldPosition(_v[5]).clone();
  girarNoMundo(canela, A1.sub(K1).normalize(), alvo.clone().sub(K1).normalize());
  h.raiz.updateMatrixWorld(true);
  const qPe = qPeMundo || new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0, 1, 0), yawPe)
    .multiply(new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(1, 0, 0), incl));
  rotacaoNoMundo(pe, qPe);
}
