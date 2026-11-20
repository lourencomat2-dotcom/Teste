// Carrega um personagem montado por motor/humanos.py (MakeHuman): malhas com esqueleto e expressões.
import * as THREE from 'three';

const texLoader = new THREE.TextureLoader();
const tex = url => new Promise(ok => texLoader.load(url, t => { t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8; ok(t); }));

function material(m, map) {
  const comum = { map, roughness: m.rugosidade, metalness: 0 };
  switch (m.tipo) {
    case 'pele': return new THREE.MeshStandardMaterial({ ...comum, roughness: 0.52, envMapIntensity: 0.55 });
    case 'olhos': return new THREE.MeshStandardMaterial({ ...comum, roughness: 0.08, alphaTest: 0.5, side: THREE.DoubleSide, envMapIntensity: 1.2 });
    case 'iogurte': return new THREE.MeshStandardMaterial({ ...comum, roughness: 0.3, transparent: true, depthWrite: false,
                                                            polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -2 });
    case 'dentes': return new THREE.MeshStandardMaterial({ ...comum, roughness: 0.35, alphaTest: 0.5 });
    case 'pelo': return new THREE.MeshStandardMaterial({ ...comum, color: 0x2a2220, transparent: true, depthWrite: false,
                                                          alphaTest: 0.05, side: THREE.DoubleSide, roughness: 0.7 });
    case 'cabelo': return new THREE.MeshStandardMaterial({ ...comum, alphaTest: 0.45, alphaToCoverage: true,
                                                           side: THREE.DoubleSide, roughness: 0.55, envMapIntensity: 0.5 });
    default: return new THREE.MeshStandardMaterial({ ...comum, roughness: 0.85, side: THREE.DoubleSide,
                                                     alphaTest: m.alfa ? 0.5 : 0, envMapIntensity: 0.5 });
  }
}

export async function carregarHumano(pasta, nome) {
  const meta = await (await fetch(`${pasta}${nome}.json`)).json();
  const bin = await (await fetch(`${pasta}${meta.bin}`)).arrayBuffer();
  const raiz = new THREE.Group(); raiz.name = 'humano_' + nome;
  // esqueleto em pose de repouso sem rotação: eixos locais = eixos do personagem (fácil de animar)
  const ossos = meta.ossos.map(o => Object.assign(new THREE.Bone(), { name: o.nome }));
  meta.ossos.forEach((o, i) => {
    const h = new THREE.Vector3(...o.cabeca);
    if (o.pai >= 0) { ossos[i].position.copy(h.sub(new THREE.Vector3(...meta.ossos[o.pai].cabeca))); ossos[o.pai].add(ossos[i]); }
    else { ossos[i].position.copy(h); raiz.add(ossos[i]); }
  });
  raiz.updateMatrixWorld(true);
  const esqueleto = new THREE.Skeleton(ossos);
  const malhas = [];
  for (const p of meta.partes) {
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.BufferAttribute(new Float32Array(bin, p.pos, p.n * 3), 3));
    g.setAttribute('uv', new THREE.BufferAttribute(new Float32Array(bin, p.uv, p.n * 2), 2));
    g.setIndex(new THREE.BufferAttribute(new Uint32Array(bin, p.idx, p.tris * 3), 1));
    g.setAttribute('skinIndex', new THREE.Uint16BufferAttribute(new Uint16Array(bin, p.si, p.n * 4), 4));
    g.setAttribute('skinWeight', new THREE.BufferAttribute(new Float32Array(bin, p.sw, p.n * 4), 4));
    const nm = Object.keys(p.morph);
    if (nm.length) {
      g.morphAttributes.position = nm.map(k => Object.assign(new THREE.BufferAttribute(new Float32Array(bin, p.morph[k], p.n * 3), 3), { name: k }));
      g.morphTargetsRelative = true;
    }
    g.computeVertexNormals();
    const m = new THREE.SkinnedMesh(g, material(p.mat, await tex(pasta + p.mat.map)));
    m.name = p.nome; m.castShadow = p.mat.tipo !== 'pelo'; m.receiveShadow = true; m.frustumCulled = false;
    if (p.mat.tipo === 'pelo') m.renderOrder = 3;
    raiz.add(m); m.bind(esqueleto); if (nm.length) m.updateMorphTargets();
    malhas.push(m);
  }
  const osso = Object.fromEntries(ossos.map(b => [b.name, b]));
  // expressões: mesmo nome em todas as malhas que têm o morph
  const pesos = {};
  function expressao(nomeMorph, v) {
    pesos[nomeMorph] = v;
    for (const m of malhas) {
      const i = m.morphTargetDictionary?.[nomeMorph];
      if (i !== undefined) m.morphTargetInfluences[i] = v;
    }
  }
  return { raiz, osso, malhas, expressao, pesos, meta };
}
