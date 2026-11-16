#!/usr/bin/env python3
"""Teste de sincronia do Sigilo: plano 26 gerado no Seedance 2.5 Flash a partir da voz aprovada (M).

Um envio só, sem reenvio automático. Teto US$ 0,40. Só rodar com o "pode" do Lucas.
Se o Runware recusar o nome do campo de áudio, a recusa não custa nada: ajustar e rodar de novo.
"""
import base64
import json
import subprocess
import sys
import time
import uuid
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import mininovela as mn  # noqa: E402

B = Path(__file__).resolve().parent
P = B / "sincronia"
REF = B.parent / "referencias"
VOZ = B.parent / "voz_sigilo" / "M.mp3"
API = "https://api.runware.ai/v1"
CAB = {"Authorization": "Bearer proxy-injected"}
TETO = 0.40
DUR = 4

PROMPT = ("Close-up of the green parrot with a yellow face of @Image1, on its curved branch perch at the end of the "
          "dark wooden counter of @Image2; out of focus behind it, the metal mailboxes. @Audio1 is the parrot's own "
          "voice: the parrot says exactly the words of @Audio1, with the same timing, its beak opening and closing in "
          "sync with every syllable, head bobbing to the rhythm, and laughs at the end exactly when @Audio1 laughs. "
          "Nobody else speaks. 1990s TV sitcom look, warm studio lighting, rich saturated colors, subtle film grain, "
          "background softly out of focus. Static camera, one continuous shot, no cuts. Audio: only @Audio1 and soft "
          "room tone. No music, no laugh track. No subtitles, no text on screen.")


def preparar_audio():
    """Voz M sem silêncio nas pontas, começando em 0,4 s, completada até 4 s."""
    P.mkdir(exist_ok=True)
    saida = P / "voz_m_4s.mp3"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(VOZ), "-af",
                    "silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.05,areverse,"
                    "silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.1,areverse,"
                    f"adelay=400|400,apad,atrim=duration={DUR}", "-ar", "44100", "-ac", "1", "-b:a", "128k",
                    str(saida)], check=True)
    return saida


def main():
    if (P / "sigilo_sincronia.mp4").exists():
        sys.exit("já existe; nada gerado")
    audio = preparar_audio()
    cache_f = P / "uploads.json"
    cache = json.loads(cache_f.read_text()) if cache_f.exists() else {}
    refs = [mn.subir_imagem(REF / "sigilo.jpg", cache), mn.subir_imagem(REF / "portaria.jpg", cache)]
    cache_f.write_text(json.dumps(cache))
    tid = str(uuid.uuid4())
    tarefa = {"taskType": "videoInference", "taskUUID": tid, "model": "bytedance:seedance@2.5-flash",
              "positivePrompt": PROMPT, "width": 854, "height": 480, "duration": DUR, "numberResults": 1,
              "outputType": "URL", "outputFormat": "MP4", "deliveryMethod": "async", "includeCost": True,
              "inputs": {"referenceImages": refs,
                         "referenceAudios": ["data:audio/mpeg;base64," + base64.b64encode(audio.read_bytes()).decode()]},
              "settings": {"audio": True}}
    (P / "prompt.txt").write_text(PROMPT)
    if DUR * 0.068 > TETO:
        sys.exit("PARADO: previsto passa do teto")
    r = requests.post(API, headers=CAB, json=[tarefa], timeout=120)
    j = r.json()
    if r.status_code >= 300 or j.get("errors"):
        sys.exit("RECUSADO, sem custo (nada reenviado): " + json.dumps(j.get("errors", j), ensure_ascii=False)[:900])
    log = {"taskUUID": tid, "teto": TETO, "custo": None}
    (P / "gasto.json").write_text(json.dumps(log, indent=1))
    print("enviado", tid, flush=True)
    fim = time.time() + 45 * 60
    while time.time() < fim:  # só consulta; nunca reenvia
        time.sleep(10)
        try:
            j = requests.post(API, headers=CAB, timeout=60, json=[{"taskType": "getResponse", "taskUUID": tid}]).json()
        except (requests.RequestException, ValueError):
            continue
        res = next((d for d in j.get("data", []) if d.get("taskUUID") == tid), {})
        if res.get("videoURL"):
            mn.baixar(res["videoURL"], P / "sigilo_sincronia.mp4")
            log["custo"] = res.get("cost")
            (P / "gasto.json").write_text(json.dumps(log, indent=1))
            print("ok custo", log["custo"], flush=True)
            return
        if res.get("status") in ("error", "failed") or j.get("errors"):
            sys.exit("FALHOU (nada reenviado): " + json.dumps(res or j.get("errors"), ensure_ascii=False)[:600])
    sys.exit(f"sem resultado em 45 min (nada reenviado); taskUUID {tid}")


if __name__ == "__main__":
    main()
