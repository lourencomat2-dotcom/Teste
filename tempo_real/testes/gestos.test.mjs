// Gestos de fala por cima do mocap (gestos.js), com o idle aplicado.
// Critérios do plano (g = 1):
//   ombros:  mãos a mais de 0,55 m uma da outra e acima do quadril + 0,05 m; palmas para cima
//   aponta:  mão do lado certo, à frente do peito, a mais de 0,35 m do tronco e na direção do outro (< 15°)
//   cintura: punhos a menos de 0,12 m da lateral do quadril
// E na mistura (g de 0 a 1 em 8 quadros, como na cena): a mão anda menos de 12 cm por quadro e não
// passa por dentro do corpo (fica a mais de 0,12 m do eixo do tronco); com g = 0 nada muda.
import * as THREE from 'three';
import { pos, teste, afirmar } from './esqueleto.mjs';
import { cena, MOC, CORPO, angulo } from './comum.mjs';
import * as GES from '../gestos.js';

const { HUM, M } = await cena();
for (const h of Object.values(HUM)) GES.preparar(h);
const T = { clara: 4.0, beto: 6.5 };                     // instantes de idle (o Beto já chegou)
const LADO = { clara: 'L', beto: 'R' };                  // braço que aponta para o outro (o da marionete)
const S = { L: 1, R: -1 };
const fmt = (x, d = 2) => x.toFixed(d).replace('.', ',');
const ALVO = h => pos(h, 'spine01').add(new THREE.Vector3(S[LADO[h.nome]] * 1.2, 0, 1.2));   // o outro, à frente e ao lado
function montar(quem, pose, g) {
  const h = HUM[quem];
  MOC.pose(M, quem, T[quem], { tAndar: 0 }); MOC.olhar(M, quem);
  GES.aplicar(h, pose, g, { lado: LADO[quem], alvo: ALVO(h) });
  h.raiz.updateMatrixWorld(true);
  return h;
}
// eixo do tronco: do quadril ao pescoço; distância de um ponto até ele
const distTronco = (h, p) => {
  const a = pos(h, 'root'), b = pos(h, 'neck01'), ab = b.clone().sub(a), t = THREE.MathUtils.clamp(p.clone().sub(a).dot(ab) / ab.lengthSq(), 0, 1);
  return p.distanceTo(a.clone().addScaledVector(ab, t));
};
const frente = h => new THREE.Vector3(0, 0, 1).applyQuaternion(h.osso.spine01.getWorldQuaternion(new THREE.Quaternion())).setY(0).normalize();
const palma = (h, s) => {                                   // normal da palma no mundo (a mesma regra do gestos.js)
  const m = pos(h, 'finger3-1.' + s).sub(pos(h, 'wrist.' + s)), k = pos(h, 'finger5-1.' + s).sub(pos(h, 'finger2-1.' + s));
  const n = new THREE.Vector3().crossVectors(m, k).normalize();
  const n0 = (() => { const c = x => new THREE.Vector3(...h.meta.ossos.find(o => o.nome === x).cabeca);
    return new THREE.Vector3().crossVectors(c('finger3-1.' + s).sub(c('wrist.' + s)), c('finger5-1.' + s).sub(c('finger2-1.' + s))); })();
  return n0.x * S[s] > 0 ? n.negate() : n;                  // mesmo sinal escolhido no repouso
};

for (const quem of ['clara', 'beto']) {
  const Q = quem[0].toUpperCase() + quem.slice(1);
  teste(`${Q} "ombros": mãos afastadas, acima do quadril, palmas para cima`, () => {
    const h = montar(quem, 'ombros', 1), L = pos(h, 'wrist.L'), R = pos(h, 'wrist.R'), q = pos(h, 'root').y;
    const dist = L.distanceTo(R), alt = Math.min(L.y, R.y) - q, cima = Math.min(palma(h, 'L').y, palma(h, 'R').y);
    afirmar(dist > 0.55 && alt > 0.05 && cima > 0.5, `mãos a ${fmt(dist)} m, ${fmt(alt)} m acima do quadril, palma para cima ${fmt(cima)}`);
    return `mãos a ${fmt(dist)} m, ${fmt(alt)} m acima do quadril`;
  });
  teste(`${Q} "aponta": braço ${LADO[quem]} à frente, longe do tronco, na direção do outro`, () => {
    const h = montar(quem, 'aponta', 1), s = LADO[quem], W = pos(h, 'wrist.' + s), O = pos(h, 'upperarm01.' + s);
    const ladoOk = (W.x - pos(h, 'spine01').x) * S[s] > 0, aFrente = W.clone().sub(pos(h, 'spine01')).dot(frente(h));
    const dT = distTronco(h, W), erro = W.clone().sub(O).angleTo(ALVO(h).sub(O)) * 180 / Math.PI;
    afirmar(ladoOk && aFrente > 0.2 && dT > 0.35 && erro < 15, `lado ${ladoOk}, ${fmt(aFrente)} m à frente, ${fmt(dT)} m do tronco, ${fmt(erro, 0)}° fora do alvo`);
    return `${fmt(dT)} m do tronco, ${fmt(erro, 0)}° fora do alvo`;
  });
  teste(`${Q} "cintura": punhos na lateral do quadril`, () => {
    const h = montar(quem, 'cintura', 1), qq = h.osso.root.getWorldQuaternion(new THREE.Quaternion());
    const lateral = s => pos(h, 'upperleg01.' + s).add(new THREE.Vector3(S[s] * 0.06, 0.08, 0).applyQuaternion(qq));
    const d = Math.max(pos(h, 'wrist.L').distanceTo(lateral('L')), pos(h, 'wrist.R').distanceTo(lateral('R')));
    afirmar(d < 0.12, `punho a ${fmt(d)} m da lateral do quadril`);
    return `${fmt(d)} m`;
  });
  teste(`${Q}: entrar no gesto sem pulo e sem atravessar o corpo`, () => {
    let pior = { passo: 0, dentro: 9, txt: '' };
    for (const pose of ['ombros', 'aponta', 'cintura']) {
      let ant = null;
      for (let i = 0; i <= 8; i++) {
        const h = montar(quem, pose, i / 8), agora = {};
        for (const s of ['L', 'R']) {
          const W = pos(h, 'wrist.' + s), E = pos(h, 'lowerarm01.' + s);
          if (ant) { const p = Math.max(W.distanceTo(ant[s].W), E.distanceTo(ant[s].E)); if (p > pior.passo) pior = { ...pior, passo: p, txt: `${pose} ${s} g=${i}/8` }; }
          pior.dentro = Math.min(pior.dentro, distTronco(h, W));
          agora[s] = { W, E };
        }
        ant = agora;
      }
    }
    afirmar(pior.passo < 0.12 && pior.dentro > 0.12, `maior passo ${fmt(pior.passo)} m (${pior.txt}); mão a ${fmt(pior.dentro)} m do eixo do tronco`);
    return `maior passo ${fmt(pior.passo)} m, mão a ≥ ${fmt(pior.dentro)} m do tronco`;
  });
  teste(`${Q}: com g = 0 a pose do mocap não muda (nem depois de um gesto no mesmo instante)`, () => {
    const h = montar(quem, null, 0), nomes = CORPO(h), antes = nomes.map(n => h.osso[n].quaternion.clone());
    montar(quem, 'ombros', 1);                // o mixer não reescreve valores repetidos: o gesto não pode sobrar
    montar(quem, 'ombros', 0);
    const dif = Math.max(...nomes.map((n, i) => angulo(h.osso[n].quaternion, antes[i])));
    afirmar(dif < 0.01, `mudou ${fmt(dif)}°`);
  });
}
