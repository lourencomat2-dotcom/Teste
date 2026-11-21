import { humano, pos, teste, afirmar } from './esqueleto.mjs';
const beto = humano('beto');
teste('Beto tem 163 ossos', () => afirmar(Object.keys(beto.osso).length === 163, `tem ${Object.keys(beto.osso).length}`));
teste('quadril do Beto a 0,947 m', () => { const y = pos(beto, 'root').y; afirmar(Math.abs(y - 0.947) < 0.005, `y = ${y.toFixed(3)}`); });
