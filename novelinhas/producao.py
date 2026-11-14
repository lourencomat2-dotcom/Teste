#!/usr/bin/env python3
"""
Produção com travas de continuidade (segue o briefing.md do episódio).

  python producao.py <pasta-do-episodio> --limite 3.0 [--so-mestres]

Ordem:
  1. referências fixas dos personagens (seed fixa)
  2. imagens-mestras dos planos (refs dos personagens + mestre do cenário; seed fixa por plano)
  3. vozes pt-BR (sem instrução de tom, silêncio cortado, 8% mais rápido)
  4. vídeos em ordem de dependência; "primeiro_quadro_de": N usa o ÚLTIMO quadro real do vídeo N
  5. checagem automática de rosto (LBP x referência) e cor (ΔE Lab entre planos vizinhos),
     com no máximo 1 nova tentativa por plano e teto de US$ 0,60 em novas tentativas
  6. correção de cor única (igualada ao plano mestre) + montagem + card final + -14 LUFS
  7. relatório de continuidade (pares de quadros de cada corte)
"""
import argparse
import json
import math
import subprocess
from pathlib import Path

import cv2
import numpy as np

import mininovela as mn
import novelinha as nv

W, H, FPS = mn.W, mn.H, mn.FPS
LIMIAR_ROSTO_FATOR = 1.35
LIMIAR_COR_DE = 12.0
MAX_TENTATIVAS_EXTRAS = 1
TETO_RETENTATIVAS = 0.60


# --------------------------------------------------------------------------- utilidades de imagem

def quadro(video, onde, destino):
    """onde: 'primeiro' | 'meio' | 'ultimo' | fração 0..1 -> PNG."""
    if isinstance(onde, float):
        args = ["-ss", f"{nv.duracao(video) * onde:.2f}", "-i", str(video)]
    elif onde == "ultimo":
        args = ["-sseof", "-0.1", "-i", str(video), "-update", "1"]
    elif onde == "meio":
        args = ["-ss", f"{nv.duracao(video) / 2:.2f}", "-i", str(video)]
    else:
        args = ["-i", str(video)]
    nv.rodar(["ffmpeg", "-v", "error", "-y", *args, "-frames:v", "1", "-vf", f"scale={W}:{H}", str(destino)])
    return destino


_frontal = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
_perfil = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_profileface.xml")


def _caixas(cinza):
    """Rostos de frente e de perfil (nos dois sentidos), sem duplicatas."""
    larg = cinza.shape[1]
    cx = [tuple(r) for r in _frontal.detectMultiScale(cinza, 1.1, 5, minSize=(60, 60))]
    cx += [tuple(r) for r in _perfil.detectMultiScale(cinza, 1.1, 4, minSize=(60, 60))]
    cx += [(larg - x - w, y, w, h) for (x, y, w, h) in _perfil.detectMultiScale(cv2.flip(cinza, 1), 1.1, 4, minSize=(60, 60))]
    cx.sort(key=lambda r: -r[2] * r[3])
    unicas = []
    for (x, y, w, h) in cx:
        if all(abs((x + w / 2) - (u[0] + u[2] / 2)) > max(w, u[2]) * 0.5 for u in unicas):
            unicas.append((x, y, w, h))
    return unicas


def rostos(img_path):
    cinza = cv2.imread(str(img_path), cv2.IMREAD_GRAYSCALE)
    return [(x, cv2.resize(cinza[y:y + h, x:x + w], (160, 160)))
            for (x, y, w, h) in sorted(_caixas(cinza), key=lambda r: r[0])]


def maior_rosto(img_path):
    cinza = cv2.imread(str(img_path), cv2.IMREAD_GRAYSCALE)
    cx = _caixas(cinza)
    if not cx:
        return None
    x, y, w, h = cx[0]
    return cv2.resize(cinza[y:y + h, x:x + w], (160, 160))


def media_lab(img_path):
    lab = cv2.cvtColor(cv2.imread(str(img_path)), cv2.COLOR_BGR2LAB).reshape(-1, 3).astype(float)
    m = lab.mean(0)
    return np.array([m[0] * 100 / 255, m[1] - 128, m[2] - 128])


def delta_e(a, b):
    return float(np.linalg.norm(media_lab(a) - media_lab(b)))


def treinar_individuais(refs):
    rec = {}
    for n, arq in refs.items():
        r = maior_rosto(arq)
        if r is None:
            nv.erro(f"não achei rosto na referência de {n}")
        m = cv2.face.LBPHFaceRecognizer_create()
        m.train([r, cv2.flip(r, 1)], np.array([0, 0]))
        rec[n] = m
    return rec


def dist_rosto(rec, nome, rosto):
    return rec[nome].predict(rosto)[1]


# --------------------------------------------------------------------------- produção

def produzir(pasta, limite, so_mestres=False, aceitos=None):
    pasta = Path(pasta).resolve()
    rot = json.loads((pasta / "roteiro.json").read_text(encoding="utf-8"))
    for sub in ("refs", "mestres", "audio", "videos", "quadros_extra", "sfx", "segmentos", "checagem"):
        (pasta / sub).mkdir(exist_ok=True)
    planos = rot["planos"]
    pers = rot["personagens"]
    cache_arq = pasta / "uploads.json"
    cache = json.loads(cache_arq.read_text()) if cache_arq.exists() else {}
    orc = mn.Orcamento(limite)
    est = mn.CFG["estimativa"]
    custos = {"retentativas": 0.0}

    def pago(etapa, estimado, funcao):
        orc.reservar(estimado, etapa)
        real = None
        try:
            real = funcao()
        finally:
            orc.pagar(estimado, real)
        custos[etapa] = custos.get(etapa, 0) + (real if real is not None else estimado)
        return real if real is not None else estimado

    def prompt(pl, extra=""):
        partes = [rot["estilo_visual"], rot["cenario"]]
        for p in pl.get("personagens", []):
            partes.append(f"{pers[p]['nome']}: {pers[p]['visual']}. MUST NOT CHANGE: {pers[p]['fixo']}")
        partes += [pl["imagem"], extra, "no text, no captions, no watermark"]
        return ". ".join(x.strip().rstrip(".") for x in partes if x and x.strip())

    # 1) referências (seed fixa)
    refs = {}
    pend = []
    for n, info in pers.items():
        pr = (f"{rot['estilo_visual']}. Character reference portrait, waist-up, facing the camera, plain warm "
              f"neutral background, soft light. {info['visual']}. MUST NOT CHANGE: {info['fixo']}. no text")
        arq = pasta / "refs" / f"{n}_{nv.h8(pr, info['seed'])}.png"
        refs[n] = arq
        if not arq.exists():
            pend.append((pr, arq, info["seed"]))
    nv.paralelo(lambda it: pago("referências", est["imagem"],
                                lambda: mn.gerar_imagem(it[0], it[1], None, 1024, 1280, it[2])),
                pend, 3, "referência")
    ref_uuid = {n: mn.subir_imagem(a, cache) for n, a in refs.items()}

    # 2) imagens-mestras: primeiro as sem ref_cenario (o mestre), depois as que usam o mestre como cenário
    mestres = {}

    def gerar_mestre(i):
        pl = planos[i - 1]
        refs_pl = [ref_uuid[p] for p in pl.get("personagens", [])]
        if pl.get("ref_cenario"):
            refs_pl.append(mn.subir_imagem(mestres[pl["ref_cenario"]], cache))
        pr = prompt(pl)
        arq = pasta / "mestres" / f"m{i:02d}_{nv.h8(pr, pl.get('seed'), *refs_pl)}.png"
        mestres[i] = arq
        return (pr, arq, refs_pl, pl.get("seed")) if not arq.exists() else None

    for grupo in ([i for i, pl in enumerate(planos, 1) if not pl.get("primeiro_quadro_de") and not pl.get("ref_cenario")],
                  [i for i, pl in enumerate(planos, 1) if not pl.get("primeiro_quadro_de") and pl.get("ref_cenario")]):
        pend = [x for x in (gerar_mestre(i) for i in grupo) if x]
        nv.paralelo(lambda it: pago("mestres", est["imagem"],
                                    lambda: mn.gerar_imagem(it[0], it[1], it[2], W, H, it[3])),
                    pend, 4, "imagem-mestra")
    # espelhamento (corrige direção de olhar pelo eixo, sem custo)
    for i, pl in enumerate(planos, 1):
        if pl.get("espelhar") and i in mestres:
            esp = mestres[i].with_name(mestres[i].stem + "_esp.png")
            if not esp.exists():
                nv.rodar(["ffmpeg", "-v", "error", "-y", "-i", str(mestres[i]), "-vf", "hflip", str(esp)])
            mestres[i] = esp
    (cache_arq).write_text(json.dumps(cache))

    # 3) vozes (MiniMax com emoção por trecho, se configurado no roteiro)
    tts = rot.get("tts", {})
    falas = {}
    pend = []
    for i, pl in enumerate(planos, 1):
        if pl["tipo"] == "fala":
            voz = pers[pl["quem"]].get("voz_tts") or pers[pl["quem"]]["voz"]
            partes = pl.get("partes") or [{"texto": pl["texto"], "emocao": pl.get("emocao")}]
            arq = pasta / "audio" / f"f{i:02d}_{nv.h8(json.dumps(partes, ensure_ascii=False), voz, json.dumps(tts, sort_keys=True))}.mp3"
            falas[i] = arq
            if not arq.exists():
                pend.append((partes, voz, arq))

    def tts_trecho(texto, voz, emocao, destino):
        if tts.get("modelo", "").startswith("minimax:"):
            speech = {"text": texto, "voice": voz}
            if emocao:
                speech["emotion"] = emocao
            if tts.get("velocidade"):
                speech["speed"] = tts["velocidade"]
            item = nv.runware({"taskType": "audioInference", "model": tts["modelo"], "speech": speech,
                               "settings": {"languageBoost": tts.get("idioma", "pt")},
                               "outputType": "base64Data", "outputFormat": "MP3"}, "audioBase64Data",
                              {"espera_maxima_s": 240})
            destino.write_bytes(__import__("base64").b64decode(item["audioBase64Data"]))
            return item.get("cost")
        nv.tts_runware(texto, voz, destino, mn.CFG, tom=None)
        return None

    def gera_voz(it):
        partes, voz, arq = it
        pedacos = []
        for k, pt in enumerate(partes):
            bruto = arq.with_name(f"{arq.stem}_p{k}.bruto.mp3")
            pago("vozes", est["voz"], lambda: tts_trecho(pt["texto"], voz, pt.get("emocao"), bruto))
            proc = arq.with_name(f"{arq.stem}_p{k}.mp3")
            mn.processar_voz(bruto, proc, tts.get("acelerar", 1.0))
            if tts.get("pausa_max"):  # encurta pausas internas longas (ritmo de novela)
                tmp = proc.with_name(proc.stem + "_c.mp3")
                nv.rodar(["ffmpeg", "-v", "error", "-y", "-i", str(proc), "-af",
                          f"silenceremove=stop_periods=-1:stop_duration={tts['pausa_max']}:stop_threshold=-40dB:"
                          f"stop_silence={tts['pausa_max']}", "-c:a", "libmp3lame", "-q:a", "2", str(tmp)])
                tmp.replace(proc)
            pedacos.append(proc)
        if len(pedacos) == 1:
            pedacos[0].rename(arq)
        else:  # junta os trechos com uma pausa curta
            ent, filt = [], []
            for k, p in enumerate(pedacos):
                ent += ["-i", str(p)]
                filt.append(f"[{k}:a]aresample=48000,apad=pad_dur=0.18[a{k}]")
            nv.rodar(["ffmpeg", "-v", "error", "-y", *ent, "-filter_complex",
                      ";".join(filt) + ";" + "".join(f"[a{k}]" for k in range(len(pedacos)))
                      + f"concat=n={len(pedacos)}:v=0:a=1[o]", "-map", "[o]", "-c:a", "libmp3lame", "-q:a", "2", str(arq)])
    nv.paralelo(gera_voz, pend, 3, "voz")

    # limiares de rosto: distância entre a referência e as próprias imagens-mestras (close de 1 pessoa)
    rec = treinar_individuais(refs)
    base = {n: [] for n in pers}
    for i, pl in enumerate(planos, 1):
        if i in mestres and len(pl.get("personagens", [])) == 1:
            r = maior_rosto(mestres[i])
            if r is not None:
                base[pl["personagens"][0]].append(dist_rosto(rec, pl["personagens"][0], r))
    limiar = {n: LIMIAR_ROSTO_FATOR * max(v) for n, v in base.items() if v}
    rel = {"limiares_rosto": limiar, "planos": {}}
    if so_mestres:
        nv.log(f"parando após imagens-mestras e vozes. custos: {custos}. limiares: {limiar}")
        (pasta / "checagem" / "relatorio.json").write_text(json.dumps(rel, indent=1, ensure_ascii=False))
        return

    # 4) vídeos em ordem de dependência, com checagem e nova tentativa
    videos = {}
    urls = {}
    medidas = {}

    def checar(i, video):
        """5 quadros. Reprova se algum rosto detectado passa do limiar, ou se o rosto
        (close de 1 pessoa) aparece em menos de 3 dos 5 quadros."""
        pl = planos[i - 1]
        res = {"rosto": [], "ok": True}
        achados = 0
        posicoes = [0.02, 0.25, 0.5, 0.75, 0.97]
        for k, f in enumerate(posicoes):
            img = quadro(video, f, pasta / "checagem" / f"p{i:02d}_q{k}.png")
            if len(pl.get("personagens", [])) == 1:
                n = pl["personagens"][0]
                r = maior_rosto(img)
                if r is None:
                    res["rosto"].append((f, n, None, "sem rosto (cabeça virada?)"))
                    continue
                achados += 1
                d = dist_rosto(rec, n, r)
                ok = n not in limiar or d <= limiar[n]
                res["rosto"].append((f, n, round(d, 1), "ok" if ok else "REPROVADO"))
                res["ok"] &= ok
            else:
                ach = rostos(img)
                ordem = pl.get("ordem_rostos", [])
                if len(ach) != len(ordem) or not ordem:
                    res["rosto"].append((f, "plano aberto", len(ach), f"inconclusivo ({len(ach)} rostos)"))
                    continue
                for (x, r), n in zip(ach, ordem):
                    d = dist_rosto(rec, n, r)
                    ok = n not in limiar or d <= limiar[n] * 1.15
                    res["rosto"].append((f, n, round(d, 1), "ok" if ok else "REPROVADO"))
                    res["ok"] &= ok
        if len(pl.get("personagens", [])) == 1 and achados < 3:
            res["ok"] = False
            res["motivo"] = f"rosto em só {achados} de 5 quadros"
        return res

    def gerar_video(i, tentativa):
        pl = planos[i - 1]
        if pl.get("primeiro_quadro_de"):
            ini = quadro(videos[pl["primeiro_quadro_de"]], "ultimo",
                         pasta / "quadros_extra" / f"ini{i:02d}_de{pl['primeiro_quadro_de']:02d}.png")
        else:
            ini = mestres[i]
        img = mn.subir_imagem(ini, cache)
        fixos = " ".join(f"{pers[p]['nome']} MUST NOT CHANGE: {pers[p]['fixo']}." for p in pl.get("personagens", []))
        modelos = rot.get("modelos", {})
        if pl["tipo"] == "fala":
            o = {**mn.CFG["fala"], "modelo": modelos.get("fala", mn.CFG["fala"]["modelo"])}
            tarefa = {"taskType": "videoInference", "model": o["modelo"],
                      "positivePrompt": (f"{pl['imagem']}. The person speaks naturally, lips perfectly in sync. "
                                         f"Keep the same framing, eye-line, clothes, hair and background. {fixos}")[:1400],
                      "inputs": {"image": img, "audio": mn.data_uri(falas[i], "audio/mpeg")},
                      "outputType": "URL", "outputFormat": "MP4"}
            estimado = (nv.duracao(falas[i]) + 1.5) * rot.get("preco_s", {}).get("fala", est["fala_s"])
        else:
            o = {**mn.CFG["acao"], "modelo": modelos.get("acao", mn.CFG["acao"]["modelo"])}
            dur = max(2, min(15, math.ceil(pl["duracao"])))
            if modelos.get("duracoes_acao"):  # modelos com durações fixas (ex.: Kling 5/10 s)
                dur = min(d for d in modelos["duracoes_acao"] if d >= pl["duracao"])
            tarefa = {"taskType": "videoInference", "model": o["modelo"],
                      "positivePrompt": (f"{pl['movimento']}. {rot['cenario']}. {fixos} "
                                         f"Realistic natural motion, nothing appears or disappears, no other people, "
                                         f"no talking, no text")[:2900],
                      "inputs": {"frameImages": [{"image": img, "frame": "first"}]},
                      "duration": dur, "outputType": "URL", "outputFormat": "MP4",
                      **({"providerSettings": modelos["provider_acao"]} if modelos.get("provider_acao") else {})}
            if "kling" in o["modelo"]:
                tarefa["inputs"] = {"frameImages": [{"image": img, "frame": "first"}]}
            estimado = dur * rot.get("preco_s", {}).get("acao", est["acao_s"])
        if tentativa > 0:
            if custos["retentativas"] + estimado > TETO_RETENTATIVAS:
                return None, "teto de novas tentativas atingido"
            if pl["tipo"] == "acao" and "kling" not in o["modelo"]:
                tarefa["seed"] = 777 + i * 10 + tentativa
        arq = pasta / "videos" / f"v{i:02d}_t{tentativa}.mp4"
        if not arq.exists():
            res = {}

            def chama():
                res["item"] = nv.runware(tarefa, "videoURL", o)
                return res["item"].get("cost")
            real = pago("vídeo " + pl["tipo"], estimado, chama)
            seg = nv.duracao(falas[i]) if pl["tipo"] == "fala" else dur
            medidas.setdefault(pl["tipo"], []).append((real or 0) / max(seg, 0.1))
            nv.log(f"plano {i}: custo real US$ {real:.3f} (~US$ {(real or 0) / max(seg, 0.1):.3f}/s)")
            if tentativa > 0:
                custos["retentativas"] += real
            mn.baixar(res["item"]["videoURL"], arq)
            arq.with_suffix(".url").write_text(res["item"]["videoURL"])
        return arq, None

    def produzir_plano(i):
        for t in range(MAX_TENTATIVAS_EXTRAS + 1):
            arq, motivo = gerar_video(i, t)
            if arq is None:
                rel["planos"][i] = {"tentativas": t, "ok": False, "motivo": motivo}
                return
            ck = checar(i, arq)
            rel["planos"][i] = {"tentativas": t + 1, **ck}
            videos[i] = arq
            urls[i] = arq.with_suffix(".url").read_text()
            if ck["ok"]:
                return
            nv.log(f"plano {i} reprovado na checagem (tentativa {t + 1}): {ck['rosto']}")

    feitos = set()
    restantes = list(range(1, len(planos) + 1))
    # plano-piloto: a primeira fala sozinha, para medir o custo real por segundo e projetar o total
    piloto = next((i for i in restantes if planos[i - 1]["tipo"] == "fala" and not planos[i - 1].get("primeiro_quadro_de")), None)
    if piloto:
        produzir_plano(piloto)
        feitos.add(piloto)
        restantes.remove(piloto)
        taxa = (medidas.get("fala") or [rot.get("preco_s", {}).get("fala", est["fala_s"])])[0]
        seg_falas = sum(nv.duracao(falas[i]) + 0.5 for i in restantes if planos[i - 1]["tipo"] == "fala")
        seg_acao = sum(5 if rot.get("modelos", {}).get("duracoes_acao") else planos[i - 1]["duracao"]
                       for i in restantes if planos[i - 1]["tipo"] == "acao")
        proj = orc.gasto + seg_falas * taxa + seg_acao * rot.get("preco_s", {}).get("acao", est["acao_s"]) + 0.15
        nv.log(f"projeção após o piloto: gasto {orc.gasto:.2f} + resto ≈ total US$ {proj:.2f} (limite {limite:.2f})")
        if limite is not None and proj > limite:
            nv.log("PARADO: a projeção passa do limite. Nada mais será gerado.")
            (pasta / "checagem" / "relatorio.json").write_text(json.dumps(rel, indent=1, ensure_ascii=False, default=str))
            return
    while restantes:
        nivel = [i for i in restantes if not planos[i - 1].get("primeiro_quadro_de")
                 or planos[i - 1]["primeiro_quadro_de"] in feitos]
        nv.paralelo(produzir_plano, nivel, mn.CFG.get("paralelo_video", 2), "plano")
        feitos |= set(nivel)
        restantes = [i for i in restantes if i not in feitos]
    falhos = [i for i, r in rel["planos"].items() if not r.get("ok") and i not in (aceitos or [])]
    aceitar = False
    (pasta / "checagem" / "relatorio.json").write_text(json.dumps(rel, indent=1, ensure_ascii=False, default=str))
    if falhos and not aceitar:
        nv.log(f"PARADO: planos reprovados na checagem mesmo após nova tentativa: {falhos} "
               f"(ver checagem/relatorio.json). Montagem não executada, conforme o briefing. "
               f"Para montar mesmo assim, só com aprovação: --aceitar {','.join(map(str, falhos))}")
        return

    # 5) efeitos sonoros (pelo link do vídeo, sincronizados)
    sfx = {}
    pend = []
    for i, pl in enumerate(planos, 1):
        if pl["tipo"] == "acao" and pl.get("sfx"):
            arq = pasta / "sfx" / f"s{i:02d}_{nv.h8(videos[i].name, pl['sfx'])}.mp4"
            sfx[i] = arq
            if not arq.exists():
                pend.append((i, pl, arq))

    def gera_sfx(it):
        i, pl, arq = it
        res = {}

        def chama():
            res["item"] = nv.runware({"taskType": "audioInference", "model": mn.CFG["sfx"]["modelo"],
                                      "positivePrompt": pl["sfx"], "inputs": {"video": urls[i]},
                                      "outputType": "URL", "outputFormat": "mp4"}, "videoURL", mn.CFG["sfx"])
            return res["item"].get("cost")
        pago("efeitos", est["sfx"], chama)
        mn.baixar(res["item"]["videoURL"], arq)
    nv.paralelo(gera_sfx, pend, 3, "efeito")

    musica = next(iter(sorted(pasta.glob("trilha_*.mp3"))), None)
    montar(rot, planos, pasta, videos, falas, sfx, musica, mestres[1], rel)
    (pasta / "custos.json").write_text(json.dumps(custos, indent=1, ensure_ascii=False))
    nv.log("custos (US$): " + json.dumps({k: round(v, 3) for k, v in custos.items()}, ensure_ascii=False)
           + f" | total {orc.gasto:.2f}")


# --------------------------------------------------------------------------- montagem + cor + relatório

def ganho_cor(img, alvo):
    """Ganhos RGB para levar a média da imagem 50% em direção à média do alvo (limitado a ±10%)."""
    a = cv2.imread(str(img)).reshape(-1, 3).mean(0)
    b = cv2.imread(str(alvo)).reshape(-1, 3).mean(0)
    g = np.clip(1 + 0.5 * (b / np.maximum(a, 1) - 1), 0.9, 1.1)
    return g[2], g[1], g[0]  # r, g, b


GRADE = "eq=contrast=1.04:saturation=1.06:gamma=0.98,colorbalance=rs=0.02:gs=0.0:bs=-0.03:rh=0.03:bh=-0.02"


def montar(rot, planos, pasta, videos, falas, sfx, musica, mestre_ref, rel):
    nv.log("montando (correção de cor única)...")
    segs, inicios, picos, t = [], [], [], 0.0
    for i, pl in enumerate(planos, 1):
        dur = nv.duracao(falas[i]) + mn.CFG["folga_fala"] if pl["tipo"] == "fala" else float(pl["duracao"])
        meio = quadro(videos[i], "meio", pasta / "checagem" / f"cor_{i:02d}.png")
        r, g, b = ganho_cor(meio, mestre_ref)
        seg = pasta / "segmentos" / f"seg{i:02d}.mp4"
        vf = (f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,fps={FPS},"
              f"colorchannelmixer=rr={r:.3f}:gg={g:.3f}:bb={b:.3f},{GRADE},"
              f"tpad=stop_mode=clone:stop_duration=5,trim=duration={dur:.3f},setpts=PTS-STARTPTS")
        if i == len(planos):
            vf += f",fade=t=out:st={max(0, dur - 0.8):.2f}:d=0.8"
        nv.rodar(["ffmpeg", "-v", "error", "-y", "-i", str(videos[i]), "-vf", vf + ",format=yuv420p", "-an",
                  "-r", str(FPS), "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", str(seg)])
        segs.append(seg)
        inicios.append((t, dur))
        if pl.get("pico"):
            picos.append((t, t + dur))
        t += dur
    historia = t

    # checagem de cor entre planos vizinhos (depois da correção) + pares para o relatório
    pares, cores = [], []
    for k in range(len(segs) - 1):
        a = quadro(segs[k], "ultimo", pasta / "checagem" / f"corte{k + 1}_a.png")
        b = quadro(segs[k + 1], "primeiro", pasta / "checagem" / f"corte{k + 1}_b.png")
        de = delta_e(a, b)
        cores.append({"corte": k + 1, "tempo_s": round(inicios[k + 1][0], 2), "deltaE": round(de, 1),
                      "ok": de <= LIMIAR_COR_DE})
        pares.append((a, b, inicios[k + 1][0], de))
    rel["cor_entre_cortes"] = cores

    card_dur = float(rot.get("card_final", {}).get("duracao", 8))
    segs.append(mn.card_final(rot, pasta, mestre_ref, card_dur))
    total = historia + card_dur
    (pasta / "segmentos" / "lista.txt").write_text("".join(f"file '{s.name}'\n" for s in segs))
    nv.rodar(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", "lista.txt", "-c", "copy",
              "video.mp4"], cwd=pasta / "segmentos")

    # áudio (mesma lógica do mininovela: diálogo + efeitos + trilha com ducking e picos)
    planos_falas = {i: falas[i] for i in falas}
    mn_montar_audio(pasta, planos, inicios, planos_falas, sfx, musica, picos, historia, total)

    # relatório de continuidade
    from PIL import Image, ImageDraw
    w2, h2 = 640, 360
    img = Image.new("RGB", (w2 * 2, h2 * len(pares)), (0, 0, 0))
    d = ImageDraw.Draw(img)
    for k, (a, b, tc, de) in enumerate(pares):
        img.paste(Image.open(a).convert("RGB").resize((w2, h2)), (0, k * h2))
        img.paste(Image.open(b).convert("RGB").resize((w2, h2)), (w2, k * h2))
        d.rectangle((0, k * h2, 470, k * h2 + 26), fill=(0, 0, 0))
        d.text((6, k * h2 + 6), f"corte {k + 1} @ {tc:.1f}s  |  antes  ->  depois  |  dE cor {de:.1f}",
               fill=(255, 255, 0))
    img.save(pasta / "continuidade.jpg", quality=88)
    (pasta / "checagem" / "relatorio.json").write_text(json.dumps(rel, indent=1, ensure_ascii=False, default=str))
    nv.log(f"pronto: {pasta / 'saida' / 'video.mp4'} ({total:.1f} s)")


def mn_montar_audio(pasta, planos, inicios, falas, sfx, musica, picos, historia, total):
    entradas, filtros, dial, efx, n = [], [], [], [], 0
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
                           f"afade=t=out:st={max(0, dur - 0.3):.2f}:d=0.3,volume={mn.CFG['sfx']['volume']},"
                           f"adelay={ms}|{ms}[e{n}]")
            efx.append(f"[e{n}]")
            n += 1
    filtros.append(f"{''.join(dial)}amix=inputs={len(dial)}:normalize=0:duration=longest,"
                   f"apad=whole_dur={total:.3f},asplit=2[dial1][dial2]")
    mix = ["[dial1]"]
    if efx:
        filtros.append(f"{''.join(efx)}amix=inputs={len(efx)}:normalize=0:duration=longest,"
                       f"apad=whole_dur={total:.3f}[efx]")
        mix.append("[efx]")
    if musica:
        o = mn.CFG["musica"]
        sobe = "+".join(f"between(t,{a:.2f},{b + 1.5:.2f})" for a, b in picos + [(historia, total)]) or "0"
        entradas += ["-stream_loop", "-1", "-i", str(musica)]
        filtros.append(f"[{n}:a]aresample=48000,aformat=channel_layouts=stereo,atrim=duration={total:.3f},"
                       f"volume='{o['volume']}+({o['volume_pico'] - o['volume']})*min(1,{sobe})':eval=frame,"
                       f"afade=t=in:d=1.0,afade=t=out:st={max(0, total - 2.5):.2f}:d=2.5[mus]")
        filtros.append("[mus][dial2]sidechaincompress=threshold=0.03:ratio=5:attack=30:release=500[duck]")
        mix.append("[duck]")
    filtros.append(f"{''.join(mix)}amix=inputs={len(mix)}:normalize=0:duration=longest,atrim=duration={total:.3f}[pre]")
    pre = pasta / "segmentos" / "audio_pre.wav"
    nv.rodar(["ffmpeg", "-v", "error", "-y", *entradas, "-filter_complex", ";".join(filtros),
              "-map", "[pre]", "-c:a", "pcm_s16le", "-ar", "48000", str(pre)])
    med = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(pre), "-af",
                          "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    js = json.loads(med[med.rindex("{"):med.rindex("}") + 1])
    ln = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={js['input_i']}:measured_TP={js['input_tp']}:"
          f"measured_LRA={js['input_lra']}:measured_thresh={js['input_thresh']}:offset={js['target_offset']}:linear=true")
    (pasta / "saida").mkdir(exist_ok=True)
    nv.rodar(["ffmpeg", "-v", "error", "-y", "-i", str(pasta / "segmentos" / "video.mp4"), "-i", str(pre),
              "-map", "0:v", "-map", "1:a", "-af", ln + ",aresample=48000", "-c:v", "copy", "-c:a", "aac",
              "-b:a", "192k", "-ac", "2", "-movflags", "+faststart", "-shortest", str(pasta / "saida" / "video.mp4")])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pasta")
    ap.add_argument("--limite", type=float, required=True)
    ap.add_argument("--so-mestres", action="store_true")
    ap.add_argument("--aceitar", default="", help="planos reprovados aceitos após revisão humana (ex.: 6)")
    a = ap.parse_args()
    produzir(a.pasta, a.limite, a.so_mestres, [int(x) for x in a.aceitar.split(",") if x.strip()])


if __name__ == "__main__":
    main()
