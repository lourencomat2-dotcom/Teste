"""Passada de IA (vídeo -> vídeo) no Runware: envia um vídeo pronto e pede uma versão realista,
mantendo cortes, câmera e movimentos. GASTA CRÉDITO do Runware: confira o custo antes.

  python3 motor/runware_v2v.py entrada.mp4 saida.mp4 [--modelo bytedance:seedance@2.0-fast] [--res 1280x720]
                               [--prompt arquivo.txt]   (sem --prompt usa PROMPT abaixo)
  Seedance 2.5 (edição de verdade): --modelo bytedance:seedance@2.5 --res 480p --auto [--ref foto.png ...]

Chave: variável RUNWARE_API_KEY (no ambiente do Claude o proxy já autentica).
Formato do pedido conferido no SDK oficial (pacote PyPI "runware"): o vídeo vai em inputs.video,
como mediaUUID de um upload (taskType mediaStorage, operation upload, media em base64).
"""
import base64, json, os, sys, time, urllib.error, urllib.request, uuid

API = "https://api.runware.ai/v1"

PROMPT = (
    "Edit @Video1: turn this 3D animated scene into photorealistic live-action footage of a Brazilian "
    "multi-camera TV sitcom, as if shot on a real studio set with real actors. Keep exactly the same shots, "
    "cuts, camera movements, framing, timing, actor positions, walking, gestures, head turns and mouth "
    "movements as @Video1. Same kitchen set and props: butter-yellow walls, white wainscot, patterned "
    "hydraulic floor tiles, red-and-white checkered tablecloth, teal pendant lamp, coral curtains, white "
    "fridge, blue-and-white tiles behind the sink, open door to a hallway. Characters: Clara, a Brazilian "
    "woman around 28, fair skin, brown hair in a ponytail, green blouse and jeans; Beto, a Black Brazilian "
    "man around 30, short black hair, plain orange t-shirt and jeans, with a white yogurt mustache on his "
    "upper lip. Bright, soft, even studio sitcom lighting, natural skin texture, TV camera look. "
    "Avoid: changing the characters' faces or clothes between shots, extra people, text, logos, morphing, "
    "cartoon look."
)

def chamar(tarefas):
    req = urllib.request.Request(API, data=json.dumps(tarefas).encode(), headers={"Content-Type": "application/json"})
    if os.environ.get("RUNWARE_API_KEY"): req.add_header("Authorization", "Bearer " + os.environ["RUNWARE_API_KEY"])
    try:
        with urllib.request.urlopen(req, timeout=300) as r: resp = json.load(r)
    except urllib.error.HTTPError as e:                     # o Runware explica o erro no corpo (JSON)
        resp = json.loads(e.read().decode() or "{}")
    if resp.get("errors"): raise SystemExit("Runware recusou: " + json.dumps(resp["errors"], ensure_ascii=False))
    return resp["data"]

def main():
    args = sys.argv[1:]
    modelo = args[args.index("--modelo") + 1] if "--modelo" in args else "bytedance:seedance@2.0-fast"
    res = args[args.index("--res") + 1] if "--res" in args else "1280x720"   # "1280x720" ou "480p"/"720p"/"1080p"
    tam = {"width": int(res.split("x")[0]), "height": int(res.split("x")[1])} if "x" in res else {"resolution": res}
    prompt = open(args[args.index("--prompt") + 1]).read().strip() if "--prompt" in args else PROMPT
    opcoes = {args[i + 1] for i, a in enumerate(args) if a == "--ref"} | {modelo, res} | ({args[args.index("--prompt") + 1]} if "--prompt" in args else set())
    entrada, saida = [a for a in args if not a.startswith("--") and a not in opcoes][:2]
    dur = max(4, min(30, round(float(os.popen(f'ffprobe -v error -show_entries format=duration -of csv=p=0 "{entrada}"').read()))))
    if "--auto" in args: dur = "auto"          # edição no Seedance 2.5: duração e proporção seguem o vídeo de entrada
    print(f"enviando {entrada} ({os.path.getsize(entrada) / 1e6:.1f} MB)...", flush=True)
    up = chamar([{"taskType": "mediaStorage", "taskUUID": str(uuid.uuid4()), "operation": "upload",
                  "media": base64.b64encode(open(entrada, "rb").read()).decode()}])[0]
    print("mediaUUID", up["mediaUUID"], flush=True)
    refs = []                                       # --ref foto.png (rosto/figurino): viram @Image1, @Image2...
    for i, a in enumerate(args):
        if a == "--ref":
            refs.append(chamar([{"taskType": "mediaStorage", "taskUUID": str(uuid.uuid4()), "operation": "upload",
                                 "media": base64.b64encode(open(args[i + 1], "rb").read()).decode()}])[0]["mediaUUID"])
            print("referência", args[i + 1], refs[-1], flush=True)
    entradas = {"video": up["mediaUUID"]}
    if refs: entradas["referenceImages"] = refs
    tid = str(uuid.uuid4())
    chamar([{"taskType": "videoInference", "taskUUID": tid, "model": modelo, "positivePrompt": prompt,
             **tam, "duration": dur, "deliveryMethod": "async", "includeCost": True,
             "outputFormat": "MP4", "inputs": entradas}])
    print(f"tarefa {tid} enviada ({modelo}, {res}, {dur}s); aguardando...", flush=True)
    t0 = time.time()
    while True:
        time.sleep(10)
        r = chamar([{"taskType": "getResponse", "taskUUID": tid}])[0]
        if r.get("status") == "success":
            print(f"pronto em {time.time() - t0:.0f}s · custo US$ {r.get('cost')}", flush=True)
            urllib.request.urlretrieve(r["videoURL"], saida); print("salvo:", saida); return
        if r.get("status") not in (None, "processing"): raise SystemExit("falhou: " + json.dumps(r))

if __name__ == "__main__":
    main()
