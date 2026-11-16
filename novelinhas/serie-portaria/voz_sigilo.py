#!/usr/bin/env python3
"""Teste de voz do Sigilo: 4 versões de uma fala, um envio cada.

Uso: python voz_sigilo.py            (rodada 2, papagaio de verdade, teto US$ 0,10)
     python voz_sigilo.py 3 0.02     (rodada 3, papagaio de TV, teto US$ 0,02)
     python voz_sigilo.py 4 0.02     (rodada 4, variações da H no Gemini, teto US$ 0,02)

Gera só o áudio e coloca por cima do clipe 3 do piloto (o bico já abre no tempo da fala).
"""
import base64
import json
import subprocess
import sys
import time
import uuid
from pathlib import Path

import requests

B = Path(__file__).resolve().parent
P = B / "voz_sigilo"
CLIPE = B / "ep01-a-caixa" / "piloto" / "clipe3_flash.mp4"
API = "https://api.runware.ai/v1"
CAB = {"Authorization": "Bearer proxy-injected"}
TETO = 0.10 if len(sys.argv) < 2 else float(sys.argv[2])
FALA = "O segundo é do Valdir!"

PAPAGAIO_1 = ("A real Amazon parrot imitating human speech. Small bird voice: high-pitched, nasal and tinny, raspy, "
              "slightly metallic and buzzy, words clipped and a little slurred, short squawky sing-song phrasing, "
              "like a talking bird repeating a phrase it overheard.")
PAPAGAIO_2 = ("A talking pet parrot mimicking a middle-aged man's voice: the words are recognizable but squeezed and "
              "shrill, harsh throaty rasp, whistly overtones, choppy rhythm, loud and excited.")

TV = ("Original comic puppet parrot character voice for a Brazilian TV show: an adult man performing a raspy, nasal, "
      "high-pitched cartoon parrot voice, cheeky, mischievous and mocking, Rio de Janeiro carioca accent, "
      "speaks fast, ends with a short cackling laugh.")
TV2 = ("Cartoon puppet parrot voice performed by a playful male comedian: squeaky and gravelly at the same time, "
       "strongly nasal, tight throat, very fast clipped delivery, teasing gossipy tone, carioca accent.")

RODADA3 = [
    ("E", {"model": "alibaba:qwen@3-tts-1.7b-voicedesign", "positivePrompt": TV, "speech": {"text": FALA}}),
    ("F", {"model": "alibaba:qwen@3-tts-1.7b-voicedesign", "positivePrompt": TV2, "speech": {"text": FALA}}),
    ("G", {"model": "google:gemini@3.1-flash-tts",
           "speech": {"text": f"[comic TV puppet parrot voice: raspy, nasal, high, fast, cheeky, carioca accent] {FALA} [laughs]",
                      "voice": "Puck", "language": "pt-BR"}}),
    ("H", {"model": "google:gemini@3.1-flash-tts",
           "speech": {"text": f"[cartoon parrot puppet voice: gravelly, nasal, squeaky, fast and mocking, carioca accent] {FALA} [laughs]",
                      "voice": "Algenib", "language": "pt-BR"}}),
]

H_TAG = "cartoon parrot puppet voice: gravelly, nasal, squeaky, fast and mocking, carioca accent"


def gemini(voz, tag, rir=True):
    return {"model": "google:gemini@3.1-flash-tts",
            "speech": {"text": f"[{tag}] {FALA}" + (" [laughs]" if rir else ""), "voice": voz, "language": "pt-BR"}}


RODADA4 = [
    ("I", gemini("Algenib", "cartoon parrot puppet voice: gravelly, nasal, higher and squeakier, very fast and mocking, carioca accent")),
    ("J", gemini("Algenib", "cartoon parrot puppet voice: very raspy and throaty, nasal, cheeky, fast, carioca accent, cackling laugh")),
    ("K", gemini("Algenib", "cartoon parrot puppet voice: gravelly, very nasal, squeaky, fast and mocking, carioca accent", rir=False)),
    ("L", gemini("Sadachbia", H_TAG)),
    ("M", gemini("Fenrir", H_TAG)),
    ("N", gemini("Zubenelgenubi", H_TAG)),
]

TESTES = [
    ("A", {"model": "alibaba:qwen@3-tts-1.7b-voicedesign", "positivePrompt": PAPAGAIO_1,
           "speech": {"text": FALA}}),
    ("B", {"model": "alibaba:qwen@3-tts-1.7b-voicedesign", "positivePrompt": PAPAGAIO_2,
           "speech": {"text": FALA}}),
    ("C", {"model": "google:gemini@3.1-flash-tts",
           "speech": {"text": f"[like a real talking parrot: shrill, raspy, nasal, clipped, squawky] {FALA}",
                      "voice": "Puck", "language": "pt-BR"}}),
    ("D", {"model": "google:gemini@3.1-flash-tts",
           "speech": {"text": f"[high-pitched screechy parrot imitation of a human voice] {FALA}",
                      "voice": "Fenrir", "language": "pt-BR"}}),
]


def enviar(nome, corpo, log):
    tid = str(uuid.uuid4())
    tarefa = {"taskType": "audioInference", "taskUUID": tid, "numberResults": 1, "outputType": "base64Data",
              "outputFormat": "MP3", "deliveryMethod": "async", "includeCost": True, **corpo}
    r = requests.post(API, headers=CAB, json=[tarefa], timeout=120)
    j = r.json()
    if r.status_code >= 300 or j.get("errors"):
        print(f"{nome}: RECUSADO, sem custo: {json.dumps(j.get('errors', j), ensure_ascii=False)[:500]}", flush=True)
        return 0
    fim = time.time() + 600
    while time.time() < fim:  # só consulta; nunca reenvia
        time.sleep(3)
        try:
            j = requests.post(API, headers=CAB, timeout=60, json=[{"taskType": "getResponse", "taskUUID": tid}]).json()
        except (requests.RequestException, ValueError):
            continue
        item = next((d for d in j.get("data", []) if d.get("taskUUID") == tid), {})
        if item.get("audioBase64Data"):
            (P / f"{nome}.mp3").write_bytes(base64.b64decode(item["audioBase64Data"]))
            log["itens"].append({"teste": nome, "modelo": corpo["model"], "custo": item.get("cost"), "taskUUID": tid})
            return item.get("cost") or 0
        if item.get("status") in ("error", "failed") or j.get("errors"):
            print(f"{nome}: FALHOU: {json.dumps(item or j.get('errors'), ensure_ascii=False)[:400]}", flush=True)
            log["itens"].append({"teste": nome, "modelo": corpo["model"], "custo": None, "taskUUID": tid, "falhou": True})
            return 0
    sys.exit(f"{nome}: sem resposta em 10 min (nada reenviado); taskUUID {tid}")


def main():
    P.mkdir(exist_ok=True)
    rodada = sys.argv[1] if len(sys.argv) > 1 else "2"
    r3 = rodada in ("3", "4")
    lf = P / ("gasto.json" if rodada == "2" else f"gasto_r{rodada}.json")
    log = json.loads(lf.read_text()) if lf.exists() else {"teto": TETO, "itens": []}
    gasto = sum(i.get("custo") or 0 for i in log["itens"])
    testes = {"2": TESTES, "3": RODADA3, "4": RODADA4}[rodada]
    for nome, corpo in testes:
        if (P / f"{nome}.mp3").exists():
            continue
        if gasto + (0.005 if r3 else 0.03) > TETO:  # rodada 2 mediu no máximo US$ 0,0017 por voz
            sys.exit(f"PARADO antes de {nome}: gasto {gasto:.3f} perto do teto {TETO:.2f}")
        c = enviar(nome, corpo, log)
        gasto += c
        log["total"] = round(gasto, 5)
        lf.write_text(json.dumps(log, indent=1, ensure_ascii=False))
        print(f"{nome}: US$ {c} | acumulado US$ {gasto:.4f}", flush=True)
    (P / f"testes_r{rodada}.json").write_text(json.dumps(testes, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
