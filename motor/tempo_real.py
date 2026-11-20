"""Prepara os dados da versão three.js (tempo real) de uma cena do roteiro:
linha do tempo por quadro (expressão, boca, piscada, olhar, gesto), texturas dos rostos,
legendas e o áudio da cena (mesmas vozes e risada da versão Blender).

  python3 motor/tempo_real.py            # cena 0 (abertura fria) -> tempo_real/dados/
  python3 motor/tempo_real.py 2          # outra cena (índice)
"""
import json, os, shutil, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw

MOTOR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, MOTOR)
import episodio3d as E3
E = E3.E
RAIZ = E3.D3
OUT = os.path.join(RAIZ, "tempo_real", "dados")

N = 512                      # textura do rosto (px)
KF = (N / 2) / 110           # escala: 110 unidades do desenho = meia textura (cabeça = 68)
CAMINHADA = dict(t0=0.0, t1=2.5, de=[2.85, 0.3], ate=[0.75, 0.0])   # Beto vem do balcão (só na cena 0)
RAIO_CORTE = 71              # o que passa da cabeça (gota de suor) vai num retalho separado

def textura_rosto(who, ex, forma, pisca, olha, bigode):
    im = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    ex_desenho = ex
    E3.rosto(im, N / 2, N / 2, KF, who, ex_desenho, (forma, 0), pisca, olha, bigode)
    a = np.asarray(im).copy(); yy, xx = np.mgrid[0:N, 0:N]
    fora = (xx - N / 2) ** 2 + (yy - N / 2) ** 2 > (RAIO_CORTE * KF) ** 2
    a[fora, 3] = 0
    return Image.fromarray(a)

def gota():
    """gota de suor (desenhada igual ao rosto, coordenadas 66..82 x -40..-10)."""
    S = 4; k = 6 * S
    im =Image.new("RGBA", (24 * 6 * S, 36 * 6 * S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    P = lambda x, y: ((x - 62) * k, (y + 42) * k)
    d.polygon([P(74, -40), P(66, -18), P(82, -18)], fill=(150, 210, 255, 255), outline=E.LINHA, width=S * 2)
    d.ellipse([P(66, -26), P(82, -10)], fill=(150, 210, 255, 255), outline=E.LINHA, width=S * 2)
    d.polygon([P(74, -38), P(67.5, -19), P(80.5, -19)], fill=(150, 210, 255, 255))
    return im.reduce(S)

def main():
    idx = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    meta, falas, planos, eventos, sons, cenas, risos, total = E.montar(os.path.join(RAIZ, "roteiro.txt"))
    for fl in falas: E.analisar_boca(fl)
    est = E.Estado(falas, eventos, cenas)
    cena = cenas[idx]; t0, t1 = cena["t0"], cena["t1"]
    shutil.rmtree(OUT, ignore_errors=True); os.makedirs(os.path.join(OUT, "rostos")); os.makedirs(os.path.join(OUT, "legendas"))
    fs = range(int(round(t0 * E.FPS)), int(round(t1 * E.FPS)) + 1)
    chaves, quadros = {}, []
    for f in fs:
        tt = f / E.FPS; linha = {}
        presentes = {w: E.ELENCO[w]["x"] for w in cena["elenco"]}
        for who in cena["elenco"]:
            ex = est.expressao(cena, who, tt); forma, vol = est.boca(cena, who, tt)
            pisca = E.piscando(who, f); olha = est.olhar(cena, who, presentes[who], tt, presentes)
            bigode = who in cena.get("bigode", ["beto"])
            ch = (who, ex, forma, bool(pisca), olha, bigode)
            if ch not in chaves:
                nome = f"{who}_{len(chaves):03d}.png"; chaves[ch] = nome
                textura_rosto(*ch).save(os.path.join(OUT, "rostos", nome))
            fala = est.fala_de(cena, who, tt); pose, g, _ = E.pose_de(ex, fala, tt)
            linha[who] = dict(rosto=chaves[ch], ex=ex, vol=round(float(vol), 3), olha=olha, pose=pose, g=round(float(g), 3),
                              forma=forma, pisca=bool(pisca))
        quadros.append(linha)
    gota().save(os.path.join(OUT, "gota.png"))
    leg = []
    for k, fl in enumerate(f for f in falas if f["cena"] is cena):
        nome = f"leg{k}.png"; E.legenda_img(fl).save(os.path.join(OUT, "legendas", nome))
        leg.append(dict(t0=fl["t0"] - 0.1 - t0, t1=fl["t1"] + 0.25 - t0, img=nome, who=fl["who"], texto=fl["text"],
                        fala0=fl["t0"] - t0, fala1=fl["t1"] - t0, shot=fl["shot"]))
    # áudio só desta cena
    fl_c = [f for f in falas if f["cena"] is cena]
    so_c = [(t, s) for t, s in sons if t0 <= t < t1]
    if idx == 0:   # passos do Beto
        k = 0
        while CAMINHADA["t0"] + 0.16 + k * 0.32 < CAMINHADA["t1"]:
            so_c.append((t0 + CAMINHADA["t0"] + 0.16 + k * 0.32, E.sfx_passo(k) * 0.8)); k += 1
    ri_c = [(t, r) for t, r in risos if t0 <= t < t1]
    ev_c = [e for e in eventos if t0 <= e["t"] < t1]
    wav = os.path.join(OUT, "bruto.wav")
    E.mixar_audio(fl_c, ev_c, so_c, [cena], ri_c, t1, wav)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{t0:.3f}", "-t", f"{t1 - t0:.3f}", "-i", wav,
                    "-af", "loudnorm=I=-16:TP=-1.5:LRA=11,alimiter=limit=0.84:level=false", "-ar", "48000",
                    os.path.join(OUT, "audio.wav")], check=True)
    os.remove(wav)
    json.dump(dict(fps=E.FPS, dur=t1 - t0, elenco=cena["elenco"], quadros=quadros, legendas=leg,
                   risos=[(t - t0, r) for t, r in ri_c], kf=KF, n=N,
                   caminhada=CAMINHADA if idx == 0 else None),
              open(os.path.join(OUT, "linha.json"), "w"), ensure_ascii=False)
    print(f"cena {idx}: {t1 - t0:.2f}s · {len(quadros)} quadros · {len(chaves)} rostos · {len(leg)} falas")

if __name__ == "__main__":
    main()
