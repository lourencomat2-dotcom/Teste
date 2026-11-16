#!/usr/bin/env python3
"""Biblioteca de plateia da série (Mirelo SFX, texto -> áudio). Gerada uma vez, usada em todos os episódios.

Um envio por som, nunca reenvia. Teto US$ 0,20. Som que já existe em plateia/ não é gerado de novo.
"""
import json
import sys
import time
import uuid
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import mininovela as mn  # noqa: E402

P = Path(__file__).resolve().parent / "plateia"
API = "https://api.runware.ai/v1"
CAB = {"Authorization": "Bearer proxy-injected"}
TETO = 0.20
BASE = ("Live studio audience of a 1990s TV sitcom, about 150 people in a theater, recorded from the stage, warm and "
        "natural. No music, no speech, no words.")
SONS = [
    ("risadinha", 2, "A short, light chuckle from the whole audience that fades out quickly. " + BASE),
    ("risada", 3, "A warm, hearty laugh from the whole audience, rising and then fading out. " + BASE),
    ("gargalhada", 5, "A big, long belly laugh from the whole audience, with some people cackling, then fading out. " + BASE),
    ("uuuh", 3, "The whole audience reacts with a teasing, surprised 'oooh!' together, then a few laughs. " + BASE),
    ("aplauso", 6, "A big laugh from the whole audience that turns into enthusiastic applause and cheering, then fades. " + BASE),
]


def main():
    P.mkdir(exist_ok=True)
    lf = P / "gasto.json"
    log = json.loads(lf.read_text()) if lf.exists() else {"modelo": "mirelo:1@1", "teto": TETO, "itens": []}
    gasto = sum(i.get("custo") or 0 for i in log["itens"])
    for nome, dur, texto in SONS:
        if (P / f"{nome}.mp3").exists():
            continue
        if gasto + 0.04 > TETO:
            sys.exit(f"PARADO antes de {nome}: gasto {gasto:.3f}")
        tid = str(uuid.uuid4())
        tarefa = {"taskType": "audioInference", "taskUUID": tid, "model": "mirelo:1@1", "positivePrompt": texto,
                  "duration": dur, "outputType": "URL", "outputFormat": "MP3", "deliveryMethod": "async",
                  "includeCost": True}
        r = requests.post(API, headers=CAB, json=[tarefa], timeout=120)
        j = r.json()
        if r.status_code >= 300 or j.get("errors"):
            sys.exit(f"{nome}: RECUSADO, sem custo: {json.dumps(j.get('errors', j), ensure_ascii=False)[:500]}")
        fim = time.time() + 600
        while time.time() < fim:  # só consulta; nunca reenvia
            time.sleep(4)
            try:
                j = requests.post(API, headers=CAB, timeout=60, json=[{"taskType": "getResponse", "taskUUID": tid}]).json()
            except (requests.RequestException, ValueError):
                continue
            item = next((d for d in j.get("data", []) if d.get("taskUUID") == tid), {})
            if item.get("audioURL"):
                mn.baixar(item["audioURL"], P / f"{nome}.mp3")
                c = item.get("cost") or 0
                gasto += c
                log["itens"].append({"som": nome, "segundos": dur, "custo": c, "prompt": texto})
                log["total"] = round(gasto, 5)
                lf.write_text(json.dumps(log, indent=1, ensure_ascii=False))
                print(f"{nome}: US$ {c} | acumulado US$ {gasto:.3f}", flush=True)
                break
            if item.get("status") in ("error", "failed") or j.get("errors"):
                sys.exit(f"{nome}: FALHOU (nada reenviado): {json.dumps(item or j.get('errors'), ensure_ascii=False)[:400]}")
        else:
            sys.exit(f"{nome}: sem resposta em 10 min; taskUUID {tid}")


if __name__ == "__main__":
    main()
