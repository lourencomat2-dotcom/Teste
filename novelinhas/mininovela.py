#!/usr/bin/env python3
"""
Mininovela — novela dublada em VÍDEO (estilo canal de mininovelas), 16:9, sem narrador e sem texto na tela.

Para cada plano do roteiro:
  - quadro inicial (Seedream, com a foto de referência de cada personagem em cena -> mesmo rosto/roupa)
  - plano de FALA  -> voz pt-BR (Gemini TTS) + vídeo com boca sincronizada (Kling Avatar)
  - plano de AÇÃO  -> vídeo imagem→vídeo com movimento real (Wan 2.6 Flash) + efeitos sonoros (Mirelo)
Depois: trilha dramática (MiniMax Music) por baixo, subindo nos picos, card final de 8 s, -14 LUFS estéreo.

Uso:
  python mininovela.py produzir episodios/ep003-.../roteiro.json [--ate 11]   (--ate N = só os N primeiros planos)
"""
import argparse
import base64
import json
import math
import random
import sys
import time
from pathlib import Path

import novelinha as nv  # runware(), tts_runware(), rodar(), duracao(), h8(), log(), erro(), paralelo()

AQUI = Path(__file__).resolve().parent
W, H, FPS = 1920, 1080, 30

CFG = {
    "imagem": {"modelo": "bytedance:seedream@5.5", "largura": 1920, "altura": 1080, "espera_maxima_s": 300},
    "acao": {"modelo": "alibaba:wan@2.6-flash", "espera_maxima_s": 900},
    "fala": {"modelo": "klingai:avatar@2.0-standard", "espera_maxima_s": 900},
    "sfx": {"modelo": "mirelo:1@1", "espera_maxima_s": 300, "volume": 0.55},
    "musica": {"modelo": "minimax:music@2.6", "espera_maxima_s": 600, "volume": 0.20, "volume_pico": 0.42},
    "tts": {"runware": {"modelo": "google:gemini@3.1-flash-tts", "idioma": "pt-BR", "usar_tom": True,
                        "espera_maxima_s": 240}},
    "paralelo": 4,
    "folga_fala": 0.25,
}


def baixar(url, destino):
    import requests
    for tentativa in range(4):
        try:
            r = requests.get(url, timeout=180)
            if r.status_code == 200 and r.content:
                destino.write_bytes(r.content)
                return
        except requests.RequestException:
            pass
        time.sleep(2 ** tentativa)
    nv.erro(f"não consegui baixar {url}")


def data_uri(caminho, mime):
    return f"data:{mime};base64," + base64.b64encode(Path(caminho).read_bytes()).decode()


def subir_imagem(caminho, cache):
    chave = nv.h8(Path(caminho).name, Path(caminho).stat().st_size)
    if chave not in cache:
        import uuid
        import requests
        cab = {"Authorization": f"Bearer {nv.os.environ.get('RUNWARE_API_KEY', 'proxy-injected')}"}
        for tentativa in range(5):
            try:
                j = requests.post("https://api.runware.ai/v1", headers=cab, timeout=120, json=[{
                    "taskType": "imageUpload", "taskUUID": str(uuid.uuid4()),
                    "image": data_uri(caminho, "image/png")}]).json()
                if j.get("data"):
                    cache[chave] = j["data"][0]["imageUUID"]
                    break
            except (requests.RequestException, ValueError):
                pass
            time.sleep(2 ** tentativa)
        else:
            nv.erro(f"falha ao enviar {caminho}")
    return cache[chave]


def gerar_imagem(prompt, destino, refs, w, h):
    o = CFG["imagem"]
    tarefa = {"taskType": "imageInference", "model": o["modelo"], "positivePrompt": prompt[:2900],
              "width": w, "height": h, "numberResults": 1, "outputType": "URL", "outputFormat": "PNG"}
    if refs:
        tarefa["referenceImages"] = refs
    item = nv.runware(tarefa, "imageURL", o)
    baixar(item["imageURL"], destino)
    return item.get("cost") or 0


def prompt_plano(rot, plano, extra=""):
    partes = [rot.get("estilo_visual", "")]
    for p in plano.get("personagens", []):
        info = rot["personagens"][p]
        partes.append(f"{info['nome']}: {info['visual']}")
    partes += [plano["imagem"], extra, "no text, no captions, no subtitles, no watermark"]
    return ". ".join(x.strip().rstrip(".") for x in partes if x and x.strip())


# --------------------------------------------------------------------------- produção

def produzir(caminho, ate=None, so_quadros=False):
    caminho = Path(caminho).resolve()
    rot = json.loads(caminho.read_text(encoding="utf-8"))
    pasta = caminho.parent
    for sub in ("refs", "quadros", "audio", "videos", "sfx", "segmentos", "saida"):
        (pasta / sub).mkdir(exist_ok=True)
    planos = rot["planos"][:ate] if ate else rot["planos"]
    cache_up_arq = pasta / "uploads.json"
    cache_up = json.loads(cache_up_arq.read_text()) if cache_up_arq.exists() else {}
    custos = {}

    def soma(etapa, valor):
        custos[etapa] = custos.get(etapa, 0) + (valor or 0)

    # 1) foto de referência de cada personagem que aparece
    usados = sorted({p for pl in planos for p in pl.get("personagens", [])} |
                    {pl["quem"] for pl in planos if pl["tipo"] == "fala"})
    pend = []
    for p in usados:
        info = rot["personagens"][p]
        prompt = (f"{rot.get('estilo_visual', '')}. Character reference portrait, waist-up, facing camera, "
                  f"neutral background, soft studio light. {info['visual']}. no text")
        arq = pasta / "refs" / f"{p}_{nv.h8(prompt)}.png"
        if not arq.exists():
            pend.append((prompt, arq))
    nv.paralelo(lambda it: soma("referências", gerar_imagem(it[0], it[1], None, 1024, 1280)), pend,
                CFG["paralelo"], "referência")
    ref_arq = {p: next((pasta / "refs").glob(f"{p}_*.png")) for p in usados}
    ref_uuid = {p: subir_imagem(a, cache_up) for p, a in ref_arq.items()}

    # 2) quadro inicial de cada plano (com as referências dos personagens em cena)
    quadros, pend = [], []
    for i, pl in enumerate(planos, 1):
        prompt = prompt_plano(rot, pl)
        refs = [ref_uuid[p] for p in pl.get("personagens", [])]
        arq = pasta / "quadros" / f"q{i:03d}_{nv.h8(prompt, *refs)}.png"
        quadros.append(arq)
        if not arq.exists():
            pend.append((prompt, arq, refs))
    nv.paralelo(lambda it: soma("quadros", gerar_imagem(it[0], it[1], it[2], W, H)), pend,
                CFG["paralelo"], "quadro")

    # 3) vozes
    falas, pend = {}, []
    for i, pl in enumerate(planos, 1):
        if pl["tipo"] != "fala":
            continue
        voz = rot["personagens"][pl["quem"]]["voz"]
        arq = pasta / "audio" / f"f{i:03d}_{nv.h8(pl['texto'], voz, pl.get('tom'))}.mp3"
        falas[i] = arq
        if not arq.exists():
            pend.append((pl, voz, arq))

    def gera_voz(it):
        pl, voz, arq = it
        tmp = arq.with_suffix(".tmp.mp3")
        nv.tts_runware(pl["texto"], voz, tmp, CFG, tom=pl.get("tom"))
        tmp.rename(arq)
    nv.paralelo(gera_voz, pend, CFG["paralelo"], "voz")

    cache_up_arq.write_text(json.dumps(cache_up))
    if so_quadros:
        nv.log("parando após referências, quadros e vozes (--so-quadros)")
        nv.log("custo (US$): " + json.dumps(custos))
        return

    # 4) vídeo de cada plano
    videos, pend = {}, []
    for i, pl in enumerate(planos, 1):
        q = quadros[i - 1]
        if pl["tipo"] == "fala":
            arq = pasta / "videos" / f"v{i:03d}_fala_{nv.h8(q.name, falas[i].name)}.mp4"
        else:
            dur = max(2, min(15, math.ceil(pl.get("duracao", 3))))
            arq = pasta / "videos" / f"v{i:03d}_acao_{nv.h8(q.name, pl.get('movimento'), dur)}.mp4"
        videos[i] = arq
        if not arq.exists():
            pend.append((i, pl, q, arq))

    def gera_video(it):
        i, pl, q, arq = it
        img = subir_imagem(q, cache_up)
        if pl["tipo"] == "fala":
            o = CFG["fala"]
            gesto = pl.get("gesto", "")
            tarefa = {"taskType": "videoInference", "model": o["modelo"],
                      "positivePrompt": f"{pl['imagem']}. The person speaks with emotion: {pl.get('tom', '')}. {gesto}"[:1400],
                      "inputs": {"image": img, "audio": data_uri(falas[i], "audio/mpeg")},
                      "outputType": "URL", "outputFormat": "MP4"}
        else:
            o = CFG["acao"]
            dur = max(2, min(15, math.ceil(pl.get("duracao", 3))))
            tarefa = {"taskType": "videoInference", "model": o["modelo"],
                      "positivePrompt": f"{pl.get('movimento', '')}. {rot.get('estilo_visual', '')}. "
                                        f"realistic natural motion, no talking, no text"[:2900],
                      "inputs": {"frameImages": [{"image": img, "frame": "first"}]},
                      "duration": dur, "outputType": "URL", "outputFormat": "MP4"}
        item = nv.runware(tarefa, "videoURL", o)
        soma("vídeo " + pl["tipo"], item.get("cost"))
        baixar(item["videoURL"], arq)
        (arq.with_suffix(".url")).write_text(item["videoURL"])
    nv.paralelo(gera_video, pend, CFG.get("paralelo_video", 2), "vídeo")

    # 5) efeitos sonoros dos planos de ação
    sfx, pend = {}, []
    for i, pl in enumerate(planos, 1):
        if pl["tipo"] == "acao" and pl.get("sfx"):
            arq = pasta / "sfx" / f"s{i:03d}_{nv.h8(videos[i].name, pl['sfx'])}.mp4"
            sfx[i] = arq
            if not arq.exists():
                pend.append((i, pl, arq))

    def gera_sfx(it):
        i, pl, arq = it
        o = CFG["sfx"]
        url = videos[i].with_suffix(".url").read_text().strip()
        item = nv.runware({"taskType": "audioInference", "model": o["modelo"], "positivePrompt": pl["sfx"],
                           "inputs": {"video": url},
                           "outputType": "URL", "outputFormat": "mp4"}, "videoURL", o)
        soma("efeitos", item.get("cost"))
        baixar(item.get("audioURL") or item.get("videoURL"), arq)
    nv.paralelo(gera_sfx, pend, CFG["paralelo"], "efeito")

    # 6) trilha
    musica = pasta / "audio" / f"trilha_{nv.h8(rot.get('musica', ''))}.mp3"
    if not musica.exists() and rot.get("musica"):
        nv.log("gerando trilha...")
        o = CFG["musica"]
        item = nv.runware({"taskType": "audioInference", "model": o["modelo"], "positivePrompt": rot["musica"],
                           "settings": {"instrumental": True},
                           "outputType": "URL", "outputFormat": "MP3"}, "audioURL", o)
        soma("trilha", item.get("cost"))
        baixar(item["audioURL"], musica)

    (pasta / "custos.json").write_text(json.dumps(custos, indent=1, ensure_ascii=False))
    montar(rot, planos, pasta, quadros, videos, falas, sfx, musica if musica.exists() else None)
    nv.log("custo desta rodada (US$): " + ", ".join(f"{k} {v:.2f}" for k, v in custos.items())
           + f" | total {sum(custos.values()):.2f}")


# --------------------------------------------------------------------------- montagem

def card_final(rot, pasta, quadro_base, dur):
    """Card final: plano aberto desfocado + ASSISTA TAMBÉM / INSCREVA-SE / ATIVA O SININHO."""
    from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
    img = Image.open(quadro_base).convert("RGB").resize((W, H))
    img = ImageEnhance.Brightness(img.filter(ImageFilter.GaussianBlur(18))).enhance(0.45)
    d = ImageDraw.Draw(img)
    f_titulo, f_btn = nv.fonte(78), nv.fonte(58)

    def centro(txt, y, f, cor=(255, 255, 255)):
        x = (W - d.textlength(txt, font=f)) / 2
        d.text((x, y), txt, font=f, fill=cor, stroke_width=4, stroke_fill=(0, 0, 0))

    centro("ASSISTA TAMBÉM", 110, f_titulo)
    for k, x in enumerate((260, 1040)):  # espaços para as telas finais do YouTube
        d.rounded_rectangle((x, 250, x + 620, 250 + 349), radius=18, outline=(255, 255, 255), width=6)
    bw, bh, by = 560, 120, 700
    d.rounded_rectangle(((W - bw) / 2, by, (W + bw) / 2, by + bh), radius=22, fill=(204, 0, 0))
    centro("INSCREVA-SE", by + 28, f_btn)
    centro("ATIVA O SININHO", by + 175, f_btn, (255, 214, 0))
    png = pasta / "segmentos" / "card.png"
    img.save(png)
    out = pasta / "segmentos" / "card.mp4"
    nv.rodar(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-framerate", str(FPS), "-i", str(png), "-t", f"{dur}",
              "-vf", f"fade=t=in:st=0:d=0.8,format=yuv420p", "-r", str(FPS),
              "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-an", str(out)])
    return out


def montar(rot, planos, pasta, quadros, videos, falas, sfx, musica):
    nv.log("montando...")
    segs, t, inicios, picos = [], 0.0, [], []
    for i, pl in enumerate(planos, 1):
        if pl["tipo"] == "fala":
            dur = nv.duracao(falas[i]) + CFG["folga_fala"]
        else:
            dur = float(pl.get("duracao", 3))
        seg = pasta / "segmentos" / f"seg{i:03d}.mp4"
        ult = (i == len(planos))
        vf = (f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,fps={FPS},"
              f"tpad=stop_mode=clone:stop_duration=5,trim=duration={dur:.3f},setpts=PTS-STARTPTS")
        if ult:
            vf += f",fade=t=out:st={max(0, dur - 0.8):.2f}:d=0.8"
        nv.rodar(["ffmpeg", "-v", "error", "-y", "-i", str(videos[i]), "-vf", vf + ",format=yuv420p",
                  "-an", "-r", str(FPS), "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", str(seg)])
        segs.append(seg)
        inicios.append((t, dur))
        if pl.get("pico"):
            picos.append((t, t + dur))
        t += dur
    historia = t
    card_dur = float(rot.get("card_final", {}).get("duracao", 8)) if rot.get("card_final") else 0
    if card_dur:
        segs.append(card_final(rot, pasta, quadros[-1], card_dur))
    total = historia + card_dur

    lista = pasta / "segmentos" / "lista.txt"
    lista.write_text("".join(f"file '{s.name}'\n" for s in segs))
    video = pasta / "segmentos" / "video.mp4"
    nv.rodar(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", "lista.txt", "-c", "copy",
              video.name], cwd=pasta / "segmentos")

    # --- áudio: diálogo + efeitos + trilha (abaixa sob as falas, sobe nos picos e no card)
    entradas, filtros, dial, efx = [], [], [], []
    n = 0
    for i, pl in enumerate(planos, 1):
        ini, dur = inicios[i - 1]
        ms = int(ini * 1000)
        if i in falas:
            entradas += ["-i", str(falas[i])]
            filtros.append(f"[{n}:a]aresample=48000,aformat=channel_layouts=stereo,adelay={ms}|{ms}[d{n}]")
            dial.append(f"[d{n}]")
            n += 1
        if i in sfx:
            entradas += ["-i", str(sfx[i])]
            filtros.append(f"[{n}:a]aresample=48000,aformat=channel_layouts=stereo,atrim=duration={dur:.3f},"
                           f"afade=t=out:st={max(0, dur - 0.3):.2f}:d=0.3,volume={CFG['sfx']['volume']},"
                           f"adelay={ms}|{ms}[e{n}]")
            efx.append(f"[e{n}]")
            n += 1
    filtros.append(f"{''.join(dial)}amix=inputs={len(dial)}:normalize=0:duration=longest,"
                   f"apad=whole_dur={total:.3f}[dial]")
    filtros.append("[dial]asplit=2[dial1][dial2]")
    mix = ["[dial1]"]
    if efx:
        filtros.append(f"{''.join(efx)}amix=inputs={len(efx)}:normalize=0:duration=longest,"
                       f"apad=whole_dur={total:.3f}[efx]")
        mix.append("[efx]")
    if musica:
        o = CFG["musica"]
        sobe = "+".join(f"between(t,{a:.2f},{b + 1.5:.2f})" for a, b in picos + [(historia, total)]) or "0"
        expr = f"{o['volume']}+({o['volume_pico'] - o['volume']})*min(1,{sobe})"
        entradas += ["-stream_loop", "-1", "-i", str(musica)]
        filtros.append(f"[{n}:a]aresample=48000,aformat=channel_layouts=stereo,atrim=duration={total:.3f},"
                       f"volume='{expr}':eval=frame,afade=t=in:d=1.0,"
                       f"afade=t=out:st={max(0, total - 2.5):.2f}:d=2.5[mus]")
        filtros.append("[mus][dial2]sidechaincompress=threshold=0.03:ratio=5:attack=30:release=500[duck]")
        mix.append("[duck]")
        n += 1
    filtros.append(f"{''.join(mix)}amix=inputs={len(mix)}:normalize=0:duration=longest,"
                   f"atrim=duration={total:.3f}[pre]")
    pre = pasta / "segmentos" / "audio_pre.wav"
    nv.rodar(["ffmpeg", "-v", "error", "-y", *entradas, "-filter_complex", ";".join(filtros),
              "-map", "[pre]", "-c:a", "pcm_s16le", "-ar", "48000", str(pre)])

    # loudnorm em duas passadas -> -14 LUFS, true peak -1.5
    medida = nv.subprocess.run(["ffmpeg", "-hide_banner", "-i", str(pre), "-af",
                                "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                               capture_output=True, text=True).stderr
    js = json.loads(medida[medida.rindex("{"):medida.rindex("}") + 1])
    ln = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={js['input_i']}:measured_TP={js['input_tp']}:"
          f"measured_LRA={js['input_lra']}:measured_thresh={js['input_thresh']}:offset={js['target_offset']}:linear=true")

    nome = pasta.name
    final = pasta / "saida" / f"{nome}.mp4"
    nv.rodar(["ffmpeg", "-v", "error", "-y", "-i", str(video), "-i", str(pre), "-map", "0:v", "-map", "1:a",
              "-af", ln + ",aresample=48000", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ac", "2",
              "-movflags", "+faststart", "-shortest", str(final)])
    nv.log(f"pronto: {final} ({total:.1f} s)")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("produzir")
    p.add_argument("roteiro")
    p.add_argument("--ate", type=int, default=None, help="só os N primeiros planos (teste)")
    p.add_argument("--so-quadros", action="store_true", help="para antes de gerar os vídeos (conferir imagens)")
    a = ap.parse_args()
    produzir(a.roteiro, a.ate, a.so_quadros)


if __name__ == "__main__":
    main()
