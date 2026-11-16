#!/usr/bin/env python3
"""Edita/combina imagens de referência (Seedream), um envio. Uso: editar_ref.py <saida> <prompt> <ref1> [ref2...]"""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import mininovela as mn
from PIL import Image
R = Path(__file__).resolve().parent / "referencias"
saida, prompt, refs = sys.argv[1], sys.argv[2], sys.argv[3:]
cache_f = R / "uploads_edicao.json"; cache = json.loads(cache_f.read_text())
ids = [mn.subir_imagem(R / r, cache) for r in refs]; cache_f.write_text(json.dumps(cache))
c = mn.gerar_imagem(prompt, R / (saida + ".png"), ids, 1920, 1080)
Image.open(R / (saida + ".png")).convert("RGB").save(R / (saida + ".jpg"), quality=92); (R / (saida + ".png")).unlink()
(R / (saida + "_prompt.txt")).write_text(prompt)
g = json.loads((R / "gasto.json").read_text()); g["itens"].append({"imagem": saida, "custo": c})
g["total"] = round(sum(i["custo"] or 0 for i in g["itens"]), 5); (R / "gasto.json").write_text(json.dumps(g, indent=1, ensure_ascii=False))
print(saida, "custo", c)
