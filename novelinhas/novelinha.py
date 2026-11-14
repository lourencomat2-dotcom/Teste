#!/usr/bin/env python3
"""
Novelinha — transforma um roteiro.json em vídeo pronto para YouTube.

Etapas: voz (TTS) -> imagens -> cenas com movimento -> legendas -> música -> vídeo final
        + thumbnail + legendas .srt + arquivo de título/descrição/tags.

Uso:
  python novelinha.py validar  episodios/ep001/roteiro.json
  python novelinha.py produzir episodios/ep001/roteiro.json
  python novelinha.py produzir episodios/ep001/roteiro.json --teste   (sem APIs: voz muda + imagens provisórias)

Tudo que já foi gerado fica em cache (pasta do episódio). Mudou o texto de uma cena?
Só aquela cena é refeita.
"""
import argparse
import asyncio
import base64
import hashlib
import json
import math
import os
import random
import re
import shutil
import subprocess
import sys
import textwrap
import time
import unicodedata
from pathlib import Path

AQUI = Path(__file__).resolve().parent

FORMATOS = {
    "vertical": (1080, 1920),    # Shorts / Reels / TikTok
    "horizontal": (1920, 1080),  # vídeo longo
}

FONTES_CANDIDATAS = [
    "C:/Windows/Fonts/impact.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
    "/System/Library/Fonts/Supplemental/Impact.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
]


# --------------------------------------------------------------------------- util

def log(msg):
    print(f"[novelinha] {msg}", flush=True)


def erro(msg):
    print(f"[novelinha] ERRO: {msg}", file=sys.stderr)
    sys.exit(1)


def h8(*partes):
    return hashlib.sha1("||".join(map(str, partes)).encode()).hexdigest()[:8]


def rodar(cmd, cwd=None):
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if r.returncode != 0:
        erro(f"comando falhou: {' '.join(map(str, cmd))}\n{r.stderr[-2000:]}")
    return r.stdout


def duracao(arquivo):
    out = rodar(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                 "-of", "default=nw=1:nk=1", str(arquivo)])
    return float(out.strip())


def mesclar(base, extra):
    out = dict(base)
    for k, v in (extra or {}).items():
        out[k] = mesclar(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else v
    return out


def carregar_config(roteiro):
    cfg = json.loads((AQUI / "config.json").read_text(encoding="utf-8"))
    local = AQUI / "config.local.json"  # opcional, fora do git
    if local.exists():
        cfg = mesclar(cfg, json.loads(local.read_text(encoding="utf-8")))
    return mesclar(cfg, roteiro.get("config", {}))


def fonte(tamanho):
    from PIL import ImageFont
    for f in FONTES_CANDIDATAS:
        if Path(f).exists():
            return ImageFont.truetype(f, tamanho)
    return ImageFont.load_default(size=tamanho)


# --------------------------------------------------------------------------- validação

def validar(roteiro):
    problemas = []
    for campo in ("titulo", "cenas"):
        if campo not in roteiro:
            problemas.append(f"falta o campo '{campo}'")
    fmt = roteiro.get("formato", "horizontal")
    if fmt not in FORMATOS:
        problemas.append(f"formato '{fmt}' inválido (use vertical ou horizontal)")
    personagens = roteiro.get("personagens", {})
    # papéis de voz: os do config.json + os definidos no roteiro (por provedor)
    cfg = json.loads((AQUI / "config.json").read_text(encoding="utf-8"))
    vozes = {"narrador"}
    for mapa in list(cfg["tts"].values()) + list(roteiro.get("vozes", {}).values()):
        if isinstance(mapa, dict):
            vozes |= set(mapa.get("vozes", mapa) if "vozes" in mapa else mapa)
    for i, c in enumerate(roteiro.get("cenas", []), 1):
        if not c.get("narracao", "").strip():
            problemas.append(f"cena {i}: narração vazia")
        if not c.get("imagem", "").strip():
            problemas.append(f"cena {i}: sem prompt de imagem")
        for p in c.get("personagens", []):
            if p not in personagens:
                problemas.append(f"cena {i}: personagem '{p}' não está em 'personagens'")
        if c.get("voz", "narrador") not in vozes:
            problemas.append(f"cena {i}: voz '{c.get('voz')}' não está em 'vozes'")
    return problemas


# --------------------------------------------------------------------------- voz

def tts_edge(texto, voz, destino, cfg):
    try:
        import edge_tts
    except ImportError:
        erro("instale o edge-tts:  pip install edge-tts")
    opts = cfg["tts"]["edge"]

    async def _go():
        com = edge_tts.Communicate(texto, voz, rate=opts.get("velocidade", "+0%"),
                                   pitch=opts.get("tom", "+0Hz"))
        await com.save(str(destino))

    for tentativa in range(4):
        try:
            asyncio.run(_go())
            return
        except Exception as e:  # rede instável
            if tentativa == 3:
                erro(f"edge-tts falhou: {e}")
            time.sleep(2 ** tentativa)


def tts_elevenlabs(texto, voz, destino, cfg):
    import requests
    chave = os.environ.get("ELEVENLABS_API_KEY") or erro("defina ELEVENLABS_API_KEY")
    opts = cfg["tts"]["elevenlabs"]
    r = requests.post(
        f"https://api.elevenlabs.io/v1/text-to-speech/{voz}?output_format=mp3_44100_128",
        headers={"xi-api-key": chave},
        json={"text": texto, "model_id": opts.get("modelo", "eleven_multilingual_v2"),
              "voice_settings": opts.get("ajustes", {"stability": 0.45, "similarity_boost": 0.8})},
        timeout=180)
    if r.status_code != 200:
        erro(f"ElevenLabs {r.status_code}: {r.text[:300]}")
    destino.write_bytes(r.content)


def tts_mudo(texto, voz, destino, cfg):
    """Sem voz: silêncio com a duração aproximada da leitura (≈15 caracteres/s). Só para testar."""
    seg = max(1.5, len(texto) / 15)
    rodar(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo",
           "-t", f"{seg:.2f}", "-c:a", "libmp3lame", "-q:a", "4", str(destino)])


TTS = {"edge": tts_edge, "elevenlabs": tts_elevenlabs, "mudo": tts_mudo}


def gerar_vozes(roteiro, cfg, pasta):
    prov = cfg["tts"]["provedor"]
    vozes_cfg = cfg["tts"][prov].get("vozes", {}) if prov in cfg["tts"] else {}
    vozes = mesclar(vozes_cfg, roteiro.get("vozes", {}).get(prov, {}))
    (pasta / "audio").mkdir(exist_ok=True)
    arquivos = []
    for i, c in enumerate(roteiro["cenas"], 1):
        papel = c.get("voz", "narrador")
        voz = vozes.get(papel) or vozes.get("narrador", "")
        texto = c["narracao"].strip()
        destino = pasta / "audio" / f"cena_{i:03d}_{prov}_{h8(texto, voz, json.dumps(cfg['tts'].get(prov, {}), sort_keys=True))}.mp3"
        if not destino.exists() or destino.stat().st_size == 0:
            log(f"voz cena {i}/{len(roteiro['cenas'])} ({papel})")
            tmp = destino.with_suffix(".tmp.mp3")
            TTS[prov](texto, voz, tmp, cfg)
            tmp.rename(destino)
        arquivos.append(destino)
    return arquivos


# --------------------------------------------------------------------------- imagens

def montar_prompt(roteiro, cena):
    partes = [roteiro.get("estilo_visual", "")]
    for p in cena.get("personagens", []):
        info = roteiro.get("personagens", {}).get(p, {})
        if info.get("visual"):
            partes.append(f"{info.get('nome', p)}: {info['visual']}")
    partes.append(cena["imagem"])
    partes.append("no text, no letters, no watermark")
    return ". ".join(x.strip().rstrip(".") for x in partes if x and x.strip())


def img_openai(prompt, destino, w, h, cfg):
    import requests
    chave = os.environ.get("OPENAI_API_KEY") or erro("defina OPENAI_API_KEY")
    opts = cfg["imagens"]["openai"]
    tamanho = "1024x1536" if h > w else "1536x1024"
    r = requests.post("https://api.openai.com/v1/images/generations",
                      headers={"Authorization": f"Bearer {chave}"},
                      json={"model": opts.get("modelo", "gpt-image-1"), "prompt": prompt,
                            "size": tamanho, "quality": opts.get("qualidade", "medium"), "n": 1},
                      timeout=300)
    if r.status_code != 200:
        erro(f"OpenAI {r.status_code}: {r.text[:300]}")
    destino.write_bytes(base64.b64decode(r.json()["data"][0]["b64_json"]))


def img_replicate(prompt, destino, w, h, cfg):
    import requests
    chave = os.environ.get("REPLICATE_API_TOKEN") or erro("defina REPLICATE_API_TOKEN")
    modelo = cfg["imagens"]["replicate"].get("modelo", "black-forest-labs/flux-schnell")
    cab = {"Authorization": f"Bearer {chave}", "Prefer": "wait"}
    r = requests.post(f"https://api.replicate.com/v1/models/{modelo}/predictions", headers=cab,
                      json={"input": {"prompt": prompt, "aspect_ratio": "9:16" if h > w else "16:9",
                                      "output_format": "png"}}, timeout=300)
    if r.status_code >= 300:
        erro(f"Replicate {r.status_code}: {r.text[:300]}")
    pred = r.json()
    while pred.get("status") not in ("succeeded", "failed", "canceled"):
        time.sleep(2)
        pred = requests.get(pred["urls"]["get"], headers=cab, timeout=60).json()
    if pred["status"] != "succeeded":
        erro(f"Replicate falhou: {pred.get('error')}")
    url = pred["output"][0] if isinstance(pred["output"], list) else pred["output"]
    destino.write_bytes(requests.get(url, timeout=120).content)


def img_runware(prompt, destino, w, h, cfg):
    """Runware (runware.ai): modo assíncrono — envia a tarefa e consulta até ficar pronta."""
    import uuid
    import requests
    # Na nuvem do Claude a chave é injetada pelo proxy; no seu computador, defina RUNWARE_API_KEY.
    chave = os.environ.get("RUNWARE_API_KEY", "proxy-injected")
    opts = cfg["imagens"]["runware"]
    cab = {"Authorization": f"Bearer {chave}"}
    url = "https://api.runware.ai/v1"
    largura, altura = (opts.get("tamanho_vertical", [768, 1344]) if h > w
                       else opts.get("tamanho_horizontal", [1344, 768]))
    tid = str(uuid.uuid4())
    tarefa = {"taskType": "imageInference", "taskUUID": tid, "positivePrompt": prompt,
              "model": opts.get("modelo", "runware:100@1"), "width": largura, "height": altura,
              "numberResults": 1, "outputType": "base64Data", "outputFormat": "PNG",
              "includeCost": True, "deliveryMethod": "async"}
    tarefa.update(opts.get("extras", {}))

    def chamar(corpo):
        for tentativa in range(4):
            try:
                r = requests.post(url, headers=cab, json=corpo, timeout=60)
                j = r.json()
                if r.status_code < 300 and not j.get("errors"):
                    return j
                if r.status_code in (400, 401, 402, 403):
                    erro(f"Runware {r.status_code}: {json.dumps(j.get('errors', j))[:400]}")
            except (requests.RequestException, ValueError):
                pass
            time.sleep(2 ** tentativa)
        erro("Runware não respondeu depois de 4 tentativas")

    chamar([tarefa])
    limite = time.time() + opts.get("espera_maxima_s", 300)
    while time.time() < limite:
        time.sleep(2)
        j = chamar([{"taskType": "getResponse", "taskUUID": tid}])
        item = next((d for d in j.get("data", []) if d.get("taskUUID") == tid), {})
        if item.get("imageBase64Data"):
            destino.write_bytes(base64.b64decode(item["imageBase64Data"]))
            if item.get("cost") is not None:
                log(f"  custo: US$ {item['cost']}")
            return
        if item.get("status") in ("error", "failed"):
            erro(f"Runware falhou: {json.dumps(item)[:400]}")
    erro(f"Runware: a imagem não ficou pronta em {opts.get('espera_maxima_s', 300)} s "
         "(conta de teste sem saldo costuma ficar presa na fila)")


def img_provisoria(prompt, destino, w, h, cfg, numero=0):
    """Imagem escura com o prompt escrito — para testar ritmo e montagem sem gastar."""
    from PIL import Image, ImageDraw
    rnd = random.Random(prompt)
    c1 = tuple(rnd.randint(20, 70) for _ in range(3))
    c2 = tuple(max(0, x - 18) for x in c1)
    img = Image.new("RGB", (w, h), c1)
    d = ImageDraw.Draw(img)
    for y in range(h):
        t = y / h
        d.line([(0, y), (w, y)], fill=tuple(int(a * (1 - t) + b * t) for a, b in zip(c1, c2)))
    f = fonte(int(w * 0.035))
    texto = "\n".join(textwrap.wrap(prompt[-400:], 38))
    d.multiline_text((w * 0.08, h * 0.3), texto, font=f, fill=(220, 220, 220), spacing=12)
    img.save(destino)


IMAGENS = {"openai": img_openai, "replicate": img_replicate, "runware": img_runware, "provisoria": img_provisoria}


def gerar_imagens(roteiro, cfg, pasta, w, h):
    prov = cfg["imagens"]["provedor"]
    (pasta / "imagens").mkdir(exist_ok=True)
    arquivos = []
    for i, c in enumerate(roteiro["cenas"], 1):
        # imagem manual tem prioridade: imagens/cena_005.png (ou .jpg)
        manual = next((pasta / "imagens" / f"cena_{i:03d}{ext}" for ext in (".png", ".jpg", ".jpeg")
                       if (pasta / "imagens" / f"cena_{i:03d}{ext}").exists()), None)
        if manual:
            arquivos.append(manual)
            continue
        # cenas podem reaproveitar a imagem de outra: "repetir_imagem": 3
        if c.get("repetir_imagem"):
            arquivos.append(arquivos[int(c["repetir_imagem"]) - 1])
            continue
        prompt = montar_prompt(roteiro, c)
        destino = pasta / "imagens" / f"gerada_{i:03d}_{prov}_{h8(prompt, w > h)}.png"
        if not destino.exists():
            log(f"imagem cena {i}/{len(roteiro['cenas'])}")
            tmp = destino.with_suffix(".tmp.png")
            IMAGENS[prov](prompt, tmp, w, h, cfg)
            tmp.rename(destino)
        arquivos.append(destino)
    return arquivos


# --------------------------------------------------------------------------- cenas com movimento

MOVIMENTOS = ["zoom_in", "zoom_out", "pan_direita", "pan_esquerda", "zoom_in", "pan_cima"]


def clipe_cena(img, audio, destino, w, h, fps, pausa, movimento, intensidade):
    dur_audio = duracao(audio)
    dur = dur_audio + pausa
    frames = max(2, math.ceil(dur * fps))
    z = intensidade
    expr = {
        "zoom_in":      (f"1+{z}*on/{frames}", "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"),
        "zoom_out":     (f"1+{z}-{z}*on/{frames}", "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"),
        "pan_direita":  (f"1+{z}", f"(iw-iw/zoom)*on/{frames}", "ih/2-(ih/zoom/2)"),
        "pan_esquerda": (f"1+{z}", f"(iw-iw/zoom)*(1-on/{frames})", "ih/2-(ih/zoom/2)"),
        "pan_cima":     (f"1+{z}", "iw/2-(iw/zoom/2)", f"(ih-ih/zoom)*(1-on/{frames})"),
    }[movimento]
    W2, H2 = w * 2, h * 2  # escala maior antes do zoompan evita tremedeira
    vf = (f"scale={W2}:{H2}:force_original_aspect_ratio=increase,crop={W2}:{H2},"
          f"zoompan=z='{expr[0]}':x='{expr[1]}':y='{expr[2]}':d={frames}:s={w}x{h}:fps={fps},"
          f"setsar=1,format=yuv420p")
    rodar(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-framerate", str(fps), "-i", str(img),
           "-i", str(audio), "-filter_complex",
           f"[0:v]{vf}[v];[1:a]aresample=48000,aformat=channel_layouts=stereo,apad[a]",
           "-map", "[v]", "-map", "[a]", "-t", f"{dur:.3f}", "-r", str(fps),
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
           "-c:a", "aac", "-b:a", "192k", str(destino)])
    return dur_audio, dur


# --------------------------------------------------------------------------- legendas

def frases(texto, max_palavras):
    """Quebra a narração em pedaços curtos (estilo Shorts), respeitando pontuação."""
    pedacos = []
    for sentenca in re.split(r"(?<=[.!?…])\s+", texto.strip()):
        palavras = sentenca.split()
        atual = []
        for p in palavras:
            atual.append(p)
            if len(atual) >= max_palavras or re.search(r"[,;:—]$", p):
                pedacos.append(" ".join(atual))
                atual = []
        if atual:
            pedacos.append(" ".join(atual))
    return [p for p in pedacos if p]


def ts_srt(s):
    ms = int(round(s * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def ts_ass(s):
    cs = int(round(s * 100))
    return f"{cs // 360000}:{cs // 6000 % 60:02d}:{cs // 100 % 60:02d}.{cs % 100:02d}"


def gerar_legendas(roteiro, tempos, pasta, w, h, cfg):
    lc = cfg["legendas"]
    max_p = lc["palavras_por_linha_vertical"] if h > w else lc["palavras_por_linha_horizontal"]
    itens = []
    for cena, (inicio, dur_audio) in zip(roteiro["cenas"], tempos):
        partes = frases(cena["narracao"], max_p)
        total = sum(len(p) + 3 for p in partes)
        t = inicio
        for p in partes:
            d = dur_audio * (len(p) + 3) / total
            itens.append((t, t + d, p))
            t += d

    srt = "\n".join(f"{n}\n{ts_srt(a)} --> {ts_srt(b)}\n{txt}\n" for n, (a, b, txt) in enumerate(itens, 1))
    (pasta / "saida").mkdir(exist_ok=True)
    (pasta / "saida" / "legendas.srt").write_text(srt, encoding="utf-8")

    tam = int(h * (lc["tamanho_vertical"] if h > w else lc["tamanho_horizontal"]))
    margem = int(h * (0.30 if h > w else 0.07))
    ass = [
        "[Script Info]", "ScriptType: v4.00+", f"PlayResX: {w}", f"PlayResY: {h}", "WrapStyle: 0", "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, "
        "Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
        "Alignment, MarginL, MarginR, MarginV, Encoding",
        f"Style: Padrao,{lc['fonte']},{tam},{lc['cor']},&H000000FF,&H00000000,&H80000000,"
        f"-1,0,0,0,100,100,0,0,1,{max(3, tam // 12)},2,2,{int(w * 0.08)},{int(w * 0.08)},{margem},1",
        "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]
    for a, b, txt in itens:
        t = txt.upper() if lc.get("maiusculas") else txt
        ass.append(f"Dialogue: 0,{ts_ass(a)},{ts_ass(b)},Padrao,,0,0,0,,{{\\fad(60,0)}}{t}")
    (pasta / "legendas.ass").write_text("\n".join(ass) + "\n", encoding="utf-8")


# --------------------------------------------------------------------------- thumbnail + textos

def gerar_thumbnail(roteiro, cfg, pasta, imagem_base):
    from PIL import Image, ImageDraw, ImageEnhance
    yt = roteiro.get("youtube", {})
    w, h = 1280, 720
    base = Image.open(imagem_base).convert("RGB")
    esc = max(w / base.width, h / base.height)
    base = base.resize((math.ceil(base.width * esc), math.ceil(base.height * esc)))
    base = base.crop(((base.width - w) // 2, (base.height - h) // 2, (base.width - w) // 2 + w,
                      (base.height - h) // 2 + h))
    base = ImageEnhance.Contrast(ImageEnhance.Color(base).enhance(1.25)).enhance(1.15)
    texto = yt.get("thumbnail_texto", "").strip().upper()
    if texto:
        d = ImageDraw.Draw(base)
        tamanho = 120
        while tamanho > 40:
            f = fonte(tamanho)
            linhas = textwrap.wrap(texto, max(8, int(22 * 110 / tamanho)))
            larg = max(d.textlength(l, font=f) for l in linhas)
            if larg < w * 0.9 and len(linhas) * tamanho * 1.1 < h * 0.45:
                break
            tamanho -= 6
        y = h - len(linhas) * tamanho * 1.1 - 40
        for l in linhas:
            x = (w - d.textlength(l, font=f)) / 2
            d.text((x, y), l, font=f, fill=(255, 225, 0), stroke_width=max(4, tamanho // 12),
                   stroke_fill=(0, 0, 0))
            y += tamanho * 1.1
    base.save(pasta / "saida" / "thumbnail.jpg", quality=92)


def gerar_textos(roteiro, pasta, capitulos):
    yt = roteiro.get("youtube", {})
    linhas = ["TÍTULOS (escolha um)", "--------------------"]
    linhas += [f"{i}. {t}" for i, t in enumerate(yt.get("titulos", [roteiro["titulo"]]), 1)]
    linhas += ["", "DESCRIÇÃO", "---------", yt.get("descricao", "").strip()]
    if capitulos:
        linhas += ["", "Capítulos:"] + [f"{int(t // 60)}:{int(t % 60):02d} {nome}" for t, nome in capitulos]
    if yt.get("hashtags"):
        linhas += ["", " ".join(yt["hashtags"])]
    linhas += ["", "TAGS", "----", ", ".join(yt.get("tags", []))]
    linhas += ["", "AVISO DE IA (YouTube Studio)", "----------------------------",
               "Marque 'conteúdo alterado ou sintético' se as imagens/vozes parecerem pessoas reais."]
    (pasta / "saida" / "youtube.txt").write_text("\n".join(linhas) + "\n", encoding="utf-8")


# --------------------------------------------------------------------------- montagem

def escolher_musica(roteiro, cfg):
    m = roteiro.get("musica") or cfg["musica"].get("arquivo")
    if m == "nenhuma":
        return None
    if m:
        p = Path(m) if Path(m).is_absolute() else AQUI / "musica" / m
        return p if p.exists() else None
    opcoes = sorted(p for p in (AQUI / "musica").glob("*") if p.suffix.lower() in (".mp3", ".wav", ".m4a", ".ogg"))
    return random.Random(roteiro["titulo"]).choice(opcoes) if opcoes else None


def produzir(caminho, teste=False):
    caminho = Path(caminho).resolve()
    roteiro = json.loads(caminho.read_text(encoding="utf-8"))
    problemas = validar(roteiro)
    if problemas:
        erro("roteiro inválido:\n  - " + "\n  - ".join(problemas))
    for prog in ("ffmpeg", "ffprobe"):
        if not shutil.which(prog):
            erro(f"{prog} não encontrado no PATH")

    cfg = carregar_config(roteiro)
    if teste:
        cfg["tts"]["provedor"] = "mudo"
        cfg["imagens"]["provedor"] = "provisoria"
    pasta = caminho.parent
    w, h = FORMATOS[roteiro.get("formato", cfg["video"]["formato"])]
    fps = cfg["video"]["fps"]
    log(f"'{roteiro['titulo']}' — {len(roteiro['cenas'])} cenas, {w}x{h}, voz={cfg['tts']['provedor']}, "
        f"imagens={cfg['imagens']['provedor']}")

    audios = gerar_vozes(roteiro, cfg, pasta)
    imagens = gerar_imagens(roteiro, cfg, pasta, w, h)

    (pasta / "clipes").mkdir(exist_ok=True)
    tempos, lista, t = [], [], 0.0
    capitulos = []
    rnd = random.Random(roteiro["titulo"])
    for i, (c, img, aud) in enumerate(zip(roteiro["cenas"], imagens, audios), 1):
        mov = c.get("movimento") or rnd.choice(MOVIMENTOS)
        pausa = float(c.get("pausa", cfg["video"]["pausa_entre_cenas"]))
        destino = pasta / "clipes" / f"clipe_{i:03d}_{h8(img.name, aud.name, mov, pausa, w, fps)}.mp4"
        if destino.exists():
            dur_audio = duracao(aud)
            dur = duracao(destino)
        else:
            log(f"montando cena {i}/{len(roteiro['cenas'])} ({mov})")
            dur_audio, dur = clipe_cena(img, aud, destino, w, h, fps, pausa, mov,
                                        cfg["video"]["intensidade_movimento"])
        if c.get("capitulo"):
            capitulos.append((t, c["capitulo"]))
        tempos.append((t, dur_audio))
        lista.append(destino)
        t += dur

    gerar_legendas(roteiro, tempos, pasta, w, h, cfg)

    (pasta / "clipes" / "lista.txt").write_text(
        "".join(f"file '{p.name}'\n" for p in lista), encoding="utf-8")
    rodar(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", "lista.txt",
           "-c", "copy", "../juntado.mp4"], cwd=pasta / "clipes")

    total = duracao(pasta / "juntado.mp4")
    musica = escolher_musica(roteiro, cfg)
    vf = "ass=legendas.ass" if cfg["legendas"]["queimar"] else "null"
    vf += f",fade=t=in:st=0:d=0.4,fade=t=out:st={max(0, total - 1.2):.2f}:d=1.2"
    voz_af = "[0:a]highpass=f=70,acompressor=threshold=-18dB:ratio=2.5:attack=10:release=200[voz]"
    if musica:
        log(f"música: {musica.name}")
        vol = cfg["musica"]["volume"]
        af = (f"{voz_af};[1:a]aresample=48000,aformat=channel_layouts=stereo,volume={vol},"
              f"afade=t=in:d=1.5,afade=t=out:st={max(0, total - 3):.2f}:d=3[mus];"
              f"[voz]asplit=2[v1][v2];"
              f"[mus][v1]sidechaincompress=threshold=0.04:ratio=6:attack=20:release=400[duck];"
              f"[v2][duck]amix=inputs=2:duration=first:normalize=0,"
              f"loudnorm=I=-14:TP=-1.5:LRA=11[a]")
        entradas = ["-i", "juntado.mp4", "-stream_loop", "-1", "-i", str(musica)]
    else:
        af = f"{voz_af};[voz]loudnorm=I=-14:TP=-1.5:LRA=11[a]"
        entradas = ["-i", "juntado.mp4"]

    nome = re.sub(r"[^a-z0-9]+", "-", unicodedata.normalize("NFKD", roteiro["titulo"].lower()).encode("ascii", "ignore").decode()).strip("-")
    final = pasta / "saida" / f"{nome or 'video'}.mp4"
    log("renderizando vídeo final (legendas + música + volume)...")
    rodar(["ffmpeg", "-v", "error", "-y", *entradas, "-filter_complex", f"[0:v]{vf}[v];{af}",
           "-map", "[v]", "-map", "[a]", "-t", f"{total:.3f}",
           "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-profile:v", "high", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart",
           str(final.relative_to(pasta))], cwd=pasta)
    (pasta / "juntado.mp4").unlink()

    thumb_img = imagens[roteiro.get("youtube", {}).get("thumbnail_cena", 1) - 1]
    gerar_thumbnail(roteiro, cfg, pasta, thumb_img)
    gerar_textos(roteiro, pasta, capitulos)

    log(f"pronto! {total / 60:.1f} min")
    log(f"  vídeo:     {final}")
    log(f"  thumbnail: {pasta / 'saida' / 'thumbnail.jpg'}")
    log(f"  legendas:  {pasta / 'saida' / 'legendas.srt'}")
    log(f"  textos:    {pasta / 'saida' / 'youtube.txt'}")


def main():
    ap = argparse.ArgumentParser(description="Produz vídeos de novelinha a partir de roteiro.json")
    sub = ap.add_subparsers(dest="cmd", required=True)
    v = sub.add_parser("validar")
    v.add_argument("roteiro")
    p = sub.add_parser("produzir")
    p.add_argument("roteiro")
    p.add_argument("--teste", action="store_true", help="sem APIs: voz muda + imagens provisórias")
    a = ap.parse_args()
    if a.cmd == "validar":
        r = json.loads(Path(a.roteiro).read_text(encoding="utf-8"))
        probs = validar(r)
        if probs:
            erro("roteiro inválido:\n  - " + "\n  - ".join(probs))
        palavras = sum(len(c["narracao"].split()) for c in r["cenas"])
        log(f"ok — {len(r['cenas'])} cenas, {palavras} palavras (~{palavras / 150:.1f} min de narração)")
    else:
        produzir(a.roteiro, teste=a.teste)


if __name__ == "__main__":
    main()
