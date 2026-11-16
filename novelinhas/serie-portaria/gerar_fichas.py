#!/usr/bin/env python3
"""Fichas como a skill seedance-video pede: personagem em 3/4 com fundo cinza, e um cenário por ângulo de câmera.

Edita as referências atuais (mesmo rosto e figurino). Um envio por imagem, teto US$ 0,25. Não refaz o que já existe.
"""
import json
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import mininovela as mn  # noqa: E402

R = Path(__file__).resolve().parent / "referencias"
TETO = 0.25
FICHA = ("Same person as image 1: identical face, hair, age, skin and the exact same clothes and accessories. Waist-up "
         "portrait in a three-quarter view (body and face turned about 45 degrees to the camera's left), relaxed, mouth "
         "closed. Plain neutral mid-grey studio background, soft even frontal light, no strong shadows, no sun rays, no "
         "backlight. Photorealistic. No text.")
IMAGENS = [
    ("neide_3q", ["neide.jpg"], 1024, 1280, FICHA),
    ("soraia_3q", ["soraia.jpg"], 1024, 1280, FICHA),
    ("juninho_3q", ["juninho.jpg"], 1024, 1280, FICHA),
    ("entrada", ["portaria.jpg"], 1920, 1080,
     "REVERSE ANGLE of the same 1990s apartment building lobby as image 1, same colors, same warm night light, same "
     "materials. The camera now stands BEHIND the doorman counter at eye level and looks toward the entrance: the glass "
     "street door with the metal frame and the dark street at night outside, the worn brown leather sofa, the large fern "
     "in a clay pot, the standing fan, beige walls, terracotta floor tiles. The counter, the phone, the lamp, the TV, the "
     "mailboxes and the elevator are NOT visible (they are behind the camera). Empty lobby, no people, no parrot. "
     "Medium-wide view. Photorealistic, 1990s TV sitcom set. No text."),
]


def main():
    log_f = R / "gasto.json"
    log = json.loads(log_f.read_text())
    gasto = 0.0
    cache_f = R / "uploads_edicao.json"
    cache = json.loads(cache_f.read_text()) if cache_f.exists() else {}
    for nome, refs, w, h, prompt in IMAGENS:
        if (R / f"{nome}.jpg").exists():
            continue
        if gasto + 0.04 > TETO:
            sys.exit(f"PARADO antes de {nome}")
        ids = [mn.subir_imagem(R / r, cache) for r in refs]
        cache_f.write_text(json.dumps(cache))
        c = mn.gerar_imagem(prompt, R / f"{nome}.png", ids, w, h) or 0
        Image.open(R / f"{nome}.png").convert("RGB").save(R / f"{nome}.jpg", quality=92)
        (R / f"{nome}.png").unlink()
        (R / f"{nome}_prompt.txt").write_text(prompt)
        gasto += c
        log["itens"].append({"imagem": nome, "custo": c})
        log["total"] = round(sum(i["custo"] or 0 for i in log["itens"]), 5)
        log_f.write_text(json.dumps(log, indent=1, ensure_ascii=False))
        print(f"{nome}: US$ {c} | acumulado US$ {gasto:.3f}", flush=True)


if __name__ == "__main__":
    main()
