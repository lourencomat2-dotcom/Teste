#!/usr/bin/env python3
"""Teste de voz do Sigilo (papagaio de verdade): 4 versões de uma fala, um envio cada, teto US$ 0,10.

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
TETO = 0.10
FALA = "O segundo é do Valdir!"

PAPAGAIO_1 = ("A real Amazon parrot imitating human speech. Small bird voice: high-pitched, nasal and tinny, raspy, "
              "slightly metallic and buzzy, words clipped and a little slurred, short squawky sing-song phrasing, "
              "like a talking bird repeating a phrase it overheard.")
PAPAGAIO_2 = ("A talking pet parrot mimicking a middle-aged man's voice: the words are recognizable but squeezed and "
              "shrill, harsh throaty rasp, whistly overtones, choppy rhythm, loud and excited.")

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
    lf = P / "gasto.json"
    log = json.loads(lf.read_text()) if lf.exists() else {"teto": TETO, "itens": []}
    gasto = sum(i.get("custo") or 0 for i in log["itens"])
    for nome, corpo in TESTES:
        if (P / f"{nome}.mp3").exists():
            continue
        if gasto + 0.03 > TETO:
            sys.exit(f"PARADO antes de {nome}: gasto {gasto:.3f} perto do teto {TETO:.2f}")
        c = enviar(nome, corpo, log)
        gasto += c
        log["total"] = round(gasto, 5)
        lf.write_text(json.dumps(log, indent=1, ensure_ascii=False))
        print(f"{nome}: US$ {c} | acumulado US$ {gasto:.4f}", flush=True)
    (P / "testes.json").write_text(json.dumps(TESTES, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
