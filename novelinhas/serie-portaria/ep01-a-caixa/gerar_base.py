#!/usr/bin/env python3
"""Tomada de visitante com o CENÁRIO TRAVADO por referência: @Image1 = contra_base.jpg (set e enquadramento exatos, sem rosto),
@Image2 = ficha do personagem. Um envio, nunca reenvia. Uso: gerar_base.py <nome> <ficha> <segundos> <teto> "<quem + ação com tempos>"
"""
import json, sys, time, uuid
from pathlib import Path
import requests
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import mininovela as mn
B = Path(__file__).resolve().parent; OUT = B / "tomadas2"; REF = B.parent / "referencias"
API = "https://api.runware.ai/v1"; CAB = {"Authorization": "Bearer proxy-injected"}
nome, ficha, dur, teto, acao = sys.argv[1], sys.argv[2], int(sys.argv[3]), float(sys.argv[4]), sys.argv[5]
PROMPT = ("@Image1 is the EXACT set, camera position, framing and lighting of this shot: copy it faithfully and change nothing in it: the "
          "dark reddish-brown wooden counter along the bottom, the lit green-shade lamp and the beige phone at the left, the doorman seen "
          "from behind at the right edge (out of focus, silent, barely moving), and behind, out of focus, the glass street door, the brown "
          "sofa, the fern and one standing fan. Add only one person, taken from @Image2 (identity and clothes only): standing in the center "
          "on the far side of the counter, waist up, in sharp focus, facing the doorman. " + acao +
          " Static camera, one continuous shot, no cuts. Real-time motion, no slow motion, lively sitcom timing. Speech in Brazilian "
          "Portuguese with a natural Rio de Janeiro accent. Audio: only the spoken line(s) and soft room tone. No music, no laugh track, "
          "no other voices. No parrot, no TV, no elevator, no mailboxes, no extra objects on the counter. No subtitles, no text.")
OUT.mkdir(exist_ok=True)
if (OUT / f"{nome}.mp4").exists(): sys.exit(f"{nome}: já existe")
if dur * 0.068 > teto: sys.exit("PARADO: passa do teto")
cache_f = OUT / "uploads.json"; cache = json.loads(cache_f.read_text()) if cache_f.exists() else {}
refs = [mn.subir_imagem(REF / "contra_base.jpg", cache), mn.subir_imagem(REF / ficha, cache)]; cache_f.write_text(json.dumps(cache))
tid = str(uuid.uuid4())
t = {"taskType": "videoInference", "taskUUID": tid, "model": "bytedance:seedance@2.5-flash", "positivePrompt": PROMPT,
     "width": 854, "height": 480, "duration": dur, "numberResults": 1, "outputType": "URL", "outputFormat": "MP4",
     "deliveryMethod": "async", "includeCost": True, "inputs": {"referenceImages": refs}, "settings": {"audio": True}}
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
        mn.baixar(res["videoURL"], OUT / f"{nome}.mp4"); (OUT / f"{nome}_prompt.txt").write_text(PROMPT)
        item["custo"] = res.get("cost") or dur * 0.068; lf.write_text(json.dumps(log, indent=1)); print(f"{nome}: ok US$ {item['custo']:.3f}", flush=True); sys.exit(0)
    if res.get("status") in ("error", "failed") or j.get("errors"):
        item["falhou"] = json.dumps(res or j.get("errors"), ensure_ascii=False)[:400]; lf.write_text(json.dumps(log, indent=1)); sys.exit(f"{nome}: FALHOU: {item['falhou']}")
sys.exit(f"{nome}: sem resultado; {tid}")
