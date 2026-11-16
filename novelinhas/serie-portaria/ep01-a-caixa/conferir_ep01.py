#!/usr/bin/env python3
"""Conferência automática do ep. 1 (grátis, roda local). Gera conferencia.md e conferencia_quadros.jpg.

Para cada plano, no trecho usado na montagem:
  1. FALA: transcreve e compara com o roteiro palavra por palavra. Também transcreve uma janela maior em volta:
     se a janela maior acerta mais palavras, o corte comeu parte da fala.
  2. VOZ: impressão digital da voz (modelo de reconhecimento de locutor) comparada com as outras tomadas
     do mesmo personagem. Nota baixa = voz diferente.
  3. CENÁRIO: um quadro por plano numa folha, com a regra de fundo da câmera, para revisão visual.

Uso: python conferir_ep01.py <pasta dos modelos>   (a pasta tem sherpa-onnx-whisper-small/ e o .onnx de locutor)
"""
import difflib
import json
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

import numpy as np
import sherpa_onnx
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
import montar_ep01 as M  # noqa: E402

B = Path(__file__).resolve().parent
SR = 16000
NUM = {"1": "um", "2": "dois", "3": "tres", "4": "quatro", "5": "cinco", "6": "seis", "7": "sete", "8": "oito",
       "9": "nove", "10": "dez", "11": "onze", "12": "doze"}
FUNDO = {  # o que deve aparecer atrás de quem está em cada câmera
    "C1": "hall aberto",
    "C2": "Valdir atrás do balcão; atrás dele escaninhos e interfone",
    "C3": "visitante na frente do balcão; atrás dele a entrada (porta de vidro, sofá, samambaia), nada de escaninhos",
    "C4": "Sigilo no poleiro; atrás escaninhos",
    "C5": "duas de perfil",
}


def norm(t):
    t = unicodedata.normalize("NFKD", t.lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = re.sub(r"[^a-z0-9 ]", " ", t)
    return [NUM.get(w, w) for w in t.split()]


def audio(f, a=None, b=None):
    cmd = ["ffmpeg", "-v", "error"]
    if a is not None:
        cmd += ["-ss", f"{a:.2f}", "-t", f"{b - a:.2f}"]
    cmd += ["-i", str(f), "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"]
    return np.frombuffer(subprocess.run(cmd, capture_output=True).stdout, dtype=np.float32)


def main():
    mod = Path(sys.argv[1])
    asr = sherpa_onnx.OfflineRecognizer.from_whisper(
        encoder=str(mod / "sherpa-onnx-whisper-small/small-encoder.onnx"),
        decoder=str(mod / "sherpa-onnx-whisper-small/small-decoder.onnx"),
        tokens=str(mod / "sherpa-onnx-whisper-small/small-tokens.txt"), language="pt", task="transcribe", num_threads=4)
    spk = sherpa_onnx.SpeakerEmbeddingExtractor(sherpa_onnx.SpeakerEmbeddingExtractorConfig(
        model=str(mod / "3dspeaker_speech_eres2net_base_sv_zh-cn_3dspeaker_16k.onnx"), num_threads=4))

    def transcrever(x):
        s = asr.create_stream()
        s.accept_waveform(SR, x)
        asr.decode_stream(s)
        return s.result.text.strip()

    def voz(x):
        s = spk.create_stream()
        s.accept_waveform(SR, x)
        s.input_finished()
        e = np.array(spk.compute(s))
        return e / (np.linalg.norm(e) + 1e-9)

    rot = {}
    for linha in (B / "roteiro.md").read_text().splitlines():
        p = [c.strip() for c in linha.split("|")]
        if len(p) > 6 and p[1].isdigit():
            m = re.match(r"(\w+): \"(.*)\"", p[5])
            rot[int(p[1])] = {"camera": p[2], "quem": p[4], "falante": m.group(1).lower() if m else None,
                              "fala": m.group(2) if m else "", "acao": p[6]}
    aj = json.loads((B / "ajustes.json").read_text()) if (B / "ajustes.json").exists() else {}
    res, embs = [], {}
    for n in sorted(M.PLANOS):
        arq, parte = M.PLANOS[n]
        f = (M.TOM / arq).resolve()
        r = {"plano": n, "arquivo": arq, **rot.get(n, {})}
        if parte == "imagem" or not f.exists():
            r["status"] = "falta gerar"
            res.append(r)
            continue
        a, b = aj.get(str(n), M.trecho(f, parte))
        d = M.duracao(f)
        r["trecho"] = [round(a, 2), round(b, 2)]
        x = audio(f, a, b)
        if r.get("fala"):
            ouvido = transcrever(x)
            esperado = norm(r["fala"])
            ok = difflib.SequenceMatcher(None, esperado, norm(ouvido)).get_matching_blocks()
            acertos = sum(m.size for m in ok)
            largo = transcrever(audio(f, max(0, a - 0.7), min(d, b + 0.7)))
            ok2 = sum(m.size for m in difflib.SequenceMatcher(None, esperado, norm(largo)).get_matching_blocks())
            r.update({"ouvido": ouvido, "palavras": f"{acertos}/{len(esperado)}", "nota_fala": acertos / max(1, len(esperado)),
                      "corte_comeu": ok2 > acertos, "ouvido_largo": largo})
            if len(x) > SR * 0.8 and r.get("falante"):
                e = voz(x)
                r["_emb"] = e
                embs.setdefault(r["falante"], []).append((n, e))
        # quadro do meio do trecho
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{(a + b) / 2:.2f}", "-i", str(f), "-frames:v", "1",
                        "-vf", "scale=427:240", str(M.TRAB / f"q{n:02d}.png")], check=True)
        res.append(r)
    # voz: semelhança de cada plano com a média dos outros planos do mesmo personagem
    for quem, lst in embs.items():
        for n, e in lst:
            outros = [o for m, o in lst if m != n]
            if outros:
                med = np.mean(outros, axis=0)
                sim = float(e @ (med / np.linalg.norm(med)))
                next(r for r in res if r["plano"] == n)["voz_sim"] = round(sim, 2)
    for r in res:
        r.pop("_emb", None)
    (B / "conferencia.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))
    # folha de quadros
    fonte = ImageFont.truetype(M.FONT, 13)
    folha = Image.new("RGB", (427 * 4, (240 + 34) * ((len(res) + 3) // 4)), (20, 20, 20))
    dr = ImageDraw.Draw(folha)
    for k, r in enumerate(res):
        x0, y0 = (k % 4) * 427, (k // 4) * 274
        q = M.TRAB / f"q{r['plano']:02d}.png"
        if q.exists():
            folha.paste(Image.open(q).convert("RGB"), (x0, y0))
        dr.text((x0 + 4, y0 + 242), f"{r['plano']} {r.get('camera', '')} {r['arquivo']}", font=fonte, fill=(255, 255, 0))
        dr.text((x0 + 4, y0 + 257), FUNDO.get(r.get("camera", ""), "")[:60], font=fonte, fill=(200, 200, 200))
    folha.save(B / "conferencia_quadros.jpg", quality=85)
    # relatório
    L = ["# Conferência automática do ep. 1", "",
         "Fala: palavras do roteiro reconhecidas no trecho usado. Voz: semelhança com as outras tomadas do mesmo "
         "personagem (1 = idêntica). O transcritor erra em voz caricata; confirmar de ouvido o que aparecer marcado.", "",
         "| Plano | Tomada | Falante | Roteiro | Ouvido no trecho | Palavras | Corte comeu? | Voz |", "|---|---|---|---|---|---|---|---|"]
    for r in res:
        if r.get("status"):
            L.append(f"| {r['plano']} | {r['arquivo']} | | | **{r['status']}** | | | |")
            continue
        L.append(f"| {r['plano']} | {r['arquivo']} | {r.get('falante') or ''} | {r.get('fala', '')} | {r.get('ouvido', '')} | "
                 f"{r.get('palavras', '')} | {'**sim**' if r.get('corte_comeu') else ''} | {r.get('voz_sim', '')} |")
    (B / "conferencia.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
