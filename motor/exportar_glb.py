"""Exporta a cozinha e os personagens do Blender para GLB (usado pela versão three.js em tempo real).

  blender -b -noaudio -P motor/exportar_glb.py      # -> tempo_real/cena.glb

Reaproveita motor/cena3d.py (mesmos modelos, cores e posições). Ficam de fora: fachada, luzes,
contornos (o three.js refaz o contorno) e os braços das poses (o three.js anima o braço de repouso).
"""
import bpy, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cena3d as C

C.construir()
fora = []
for nome, col in C.COL.items():
    if nome in ("fachada", "luz") or nome.startswith("prop_") or (nome.startswith("pose_") and not nome.endswith("_repouso")):
        fora += list(col.objects)
fora += [o for o in bpy.data.objects if o.name.endswith("_cont") or o.type not in ("MESH",)]
for o in set(fora):
    bpy.data.objects.remove(o, do_unlink=True)
# objetos da sala que nem aparecem por estarem dentro da parede (parede_alta/baixa não existem): nada a fazer
saida = os.path.join(C.DIR, "tempo_real", "cena.glb")
os.makedirs(os.path.dirname(saida), exist_ok=True)
bpy.ops.export_scene.gltf(filepath=saida, export_format="GLB", export_apply=True, export_yup=True,
                          export_lights=False, export_cameras=False, export_materials="EXPORT")
print("exportado:", saida, len(bpy.data.objects), "objetos")
