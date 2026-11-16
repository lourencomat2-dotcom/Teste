#!/usr/bin/env python3
"""estudio.py — produção de novelinha por etapas, do mais barato para o mais caro.

    validar  -> confere as regras do roteiro e mostra o custo previsto      (grátis)
    quadros  -> gera 1 quadro parado por plano                              (~US$ 0,04 cada)
    folha    -> junta os quadros numa folha só, para aprovar                (grátis)
    animatic -> vídeo-rascunho: quadros + falas escritas, no ritmo final    (grátis)
    video    -> gera o vídeo só dos planos pedidos                          (~US$ 0,05/s)
    montar   -> corta, junta e normaliza o som em -14 LUFS                  (grátis)

Uso: python estudio.py <etapa> <pasta do episódio> [ids dos planos...] [--refazer]

Nada é gerado duas vezes: o que já existe na pasta é reaproveitado (use --refazer com os
ids para gerar de novo). Todo gasto vai para gasto.json e a etapa para antes de passar do
"teto_usd" do episódio.
"""
import json
import math
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
import mininovela as mn
import novelinha as nv

IMG = {"modelo": "google:nano-banana@2.1", "w": 1376, "h": 768, "preco": 0.045, "espera_maxima_s": 300}
VID = {"modelo": "google:veo@3.1-lite", "w": 1280, "h": 720, "preco_s": 0.05, "duracoes": (4, 6, 8),
       "espera_maxima_s": 1500}
MAX_PROMPT = 2900
PALAVRAS_POR_S = 2.6  # ritmo de fala natural em pt-BR


# ---------- episódio, gasto ----------
def carregar(pasta):
    ep = json.loads((pasta / "episodio.json").read_text())
    for p in ep["planos"]:
        p.setdefault("motor", "veo" if p.get("fala") or p.get("movimento") else "parado")
        p.setdefault("quem", [])
    return ep


def gasto(pasta):
    f = pasta / "gasto.json"
    return json.loads(f.read_text()) if f.exists() else {"total": 0.0, "itens": []}


def registrar(pasta, etapa, plano, custo, obs=""):
    g = gasto(pasta)
    g["itens"].append({"etapa": etapa, "plano": plano, "custo": round(custo, 5), "obs": obs})
    g["total"] = round(sum(i["custo"] for i in g["itens"]), 5)
    (pasta / "gasto.json").write_text(json.dumps(g, indent=1, ensure_ascii=False))


def cabe_no_teto(pasta, ep, previsto):
    g = gasto(pasta)["total"]
    if g + previsto > ep["teto_usd"]:
        sys.exit(f"PARADO: gasto {g:.2f} + previsto {previsto:.2f} passa do teto {ep['teto_usd']:.2f}")


# ---------- prompts ----------
def prompt_quadro(ep, p):
    """Curto e na ordem que o modelo respeita: enquadramento e ação primeiro, estilo no fim."""
    partes = [p["quadro"]]
    for i, nome in enumerate(p["quem"]):
        partes.append(f"{nome.upper()} = the person of image {i + 1}, same face, hair and clothes: {ep['elenco'][nome]['visual']}")
    if p.get("cenario", True):
        partes.append(f"The room is the one of image {len(p['quem']) + 1}: {ep['cenario']['texto']}")
    partes += [ep["atuacao"], ep["estilo"]]
    return " ".join(partes)


def prompt_video(ep, p):
    partes = [p.get("movimento", "")]
    if p.get("fala"):
        v = ep["elenco"][p["falante"]]
        partes.append(f'{p["falante"]} says in Brazilian Portuguese: "{p["fala"]}" Voice: {v["voz"]}.')
        partes.append("Only this one line is spoken, once. Nobody else speaks.")
    else:
        partes.append("Nobody speaks. Mouths stay closed.")
    partes += ["Static camera. Same place, same light, same clothes; nothing appears or disappears.",
               ep["atuacao"], ep["estilo"],
               "Audio: quiet room, soft room tone only. No music. No subtitles, no on-screen text."]
    return " ".join(x for x in partes if x)


# ---------- etapas ----------
def validar(pasta, ep):
    erros, avisos, seg_video = [], [], 0
    for p in ep["planos"]:
        i = p["id"]
        if len(p["quem"]) > 2:
            erros.append(f"{i}: {len(p['quem'])} personagens no quadro (máximo 2)")
        for nome in p["quem"]:
            if nome not in ep["elenco"]:
                erros.append(f"{i}: personagem '{nome}' não está no elenco")
        if p.get("fala"):
            if p.get("falante") not in p["quem"]:
                erros.append(f"{i}: quem fala ({p.get('falante')}) precisa estar no quadro")
            n = len(p["fala"].split())
            cabe = int((p["dur"] - 1.2) * PALAVRAS_POR_S)
            if n > cabe:
                erros.append(f"{i}: fala com {n} palavras não cabe em {p['dur']} s (máx. {cabe})")
        if p["motor"] == "veo":
            if p["dur"] not in VID["duracoes"]:
                erros.append(f"{i}: duração {p['dur']} s; o Veo só faz {VID['duracoes']}")
            seg_video += p["dur"]
            if len(prompt_video(ep, p)) > MAX_PROMPT:
                erros.append(f"{i}: prompt de vídeo passa de {MAX_PROMPT} caracteres")
        if not p.get("quadro_pronto") and len(prompt_quadro(ep, p)) > MAX_PROMPT:
            erros.append(f"{i}: prompt de quadro passa de {MAX_PROMPT} caracteres")
        txt = (p.get("quadro", "") + p.get("movimento", "")).lower()
        if "left hand" in txt or "right hand" in txt:
            avisos.append(f"{i}: exige mão esquerda/direita; os modelos erram isso com frequência")
    n_quadros = sum(1 for p in ep["planos"] if not p.get("quadro_pronto"))
    c_q, c_v = n_quadros * IMG["preco"], seg_video * VID["preco_s"]
    total = sum(p["dur"] for p in ep["planos"])
    print(f"{len(ep['planos'])} planos, {total} s | quadros: {n_quadros} x {IMG['preco']} = US$ {c_q:.2f} | "
          f"vídeo: {seg_video} s x {VID['preco_s']} = US$ {c_v:.2f}")
    print(f"previsto sem refação: US$ {c_q + c_v:.2f} | com 30% de refação: US$ {(c_q + c_v) * 1.3:.2f} | "
          f"teto: US$ {ep['teto_usd']:.2f} | já gasto: US$ {gasto(pasta)['total']:.2f}")
    for a in avisos:
        print("aviso:", a)
    for e in erros:
        print("ERRO:", e)
    if erros:
        sys.exit(1)
    print("roteiro dentro das regras.")


def arq_quadro(pasta, p):
    return pasta / (p.get("quadro_pronto") or f"quadros/{p['id']}.jpg")


def quadros(pasta, ep, ids, refazer):
    (pasta / "quadros").mkdir(exist_ok=True)
    cache_f = pasta / "uploads.json"
    cache = json.loads(cache_f.read_text()) if cache_f.exists() else {}
    mn.CFG["imagem"] = {"modelo": IMG["modelo"], "espera_maxima_s": IMG["espera_maxima_s"]}
    for p in ep["planos"]:
        dest = arq_quadro(pasta, p)
        if p.get("quadro_pronto") or (ids and p["id"] not in ids) or (dest.exists() and not (refazer and p["id"] in ids)):
            continue
        cabe_no_teto(pasta, ep, IMG["preco"])
        refs = [mn.subir_imagem(pasta / ep["elenco"][n]["ref"], cache) for n in p["quem"]]
        if p.get("cenario", True):
            refs.append(mn.subir_imagem(pasta / ep["cenario"]["imagem"], cache))
        cache_f.write_text(json.dumps(cache))
        prompt = prompt_quadro(ep, p)
        bruto = pasta / "quadros" / f"{p['id']}.png"
        custo = mn.gerar_imagem(prompt, bruto, refs, IMG["w"], IMG["h"])
        Image.open(bruto).convert("RGB").save(dest, quality=92)
        bruto.unlink()
        (pasta / "quadros" / f"{p['id']}_prompt.txt").write_text(prompt)
        registrar(pasta, "quadro", p["id"], custo)
        print(f"quadro {p['id']}: US$ {custo:.4f}", flush=True)


def folha(pasta, ep):
    ps = ep["planos"]
    col = 3
    lin = math.ceil(len(ps) / col)
    w, h = 640, 360
    f = Image.new("RGB", (col * w, lin * (h + 56)), (20, 20, 20))
    d = ImageDraw.Draw(f)
    fonte = nv.fonte(20)
    for k, p in enumerate(ps):
        x, y = (k % col) * w, (k // col) * (h + 56)
        a = arq_quadro(pasta, p)
        if a.exists():
            f.paste(Image.open(a).convert("RGB").resize((w, h)), (x, y))
        leg = f"{p['id']} · {p['dur']}s · " + (f"{p['falante']}: {p['fala']}" if p.get("fala") else "(sem fala)")
        d.text((x + 8, y + h + 6), leg[:62], font=fonte, fill=(255, 255, 255))
        d.text((x + 8, y + h + 30), leg[62:124], font=fonte, fill=(255, 255, 255))
    f.save(pasta / "folha.jpg", quality=88)
    print("folha:", pasta / "folha.jpg")


def ff(*a):
    r = subprocess.run(["ffmpeg", "-v", "error", "-y", *map(str, a)], capture_output=True, text=True)
    if r.returncode:
        sys.exit("ffmpeg: " + r.stderr[-800:])


def seg_parado(img, dur, dest, zoom=0.06):
    """Quadro parado com aproximação lenta (grátis) + silêncio."""
    n = int(dur * 24)
    vf = (f"scale=2560:1440,zoompan=z='1+{zoom}*on/{n}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={n}:s=1280x720:fps=24,"
          "format=yuv420p")
    ff("-loop", "1", "-i", img, "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-t", dur, "-vf", vf,
       "-c:v", "libx264", "-preset", "veryfast", "-crf", "15", "-c:a", "pcm_s16le", dest)


def juntar(segs, pasta, saida, crf=21):
    tr = pasta / "trabalho"
    (tr / "lista.txt").write_text("".join(f"file '{s.resolve()}'\n" for s in segs))
    ff("-f", "concat", "-safe", "0", "-i", tr / "lista.txt", "-c", "copy", tr / "junto.mov")
    ff("-i", tr / "junto.mov", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000", "-c:v", "libx264",
       "-preset", "slow", "-crf", crf, "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", saida)
    print("pronto:", saida)


def animatic(pasta, ep):
    tr = pasta / "trabalho"
    tr.mkdir(exist_ok=True)
    fonte = nv.fonte(40)
    segs = []
    for p in ep["planos"]:
        im = Image.open(arq_quadro(pasta, p)).convert("RGB").resize((1280, 720))
        if p.get("fala"):
            d = ImageDraw.Draw(im)
            t = f"{p['falante'].upper()}: {p['fala']}"
            d.text(((1280 - d.textlength(t, font=fonte)) / 2, 640), t, font=fonte, fill=(255, 255, 255),
                   stroke_width=4, stroke_fill=(0, 0, 0))
        im.save(tr / f"a_{p['id']}.png")
        seg_parado(tr / f"a_{p['id']}.png", p.get("usar", [0, p["dur"]])[1] - p.get("usar", [0, p["dur"]])[0],
                   tr / f"a_{p['id']}.mov", zoom=0.03)
        segs.append(tr / f"a_{p['id']}.mov")
    juntar(segs, pasta, pasta / "animatic.mp4", crf=26)


def video(pasta, ep, ids, refazer):
    (pasta / "videos").mkdir(exist_ok=True)
    cache_f = pasta / "uploads.json"
    cache = json.loads(cache_f.read_text()) if cache_f.exists() else {}
    for p in ep["planos"]:
        dest = pasta / "videos" / f"{p['id']}.mp4"
        if p["motor"] != "veo" or (ids and p["id"] not in ids) or (dest.exists() and not (refazer and p["id"] in ids)):
            continue
        previsto = p["dur"] * VID["preco_s"]
        cabe_no_teto(pasta, ep, previsto)
        base = pasta / "videos" / f"{p['id']}_inicio.png"
        Image.open(arq_quadro(pasta, p)).convert("RGB").resize((VID["w"], VID["h"]), Image.LANCZOS).save(base)
        img = mn.subir_imagem(base, cache)
        cache_f.write_text(json.dumps(cache))
        prompt = prompt_video(ep, p)
        tarefa = {"taskType": "videoInference", "model": VID["modelo"], "positivePrompt": prompt,
                  "width": VID["w"], "height": VID["h"], "duration": p["dur"], "numberResults": 1,
                  "outputType": "URL", "outputFormat": "MP4",
                  "frameImages": [{"inputImage": img, "frame": "first"}],
                  "providerSettings": {"google": {"generateAudio": True}}}
        item = nv.runware(tarefa, "videoURL", VID)
        mn.baixar(item["videoURL"], dest)
        (pasta / "videos" / f"{p['id']}_prompt.txt").write_text(prompt)
        custo = item.get("cost") or previsto
        registrar(pasta, "video", p["id"], custo, "" if item.get("cost") else "estimado")
        print(f"vídeo {p['id']}: US$ {custo:.3f}", flush=True)


def montar(pasta, ep):
    tr = pasta / "trabalho"
    tr.mkdir(exist_ok=True)
    segs = []
    for p in ep["planos"]:
        a, b = p.get("usar", [0, p["dur"]])
        s = tr / f"s_{p['id']}.mov"
        clipe = pasta / "videos" / f"{p['id']}.mp4"
        if p["motor"] == "veo":
            if not clipe.exists():
                sys.exit(f"falta o vídeo do plano {p['id']}")
            d = b - a
            ff("-ss", a, "-t", d, "-i", clipe, "-vf", "scale=1280:720,setsar=1,fps=24,format=yuv420p",
               "-af", f"aresample=48000,aformat=channel_layouts=stereo,afade=t=in:d=0.04,afade=t=out:st={d - 0.06:.2f}:d=0.06",
               "-c:v", "libx264", "-preset", "veryfast", "-crf", "15", "-c:a", "pcm_s16le", s)
        else:
            seg_parado(arq_quadro(pasta, p), b - a, s)
        segs.append(s)
    juntar(segs, pasta, pasta / "final.mp4")


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    etapa, pasta = sys.argv[1], Path(sys.argv[2]).resolve()
    resto = sys.argv[3:]
    refazer = "--refazer" in resto
    ids = [x for x in resto if not x.startswith("--")]
    ep = carregar(pasta)
    if etapa == "validar":
        validar(pasta, ep)
    elif etapa == "quadros":
        quadros(pasta, ep, ids, refazer)
    elif etapa == "folha":
        folha(pasta, ep)
    elif etapa == "animatic":
        animatic(pasta, ep)
    elif etapa == "video":
        video(pasta, ep, ids, refazer)
    elif etapa == "montar":
        montar(pasta, ep)
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
