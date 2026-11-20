"""Monta personagens realistas a partir dos dados do MakeHuman (corpo paramétrico, pele, olhos,
sobrancelhas, cílios, cabelo e roupas), com esqueleto e expressões faciais (morphs), para o three.js.

  python3 motor/humanos.py            # -> tempo_real/humanos/<nome>.json + .bin + texturas

Dados (baixados pelo setup.sh, fora do git):
  vendor/makehuman/dados/    pacote npm "makehuman-data" (malha base, roupas, cabelos, peles)
  vendor/makehuman/targets.npz   alvos de forma do MakeHuman 1.3 (pacote PyPI "makehuman")
Unidades do MakeHuman: decímetros, y para cima, frente em +z. Saída: metros, pés em y=0.
"""
import json, os, sys
import numpy as np
from PIL import Image, ImageOps

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MH = os.path.join(RAIZ, "vendor", "makehuman")
DADOS = os.path.join(MH, "dados")
OUT = os.path.join(RAIZ, "tempo_real", "humanos")

# ------------------------------------------------------------------ elenco (mesmas cores da versão Blender)
ELENCO = {
    "beto": dict(
        macro=dict(genero=1.0, idade=30, musculo=0.6, peso=0.55, altura=0.47, proporcao=0.6,
                   raca=dict(african=0.8, caucasian=0.2, asian=0.0)),
        pele=("young_african_male", 0.95), olhos="brownlight", sobrancelha="eyebrow001", bigode=True,
        cabelo=("short02", (34, 28, 28)),
        roupas=[("male_casualsuit06", dict(camisa=(236, 140, 50))), ("shoes03", None)]),
    "clara": dict(
        macro=dict(genero=0.0, idade=28, musculo=0.5, peso=0.48, altura=0.5, proporcao=0.6,
                   raca=dict(african=0.0, caucasian=0.9, asian=0.1)),
        pele=("young_caucasian_female", 1.0), olhos="brownlight", sobrancelha="eyebrow001",
        cabelo=("ponytail01", (96, 56, 40)),
        roupas=[("Rolled_neck_blouse", dict(tudo=(70, 150, 120))), ("Tightjeans", None), ("shoes04", None)]),
}
# unidades de expressão (MakeHuman "expression units") usadas na animação do rosto
MORPHS = ["mouth-open", "mouth-corner-puller", "mouth-depression", "mouth-pursing", "mouth-retraction",
          "mouth-compression", "eye-left-closure", "eye-right-closure", "eye-left-slit", "eye-right-slit",
          "eyebrows-left-up", "eyebrows-right-up", "eyebrows-left-down", "eyebrows-right-down",
          "eyebrows-left-inner-up", "eyebrows-right-inner-up"]

# ------------------------------------------------------------------ leitura
def faces_legado(faces, n_uv=1):
    """formato JSON 3.1 do three.js (bitmask por face) -> lista de (verts, material, uvs)."""
    i, out = 0, []
    while i < len(faces):
        t = faces[i]; i += 1
        nv = 4 if t & 1 else 3
        vs = faces[i:i + nv]; i += nv
        mat = 0
        if t & 2: mat = faces[i]; i += 1
        if t & 4: i += n_uv
        uvs = None
        if t & 8:
            uvs = faces[i:i + nv]; i += nv * n_uv
        if t & 16: i += 1
        if t & 32: i += nv
        if t & 64: i += 1
        if t & 128: i += nv
        out.append((vs, mat, uvs))
    return out

def desdobrar(faces, uv_flat, so_material=None):
    """separa vértices nas costuras de UV; devolve (vert_origem, uv, triângulos)."""
    uv = np.array(uv_flat, np.float32).reshape(-1, 2)
    chave, origem, uvs, tris = {}, [], [], []
    for vs, mat, fuv in faces:
        if so_material is not None and mat != so_material: continue
        ids = []
        for k, v in enumerate(vs):
            c = (v, fuv[k] if fuv else -1)
            if c not in chave:
                chave[c] = len(origem); origem.append(v); uvs.append(uv[c[1]] if c[1] >= 0 else (0, 0))
            ids.append(chave[c])
        tris.append((ids[0], ids[1], ids[2]))
        if len(ids) == 4: tris.append((ids[0], ids[2], ids[3]))
    return np.array(origem), np.array(uvs, np.float32), np.array(tris, np.uint32)

class Alvos:
    def __init__(s, n):
        s.z = np.load(os.path.join(MH, "targets.npz"), allow_pickle=False); s.n = n
        s.nomes = sorted(k[len("targets/"):-len(".index")] for k in s.z.files if k.endswith(".index"))
    def delta(s, nome):
        d = np.zeros((s.n, 3), np.float32)
        i = s.z[f"targets/{nome}.index"]; v = s.z[f"targets/{nome}.vector"]
        if len(i): d[i.astype(np.int64)] = v.astype(np.float32) * 1e-3
        return d

def valores_macro(m):
    """mesmas fórmulas do MakeHuman (human.py) para combinar os alvos 'macrodetails'."""
    g = m["genero"]; anos = m["idade"]
    idade = (anos - 1) / ((25 - 1) * 2) if anos < 25 else (anos - 25) / ((90 - 25) * 2) + 0.5
    v = dict(male=g, female=1 - g, universal=1.0)
    if idade < 0.5:
        v["old"] = 0.0; v["baby"] = max(0.0, 1 - idade * 5.333); v["young"] = max(0.0, (idade - 0.1875) * 3.2)
        v["child"] = max(0.0, min(1.0, 5.333 * idade) - v["young"])
    else:
        v["child"] = v["baby"] = 0.0; v["old"] = max(0.0, idade * 2 - 1); v["young"] = 1 - v["old"]
    for nome, x in (("muscle", m["musculo"]), ("weight", m["peso"])):
        v["max" + nome] = max(0.0, x * 2 - 1); v["min" + nome] = max(0.0, 1 - x * 2)
        v["average" + nome] = 1 - (v["max" + nome] + v["min" + nome])
    h = m["altura"]; v["maxheight"] = max(0.0, h * 2 - 1); v["minheight"] = max(0.0, 1 - h * 2)
    p = m["proporcao"]; v["idealproportions"] = max(0.0, p * 2 - 1); v["uncommonproportions"] = max(0.0, 1 - p * 2)
    r = m["raca"]; tot = sum(r.values()) or 1.0
    for k, x in r.items(): v[k] = x / tot
    return v

def corpo_macro(alvos, m):
    v = valores_macro(m); d = np.zeros((alvos.n, 3), np.float32)
    for nome in alvos.nomes:
        if not nome.startswith("macrodetails/"): continue
        peso = 1.0
        for parte in os.path.basename(nome).split("-"):
            peso *= v.get(parte.lower(), 0.0 if parte.lower() not in ("universal",) else 1.0)
        if peso > 1e-4: d += peso * alvos.delta(nome)
    return d

def expressoes(alvos, m):
    r = m["raca"]; tot = sum(r.values()) or 1.0; out = {}
    for u in MORPHS:
        d = np.zeros((alvos.n, 3), np.float32)
        for raca, x in r.items():
            if x > 0: d += (x / tot) * alvos.delta(f"expression/units/{raca}/{u}")
        out[u] = d
    return out

# ------------------------------------------------------------------ texturas
def tingir(img, cor, mascara=None):
    """mantém o sombreado (luminância) da textura e troca a cor; mascara=função(rgb)->bool."""
    im = img.convert("RGBA"); a = np.asarray(im).astype(np.float32)
    lum = (0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2]) / 255.0
    lum = np.clip(lum / max(np.percentile(lum[a[..., 3] > 0], 92), 1e-3), 0, 1.15)
    novo = a.copy()
    for c in range(3): novo[..., c] = np.clip(lum * cor[c], 0, 255)
    if mascara is not None:
        m = mascara(a)[..., None]; novo = np.where(m, novo, a)
    return Image.fromarray(novo.astype(np.uint8), "RGBA")

def camisa_lisa(img, geo, limiar_y, cor):
    """pinta de cor lisa (com dobras suaves) as faces da camisa, rasterizando as faces no mapa UV."""
    from PIL import ImageDraw, ImageFilter
    im = img.convert("RGBA"); W, H = im.size
    m = Image.new("L", (W, H), 0); d = ImageDraw.Draw(m)
    P, uv = geo["P"], geo["uv"]
    for t in geo["tris"]:
        if P[t, 1].mean() < limiar_y: continue
        d.polygon([(uv[i, 0] * W, (1 - uv[i, 1]) * H) for i in t], fill=255)
    m = m.filter(ImageFilter.MaxFilter(5))
    a = np.asarray(im).astype(np.float32)
    lum = np.asarray(im.convert("L").filter(ImageFilter.GaussianBlur(6))).astype(np.float32) / 255.0
    sel = (np.asarray(m) > 0) & ~((a[..., 2] - a[..., 0]) > 30)        # o jeans (azul) fica de fora
    ref = np.percentile(lum[sel], 80) if sel.any() else 1.0
    lum = np.clip(lum / max(ref, 1e-3), 0.8, 1.04)
    for c in range(3): a[..., c] = np.where(sel, lum * cor[c], a[..., c])
    return Image.fromarray(a.clip(0, 255).astype(np.uint8), "RGBA")

def bigode_iogurte(parte, P, tris, si, sw, morphs, ossos, para_m, nome):
    """faixa de iogurte acima do lábio (a piada da cena), feita da própria pele, 1,5 mm para fora."""
    from PIL import ImageDraw, ImageFilter
    o = {x["nome"]: x for x in ossos}
    Pm = para_m(P); lab = o["oris05"]["cabeca"]          # meio do lábio de cima
    yc, zc, ry, rx = lab[1] + 0.006, lab[2], 0.0095, 0.03
    y0 = yc - ry
    sel = ((Pm[:, 0] / rx) ** 2 + ((Pm[:, 1] - yc) / ry) ** 2 < 1) & (Pm[:, 2] > zc - 0.025) & (Pm[:, 2] < zc + 0.014)
    tt = tris[sel[tris].all(1)]
    usados = np.unique(tt); mapa = -np.ones(len(P), np.int64); mapa[usados] = np.arange(len(usados))
    n = np.zeros_like(Pm)                                   # normais por vértice
    fn = np.cross(Pm[tris[:, 1]] - Pm[tris[:, 0]], Pm[tris[:, 2]] - Pm[tris[:, 0]])
    for k in range(3): np.add.at(n, tris[:, k], fn)
    n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-9
    Q = Pm[usados] + n[usados] * 0.0015
    uv = np.stack([(Pm[usados, 0] + rx) / (2 * rx), (Pm[usados, 1] - y0) / (2 * ry)], 1).astype(np.float32)
    S = 4; Wt, Ht = 256, 96; im = Image.new("L", (Wt * S, Ht * S), 0); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0.12 * Wt * S, 0.25 * Ht * S, 0.88 * Wt * S, 0.85 * Ht * S], radius=18 * S, fill=255)
    for cx, comp in ((0.3, 0.98), (0.47, 0.99), (0.63, 0.97), (0.74, 0.93)):       # pingos
        d.ellipse([(cx - 0.035) * Wt * S, (comp - 0.16) * Ht * S, (cx + 0.035) * Wt * S, comp * Ht * S], fill=255)
    alfa = im.filter(ImageFilter.GaussianBlur(3 * S)).resize((Wt, Ht), Image.LANCZOS)
    tex = Image.new("RGBA", (Wt, Ht), (252, 250, 242, 255)); tex.putalpha(alfa)
    img_nome = f"{nome}_iogurte.png"; tex.save(os.path.join(OUT, img_nome))
    base_dm = Q / 0.1; base_dm[:, 1] += para_m(np.zeros((1, 3), np.float32))[0, 1] * -10   # desfaz o deslocamento do pé
    parte("iogurte", base_dm, uv, mapa[tt], si[usados], sw[usados], {k: v[usados] for k, v in morphs.items()},
          (img_nome, True), dict(rugosidade=0.25, tipo="iogurte"))

def salvar_tex(img, nome, max_lado=1024):
    if max(img.size) > max_lado: img = img.resize((max_lado, max_lado * img.size[1] // img.size[0]), Image.LANCZOS)
    tem_alfa = img.mode == "RGBA" and np.asarray(img)[..., 3].min() < 250
    img = img if tem_alfa else img.convert("RGB")
    img.save(os.path.join(OUT, nome), optimize=True)
    return nome, bool(tem_alfa)

# ------------------------------------------------------------------ montagem
class Buffer:
    def __init__(s): s.partes = []; s.tam = 0
    def add(s, arr):
        b = np.ascontiguousarray(arr).tobytes(); pad = (-len(b)) % 4
        off = s.tam; s.partes.append(b + b"\0" * pad); s.tam += len(b) + pad; return off
    def bytes(s): return b"".join(s.partes)

def montar(nome, cfg, base, alvos):
    print(f"[{nome}] corpo...")
    V0 = np.array(base["vertices"], np.float32).reshape(-1, 3)
    d_corpo = corpo_macro(alvos, cfg["macro"]); V = V0 + d_corpo
    expr = expressoes(alvos, cfg["macro"])
    faces = faces_legado(base["faces"])
    org, uv, tris = desdobrar(faces, base["uvs"][0], so_material=0)        # material 0 = pele
    pe = V[org][:, 1].min()
    para_m = lambda P: (P - np.array([0, pe, 0], np.float32)) * 0.1
    # esqueleto: ossos "X____head" do export do MakeHuman (são os que deformam)
    B = base["bones"]; jp = base["metadata"]["joint_pos_idxs"]
    ossos, idx_osso = [], {}
    for i, b in enumerate(B):
        if b["name"].endswith("____head"): idx_osso[i] = len(ossos); ossos.append(dict(nome=b["name"][:-8]))
    for i, b in enumerate(B):
        if i not in idx_osso: continue
        p = b["parent"]
        while p >= 0 and p not in idx_osso: p = B[p]["parent"]
        o = ossos[idx_osso[i]]; o["pai"] = idx_osso.get(p, -1)
        cab = jp.get(o["nome"] + "____head"); cau = jp.get(o["nome"] + "____tail")
        o["cabeca"] = para_m(V[cab].mean(0)).round(5).tolist() if cab else None
        o["cauda"] = para_m(V[cau].mean(0)).round(5).tolist() if cau else None
    for o in ossos:   # osso sem marcador: usa a cauda do pai
        if o["cabeca"] is None: o["cabeca"] = ossos[o["pai"]]["cauda"] or ossos[o["pai"]]["cabeca"]
    def pele_ossos(si, sw, n):
        k_inf = len(si) // n
        si = np.array(si).reshape(n, k_inf); sw = np.array(sw, np.float32).reshape(n, k_inf)
        out = np.zeros((n, 4), np.int64); w4 = np.zeros((n, 4), np.float32)
        for k in range(min(4, k_inf)):
            out[:, k] = [idx_osso.get(int(x), 0) for x in si[:, k]]; w4[:, k] = sw[:, k]
        w4 = w4 / np.maximum(w4.sum(1, keepdims=True), 1e-6)
        return out.astype(np.uint16), w4.astype(np.float32)

    buf = Buffer(); partes = []
    os.makedirs(OUT, exist_ok=True)
    def parte(rotulo, P, uvp, trisp, skI, skW, morphs, tex, mat):
        ent = dict(nome=rotulo, n=len(P), tris=len(trisp), mat=mat)
        ent["pos"] = buf.add(para_m(P).astype(np.float32)); ent["uv"] = buf.add(uvp.astype(np.float32))
        ent["idx"] = buf.add(trisp.astype(np.uint32)); ent["si"] = buf.add(skI); ent["sw"] = buf.add(skW)
        ent["morph"] = {}
        for k, dm in morphs.items():
            dm = dm * 0.1
            if np.abs(dm).max() < 1e-5: continue
            ent["morph"][k] = buf.add(dm.astype(np.float32))
        mat["map"], mat["alfa"] = tex
        partes.append(ent)
    # pele
    si, sw = pele_ossos(base["skinIndices"], base["skinWeights"], len(base["vertices"]) // 3)
    pele_nome, escuro = cfg["pele"]
    sk = json.load(open(os.path.join(DADOS, "skins", pele_nome, pele_nome + ".json")))
    img = Image.open(os.path.join(DADOS, "skins", pele_nome, sk["mapDiffuse"])).convert("RGB")
    if escuro != 1.0: img = Image.eval(img, lambda x: int(x * escuro))
    parte("pele", V[org], uv, tris, si[org], sw[org], {k: d[org] for k, d in expr.items()},
          salvar_tex(img, f"{nome}_pele.png"), dict(rugosidade=0.55, tipo="pele"))
    # proxies: olhos, sobrancelhas, cílios, dentes, cabelo, roupas
    def proxy(cat, pnome, tingimento=None, material_idx=None, rot=None, tipo="roupa"):
        d = json.load(open(os.path.join(DADOS, "proxies", cat, pnome, pnome + ".json")))
        ref = np.array(d["ref_vIdxs"]); w = np.array(d["weights"], np.float32); off = np.array(d["offsets"], np.float32)
        ref = np.minimum(ref, alvos.n - 1)
        P = (V[ref] * w[..., None]).sum(1) + off
        f = faces_legado(d["faces"])
        mats = d["materials"]; mi = material_idx if material_idx is not None else 0
        org_p, uv_p, tris_p = desdobrar(f, d["uvs"][0])
        n = len(d["vertices"]) // 3
        si_p, sw_p = pele_ossos(d["skinIndices"], d["skinWeights"], n)
        morphs = {k: (dd[ref] * w[..., None]).sum(1)[org_p] for k, dd in expr.items()}
        caminho = os.path.join(DADOS, "proxies", cat, pnome, mats[mi]["mapDiffuse"])
        img = Image.open(caminho)
        if tingimento: img = tingimento(img, dict(P=P[org_p], uv=uv_p, tris=tris_p))
        parte(rot or pnome, P[org_p], uv_p, tris_p, si_p[org_p], sw_p[org_p], morphs,
              salvar_tex(img, f"{nome}_{rot or pnome}.png"), dict(rugosidade=0.8, tipo=tipo))
    olhos = json.load(open(os.path.join(DADOS, "proxies", "eyes", "HighPolyEyes", "HighPolyEyes.json")))["materials"]
    proxy("eyes", "HighPolyEyes", material_idx=[m["DbgName"] for m in olhos].index(cfg["olhos"]), rot="olhos", tipo="olhos")
    proxy("eyebrows", cfg["sobrancelha"], rot="sobrancelhas", tipo="pelo")
    proxy("eyelashes", "Eyelashes_01", rot="cilios", tipo="pelo")
    proxy("teeth", "Teeth_Base", rot="dentes", tipo="dentes")
    cab, cor_cab = cfg["cabelo"]
    proxy("hair", cab, tingimento=(lambda im, g: tingir(im, cor_cab)) if cor_cab else None, rot="cabelo", tipo="cabelo")
    quadril = V[jp["upperleg01.L____head"]].mean(0)[1] - 0.8           # dm: abaixo do quadril (a camisa vai por cima do jeans)
    for roupa, tint in cfg["roupas"]:
        fn = None
        if tint and "tudo" in tint: fn = lambda im, g, c=tint["tudo"]: tingir(im, c)
        elif tint and "camisa" in tint:   # só a camisa (faces acima do quadril); estampa e logo somem
            fn = lambda im, g, c=tint["camisa"]: camisa_lisa(im, g, quadril, c)
        proxy("clothes", roupa, tingimento=fn, rot=roupa)
    if cfg.get("bigode"): bigode_iogurte(parte, V[org], tris, si[org], sw[org], {k: d[org] for k, d in expr.items()}, ossos, para_m, nome)
    meta = dict(nome=nome, ossos=ossos, partes=partes, morphs=MORPHS, bin=f"{nome}.bin")
    open(os.path.join(OUT, f"{nome}.bin"), "wb").write(buf.bytes())
    json.dump(meta, open(os.path.join(OUT, f"{nome}.json"), "w"))
    print(f"[{nome}] {len(partes)} partes · {len(ossos)} ossos · {buf.tam / 1e6:.1f} MB · altura ~{para_m(V[org])[:, 1].max():.2f} m")

def main():
    base = json.load(open(os.path.join(DADOS, "models", "human_full_size.json")))
    alvos = Alvos(len(base["vertices"]) // 3)
    nomes = sys.argv[1:] or list(ELENCO)
    for n in nomes: montar(n, ELENCO[n], base, alvos)

if __name__ == "__main__":
    main()
