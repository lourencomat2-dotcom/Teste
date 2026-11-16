#!/usr/bin/env python3
"""Tomada a partir de um PRIMEIRO QUADRO travado (image-to-video, Seedance 2.5 Flash). Um envio, nunca reenvia.

Uso: gerar_travada.py <nome> <quadro em referencias/> <segundos> <teto US$> "<prompt>"
"""
import json, sys, time, uuid
from pathlib import Path
import requests
from PIL import Image
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import mininovela as mn
B = Path(__file__).resolve().parent; OUT = B / "tomadas2"; REF = B.parent / "referencias"
API = "https://api.runware.ai/v1"; CAB = {"Authorization": "Bearer proxy-injected"}
nome, quadro, dur, teto, prompt = sys.argv[1], sys.argv[2], int(sys.argv[3]), float(sys.argv[4]), sys.argv[5]
OUT.mkdir(exist_ok=True)
if (OUT / f"{nome}.mp4").exists(): sys.exit(f"{nome}: já existe")
if dur * 0.068 > teto: sys.exit("PARADO: passa do teto")
q = OUT / f"_{Path(quadro).stem}_854.png"
if not q.exists(): Image.open(REF / quadro).convert("RGB").resize((854, 480), Image.LANCZOS).save(q)
cache_f = OUT / "uploads.json"; cache = json.loads(cache_f.read_text()) if cache_f.exists() else {}
img = mn.subir_imagem(q, cache); cache_f.write_text(json.dumps(cache))
tid = str(uuid.uuid4())
t = {"taskType": "videoInference", "taskUUID": tid, "model": "bytedance:seedance@2.5-flash", "positivePrompt": prompt,
     "resolution": "480p", "duration": dur, "numberResults": 1, "outputType": "URL", "outputFormat": "MP4",
     "deliveryMethod": "async", "includeCost": True, "inputs": {"frameImages": [{"image": img, "frame": "first"}]},
     "settings": {"audio": True}}
lf = OUT / "gasto.json"; log = json.loads(lf.read_text()) if lf.exists() else {"itens": []}
for _ in range(30):
    r = requests.post(API, headers=CAB, json=[t], timeout=120); j = r.json(); er = j.get("errors") or []
    if r.status_code < 300 and not er: break
    if any(e.get("code") == "concurrentRequestLimitExceeded" for e in er): time.sleep(60); continue
    sys.exit(f"{nome}: RECUSADO, sem custo: {json.dumps(er or j, ensure_ascii=False)[:700]}")
item = {"tomada": nome, "segundos": dur, "taskUUID": tid, "custo": None}; log["itens"].append(item); lf.write_text(json.dumps(log, indent=1))
fim = time.time() + 2700
while time.time() < fim:
    time.sleep(10)
    try: j = requests.post(API, headers=CAB, timeout=60, json=[{"taskType": "getResponse", "taskUUID": tid}]).json()
    except Exception: continue
    res = next((d for d in j.get("data", []) if d.get("taskUUID") == tid), {})
    if res.get("videoURL"):
        mn.baixar(res["videoURL"], OUT / f"{nome}.mp4"); (OUT / f"{nome}_prompt.txt").write_text(prompt)
        item["custo"] = res.get("cost") or dur * 0.068; lf.write_text(json.dumps(log, indent=1)); print(f"{nome}: ok US$ {item['custo']:.3f}"); sys.exit(0)
    if res.get("status") in ("error", "failed") or j.get("errors"):
        item["falhou"] = json.dumps(res or j.get("errors"), ensure_ascii=False)[:400]; lf.write_text(json.dumps(log, indent=1)); sys.exit(f"{nome}: FALHOU: {item['falhou']}")
sys.exit(f"{nome}: sem resultado; {tid}")
