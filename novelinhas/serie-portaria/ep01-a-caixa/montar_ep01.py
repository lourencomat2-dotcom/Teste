#!/usr/bin/env python3
"""Monta o ep. 1 na ordem do roteiro (grátis, só ffmpeg).

Cada plano usa um trecho de uma tomada. O trecho é achado pela fala: para planos de fala, do começo da fala
(menos 0,25 s) até o fim dela (mais 0,5 s); para planos de reação, o que vem depois da fala.
Tomadas com duas falas são divididas na pausa entre elas.
Plano sem tomada pronta entra como cartela preta com o texto do plano (para ver o ritmo).

Uso: python montar_ep01.py            -> ep01_montagem.mp4
Ajuste fino: ajustes.json {"7": [inicio, fim]} sobrescreve o trecho de um plano (segundos da tomada).
"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

B = Path(__file__).resolve().parent
TOM = B / "tomadas"
TRAB = B / "montagem"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

# plano -> (arquivo, parte). parte: "fala" (única fala), "fala1"/"fala2" (tomada com duas falas), "depois" (reação após a fala)
PLANOS = {
    1: ("hall1.mp4", "tudo"), 2: ("valdir1.mp4", "fala"), 3: ("juninho1.mp4", "fala"), 4: ("caixa.jpg", "imagem"),
    5: ("soraia1.mp4", "fala"), 6: ("valdir2.mp4", "fala1"), 7: ("soraia1.mp4", "depois"), 8: ("valdir2.mp4", "fala2"),
    9: ("soraia2.mp4", "fala"), 10: ("sigilo1.mp4", "fala"), 11: ("valdir3.mp4", "fala"), 12: ("hall2.mp4", "tudo"),
    13: ("soraia3.mp4", "fala"), 14: ("perfil.mp4", "tudo"), 15: ("valdir4.mp4", "fala"), 16: ("neide1.mp4", "fala"),
    17: ("soraia4.mp4", "fala"), 18: ("neide2.mp4", "fala"), 19: ("../piloto/clipe2_flash.mp4", "fala"),
    20: ("neide2.mp4", "depois"), 21: ("juninho2.mp4", "fala"), 22: ("soraia5.mp4", "fala"), 23: ("neide3.mp4", "fala"),
    24: ("soraia6.mp4", "fala"), 25: ("valdir5.mp4", "fala"), 26: ("sigilo2.mp4", "fala"), 27: ("valdir5.mp4", "depois"),
    28: ("sigilo3.mp4", "fala1"), 29: ("neide4.mp4", "fala"), 30: ("sigilo3.mp4", "fala2"), 31: ("juninho3.mp4", "fala"),
}


def ff(*a):
    r = subprocess.run(["ffmpeg", "-v", "error", "-y", *map(str, a)], capture_output=True, text=True)
    if r.returncode:
        sys.exit("ffmpeg: " + r.stderr[-600:])


def duracao(f):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(f)],
                                capture_output=True, text=True).stdout)


def falas(f):
    """Trechos com voz (início, fim) em segundos, juntando buracos menores que 0,35 s."""
    x = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", str(f), "-ac", "1", "-ar", "16000", "-f", "f32le", "-"],
                                     capture_output=True).stdout, dtype=np.float32)
    w = 320
    n = len(x) // w
    e = 20 * np.log10(np.sqrt((x[:n * w].reshape(n, w) ** 2).mean(1) + 1e-12))
    on = e > e.max() - 22
    seg, a = [], None
    for k, v in enumerate(list(on) + [False]):
        if v and a is None:
            a = k
        if not v and a is not None:
            seg.append([a * 0.02, k * 0.02])
            a = None
    junt = []
    for s in seg:
        if junt and s[0] - junt[-1][1] < 0.35:
            junt[-1][1] = s[1]
        else:
            junt.append(s)
    return [s for s in junt if s[1] - s[0] > 0.15]


def trecho(f, parte):
    d = duracao(f)
    if parte == "tudo":
        return 0.0, d
    fs = falas(f)
    if not fs:
        return 0.0, d
    if parte in ("fala1", "fala2"):  # divide na maior pausa
        if len(fs) == 1:
            meio = (fs[0][0] + fs[0][1]) / 2
            g1, g2 = [fs[0][0], meio], [meio, fs[0][1]]
        else:
            k = max(range(len(fs) - 1), key=lambda i: fs[i + 1][0] - fs[i][1])
            g1, g2 = [fs[0][0], fs[k][1]], [fs[k + 1][0], fs[-1][1]]
        a, b = g1 if parte == "fala1" else g2
        return max(0, a - 0.25), min(d, b + 0.5)
    ini, fim = fs[0][0], fs[-1][1]
    if parte == "fala":
        return max(0, ini - 0.25), min(d, fim + 0.5)
    if parte == "depois":
        return min(d - 1.0, fim + 0.2), d
    return 0.0, d


def main():
    TRAB.mkdir(exist_ok=True)
    roteiro = {}
    for linha in (B / "roteiro.md").read_text().splitlines():
        p = [c.strip() for c in linha.split("|")]
        if len(p) > 6 and p[1].isdigit():
            roteiro[int(p[1])] = (p[5] if p[5] != "(sem fala)" else p[6])
    aj = json.loads((B / "ajustes.json").read_text()) if (B / "ajustes.json").exists() else {}
    segs, faltando, tabela = [], [], []
    for n in sorted(PLANOS):
        arq, parte = PLANOS[n]
        f = (TOM / arq).resolve()
        s = TRAB / f"p{n:02d}.mov"
        if parte == "imagem":
            if f.exists():
                ff("-loop", "1", "-i", f, "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-t", 2,
                   "-vf", "scale=1708:960,zoompan=z='1+0.05*on/48':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=48:s=854x480:fps=24,format=yuv420p",
                   "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-c:a", "pcm_s16le", s)
            else:
                faltando.append(n)
                cartela(n, roteiro.get(n, arq), 2.0, s)
            segs.append(s)
            continue
        if not f.exists():
            faltando.append(n)
            cartela(n, roteiro.get(n, arq), 3.0, s)
            segs.append(s)
            continue
        a, b = aj.get(str(n), trecho(f, parte))
        d = b - a
        tabela.append((n, arq, round(a, 2), round(b, 2)))
        ff("-ss", f"{a:.2f}", "-t", f"{d:.2f}", "-i", f, "-vf", "scale=854:480,setsar=1,fps=24,format=yuv420p",
           "-af", f"aresample=48000,aformat=channel_layouts=stereo,loudnorm=I=-16:TP=-2,afade=t=in:d=0.03,afade=t=out:st={max(0, d - 0.05):.2f}:d=0.05",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-c:a", "pcm_s16le", s)
        segs.append(s)
    (TRAB / "lista.txt").write_text("".join(f"file '{p.resolve()}'\n" for p in segs))
    ff("-f", "concat", "-safe", "0", "-i", TRAB / "lista.txt", "-c", "copy", TRAB / "junto.mov")
    saida = B / "ep01_montagem.mp4"
    ff("-i", TRAB / "junto.mov", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000", "-c:v", "libx264", "-preset", "slow",
       "-crf", "20", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", saida)
    (B / "montagem_trechos.json").write_text(json.dumps(tabela, indent=1))
    print(f"{saida.name}: {duracao(saida):.1f} s | planos faltando: {faltando or 'nenhum'}")


def cartela(n, texto, dur, s):
    t = f"plano {n}: {texto}".replace("'", "’").replace(":", "\\:")
    ff("-f", "lavfi", "-i", f"color=c=black:s=854x480:r=24:d={dur}", "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
       "-t", dur, "-vf", f"drawtext=fontfile={FONT}:text='{t[:70]}':x=(w-tw)/2:y=(h-th)/2:fontsize=22:fontcolor=white,format=yuv420p",
       "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-c:a", "pcm_s16le", s)


if __name__ == "__main__":
    main()
