"""Renderiza só uma cena na versão Blender (sprites) e monta o lado a lado com a versão three.js.

  python3 motor/comparar_cena.py 0     # -> saida/abertura_blender.mp4 e saida/abertura_comparacao.mp4
"""
import os, subprocess, sys
from multiprocessing import Pool
MOTOR = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, MOTOR)
import episodio3d as E3
E = E3.E
RAIZ = E3.D3; SAIDA = os.path.join(RAIZ, "saida")

def main():
    idx = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    E3.carregar()
    meta, falas, planos, eventos, sons, cenas, risos, total = E.montar(os.path.join(RAIZ, "roteiro.txt"))
    E._QD[:] = [e for e in eventos if e["nome"] == "quadro"]
    for fl in falas: E.analisar_boca(fl)
    E.G.update(planos=planos, estado=E.Estado(falas, eventos, cenas), cartelas=E.Cartelas(meta))
    cena = cenas[idx]
    meus = [i for i, p in enumerate(planos) if p["tipo"] == "cena" and p["cena"] is cena]
    os.makedirs(os.path.join(RAIZ, "planos"), exist_ok=True); os.makedirs(SAIDA, exist_ok=True)
    with Pool(os.cpu_count() or 2) as pool: list(pool.imap_unordered(E.render_plano, meus))
    lista = os.path.join(RAIZ, "planos", "lista_cena.txt")
    with open(lista, "w") as fh: fh.writelines(f"file '{os.path.join(RAIZ, 'planos', f'p{i:03d}.mp4')}'\n" for i in meus)
    wav = os.path.join(RAIZ, "planos", "cena.wav")
    E.mixar_audio([f for f in falas if f["cena"] is cena], [e for e in eventos if cena["t0"] <= e["t"] < cena["t1"]],
                  [(t, s) for t, s in sons if cena["t0"] <= t < cena["t1"]], [cena],
                  [(t, r) for t, r in risos if cena["t0"] <= t < cena["t1"]], cena["t1"], wav)
    nome = "abertura" if idx == 0 else f"cena{idx}"
    bl = os.path.join(SAIDA, f"{nome}_blender.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lista, "-ss", f"{cena['t0']:.3f}",
                    "-t", f"{cena['t1'] - cena['t0']:.3f}", "-i", wav, "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                    "-af", "loudnorm=I=-16:TP=-1.5:LRA=11,alimiter=limit=0.84:level=false", "-ar", "48000", "-c:a", "aac",
                    "-b:a", "192k", "-shortest", bl], check=True)
    tj = os.path.join(SAIDA, f"{nome}_threejs.mp4")
    if os.path.exists(tj):   # um em cima do outro (bom para ver no celular), áudio da versão three.js
        fonte = os.path.join(RAIZ, "fontes", "Poppins-Bold.ttf").replace(":", r"\:")
        rot = lambda t: f"drawtext=fontfile='{fonte}':text='{t}':x=24:y=20:fontsize=34:fontcolor=white:box=1:boxcolor=black@0.55:boxborderw=12"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", bl, "-i", tj, "-filter_complex",
                        f"[0:v]scale=1280:720,{rot('Antes - Blender (sprites)')}[a];[1:v]scale=1280:720,{rot('Agora - three.js (tempo real)')}[b];"
                        "[a][b]vstack[v]", "-map", "[v]", "-map", "1:a", "-c:v", "libx264", "-crf", "20", "-preset", "medium",
                        "-pix_fmt", "yuv420p", "-c:a", "copy", "-shortest", os.path.join(SAIDA, f"{nome}_comparacao.mp4")], check=True)
    print("pronto:", bl)

if __name__ == "__main__":
    main()
