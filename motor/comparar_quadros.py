"""Compara quadros gerados com os de referência (aprovados) e aponta o que mudou.

  python3 motor/comparar_quadros.py <referencia> <gerados> [prancha.jpg]

As duas pastas têm a mesma estrutura (<modo>/rt_<quadro>.png). Para cada quadro mede:
  - diferença média dos pixels (0–100%);
  - área mudada: % dos pixels com diferença acima de 10% (pega mudanças localizadas, como uma cabeça
    que tombou, que quase não mexem na média).
Mudou = média > 2% ou área > 0,5% (a cabeça tombada num plano aberto mexe em 0,7%). Monta uma prancha "referência | agora" só com os que mudaram.
Sai com código 1 se algum mudou (ou se falta algum quadro).
"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

LIM_MEDIA, LIM_AREA = 2.0, 0.5           # ruído do render (mesmo código, duas vezes): média 0,12%, área 0,00%
FONTE = Path(__file__).resolve().parent.parent / "fontes" / "Poppins-Medium.ttf"

def carregar(p):
    return np.asarray(Image.open(p).convert("RGB"), dtype=np.float32) / 255.0

def main():
    ref, ger = Path(sys.argv[1]), Path(sys.argv[2])
    prancha = Path(sys.argv[3]) if len(sys.argv) > 3 else ger / "prancha_mudancas.jpg"
    mudados, faltam = [], []
    refs = sorted(ref.rglob("rt_*.png"))
    if not refs:                               # sem referência não dá para dizer que nada mudou
        print(f"sem quadros de referência em {ref}: gere, mostre ao Lucas e rode 'regressao.sh aprovar'")
        sys.exit(2)
    novos = sorted(str(g.relative_to(ger)) for g in ger.rglob("rt_*.png") if not (ref / g.relative_to(ger)).exists())
    print(f"{'quadro':34s} {'média':>7s} {'área':>7s}")
    for r in refs:
        nome = r.relative_to(ref); g = ger / nome
        if not g.exists():
            faltam.append(str(nome)); continue
        a, b = carregar(r), carregar(g)
        if a.shape != b.shape:
            b = np.asarray(Image.open(g).convert("RGB").resize(a.shape[1::-1]), dtype=np.float32) / 255.0
        d = np.abs(a - b).max(axis=2)
        media, area = 100 * d.mean(), 100 * (d > 0.10).mean()
        mudou = media > LIM_MEDIA or area > LIM_AREA
        print(f"{str(nome):34s} {media:6.2f}% {area:6.2f}% {'MUDOU' if mudou else ''}")
        if mudou: mudados.append((nome, r, g, media, area))
    for f in faltam: print(f"{f:34s} FALTA (não foi gerado)")
    for f in novos: print(f"{f:34s} SEM REFERÊNCIA (quadro novo: aprovar antes)")
    faltam += novos
    if mudados:
        W, H = 640, 360
        img = Image.new("RGB", (2 * W + 30, len(mudados) * (H + 50) + 10), (24, 24, 28))
        dr = ImageDraw.Draw(img); fonte = ImageFont.truetype(str(FONTE), 22)
        for i, (nome, r, g, media, area) in enumerate(mudados):
            y = 10 + i * (H + 50)
            dr.text((10, y), f"{nome} · média {media:.1f}% · área {area:.1f}%   (referência | agora)", font=fonte, fill=(255, 230, 120))
            for j, p in enumerate((r, g)):
                img.paste(Image.open(p).convert("RGB").resize((W, H)), (10 + j * (W + 10), y + 36))
        prancha.parent.mkdir(parents=True, exist_ok=True); img.save(prancha, quality=88)
        print(f"\n{len(mudados)} quadro(s) mudaram: {prancha}")
    else:
        print("\nnenhum quadro mudou")
    sys.exit(1 if (mudados or faltam) else 0)

if __name__ == "__main__":
    main()
