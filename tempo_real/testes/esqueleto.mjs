// Monta o esqueleto de um personagem do MakeHuman (tempo_real/humanos/<nome>.json) sem gráficos,
// para testes automáticos de animação em Node (mesmo esqueleto que o humano.js monta no navegador).
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import * as THREE from 'three';

const AQUI = path.dirname(fileURLToPath(import.meta.url));
export const RAIZ = path.resolve(AQUI, '..');

export function humano(nome) {
  const meta = JSON.parse(fs.readFileSync(path.join(RAIZ, 'humanos', nome + '.json'), 'utf8'));
  const raiz = new THREE.Group();
  const ossos = meta.ossos.map(o => Object.assign(new THREE.Bone(), { name: o.nome }));
  meta.ossos.forEach((o, i) => {
    const h = new THREE.Vector3(...o.cabeca);
    if (o.pai >= 0) { ossos[i].position.copy(h.sub(new THREE.Vector3(...meta.ossos[o.pai].cabeca))); ossos[o.pai].add(ossos[i]); }
    else { ossos[i].position.copy(h); raiz.add(ossos[i]); }
  });
  raiz.updateMatrixWorld(true);
  const malha = new THREE.SkinnedMesh(new THREE.BufferGeometry(), new THREE.MeshBasicMaterial());
  raiz.add(malha); malha.bind(new THREE.Skeleton(ossos));
  const osso = Object.fromEntries(ossos.map(b => [b.name, b]));
  raiz.traverse(o => { if (o.isBone) o.userData.p0 = o.position.clone(); });
  return { nome, raiz, osso, malhas: [malha], meta };
}
// posição no mundo de um osso
export const pos = (h, n) => { h.raiz.updateMatrixWorld(true); return h.osso[n].getWorldPosition(new THREE.Vector3()); };
// direção (unitária) de a até b
export const dir = (h, a, b) => pos(h, b).sub(pos(h, a)).normalize();
// eixo local de um osso no mundo (ex.: [0,1,0] = "para cima" do osso)
export const eixo = (h, n, v) => new THREE.Vector3(...v).applyQuaternion(h.osso[n].getWorldQuaternion(new THREE.Quaternion())).normalize();
export const graus = r => r * 180 / Math.PI;

// mini executor de testes: teste('nome', () => { ... throw se falhar; pode devolver um texto com o valor medido })
const resultados = [];
export function teste(nome, fn) {
  try { const det = fn(); resultados.push([nome, true]); console.log('  ok   ', nome, typeof det === 'string' ? `(${det})` : ''); }
  catch (e) { resultados.push([nome, false]); console.log('  FALHA', nome, '\n        ', e.message); }
}
export function afirmar(cond, msg) { if (!cond) throw new Error(msg); }
process.on('exit', () => { if (resultados.some(r => !r[1])) process.exitCode = 1; });
