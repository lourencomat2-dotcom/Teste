#!/usr/bin/env python3
"""Piloto do ep. 1 (etapa B). Gera UM clipe por chamada, um envio só, e para antes de passar do teto.

Uso: python piloto.py <clipe 1-4> <modelo: 2.5 | flash>
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
P = B / "piloto"
REF = B.parent / "referencias"
API = "https://api.runware.ai/v1"
CAB = {"Authorization": "Bearer proxy-injected"}
TETO = 2.50
MODELOS = {"2.5": "bytedance:seedance@2.5", "flash": "bytedance:seedance@2.5-flash"}
W, H = 854, 480

COMUM = ("1990s TV sitcom look, warm studio lighting, rich saturated colors, subtle film grain, background softly out "
         "of focus. Static camera, one continuous shot, no cuts. Audio: only the spoken line(s) and soft room tone. "
         "No music, no laugh track, no other voices. No subtitles, no text on screen.")

JUNINHO = ("Close-up at eye level of the young delivery man of @Image1: same face, black motorcycle helmet with the visor "
           "raised, bright orange jacket, orange delivery backpack straps on his shoulders. He stands in the lobby of "
           "@Image2, seen from behind the doorman counter; behind him, out of focus, the glass street door, the fern and "
           "the brown leather sofa. He looks down at a small blank paper slip in his hand, then looks up at someone just "
           "off-screen to the left and says, sincere and naive, in Brazilian Portuguese with a natural São Paulo accent: "
           "\"Ué. Na nota tá escrito karaokê.\" Young man's voice, light and quick. Only he speaks, once.")

CLIPES = {
    1: ("juninho", 4, JUNINHO),
    2: ("juninho", 4, JUNINHO),
    3: ("sigilo", 4,
        "Close-up of the green parrot with a yellow face of @Image1, on its curved branch perch at the end of the dark "
        "wooden counter of @Image2; out of focus behind it, the metal mailboxes. The parrot bobs its head, flaps its "
        "wings once and says loudly, in a squawky parrot voice, in Brazilian Portuguese: \"O segundo é do Valdir!\" "
        "Its beak opens and closes with the words. Only the parrot speaks, once."),
    4: ("valdir", 8,
        "Close-up at eye level of the doorman of @Image1: same face, grey mustache, light blue short-sleeve shirt, navy "
        "tie, reading glasses hanging on a cord. He stands behind the dark wooden counter of @Image2, seen from the "
        "front; behind him, out of focus, the metal mailboxes and the intercom panel. "
        "0 to 3 s: without looking at anyone, calm, deep, unhurried voice, in Brazilian Portuguese with a natural "
        "São Paulo accent: \"Eu não sou de comentar.\" "
        "3 to 5 s: silence; he keeps a straight face, then glances once to the left, as if someone is staring at him. "
        "5 to 8 s: he leans a little forward and says quietly, almost whispering: \"É da Dona Marlene.\" "
        "Only he speaks."),
}


def saldo():
    j = requests.post(API, headers=CAB, timeout=60, json=[{
        "taskType": "accountManagement", "taskUUID": str(uuid.uuid4()), "operation": "getDetails"}]).json()
    return j["data"][0]["balance"]


def main():
    n, mod = int(sys.argv[1]), sys.argv[2]
    P.mkdir(exist_ok=True)
    nome = f"clipe{n}_{mod}"
    if (P / f"{nome}.mp4").exists():
        sys.exit(f"{nome}.mp4 já existe; nada gerado")
    lf = P / "gasto.json"
    log = json.loads(lf.read_text()) if lf.exists() else {"teto": TETO, "saldo_inicio": saldo(), "itens": []}
    gasto = sum(i.get("custo") or 0 for i in log["itens"])
    seg = sum(i["segundos"] for i in log["itens"] if i.get("custo"))
    preco = (gasto / seg) if seg else 0.23  # sem medida ainda: usa o preço medido em 720p, o pior caso conhecido
    quem, dur, texto = CLIPES[n]
    previsto = preco * dur
    if gasto + previsto > TETO:
        sys.exit(f"PARADO: gasto {gasto:.3f} + previsto {previsto:.3f} passa do teto {TETO:.2f}")

    cache_f = P / "uploads.json"
    cache = json.loads(cache_f.read_text()) if cache_f.exists() else {}
    refs = [mn.subir_imagem(REF / f"{quem}.jpg", cache), mn.subir_imagem(REF / "portaria.jpg", cache)]
    cache_f.write_text(json.dumps(cache))

    prompt = f"{texto} {COMUM}"
    tid = str(uuid.uuid4())
    tarefa = {"taskType": "videoInference", "taskUUID": tid, "model": MODELOS[mod], "positivePrompt": prompt,
              "width": W, "height": H, "duration": dur, "numberResults": 1, "outputType": "URL",
              "outputFormat": "MP4", "deliveryMethod": "async", "includeCost": True,
              "inputs": {"referenceImages": refs}, "settings": {"audio": True}}
    (P / f"{nome}_prompt.txt").write_text(prompt)
    r = requests.post(API, headers=CAB, json=[tarefa], timeout=120)
    j = r.json()
    if r.status_code >= 300 or j.get("errors"):
        sys.exit("ERRO no envio (nada reenviado): " + json.dumps(j.get("errors", j), ensure_ascii=False)[:800])
    item = {"clipe": n, "modelo": MODELOS[mod], "segundos": dur, "taskUUID": tid, "custo": None}
    log["itens"].append(item)
    lf.write_text(json.dumps(log, indent=1))
    print(f"enviado {nome} ({tid}); previsto até US$ {previsto:.2f}", flush=True)

    fim = time.time() + 45 * 60
    while time.time() < fim:  # só consulta; nunca reenvia
        time.sleep(10)
        try:
            j = requests.post(API, headers=CAB, timeout=60, json=[{"taskType": "getResponse", "taskUUID": tid}]).json()
        except (requests.RequestException, ValueError):
            continue
        res = next((d for d in j.get("data", []) if d.get("taskUUID") == tid), {})
        if res.get("videoURL"):
            mn.baixar(res["videoURL"], P / f"{nome}.mp4")
            item["custo"] = res.get("cost")
            item["preco_s"] = round((res.get("cost") or 0) / dur, 4)
            lf.write_text(json.dumps(log, indent=1))
            print(f"ok {nome}: US$ {item['custo']} ({item['preco_s']}/s)", flush=True)
            return
        if res.get("status") in ("error", "failed") or j.get("errors"):
            sys.exit("FALHOU (nada reenviado): " + json.dumps(res or j.get("errors"), ensure_ascii=False)[:600])
    sys.exit(f"sem resultado em 45 min (nada reenviado); taskUUID {tid}")


if __name__ == "__main__":
    main()
