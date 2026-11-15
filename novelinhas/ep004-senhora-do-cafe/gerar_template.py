"""Teste do método de template (ep004): monta o prompt só com blocos fixos de templates.md + 1 linha de ação."""
import sys, re, json, requests
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import mininovela as mn

B = Path(__file__).resolve().parent; S = B / "storyboard"; R = B / "refs"
TETO = 0.10

def blocos():
    t = (B / "templates.md").read_text()
    return {m.group(1): m.group(2).strip() for m in re.finditer(r"<!-- BLOCO:(\w+) -->\n(.*?)\n<!-- FIM -->", t, re.S)}

def saldo():
    r = requests.post("https://api.runware.ai/v1", headers={"Authorization": "Bearer proxy-injected"}, timeout=60,
                      json=[{"taskType": "accountManagement", "taskUUID": "8a1c2a52-9d0e-4b8e-a1a1-1b2c3d4e5f71", "operation": "getDetails"}])
    return r.json()["data"][0]["balance"]

def montar(personagens, acao):
    b = blocos()
    return " ".join([b["ESTILO"], b["CENARIO"]] + [b[p] for p in personagens] + [b["ATUACAO"], "ACTION OF THIS SHOT: " + acao])

ACAO_P04 = ("MEDIUM shot, camera on the front side, slightly left of the coffee table. Ana has STOOD UP from her seat and stands in front of the RIGHT seat of the sofa, "
            "at the right end of the coffee table, body and face turned to screen RIGHT toward Helena, looking to the RIGHT, the closed blue folder held in her LEFT hand at her side, right arm relaxed. "
            "Paula still seated on the LEFT seat, PARTLY visible at the LEFT edge of the frame, looking down at her phone. "
            "At the RIGHT edge of the frame only the edge of Helena's grey cardigan sleeve and shoulder (her face out of frame). Ana's expression restrained and attentive.")

if __name__ == "__main__":
    saldo_antes = float(sys.argv[1])
    prompt = montar(["ANA", "PAULA", "HELENA"], ACAO_P04)
    if len(prompt) > 2900:  # gerar_imagem corta em 2900: nunca deixar a ação ser cortada
        sys.exit(f"PARADO: prompt com {len(prompt)} caracteres (> 2900); a linha de ação seria cortada")
    cache_f = B / "uploads.json"; cache = json.loads(cache_f.read_text())
    up = lambda p: mn.subir_imagem(Path(p), cache)
    refs = [up(S / "master.png"), up(R / "ref_ana.png"), up(R / "ref_paula.png"), up(R / "ref_helena.png")]
    cache_f.write_text(json.dumps(cache))
    est = 0.02 + 0.008 * len(refs); s = saldo()
    print(f"saldo {s:.5f} | debitado {saldo_antes - s:.5f} | estimado {est:.3f} | prompt {len(prompt)} chars", flush=True)
    if (saldo_antes - s) + est > TETO: sys.exit("PARADO: passaria do teto")
    custo = mn.gerar_imagem(prompt, S / "teste_template_p04.png", refs, 1920, 1080, 84004)
    (S / "teste_template_p04_prompt.txt").write_text(prompt)
    print("custo registrado", custo, "| saldo depois", saldo())
