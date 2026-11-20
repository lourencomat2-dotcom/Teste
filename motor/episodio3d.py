"""Montador da versão 3D: cenários e personagens pré-renderizados no Blender (sprites),
rostos desenhados por cima (troca de textura, como em jogos), mesma linha do tempo,
vozes, risadas e legendas da versão anterior.

    python3 episodio3d.py                 # render completo
    python3 episodio3d.py preview 12 40   # quadros de checagem
"""
import json, math, os, re, shutil, subprocess, sys
from multiprocessing import Pool
import numpy as np
from PIL import Image, ImageDraw
os.environ.setdefault("OPENCV_IO_ENABLE_OPENEXR", "1")
import cv2

MOTOR = os.path.dirname(os.path.abspath(__file__))
D3 = os.path.dirname(MOTOR)                       # raiz do projeto
sys.path.insert(0, MOTOR)
import episodio as E

E.DIR = D3
W, H, FPS, SS = E.W, E.H, E.FPS, 2
REND = os.path.join(D3, "render")
PROJ = json.load(open(os.path.join(REND, "projecoes.json")))
LINHA = E.LINHA

# ------------------------------------------------------------------ carregar renders
PLACAS, SPR, PROPS = {}, {}, {}
def recorte(path):
    im = Image.open(path).convert("RGBA"); a = np.asarray(im)[..., 3].copy()
    a[a < 8] = 0; arr = np.asarray(im).copy(); arr[..., 3] = a
    ys, xs = np.nonzero(a)
    if len(xs) == 0: return None
    x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    return Image.fromarray(arr[y0:y1, x0:x1]), int(x0), int(y0)

def carregar():
    for setup in os.listdir(REND):
        pd = os.path.join(REND, setup)
        if not os.path.isdir(pd): continue
        for fn in os.listdir(pd):
            if not fn.endswith("_limpo.png"): continue
            nome = fn[:-len("_limpo.png")]; p = os.path.join(pd, fn)
            if nome == "placa": PLACAS[setup] = Image.open(p).convert("RGB")
            elif nome.startswith("prop_"):
                r = recorte(p)
                if r: PROPS[(setup, nome[5:])] = r
            else:
                quem, pose = nome.split("_", 1); r = recorte(p)
                if r: SPR[(setup, quem, pose)] = r

def setup_de(shot, cena):
    if shot == "geral": return "geral3" if len(cena["elenco"]) >= 3 else "geral2"
    return shot

# ------------------------------------------------------------------ colagem
def colar_seguro(im, src, x, y):
    """cola RGBA com alfa recortando o que sai da imagem (offset negativo inclusive)."""
    x, y = int(round(x)), int(round(y)); w, h = src.size
    sx0, sy0 = max(0, -x), max(0, -y); sx1, sy1 = min(w, im.width - x), min(h, im.height - y)
    if sx1 <= sx0 or sy1 <= sy0: return
    if (sx0, sy0, sx1, sy1) != (0, 0, w, h): src = src.crop((sx0, sy0, sx1, sy1))
    im.paste(src, (x + sx0, y + sy0), src)

def colar(im, spr, dx=0, dy=0, alpha=1.0, escala=1.0):
    crop, x0, y0 = spr
    if escala != 1.0:
        cw, ch = crop.size; nw, nh = max(1, int(cw * escala)), max(1, int(ch * escala))
        cx, cy = x0 + cw / 2, y0 + ch / 2; crop = crop.resize((nw, nh), Image.LANCZOS); x0, y0 = cx - nw / 2, cy - nh / 2
    if alpha < 1.0:
        crop = crop.copy(); crop.putalpha(crop.split()[3].point(lambda v: int(v * alpha)))
    colar_seguro(im, crop, x0 + dx, y0 + dy)

def colar_mistura(im, a, b, t, dx, dy):
    """mistura dois sprites (transição de pose)."""
    (ca, xa, ya), (cb, xb, yb) = a, b
    x0, y0 = min(xa, xb), min(ya, yb); x1, y1 = max(xa + ca.width, xb + cb.width), max(ya + ca.height, yb + cb.height)
    A = Image.new("RGBA", (x1 - x0, y1 - y0), (0, 0, 0, 0)); B = A.copy()
    A.paste(ca, (xa - x0, ya - y0)); B.paste(cb, (xb - x0, yb - y0))
    M = Image.blend(A, B, t); colar_seguro(im, M, x0 + dx, y0 + dy)

def pose_sprite(setup, quem, nome_pose, olha):
    if nome_pose is None: return "repouso"
    if nome_pose == "aponta":
        lado = olha if olha else (1 if quem == "clara" else -1)
        alvo = f"aponta{'+' if lado > 0 else '-'}1"
        return alvo if (setup, quem, alvo) in SPR else ("ombros" if (setup, quem, "ombros") in SPR else "repouso")
    return nome_pose if (setup, quem, nome_pose) in SPR else "repouso"

# ------------------------------------------------------------------ rosto (desenhado por cima da cabeça 3D)
class TR:
    """transforma coordenadas do desenho (cabeça de raio 68) para pixels do retalho."""
    def __init__(s, k, meio): s.k, s.m = k * SS, meio * SS
    def p(s, x, y): return (s.m + x * s.k, s.m + y * s.k)
    def r(s, v): return v * s.k
    def w(s, v): return max(1, int(round(v * s.k)))
    def box(s, x0, y0, x1, y1):
        a, b = s.p(x0, y0), s.p(x1, y1); return [min(a[0], b[0]), min(a[1], b[1]), max(a[0], b[0]), max(a[1], b[1])]

def rosto(im, cx, cy, k, who, ex, boca, pisca, olha, bigode):
    meio = int(105 * k) + 4
    P_ = Image.new("RGBA", (2 * meio * SS, 2 * meio * SS), (0, 0, 0, 0)); d = ImageDraw.Draw(P_)
    T = TR(k, meio); P, R, Bx, w = T.p, T.r, T.box, T.w; c = E.ELENCO[who]
    forma, vol = boca; x = hy = 0
    # bochechas suaves
    for s in (-1, 1): d.ellipse(Bx(s * 40 - 14, 13, s * 40 + 14, 29), fill=(236, 120, 120, 70))
    ox = olha * 6
    for s in (-1, 1):
        ex0, ey = s * 26, -5
        if pisca: d.arc(Bx(ex0 - 12, ey - 8, ex0 + 12, ey + 6), 20, 160, fill=LINHA, width=w(4))
        else:
            ab = E.ABRE.get(ex, 12); pr = 4 if ex == "surpresa" else 6.5
            d.ellipse(Bx(ex0 - 13, ey - ab, ex0 + 13, ey + 12), fill=(255, 255, 255, 255), outline=LINHA, width=w(2))
            py = -4 if ex == "inocente" else (3 if ab < 10 else 1)
            d.ellipse(Bx(ex0 + ox - pr, ey + py - pr, ex0 + ox + pr, ey + py + pr), fill=(35, 28, 28, 255))
            d.ellipse(Bx(ex0 + ox - pr * 0.2, ey + py - pr * 0.75, ex0 + ox + pr * 0.35, ey + py - pr * 0.2), fill=(255, 255, 255, 255))
            if ab < 10:   # pálpebra: apaga o topo do olho e traça a linha
                d.rectangle(Bx(ex0 - 16, ey - ab - 4, ex0 + 16, ey - ab + 4.5), fill=(0, 0, 0, 0))
                d.line([P(ex0 - 14, ey - ab + 5), P(ex0 + 14, ey - ab + 5)], fill=LINHA, width=w(3))
        if ex == "suspeita": out_, in_ = (-17, -13) if s == -1 else (-27, -25)
        else: out_, in_ = E.SOBR.get(ex, E.SOBR["neutro"])
        yl, yr = (ey + out_, ey + in_) if s == -1 else (ey + in_, ey + out_)
        cs = (150, 150, 155) if who == "neide" else tuple(max(0, v - 10) for v in c["cabelo"])
        d.line([P(ex0 - 14, yl), P(ex0 + 14, yr)], fill=cs, width=w(6.5))
    if who == "neide":
        for s in (-1, 1): d.ellipse(Bx(s * 26 - 19, -22, s * 26 + 19, 16), outline=(90, 60, 110), width=w(4))
        d.line([P(-8, -6), P(8, -6)], fill=(90, 60, 110), width=w(4))
    if bigode:
        d.chord(Bx(-26, 14, 26, 36), 180, 360, fill=(252, 252, 247, 255), outline=(215, 215, 205), width=w(1.5))
        for gx in (-14, 4, 18): d.ellipse(Bx(gx - 4, 22, gx + 4, 32), fill=(252, 252, 247, 255))
    my = 42; lb, ln = (110, 40, 40, 255), (225, 110, 110, 255)
    if forma == "fechada":
        if ex == "nervoso": d.line([P(-22 + i * 4, my + (3 if i % 2 else -3)) for i in range(12)], fill=LINHA, width=w(4))
        elif ex == "inocente": d.arc(Bx(-20, my - 14, 20, my + 8), 20, 160, fill=LINHA, width=w(4))
        elif ex == "feliz":
            d.chord(Bx(-23, my - 13, 23, my + 15), 0, 180, fill=lb, outline=LINHA, width=w(2.5))
            d.rectangle(Bx(-15, my + 1, 15, my + 5), fill=(255, 255, 255, 255))
        elif ex == "brava": d.arc(Bx(-18, my, 18, my + 22), 200, 340, fill=LINHA, width=w(4))
        elif ex == "surpresa": d.ellipse(Bx(-7, my - 6, 7, my + 10), fill=lb, outline=LINHA, width=w(2))
        else: d.line([P(-16, my), P(16, my)], fill=LINHA, width=w(4))
    else:
        tw, th = {"pequena": (14, 9), "aberta": (16, 18), "larga": (22, 10), "redonda": (10, 15)}[forma]
        d.ellipse(Bx(-tw, my - th / 2, tw, my + th), fill=lb, outline=LINHA, width=w(2.5))
        if th > 9: d.ellipse(Bx(-tw * 0.6, my + th * 0.35, tw * 0.6, my + th * 0.9), fill=ln)
        if forma in ("aberta", "larga"): d.chord(Bx(-tw * 0.62, my - th / 2 + 1.5, tw * 0.62, my - th / 2 + 9), 180, 360, fill=(255, 255, 255, 255))
    if ex == "nervoso":
        d.polygon([P(74, -40), P(66, -18), P(82, -18)], fill=(150, 210, 255, 255), outline=LINHA)
        d.ellipse(Bx(66, -26, 82, -10), fill=(150, 210, 255, 255))
    P_ = P_.reduce(SS); colar_seguro(im, P_, cx - meio, cy - meio)

# ------------------------------------------------------------------ adereços
def texto_quadro(setup, atual, ant, tt):
    """escreve o texto do quadro numa imagem 'reta' e projeta na porta da geladeira (homografia)."""
    BW, BH = 900, 740
    img = Image.new("RGBA", (BW, BH), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    novas = E.linhas_quadro(atual["arg"]); velhas = E.linhas_quadro(ant["arg"]) if ant else []
    mud = [i for i, l in enumerate(novas) if i >= len(velhas) or velhas[i] != l]
    for i, txt in enumerate(novas):
        cor = (40, 80, 170, 255) if i == 0 else (200, 50, 50, 255); fs = 92 if i == 0 else 84
        full = txt
        if i in mud:
            prog = (tt - atual["t"] - mud.index(i) * 0.55) / 0.45
            if prog <= 0: continue
            txt = txt[: max(1, int(len(txt) * min(1, prog)))]
        f = E.font(fs, "marcador"); larg = f.getlength(full)
        if larg > BW - 90: f = E.font(fs * (BW - 90) / larg, "marcador")
        yy = BH * (0.17 if i == 0 else 0.40 + (i - 1) * 0.2)
        d.text((BW / 2, yy), txt, font=f, fill=cor, anchor="mm")
    dst = np.float32(PROJ[setup]["quadro"]); x0, y0 = np.floor(dst.min(0)).astype(int); x1, y1 = np.ceil(dst.max(0)).astype(int)
    if x1 < 0 or y1 < 0 or x0 > W or y0 > H: return None
    Hm = cv2.getPerspectiveTransform(np.float32([[0, 0], [BW, 0], [BW, BH], [0, BH]]), dst - np.float32([x0, y0]))
    arr = cv2.warpPerspective(np.asarray(img), Hm, (int(x1 - x0), int(y1 - y0)), flags=cv2.INTER_AREA)
    return Image.fromarray(arr), int(x0), int(y0)

def aderecos(im, setup, tt, Est):
    if (setup, "etiq0") not in PROPS: return
    te = Est.primeiro("etiquetas")
    if te is not None:
        for k in range(4):
            u = (tt - te - k * 0.3) / 0.15
            if u < 0 or (setup, f"etiq{k}") not in PROPS: continue
            colar(im, PROPS[(setup, f"etiq{k}")], escala=1 + 0.3 * max(0, 1 - u) if u < 2 else 1)
    tc = Est.primeiro("cadeado")
    if tc is not None and tt >= tc and (setup, "cadeado") in PROPS:
        u = min(1, (tt - tc) / 0.22); colar(im, PROPS[(setup, "cadeado")], dy=-60 * (1 - u) ** 2 * PROJ[setup]["clara"]["r"] / 100)
    atual, ant = Est.quadro(tt)
    if atual is not None and (setup, "quadro") in PROPS:
        colar(im, PROPS[(setup, "quadro")], alpha=min(1, (tt - atual["t"]) / 0.2) if ant is None else 1)
        t = texto_quadro(setup, atual, ant, tt)
        if t: colar(im, t)

# ------------------------------------------------------------------ quadro (frame)
def preparar3d(pl):
    if pl["tipo"] != "cena": return None
    s = setup_de(pl["shot"], pl["cena"]); pl["setup"] = s
    tipo = "dois" if pl["shot"] == "dois" else "close" if pl["shot"].startswith("close") else None
    pl["aprox"] = E.APROXIMA.get(tipo, 0)
    return PLACAS[s]

def quadro3d(f, pl, base):
    tt = f / FPS
    if pl["tipo"] == "card":
        c, lt, C = pl["card"], tt - pl["t0"], E.G["cartelas"]
        if c["nome"] == "abertura": return abertura3d(lt, f)
        if c["nome"] == "vinheta": return vinheta3d(lt, f, c["texto"]) if "fachada" in PLACAS else C.vinheta(lt, f, c["texto"])
        return C.creditos(lt, f)
    Est, cena, S = E.G["estado"], pl["cena"], pl["setup"]
    im = base.copy(); aderecos(im, S, tt, Est)
    pos = {who: Est.posicao(cena, who, tt) for who in cena["elenco"]}
    presentes = {w_: p[0] for w_, p in pos.items() if p[0] is not None}
    for who in sorted(presentes, key=lambda w_: -PROJ[S][w_]["prof"]):
        if (S, who, "repouso") not in SPR: continue
        x2d, anda = pos[who]; info = PROJ[S][who]; k = info["r"] / 68.0
        dx = (x2d - E.ELENCO[who]["x"]) * k
        bob = (-abs(math.sin(tt * 11)) * 7 if anda else math.sin(tt * 2.2 + len(who)) * 1.6) * k
        ex = Est.expressao(cena, who, tt); boca = Est.boca(cena, who, tt); fala = Est.fala_de(cena, who, tt)
        olha = Est.olhar(cena, who, x2d, tt, presentes)
        nome_pose, g, _ = E.pose_de(ex, fala, tt); alvo = pose_sprite(S, who, nome_pose, olha)
        t = E.ease((g - 0.15) / 0.6) if alvo != "repouso" else 0
        if t <= 0.01: colar(im, SPR[(S, who, "repouso")], dx, bob)
        elif t >= 0.99: colar(im, SPR[(S, who, alvo)], dx, bob)
        else: colar_mistura(im, SPR[(S, who, "repouso")], SPR[(S, who, alvo)], t, dx, bob)
        if -info["r"] < info["cx"] + dx < W + info["r"]:
            rosto(im, info["cx"] + dx, info["cy"] + bob, k, who, ex, boca, E.piscando(who, f), olha,
                  who in cena.get("bigode", ["beto"]))
    if pl["aprox"]:
        z = 1 + pl["aprox"] * E.ease((tt - pl["t0"]) / max(0.5, pl["t1"] - pl["t0"]))
        cw, ch = W / z, H / z; x0, y0 = (W - cw) / 2, (H - ch) / 2
        im = im.resize((W, H), Image.BICUBIC, box=(x0, y0, x0 + cw, y0 + ch))
    fl = Est.legenda(cena, tt)
    if fl: li = E.legenda_img(fl); im.paste(li, (int((W - li.width) / 2), H - 50 - li.height), li)
    return im

def vinheta3d(lt, f, texto):
    C = E.G["cartelas"]; lt = max(0.0, lt); z = 1.0 + 0.06 * lt / 2.4
    cw, ch = W / z, H / z; x0, y0 = (W - cw) / 2, (H - ch) * 0.35
    im = PLACAS["fachada"].resize((W, H), Image.BICUBIC, box=(x0, y0, x0 + cw, y0 + ch))
    if texto not in C.txt: C.txt[texto] = E.texto_img(texto, 72, "titulo", contorno=(40, 40, 60), sw=6)
    E.colar(im, C.txt[texto], W / 2, 110, 1.0, E.ease(lt / 0.4)); return im

def abertura3d(lt, f):
    C = E.G["cartelas"]
    im = Image.new("RGB", (W, H), (246, 192, 74)); d = ImageDraw.Draw(im); cx, cy = W / 2, H * 0.3
    for k in range(18):
        a0 = math.radians(k * 20 + lt * 8); a1 = a0 + math.radians(10); Rr = W * 1.2
        d.polygon([(cx, cy), (cx + Rr * math.cos(a0), cy + Rr * math.sin(a0)), (cx + Rr * math.cos(a1), cy + Rr * math.sin(a1))], fill=(240, 178, 58))
    for k, who in enumerate(("clara", "neide", "beto")):
        if ("abertura", who, "repouso") not in SPR: continue
        u = E.ease((lt - 0.3 - k * 0.25) / 0.5); dy = (1 - u) * 760 + 170
        colar(im, SPR[("abertura", who, "repouso")], 0, dy); info = PROJ["abertura"][who]; kk = info["r"] / 68
        rosto(im, info["cx"], info["cy"] + dy, kk, who, "feliz", ("fechada", 0), E.piscando(who, f), 0, False)
    u = (lt - 1.2) / 0.5
    esc = 0 if u < 0 else (1.15 * E.ease(u) if u < 1 else 1.15 - 0.15 * E.ease((u - 1) * 2))
    E.colar(im, C.titulo, W / 2, 225, esc); E.colar(im, C.sub, W / 2, 370, 1.0, E.ease((lt - 2.4) / 0.5))
    return im

E.preparar = preparar3d
E.quadro = quadro3d

# ------------------------------------------------------------------ principal
def main():
    args = sys.argv[1:]; roteiro = os.path.join(D3, "roteiro.txt")
    carregar()
    print(f"placas {len(PLACAS)} · sprites {len(SPR)} · adereços {len(PROPS)}")
    meta, falas, planos, eventos, sons, cenas, risos, total = E.montar(roteiro)
    E._QD[:] = [e for e in eventos if e["nome"] == "quadro"]
    for fl in falas: E.analisar_boca(fl)
    E.G.update(planos=planos, estado=E.Estado(falas, eventos, cenas), cartelas=E.Cartelas(meta))
    print(f"duração {total:.1f}s · {len(planos)} planos")
    if args and args[0] == "preview":
        for ts in args[1:]:
            tt = float(ts); i = next(k for k, p in enumerate(planos) if p["t0"] <= tt < p["t1"])
            quadro3d(int(tt * FPS), planos[i], preparar3d(planos[i])).save(os.path.join(D3, f"prev_{ts}.png"))
        return
    E.mixar_audio(falas, eventos, sons, cenas, risos, total, os.path.join(D3, "audio.wav"))
    shutil.rmtree(os.path.join(D3, "planos"), ignore_errors=True); os.makedirs(os.path.join(D3, "planos"))
    ordem = sorted(range(len(planos)), key=lambda i: -(planos[i]["t1"] - planos[i]["t0"]))
    with Pool(os.cpu_count() or 2) as pool:
        for n, _ in enumerate(pool.imap_unordered(E.render_plano, ordem), 1):
            if n % 15 == 0: print(f"  {n}/{len(planos)} planos", flush=True)
    feitos = [os.path.join(D3, "planos", f"p{i:03d}.mp4") for i in range(len(planos)) if os.path.exists(os.path.join(D3, "planos", f"p{i:03d}.mp4"))]
    with open(os.path.join(D3, "planos", "lista.txt"), "w") as fh: fh.writelines(f"file '{x}'\n" for x in feitos)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", os.path.join(D3, "planos", "lista.txt"),
                    "-c", "copy", os.path.join(D3, "video.mp4")], check=True)
    os.makedirs(os.path.join(D3, "saida"), exist_ok=True)
    nome = os.path.join("saida", re.sub(r"[^\w]+", "_", meta.get("TITULO", "episodio")).strip("_") + "_3D.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", os.path.join(D3, "video.mp4"), "-i", os.path.join(D3, "audio.wav"),
                    "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-af", "loudnorm=I=-16:TP=-1.5:LRA=11,alimiter=limit=0.84:level=false",
                    "-ar", "48000", "-c:a", "aac", "-b:a", "192k", "-shortest", os.path.join(D3, nome)], check=True)
    print("pronto:", nome)

if __name__ == "__main__":
    main()
