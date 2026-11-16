#!/usr/bin/env python3
"""Etapa A: as 6 imagens de referência da série (elenco, Sigilo e portaria).

Uma tentativa por imagem, um envio só (nunca reenvia). Para antes de passar do TETO.
Imagem que já existe na pasta não é gerada de novo.
"""
import json
import sys
import time
import uuid
from pathlib import Path

import requests

PASTA = Path(__file__).resolve().parent / "referencias"
TETO = 0.50
MODELO = "bytedance:seedream@5.5"
API = "https://api.runware.ai/v1"
CAB = {"Authorization": "Bearer proxy-injected"}  # chave injetada pelo proxy da nuvem; no seu PC use RUNWARE_API_KEY

ESTILO = ("Photorealistic still from a 1990s TV sitcom, warm studio lighting, rich saturated colors, "
          "subtle film grain, sharp focus. No text, no letters, no numbers, no logos, no watermark.")
RETRATO = ("Full body, standing, facing the camera, arms relaxed, mouth closed, calm expression, "
           "against a plain warm beige studio backdrop.")

IMAGENS = [
    ("valdir", 1024, 1280,
     "Brazilian Black man, 58 years old, short grey hair, grey mustache, kind tired eyes. Building doorman: "
     "light blue short-sleeve button-up shirt, navy blue tie, reading glasses hanging on a cord around his neck, "
     "dark grey trousers, black shoes. " + RETRATO),
    ("marlene", 1024, 1280,
     "Brazilian white woman, 62 years old, short voluminous teased blonde hair, pearl necklace, small pearl earrings. "
     "Bright red 1990s blazer with shoulder pads over a white blouse, knee-length navy skirt, low heels. "
     "Holds a plain brown clipboard against her chest with blank paper. Stern, upright posture. " + RETRATO),
    ("soraia", 1024, 1280,
     "Brazilian woman, 40 years old, medium brown skin, dark hair rolled in pink hair curlers. "
     "Shiny hot pink satin bathrobe tied at the waist, pink fluffy slippers. Curious, one eyebrow slightly raised. " + RETRATO),
    ("juninho", 1024, 1280,
     "Brazilian young man, 22 years old, light brown skin, slim, short black hair. Plain bright orange nylon jacket, "
     "jeans, white sneakers. Wears a black motorcycle helmet with the visor raised so his whole face is visible. "
     "Plain orange square delivery backpack on his back. Friendly, naive look. " + RETRATO),
    ("sigilo", 1024, 1280,
     "A green Amazon parrot with a yellow forehead and yellow face, standing on a simple wooden perch, "
     "whole bird visible, side three-quarter view, beak closed, against a plain warm beige studio backdrop."),
    ("portaria", 1920, 1080,
     "Wide shot of the entrance lobby of a small Brazilian apartment building in the 1990s, empty, no people. "
     "Center-right: a dark wooden doorman counter; on it a beige corded desk phone, a small CRT television, "
     "a small portable radio, a lit desk lamp with a green shade, and at the right end of the counter an empty "
     "wooden bird perch. Behind the counter a wall of plain metal mailboxes without numbers and an old intercom "
     "panel with round buttons. Left: a worn brown leather sofa and a large fern in a clay pot. "
     "Left wall: a glass street door with a metal frame, night outside. Back wall: an elevator door with a gold "
     "frame. A standing fan. Beige walls, terracotta floor tiles. Camera at eye level, the counter fully visible."),
]


def saldo():
    j = requests.post(API, headers=CAB, timeout=60, json=[{
        "taskType": "accountManagement", "taskUUID": str(uuid.uuid4()), "operation": "getDetails"}]).json()
    return j["data"][0]["balance"]


def gerar(nome, w, h, texto, log):
    tid = str(uuid.uuid4())
    tarefa = {"taskType": "imageInference", "taskUUID": tid, "model": MODELO,
              "positivePrompt": f"{texto} {ESTILO}", "width": w, "height": h, "numberResults": 1,
              "outputType": "URL", "outputFormat": "JPG", "deliveryMethod": "async", "includeCost": True}
    r = requests.post(API, headers=CAB, timeout=120, json=[tarefa])
    j = r.json()
    if r.status_code >= 300 or j.get("errors"):
        sys.exit(f"ERRO no envio de {nome} (nada reenviado): {json.dumps(j.get('errors', j))[:500]}")
    fim = time.time() + 600
    while time.time() < fim:  # só consulta o resultado; nunca reenvia
        time.sleep(3)
        try:
            j = requests.post(API, headers=CAB, timeout=60, json=[{"taskType": "getResponse", "taskUUID": tid}]).json()
        except (requests.RequestException, ValueError):
            continue
        item = next((d for d in j.get("data", []) if d.get("taskUUID") == tid), {})
        if item.get("imageURL"):
            (PASTA / f"{nome}.jpg").write_bytes(requests.get(item["imageURL"], timeout=180).content)
            (PASTA / f"{nome}_prompt.txt").write_text(tarefa["positivePrompt"])
            log["itens"].append({"imagem": nome, "custo": item.get("cost"), "taskUUID": tid})
            return item.get("cost") or 0
        if item.get("status") in ("error", "failed"):
            sys.exit(f"FALHOU {nome}: {json.dumps(item)[:400]}")
    sys.exit(f"sem resposta para {nome} em 10 min (nada reenviado); taskUUID {tid}")


def main():
    PASTA.mkdir(exist_ok=True)
    f = PASTA / "gasto.json"
    log = json.loads(f.read_text()) if f.exists() else {"modelo": MODELO, "teto": TETO, "itens": []}
    log.setdefault("saldo_antes", saldo())
    gasto = sum(i["custo"] or 0 for i in log["itens"])
    for nome, w, h, texto in IMAGENS:
        if (PASTA / f"{nome}.jpg").exists():
            continue
        previsto = 0.06 if w * h > 1.5e6 else 0.03
        if gasto + previsto > TETO:
            sys.exit(f"PARADO antes de {nome}: gasto {gasto:.3f} + previsto {previsto:.2f} passa do teto {TETO:.2f}")
        c = gerar(nome, w, h, texto, log)
        gasto += c
        log["total"] = round(gasto, 5)
        f.write_text(json.dumps(log, indent=1, ensure_ascii=False))
        print(f"{nome}: US$ {c:.4f} | acumulado US$ {gasto:.4f}", flush=True)
    log["saldo_depois"] = saldo()
    f.write_text(json.dumps(log, indent=1, ensure_ascii=False))
    print(f"total US$ {gasto:.4f} | saldo antes {log['saldo_antes']:.5f} | saldo agora {log['saldo_depois']:.5f}")


if __name__ == "__main__":
    main()
