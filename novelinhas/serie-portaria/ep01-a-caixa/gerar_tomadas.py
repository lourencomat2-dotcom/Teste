#!/usr/bin/env python3
"""Gera as tomadas do ep. 1 listadas na linha de comando, uma por vez, a partir de tomadas.json.

Uso: python gerar_tomadas.py <teto da leva em US$> <tomada> [<tomada> ...]
Ex.: python gerar_tomadas.py 2.00 valdir1 valdir2 valdir3 valdir4 valdir5

- Tomada que já existe em tomadas/ não é gerada de novo.
- Um envio aceito nunca é reenviado. Envio RECUSADO (não cobrado) por crédito reservado espera e tenta de novo.
- Para antes de passar do teto da leva ou do teto do episódio (US$ 20, contando etapas A e B).
"""
import json
import sys
import time
import uuid
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import mininovela as mn  # noqa: E402

B = Path(__file__).resolve().parent
OUT = B / "tomadas"
REF = B.parent / "referencias"
API = "https://api.runware.ai/v1"
CAB = {"Authorization": "Bearer proxy-injected"}
MODELO = "bytedance:seedance@2.5-flash"
PRECO_S = 0.068
TETO_EPISODIO = 20.0
GASTO_ANTES = 1.51  # etapa A (US$ 0,14) + piloto e testes de voz (US$ 1,37)


def chamar(corpo):
    r = requests.post(API, headers=CAB, json=corpo, timeout=120)
    return r.status_code, r.json()


def main():
    teto_leva = float(sys.argv[1])
    nomes = sys.argv[2:]
    T = {t["tomada"]: t for t in json.loads((B / "tomadas.json").read_text())}
    OUT.mkdir(exist_ok=True)
    lf = OUT / "gasto.json"
    log = json.loads(lf.read_text()) if lf.exists() else {"itens": []}
    gasto_ep = GASTO_ANTES + sum(i.get("custo") or 0 for i in log["itens"])
    gasto_leva = 0.0
    cache_f = OUT / "uploads.json"
    cache = json.loads(cache_f.read_text()) if cache_f.exists() else {}
    for nome in nomes:
        t = T[nome]
        if (OUT / f"{nome}.mp4").exists():
            print(f"{nome}: já existe, pulado", flush=True)
            continue
        previsto = t["segundos"] * PRECO_S
        if gasto_leva + previsto > teto_leva or gasto_ep + previsto > TETO_EPISODIO:
            sys.exit(f"PARADO antes de {nome}: leva {gasto_leva:.2f} / episódio {gasto_ep:.2f} + {previsto:.2f} passaria do teto")
        refs = [mn.subir_imagem(REF / r, cache) for r in t["refs"]]
        cache_f.write_text(json.dumps(cache))
        tid = str(uuid.uuid4())
        tarefa = {"taskType": "videoInference", "taskUUID": tid, "model": MODELO, "positivePrompt": t["prompt"],
                  "width": 854, "height": 480, "duration": t["segundos"], "numberResults": 1, "outputType": "URL",
                  "outputFormat": "MP4", "deliveryMethod": "async", "includeCost": True,
                  "inputs": {"referenceImages": refs}, "settings": {"audio": True}}
        for tentativa in range(30):  # só repete envio RECUSADO por crédito reservado (não cobrado)
            st, j = chamar([tarefa])
            erros = j.get("errors") or []
            if st < 300 and not erros:
                break
            if any(e.get("code") == "concurrentRequestLimitExceeded" for e in erros):
                time.sleep(60)
                continue
            sys.exit(f"{nome}: RECUSADO, sem custo: {json.dumps(erros or j, ensure_ascii=False)[:600]}")
        else:
            sys.exit(f"{nome}: crédito continuou reservado por 30 min; nada enviado")
        item = {"tomada": nome, "segundos": t["segundos"], "taskUUID": tid, "custo": None}
        log["itens"].append(item)
        lf.write_text(json.dumps(log, indent=1, ensure_ascii=False))
        print(f"{nome}: enviado ({t['segundos']} s, previsto US$ {previsto:.2f})", flush=True)
        fim = time.time() + 45 * 60
        while time.time() < fim:  # só consulta; nunca reenvia
            time.sleep(10)
            try:
                st, j = chamar([{"taskType": "getResponse", "taskUUID": tid}])
            except (requests.RequestException, ValueError):
                continue
            res = next((d for d in j.get("data", []) if d.get("taskUUID") == tid), {})
            if res.get("videoURL"):
                mn.baixar(res["videoURL"], OUT / f"{nome}.mp4")
                (OUT / f"{nome}_prompt.txt").write_text(t["prompt"])
                item["custo"] = res.get("cost") or previsto
                gasto_leva += item["custo"]
                gasto_ep += item["custo"]
                lf.write_text(json.dumps(log, indent=1, ensure_ascii=False))
                print(f"{nome}: ok US$ {item['custo']:.3f} | leva US$ {gasto_leva:.2f} | episódio US$ {gasto_ep:.2f}", flush=True)
                break
            if res.get("status") in ("error", "failed") or j.get("errors"):
                item["falhou"] = json.dumps(res or j.get("errors"), ensure_ascii=False)[:400]
                lf.write_text(json.dumps(log, indent=1, ensure_ascii=False))
                print(f"{nome}: FALHOU (nada reenviado): {item['falhou']}", flush=True)
                break
        else:
            print(f"{nome}: sem resultado em 45 min (nada reenviado); taskUUID {tid}", flush=True)


if __name__ == "__main__":
    main()
