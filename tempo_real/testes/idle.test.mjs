// O idle (parado) não pode dar "pulo": quando o trecho da CMU acaba e recomeça, a pose tem que emendar.
// Antes da correção: a Clara pulava aos 5,7 s (coxa girava 34° e o quadril andava 15 cm num quadro só)
// e o Beto aos 10 s (pé 20°). Mede a cena inteira (13 s, 30 fps) enquanto o personagem está parado.
// Limites por quadro: nenhum osso do corpo gira mais de 6°; o quadril não anda mais de 2 cm.
import { teste, afirmar } from './esqueleto.mjs';
import { cena, MOC, CORPO, angulo } from './comum.mjs';

const { HUM, M } = await cena();
const fmt = (x, d = 1) => x.toFixed(d).replace('.', ',');
for (const quem of ['clara', 'beto']) {
  const h = HUM[quem], nomes = CORPO(h), parado = t => !M[quem].andar || t > M[quem].andar.dur + 0.1;
  let ant = null, pior = { ang: 0, t: 0, osso: '' }, piorQ = { d: 0, t: 0 };
  for (let f = 0; f <= 13 * 30; f++) {
    const t = f / 30; MOC.pose(M, quem, t, { tAndar: 0 }); MOC.olhar?.(M, quem, [0, 0, 0]);
    const agora = { q: nomes.map(n => h.osso[n].quaternion.clone()), r: h.osso.root.position.clone() };
    if (ant && parado(t) && parado(t - 1 / 30)) {
      agora.q.forEach((q, i) => { const a = angulo(q, ant.q[i]); if (a > pior.ang) pior = { ang: a, t, osso: nomes[i] }; });
      const d = agora.r.distanceTo(ant.r) * 100; if (d > piorQ.d) piorQ = { d, t };
    }
    ant = agora;
  }
  const Q = quem[0].toUpperCase() + quem.slice(1);
  teste(`${Q}: idle sem pulo nos ossos (< 6° por quadro)`, () =>
    { afirmar(pior.ang < 6, `${pior.osso} girou ${fmt(pior.ang)}° de um quadro para o outro em t = ${fmt(pior.t, 2)} s`); return `pior ${fmt(pior.ang)}°, ${pior.osso}`; });
  teste(`${Q}: idle sem pulo no quadril (< 2 cm por quadro)`, () =>
    { afirmar(piorQ.d < 2, `o quadril andou ${fmt(piorQ.d)} cm de um quadro para o outro em t = ${fmt(piorQ.t, 2)} s`); return `pior ${fmt(piorQ.d)} cm`; });
}
