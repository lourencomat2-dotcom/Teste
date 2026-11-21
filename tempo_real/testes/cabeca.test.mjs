// A cabeça não pode tombar nem o pescoço entortar (versão ?humanos&mocap).
// Mede a pose que o mocap.js entrega (sem o olhar e os gestos da cena), em 40 instantes de cada clipe:
//   inclinação lateral da cabeça: ângulo entre o eixo "para cima" da cabeça e a vertical, no plano lateral
//     (perpendicular à frente da cabeça; acenar com a cabeça não conta);
//   curvatura do pescoço: quanto a direção neck01->head mudou em relação ao tronco (spine01), comparada
//     com a pose de repouso. (O ângulo cru spine01->neck01 x neck01->head não serve: no repouso ele já é
//     25° na Clara e 1° no Beto, por causa do formato do corpo.)
// Limites: inclinação < 12°, curvatura < 15°.
import fs from 'fs'; import path from 'path'; import * as THREE from 'three';
import { BVHLoader } from 'three/addons/loaders/BVHLoader.js';
import { humano, pos, eixo, graus, teste, afirmar, RAIZ } from './esqueleto.mjs';
import * as MOC from '../mocap.js';

const LIMITE_INCL = 12, LIMITE_CURVA = 15, N = 40;
const ler = async url => new BVHLoader().parse(fs.readFileSync(path.join(RAIZ, url), 'utf8'));
const HUM = { clara: humano('clara'), beto: humano('beto') };          // mesma ordem da cena
const M = await MOC.preparar(HUM, { pasta: 'mocap/', ler });
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
    MOC.pose(M, quem, t, { tAndar });
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
    afirmar(r.incl.v < LIMITE_INCL, `inclinação lateral de ${fmt(r.incl.v)}° em t = ${fmt(r.incl.t, 2)} s`));
  teste(`${nome}: pescoço não entorta (< ${LIMITE_CURVA}°)`, () =>
    afirmar(r.curva.v < LIMITE_CURVA, `curvatura de ${fmt(r.curva.v)}° em t = ${fmt(r.curva.t, 2)} s`));
}
