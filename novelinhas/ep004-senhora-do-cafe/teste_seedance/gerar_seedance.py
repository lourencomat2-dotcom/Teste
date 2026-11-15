"""Teste Seedance 2.5 (ep004): 1 tentativa, 15 s, 1280x720, áudio nativo, 5 referências."""
import sys, json, requests
from pathlib import Path
sys.path.insert(0, "/home/user/Teste/novelinhas")
import mininovela as mn, novelinha as nv
T = Path(__file__).resolve().parent; B = T.parent
TETO = 4.00; PRECO_S = 0.23; DUR = 15
def saldo():
    r = requests.post("https://api.runware.ai/v1", headers={"Authorization": "Bearer proxy-injected"}, timeout=60,
        json=[{"taskType": "accountManagement", "taskUUID": "8a1c2a52-9d0e-4b8e-a1a1-1b2c3d4e5f71", "operation": "getDetails"}])
    return r.json()["data"][0]["balance"]
s0 = saldo(); est = DUR * PRECO_S
print(f"saldo antes {s0:.5f} | estimado {est:.2f} | teto {TETO:.2f}", flush=True)
if est > TETO: sys.exit("PARADO: estimado passa do teto")
cache_f = B / "uploads.json"; cache = json.loads(cache_f.read_text())
refs = [mn.subir_imagem(B / p, cache) for p in ("refs/ref_helena.jpg", "refs/ref_paula.jpg", "refs/ref_ana.jpg", "refs/ref_joice.jpg", "storyboard/master.jpg")]
cache_f.write_text(json.dumps(cache))
prompt = (T / "prompt.txt").read_text()
t = {"taskType": "videoInference", "model": "bytedance:seedance@2.5", "positivePrompt": prompt, "width": 1280, "height": 720,
     "duration": DUR, "numberResults": 1, "outputFormat": "MP4", "deliveryMethod": "async", "includeCost": True,
     "inputs": {"referenceImages": refs}, "settings": {"audio": True}}
g = {"modelo": "bytedance:seedance@2.5", "teto": TETO, "saldo_antes": s0, "duracao_s": DUR, "resolucao": "1280x720", "estimado": est}
(T / "gasto_seedance.json").write_text(json.dumps(g, indent=1))
import uuid, time
tid = str(uuid.uuid4()); t["taskUUID"] = tid; H = {"Authorization": "Bearer proxy-injected"}
r = requests.post("https://api.runware.ai/v1", headers=H, json=[t], timeout=120); j = r.json()
if r.status_code >= 300 or j.get("errors"): sys.exit("ERRO no envio (nada reenviado): " + json.dumps(j.get("errors", j))[:600])
print("enviado", tid, flush=True); g["taskUUID"] = tid; (T / "gasto_seedance.json").write_text(json.dumps(g, indent=1))
item = {}; fim = time.time() + 3 * 3600
while time.time() < fim:  # só consulta; NUNCA reenvia (uma tentativa)
    time.sleep(15)
    try: j = requests.post("https://api.runware.ai/v1", headers=H, json=[{"taskType": "getResponse", "taskUUID": tid}], timeout=60).json()
    except Exception: continue
    if j.get("errors"): print("aviso getResponse:", json.dumps(j["errors"])[:300], flush=True)
    item = next((d for d in j.get("data", []) if d.get("taskUUID") == tid), {})
    if item.get("videoURL"): break
    if item.get("status") in ("error", "failed"): sys.exit("FALHOU: " + json.dumps(item)[:500])
if not item.get("videoURL"): sys.exit("ERRO: sem resultado em 3 h (nada reenviado); taskUUID " + tid)
mn.baixar(item["videoURL"], T / "seedance_original.mp4")
g["custo_api"] = item.get("cost"); g["saldo_logo_apos"] = saldo()
(T / "gasto_seedance.json").write_text(json.dumps(g, indent=1))
print("ok custo", g["custo_api"], "| saldo", g["saldo_logo_apos"], flush=True)
