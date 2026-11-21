// Prepara o mocap da cena em Node (mesma ordem e trechos de cena.js), para os testes.
import fs from 'fs'; import path from 'path';
import { BVHLoader } from 'three/addons/loaders/BVHLoader.js';
import { humano, RAIZ } from './esqueleto.mjs';
import * as MOC from '../mocap.js';
export { MOC };
const ler = async url => new BVHLoader().parse(fs.readFileSync(path.join(RAIZ, url), 'utf8'));
export async function cena(opcoes = {}) {
  const HUM = { clara: humano('clara'), beto: humano('beto') };          // mesma ordem da cena
  const M = await MOC.preparar(HUM, { pasta: 'mocap/', ler, ...opcoes });
  return { HUM, M };
}
// ossos do corpo (sem dedos e rosto)
export const CORPO = h => Object.keys(h.osso).filter(n => !/finger|toe|eye|jaw|tongue|lid|brow|cheek|lip|nose|ear|temple|levator|oris|risorius|orbicularis|special|mandible|metacarpal/.test(n));
