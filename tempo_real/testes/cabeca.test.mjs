// A cabeça não pode tombar nem o pescoço entortar (versão ?humanos&mocap).
// Mede a pose que o mocap.js entrega (pose + olhar sem alvo; sem os gestos da cena), em 40 instantes de cada clipe:
//   inclinação lateral da cabeça: ângulo entre o eixo "para cima" da cabeça e a vertical, no plano lateral
//     (perpendicular à frente da cabeça; acenar com a cabeça não conta);
//   curvatura do pescoço: quanto a direção neck01->head mudou em relação ao tronco (spine01), comparada
//     com a pose de repouso. (O ângulo cru spine01->neck01 x neck01->head não serve: no repouso ele já é
//     25° na Clara e 1° no Beto, por causa do formato do corpo.)
// Limites: inclinação < 12°, curvatura < 15°.
import * as THREE from 'three';
import { pos, eixo, graus, teste, afirmar } from './esqueleto.mjs';
import { cena, MOC } from './comum.mjs';

const LIMITE_INCL = 12, LIMITE_CURVA = 15, N = 40;
const { HUM, M } = await cena();
const Y = new THREE.Vector3(0, 1, 0);
const repouso = (h, n) => new THREE.Vector3(...h.meta.ossos.find(o => o.nome === n).cabeca);

function inclinacao(h) {
  const cima = eixo(h, 'head', [0, 1, 0]), frente = eixo(h, 'head', [0, 0, 1]).setY(0).normalize();
  const lado = new THREE.Vector3().crossVectors(Y, frente).normalize();
  const c = cima.addScaledVector(frente, -cima.dot(frente));
  return graus(Math.atan2(c.dot(lado), c.dot(Y)));
}
function curvatura(h) {
  const tronco = h.osso.spine01.getWorldQuaternion(new THREE.Quaternion()).invert();
  const agora = pos(h, 'head').sub(pos(h, 'neck01')).normalize().applyQuaternion(tronco);
  return graus(agora.angleTo(repouso(h, 'head').sub(repouso(h, 'neck01')).normalize()));
}
// pior valor de cada medida em N instantes; tAndar muito negativo = caminhada já terminou (só idle)
function pior(quem, t0, t1, tAndar) {
  const r = { incl: { v: 0, t: 0 }, curva: { v: 0, t: 0 } };
  for (let i = 0; i < N; i++) {
    const t = t0 + (t1 - t0) * i / (N - 1);
    MOC.pose(M, quem, t, { tAndar }); MOC.olhar?.(M, quem, [0, 0, 0]);
    const v = { incl: Math.abs(inclinacao(HUM[quem])), curva: curvatura(HUM[quem]) };
    for (const k of ['incl', 'curva']) if (v[k] > r[k].v) r[k] = { v: v[k], t };
  }
  return r;
}
const fmt = (x, d = 1) => x.toFixed(d).replace('.', ',');
const casos = [
  ['Beto, caminhada 16_34', 'beto', 0, M.beto.andar.dur - 0.5, 0],            // até começar a transição p/ o idle
  ['Beto, idle', 'beto', 0, M.beto.idle.dur, -1000],
  ['Clara, idle', 'clara', 0, M.clara.idle.dur, 0],
];
for (const [nome, quem, t0, t1, tAndar] of casos) {
  const r = pior(quem, t0, t1, tAndar);
  teste(`${nome}: cabeça não tomba (< ${LIMITE_INCL}°)`, () =>
    { afirmar(r.incl.v < LIMITE_INCL, `inclinação lateral de ${fmt(r.incl.v)}° em t = ${fmt(r.incl.t, 2)} s`); return `pior ${fmt(r.incl.v)}°`; });
  teste(`${nome}: pescoço não entorta (< ${LIMITE_CURVA}°)`, () =>
    { afirmar(r.curva.v < LIMITE_CURVA, `curvatura de ${fmt(r.curva.v)}° em t = ${fmt(r.curva.t, 2)} s`); return `pior ${fmt(r.curva.v)}°`; });
}

// o olhar continua funcionando: com o tronco do mocap balançando, a cabeça vira o quanto a cena pede
const rumo = h => { const f = eixo(h, 'head', [0, 0, 1]); return { yaw: graus(Math.atan2(f.x, f.z)), pitch: graus(Math.asin(f.y)) }; };
for (const [quem, t] of [['clara', 4.0], ['beto', 6.5]]) {
  const Q = quem[0].toUpperCase() + quem.slice(1);
  teste(`${Q}: cabeça vira 34° para o lado e 17° para cima quando o olhar pede`, () => {
    MOC.pose(M, quem, t, { tAndar: 0 }); MOC.olhar(M, quem, [-0.3, 0.6, 0]);
    const r = rumo(HUM[quem]), incl = Math.abs(inclinacao(HUM[quem]));
    afirmar(Math.abs(r.yaw - 34.4) < 2 && Math.abs(r.pitch - 17.2) < 2 && incl < 2,
      `virou ${fmt(r.yaw)}° para o lado, ${fmt(r.pitch)}° para cima e inclinou ${fmt(incl)}°`);
    return `${fmt(r.yaw)}° e ${fmt(r.pitch)}°`;
  });
}
