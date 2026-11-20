"""Cena 3D da sitcom (Blender 4.0, Cycles CPU).
Constrói cozinha + personagens e renderiza 'placas' (cenário por câmera) e 'sprites'
(personagem por pose, com sombra) — técnica de sprites pré-renderizados.

  blender -b -noaudio -P motor/cena3d.py -- teste                  # render rápido de checagem
  blender -b -noaudio -P motor/cena3d.py -- planejar               # gera render/jobs.json e render/projecoes.json
  blender -b -noaudio -P motor/cena3d.py -- jobs render/jobs.json  # executa a lista de renders (retomável)
"""
import bpy, bmesh, math, json, os, sys, time
from mathutils import Vector, Quaternion
from bpy_extras.object_utils import world_to_camera_view

DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # raiz do projeto
OUT = os.path.join(DIR, "render")
W, H = 1920, 1080

# ------------------------------------------------------------------ materiais
def lin(c):
    f = lambda v: (v / 255) / 12.92 if v / 255 <= 0.04045 else (((v / 255) + 0.055) / 1.055) ** 2.4
    return (f(c[0]), f(c[1]), f(c[2]), 1.0)

_mats = {}
def material(nome, cor, rough=0.55, metal=0.0, spec=0.5, coat=0.0, sheen=0.0):
    if nome in _mats: return _mats[nome]
    m = bpy.data.materials.new(nome); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = lin(cor); b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal; b.inputs["Specular IOR Level"].default_value = spec
    if coat: b.inputs["Coat Weight"].default_value = coat
    if sheen: b.inputs["Sheen Weight"].default_value = sheen
    _mats[nome] = m; return m

def mat_emissao(nome, cor, forca):
    m = bpy.data.materials.new(nome); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    e = nt.nodes.new("ShaderNodeEmission"); e.inputs[0].default_value = lin(cor); e.inputs[1].default_value = forca
    o = nt.nodes.new("ShaderNodeOutputMaterial"); nt.links.new(e.outputs[0], o.inputs[0]); return m

def mat_procedural(nome, tipo):
    """piso de tábuas, azulejo, parede com textura leve, madeira de armário, céu."""
    m = bpy.data.materials.new(nome); m.use_nodes = True; nt = m.node_tree
    b = nt.nodes["Principled BSDF"]; L = nt.links
    tc = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping"); L.new(tc.outputs["Object"], mp.inputs[0])
    if tipo in ("piso", "azulejo"):
        br = nt.nodes.new("ShaderNodeTexBrick"); L.new(mp.outputs[0], br.inputs["Vector"])
        if tipo == "piso":
            br.inputs["Color1"].default_value = lin((178, 122, 86)); br.inputs["Color2"].default_value = lin((160, 104, 72))
            br.inputs["Mortar"].default_value = lin((96, 60, 42)); br.inputs["Scale"].default_value = 1.0
            br.inputs["Mortar Size"].default_value = 0.006; br.inputs["Brick Width"].default_value = 1.3
            br.inputs["Row Height"].default_value = 0.2; br.offset = 0.37
            ns = nt.nodes.new("ShaderNodeTexNoise"); ns.inputs["Scale"].default_value = 18; ns.inputs["Detail"].default_value = 6
            mp2 = nt.nodes.new("ShaderNodeMapping"); mp2.inputs["Scale"].default_value = (0.15, 3.0, 1.0); L.new(tc.outputs["Object"], mp2.inputs[0])
            L.new(mp2.outputs[0], ns.inputs["Vector"])
            mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"; mix.blend_type = "MULTIPLY"; mix.inputs["Factor"].default_value = 0.35
            L.new(br.outputs["Color"], mix.inputs[6]); L.new(ns.outputs["Color"], mix.inputs[7]); L.new(mix.outputs[2], b.inputs["Base Color"])
            b.inputs["Roughness"].default_value = 0.38
        else:
            br.inputs["Color1"].default_value = lin((240, 220, 190)); br.inputs["Color2"].default_value = lin((234, 212, 180))
            br.inputs["Mortar"].default_value = lin((210, 186, 152)); br.inputs["Scale"].default_value = 1.0
            br.inputs["Mortar Size"].default_value = 0.008; br.inputs["Brick Width"].default_value = 0.15
            br.inputs["Row Height"].default_value = 0.15; br.offset = 0.0
            L.new(br.outputs["Color"], b.inputs["Base Color"]); b.inputs["Roughness"].default_value = 0.25
        bp = nt.nodes.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = 0.4; bp.invert = True
        L.new(br.outputs["Fac"], bp.inputs["Height"]); L.new(bp.outputs["Normal"], b.inputs["Normal"])
    elif tipo in ("parede", "armario"):
        ns = nt.nodes.new("ShaderNodeTexNoise"); ns.inputs["Scale"].default_value = 6 if tipo == "parede" else 3
        ns.inputs["Detail"].default_value = 4
        if tipo == "armario": mp.inputs["Scale"].default_value = (1.0, 1.0, 14.0)
        L.new(mp.outputs[0], ns.inputs["Vector"])
        cr = nt.nodes.new("ShaderNodeValToRGB"); L.new(ns.outputs["Fac"], cr.inputs[0])
        c0, c1 = ((236, 216, 186), (248, 232, 206)) if tipo == "parede" else ((136, 92, 62), (162, 114, 80))
        cr.color_ramp.elements[0].color = lin(c0); cr.color_ramp.elements[1].color = lin(c1)
        cr.color_ramp.elements[0].position = 0.35; cr.color_ramp.elements[1].position = 0.65
        L.new(cr.outputs["Color"], b.inputs["Base Color"]); b.inputs["Roughness"].default_value = 0.85 if tipo == "parede" else 0.45
    return m

def mat_ceu():
    m = bpy.data.materials.new("ceu"); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear(); L = nt.links
    tc = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Generated"], sep.inputs[0])
    mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs["From Min"].default_value = 0.25; mr.inputs["From Max"].default_value = 0.85
    L.new(sep.outputs["Y"], mr.inputs["Value"])
    cr = nt.nodes.new("ShaderNodeValToRGB"); L.new(mr.outputs["Result"], cr.inputs[0])
    cr.color_ramp.elements[0].color = lin((222, 238, 250)); cr.color_ramp.elements[1].color = lin((86, 156, 228))
    e = nt.nodes.new("ShaderNodeEmission"); e.inputs[1].default_value = 2.2; L.new(cr.outputs["Color"], e.inputs[0])
    o = nt.nodes.new("ShaderNodeOutputMaterial"); L.new(e.outputs[0], o.inputs[0]); return m

def mat_contorno():
    m = bpy.data.materials.new("contorno"); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear(); L = nt.links
    g = nt.nodes.new("ShaderNodeNewGeometry"); e = nt.nodes.new("ShaderNodeEmission")
    e.inputs[0].default_value = lin((48, 32, 30)); e.inputs[1].default_value = 1.0
    t = nt.nodes.new("ShaderNodeBsdfTransparent"); mx = nt.nodes.new("ShaderNodeMixShader"); o = nt.nodes.new("ShaderNodeOutputMaterial")
    L.new(g.outputs["Backfacing"], mx.inputs[0]); L.new(e.outputs[0], mx.inputs[1]); L.new(t.outputs[0], mx.inputs[2])
    L.new(mx.outputs[0], o.inputs[0]); return m

# ------------------------------------------------------------------ geometria
COL = {}
def colecao(nome):
    if nome not in COL:
        c = bpy.data.collections.new(nome); bpy.context.scene.collection.children.link(c); COL[nome] = c
    return COL[nome]

def ligar(ob, col):
    colecao(col).objects.link(ob); return ob

def caixa(nome, x0, x1, y0, y1, z0, z1, mat, col="sala", bevel=0.0, seg=3):
    me = bpy.data.meshes.new(nome); bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0); bm.to_mesh(me); bm.free()
    from mathutils import Matrix
    me.transform(Matrix.Diagonal((x1 - x0, y1 - y0, z1 - z0, 1.0)))
    ob = bpy.data.objects.new(nome, me); ob.location = ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)
    me.materials.append(mat); ligar(ob, col)
    if bevel:
        md = ob.modifiers.new("bev", "BEVEL"); md.width = bevel; md.segments = seg; md.limit_method = "NONE"
        for p in me.polygons: p.use_smooth = True
    return ob

def plano(nome, w, h, co, rot, mat, col="sala"):
    me = bpy.data.meshes.new(nome); bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=0.5); bmesh.ops.scale(bm, vec=(w, h, 1), verts=bm.verts)
    bm.to_mesh(me); bm.free(); ob = bpy.data.objects.new(nome, me); ob.location = co; ob.rotation_euler = rot
    me.materials.append(mat); return ligar(ob, col)

def esfera(nome, r, co, mat, col, escala=(1, 1, 1), seg=48, aneis=24):
    me = bpy.data.meshes.new(nome); bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=aneis, radius=r)
    bmesh.ops.scale(bm, vec=escala, verts=bm.verts); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    ob = bpy.data.objects.new(nome, me); ob.location = co; me.materials.append(mat); return ligar(ob, col)

def cilindro(nome, r1, r2, h, co, mat, col, rot=(0, 0, 0), seg=40, tampa=True):
    me = bpy.data.meshes.new(nome); bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=tampa, cap_tris=False, segments=seg, radius1=r1, radius2=r2, depth=h)
    bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    ob = bpy.data.objects.new(nome, me); ob.location = co; ob.rotation_euler = rot; me.materials.append(mat); return ligar(ob, col)

def toro(nome, R, r, co, mat, col, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=r, major_segments=48, minor_segments=12, location=co, rotation=rot)
    ob = bpy.context.object; ob.name = nome; ob.data.materials.append(mat)
    for c in ob.users_collection: c.objects.unlink(ob)
    for p in ob.data.polygons: p.use_smooth = True
    return ligar(ob, col)

def cortar(ob, ponto, normal):
    bm = bmesh.new(); bm.from_mesh(ob.data); local = Vector(ponto) - ob.location
    bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=local, plane_no=normal, clear_inner=True)
    bm.to_mesh(ob.data); bm.free()

# metaballs (formas "de massinha") convertidas para malha
FATOR = None
def _calibrar():
    global FATOR
    mb = bpy.data.metaballs.new("cal"); mb.resolution = 0.02; ob = bpy.data.objects.new("cal", mb)
    bpy.context.scene.collection.objects.link(ob); el = mb.elements.new(); el.radius = 1.0; el.co = (0, 0, 0)
    dg = bpy.context.evaluated_depsgraph_get(); me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    FATOR = max(abs(v.co.x) for v in me.vertices); bpy.data.objects.remove(ob); bpy.data.meshes.remove(me)

def massa(nome, elementos, mat, col, res=0.008):
    if FATOR is None: _calibrar()
    mb = bpy.data.metaballs.new(nome); mb.resolution = res; mb.render_resolution = res
    ob = bpy.data.objects.new(nome, mb); bpy.context.scene.collection.objects.link(ob)
    for e in elementos:
        el = mb.elements.new(); el.type = e.get("tipo", "BALL"); el.co = e["co"]; el.radius = e["r"] / FATOR
        for k in ("size_x", "size_y", "size_z"):
            if k in e: setattr(el, k, e[k])
        if "rot" in e: el.rotation = e["rot"]
    dg = bpy.context.evaluated_depsgraph_get(); me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    bpy.data.objects.remove(ob); bpy.data.metaballs.remove(mb)
    for p in me.polygons: p.use_smooth = True
    obm = bpy.data.objects.new(nome, me); me.materials.append(mat); return ligar(obm, col)

def capsula_el(a, b, r):
    a, b = Vector(a), Vector(b); d = b - a
    q = Vector((1, 0, 0)).rotation_difference(d.normalized())
    return dict(tipo="CAPSULE", co=tuple((a + b) / 2), r=r, size_x=d.length / 2, rot=q)

CONTORNO = None
def contorno(ob, esp=0.009):
    dg = bpy.context.evaluated_depsgraph_get(); me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    bm = bmesh.new(); bm.from_mesh(me); bm.normal_update()
    for v in bm.verts: v.co += v.normal * esp
    bmesh.ops.reverse_faces(bm, faces=bm.faces[:]); bm.to_mesh(me); bm.free()
    me.materials.clear(); me.materials.append(CONTORNO)
    for p in me.polygons: p.use_smooth = True
    dup = bpy.data.objects.new(ob.name + "_cont", me); dup.matrix_world = ob.matrix_world.copy()
    for k in ("visible_shadow", "visible_diffuse", "visible_glossy", "visible_transmission", "visible_volume_scatter"):
        setattr(dup, k, False)
    for c in ob.users_collection: c.objects.link(dup)
    return dup

# ------------------------------------------------------------------ cozinha
# Cenário de sitcom: três paredes, porta com corredor ao fundo (entradas), mesa sob a janela,
# bancada com pia e fogão, objetos de cena. Coordenadas: x direita, y fundo, z cima; parede em y=1.6.
JX0, JX1, JZ0, JZ1 = -0.55, 0.65, 1.15, 2.05          # janela
DX0, DX1, DZ1 = 1.5, 2.4, 2.12                         # porta (atrás da marca da Dona Neide)
BX0 = 2.55                                             # início da bancada
MESA = (0.05, 0.95)                                    # centro da mesa (x, y)
LUMINARIA = (0.05, 0.95)                               # pendente em cima da mesa

def sala():
    mp, mt = mat_procedural("parede", "parede"), mat_procedural("azulejo", "azulejo")
    piso = mat_procedural("piso", "piso"); arm = mat_procedural("armario", "armario")
    branco = material("branco", (250, 246, 238), 0.4); geladeira = material("geladeira", (238, 242, 246), 0.22, coat=0.3)
    metal = material("metal", (180, 186, 196), 0.25, metal=1.0); tampo = material("tampo", (228, 226, 220), 0.2)
    inox = material("inox", (196, 200, 206), 0.18, metal=1.0); preto = material("preto", (30, 30, 34), 0.15, coat=0.6)
    plano("piso", 11, 8, (0.2, -1.0, 0), (0, 0, 0), piso)
    # parede do fundo com os vãos da janela e da porta
    for nome, x0, x1, z0, z1 in (("p_esq", -4.6, JX0, 1.0, 3.0), ("p_baixo", JX0, JX1, 1.0, JZ0), ("p_cima", JX0, JX1, JZ1, 3.0),
                                 ("p_dir", JX1, DX0, 1.0, 3.0), ("p_porta_cima", DX0, DX1, DZ1, 3.0), ("p_dir2", DX1, 5.2, 1.0, 3.0)):
        caixa(nome, x0, x1, 1.6, 1.75, z0, z1, mp)
    for suf, x0, x1 in (("", -4.6, DX0), ("2", DX1, 5.2)):
        caixa("azulejos" + suf, x0, x1, 1.6, 1.75, 0, 1.0, mt)
        xf = min(x1, BX0) if suf else x1                                 # atrás da bancada não tem friso
        caixa("friso" + suf, x0, xf, 1.57, 1.62, 0.97, 1.03, branco, bevel=0.008)
        caixa("rodape" + suf, x0, xf, 1.56, 1.62, 0, 0.1, branco, bevel=0.006)
    caixa("parede_e", -4.75, -4.6, -4, 1.75, 0, 3, mp); caixa("parede_d", 5.2, 5.35, -4, 1.75, 0, 3, mp)
    # lambri, friso e rodapé também nas paredes laterais (a da direita fica atrás da bancada)
    caixa("lambri_e", -4.6, -4.58, -4, 1.6, 0, 1.0, mt)
    caixa("friso_e", -4.6, -4.55, -4, 1.57, 0.97, 1.03, branco, bevel=0.008)
    caixa("rodape_e", -4.6, -4.56, -4, 1.56, 0, 0.1, branco, bevel=0.006)
    caixa("lambri_d", 5.18, 5.2, -4, 0.95, 0, 1.0, mt)
    caixa("friso_d", 5.15, 5.2, -4, 0.95, 0.97, 1.03, branco, bevel=0.008)
    caixa("rodape_d", 5.16, 5.2, -4, 0.95, 0, 0.1, branco, bevel=0.006)
    caixa("teto", -4.75, 5.35, -4, 3.6, 2.95, 3.05, branco)
    # janela, cortinas e vista pintada (o three.js pinta a cidade no plano do "céu")
    for nome, x0, x1, z0, z1 in (("jan_e", JX0 - 0.06, JX0 + 0.02, JZ0 - 0.06, JZ1 + 0.06), ("jan_d", JX1 - 0.02, JX1 + 0.06, JZ0 - 0.06, JZ1 + 0.06),
                                 ("jan_c", JX0 - 0.06, JX1 + 0.06, JZ1 - 0.02, JZ1 + 0.06), ("jan_b", JX0 - 0.06, JX1 + 0.06, JZ0 - 0.06, JZ0 + 0.02),
                                 ("jan_m", (JX0 + JX1) / 2 - 0.025, (JX0 + JX1) / 2 + 0.025, JZ0, JZ1)):
        caixa(nome, x0, x1, 1.58, 1.66, z0, z1, branco, bevel=0.01)
    caixa("peitoril", JX0 - 0.12, JX1 + 0.12, 1.5, 1.66, JZ0 - 0.09, JZ0 - 0.04, branco, bevel=0.01)
    plano("ceu", 14, 8, (0.0, 4.5, 1.5), (math.radians(90), 0, 0), mat_ceu())
    tecido = material("cortina", (226, 112, 92), 0.8, sheen=0.6)
    for s, cx in ((-1, JX0 - 0.12), (1, JX1 + 0.12)):
        me = bpy.data.meshes.new("cortina"); bm = bmesh.new()
        bmesh.ops.create_grid(bm, x_segments=40, y_segments=4, size=0.5); bm.to_mesh(me); bm.free()
        for v in me.vertices:
            u = v.co.x + 0.5; v.co.x = (u - 0.5) * 0.36; v.co.z = 0.04 * math.sin(u * math.pi * 7); v.co.y *= 1.15
        ob = bpy.data.objects.new("cortina", me); ob.location = (cx, 1.5, 1.55); ob.rotation_euler = (math.radians(90), 0, 0)
        me.materials.append(tecido); ligar(ob, "sala")
        md = ob.modifiers.new("s", "SOLIDIFY"); md.thickness = 0.01
        for p in me.polygons: p.use_smooth = True
    cilindro("varao", 0.018, 0.018, 1.9, ((JX0 + JX1) / 2, 1.48, 2.2), metal, "sala", rot=(0, math.radians(90), 0))
    for vx in ((JX0 + JX1) / 2 - 0.95, (JX0 + JX1) / 2 + 0.95): esfera("ponteira", 0.03, (vx, 1.48, 2.2), metal, "sala")
    # geladeira (mesmo lugar: as etiquetas, o cadeado e o quadro dependem dela)
    caixa("gel_corpo", -3.0, -2.3, 0.9, 1.6, 0.0, 1.29, geladeira, bevel=0.05, seg=4)
    caixa("gel_freezer", -3.0, -2.3, 0.9, 1.6, 1.31, 1.86, geladeira, bevel=0.05, seg=4)
    caixa("gel_vao", -2.98, -2.32, 0.92, 1.58, 1.28, 1.32, material("vao", (70, 70, 76), 0.6))
    for nome, z0, z1 in (("gel_puxador1", 1.42, 1.72), ("gel_puxador2", 0.78, 1.18)):
        caixa(nome, -2.42, -2.37, 0.82, 0.86, z0, z1, metal, bevel=0.012)
        for zz in (z0 + 0.02, z1 - 0.02): caixa(nome + "_p", -2.42, -2.38, 0.85, 0.9, zz - 0.012, zz + 0.012, metal)
    # aparador com filtro de barro e fruteira (entre a geladeira e a Clara)
    caixa("aparador", -2.15, -1.45, 1.22, 1.6, 0.08, 0.86, arm, bevel=0.01)
    caixa("aparador_tampo", -2.18, -1.42, 1.19, 1.6, 0.86, 0.9, arm, bevel=0.006)
    for i, x in enumerate((-2.13, -1.8)):
        caixa(f"aparador_porta{i}", x, x + 0.32, 1.2, 1.22, 0.14, 0.8, arm, bevel=0.008)
        esfera(f"aparador_pux{i}", 0.014, (x + (0.28 if i == 0 else 0.04), 1.19, 0.6), metal, "sala")
    barro = material("barro", (176, 92, 58), 0.85)
    cilindro("filtro_base", 0.12, 0.11, 0.2, (-1.98, 1.42, 1.0), barro, "sala")
    cilindro("filtro_cima", 0.125, 0.12, 0.2, (-1.98, 1.42, 1.21), barro, "sala")
    esfera("filtro_tampa", 0.12, (-1.98, 1.42, 1.31), barro, "sala", escala=(1, 1, 0.45))
    esfera("filtro_pegador", 0.025, (-1.98, 1.42, 1.37), barro, "sala")
    cilindro("filtro_torneira", 0.012, 0.012, 0.07, (-1.98, 1.28, 0.97), material("torneira_branca", (240, 240, 236), 0.3), "sala", rot=(math.radians(90), 0, 0))
    tigela = material("tigela", (240, 240, 234), 0.25)
    esf = esfera("tigela", 0.13, (-1.66, 1.4, 0.95), tigela, "sala", escala=(1, 1, 0.5)); cortar(esf, Vector((-1.66, 1.4, 0.95)), Vector((0, 0, -1)))
    esf.modifiers.new("s", "SOLIDIFY").thickness = 0.01
    for i, (fx, fy, c) in enumerate(((-1.72, 1.39, (230, 70, 60)), (-1.62, 1.35, (250, 200, 60)), (-1.6, 1.44, (120, 180, 80)), (-1.69, 1.45, (240, 150, 50)))):
        esfera(f"fruta{i}", 0.045, (fx, fy, 0.99), material(f"fruta{i}", c, 0.35), "sala")
    # prateleira com livros e planta (longe da cortina) e calendário
    caixa("prateleira", -2.15, -1.05, 1.36, 1.6, 1.86, 1.9, arm, bevel=0.006)
    for i, (bx, c, bh) in enumerate(((-2.08, (200, 80, 70), 0.24), (-2.01, (80, 110, 170), 0.27), (-1.94, (230, 190, 80), 0.21), (-1.86, (110, 150, 110), 0.25))):
        caixa(f"livro{i}", bx, bx + 0.065, 1.4, 1.57, 1.9, 1.9 + bh, material(f"livro{i}", c, 0.6), bevel=0.006)
    vaso = material("vaso", (204, 112, 70), 0.6); folha = material("folha", (86, 158, 88), 0.5)
    cilindro("vaso", 0.07, 0.09, 0.16, (-1.3, 1.47, 1.98), vaso, "sala")
    for i, (dx, dz, ang) in enumerate(((0, 0.17, 0), (-0.08, 0.12, -40), (0.08, 0.12, 40), (-0.05, 0.2, -20), (0.05, 0.2, 20))):
        esfera(f"folha{i}", 0.06, (-1.3 + dx, 1.47, 1.98 + dz), folha, "sala", escala=(0.6, 0.35, 1.3)).rotation_euler = (0, math.radians(ang), 0)
    plano("calendario", 0.3, 0.42, (-1.62, 1.595, 1.42), (math.radians(90), 0, 0), material("calendario", (250, 250, 245), 0.7))
    # relógio entre a janela e a porta (antes ficava atrás do varão da cortina)
    RX, RZ = 1.1, 2.4
    cilindro("relogio", 0.15, 0.15, 0.04, (RX, 1.57, RZ), material("relogio", (252, 250, 244), 0.3), "sala", rot=(math.radians(90), 0, 0))
    toro("relogio_aro", 0.15, 0.016, (RX, 1.55, RZ), material("aro", (60, 50, 50), 0.4), "sala", rot=(math.radians(90), 0, 0))
    ponteiro = material("ponteiro", (40, 36, 36), 0.5)
    caixa("ponteiro_h", RX - 0.01, RX + 0.01, 1.54, 1.545, RZ, RZ + 0.08, ponteiro); caixa("ponteiro_m", RX, RX + 0.09, 1.538, 1.543, RZ - 0.01, RZ + 0.01, ponteiro)
    for k in range(12):
        a = math.radians(k * 30); cx, cz = RX + 0.125 * math.sin(a), RZ + 0.125 * math.cos(a)
        caixa(f"marca{k}", cx - 0.006, cx + 0.006, 1.545, 1.55, cz - 0.011, cz + 0.011, ponteiro)
    # porta com batente e corredor ao fundo (de onde os personagens entram)
    for nome, x0, x1, z0, z1 in (("batente_e", DX0 - 0.08, DX0, 0, DZ1 + 0.08), ("batente_d", DX1, DX1 + 0.08, 0, DZ1 + 0.08),
                                 ("batente_c", DX0 - 0.08, DX1 + 0.08, DZ1, DZ1 + 0.08)):
        caixa(nome, x0, x1, 1.56, 1.62, z0, z1, branco, bevel=0.008)
    for nome, x0, x1, z0, z1 in (("forra_e", DX0, DX0 + 0.02, 0, DZ1), ("forra_d", DX1 - 0.02, DX1, 0, DZ1), ("forra_c", DX0, DX1, DZ1 - 0.02, DZ1)):
        caixa(nome, x0, x1, 1.6, 1.75, z0, z1, branco)
    porta = material("porta", (122, 168, 176), 0.5)                        # porta pintada (azul-acinzentado)
    caixa("porta_folha", DX0 + 0.02, DX0 + 0.06, 1.76, 2.62, 0.01, DZ1 - 0.03, porta, bevel=0.006)
    for zz in (0.25, 1.15):
        caixa(f"porta_almofada{zz}", DX0 + 0.06, DX0 + 0.07, 1.86, 2.52, zz, zz + 0.75, porta, bevel=0.004)
    esfera("macaneta", 0.028, (DX0 + 0.09, 2.5, 1.0), material("latao", (200, 160, 80), 0.25, metal=1.0), "sala")
    CX0, CX1, CY1 = 1.15, 2.95, 3.5
    corr = material("corredor", (214, 226, 232), 0.85); piso_c = material("piso_corredor", (150, 104, 72), 0.45)
    caixa("corredor_piso", CX0, CX1, 1.75, CY1, -0.02, 0.0, piso_c)
    caixa("corredor_pe", CX0 - 0.1, CX0, 1.75, CY1, 0, 2.95, corr); caixa("corredor_pd", CX1, CX1 + 0.1, 1.75, CY1, 0, 2.95, corr)
    caixa("corredor_fundo", CX0 - 0.1, CX1 + 0.1, CY1, CY1 + 0.1, 0, 2.95, corr)
    caixa("corredor_rodape", CX0, CX1, CY1 - 0.02, CY1, 0, 0.1, branco)
    plano("quadro_corredor", 0.7, 0.5, ((CX0 + CX1) / 2 + 0.15, CY1 - 0.01, 1.55), (math.radians(90), 0, 0), material("pintura2", (200, 200, 200), 0.6))
    caixa("quadro_corredor_moldura", (CX0 + CX1) / 2 - 0.23, (CX0 + CX1) / 2 + 0.53, CY1 - 0.005, CY1, 1.27, 1.83, material("moldura_madeira", (90, 60, 40), 0.5))
    caixa("aparador_corredor", CX1 - 0.6, CX1 - 0.05, CY1 - 0.35, CY1, 0.75, 0.8, arm, bevel=0.006)
    for lx in (CX1 - 0.55, CX1 - 0.1):
        caixa(f"aparador_corredor_pe{lx}", lx, lx + 0.04, CY1 - 0.33, CY1 - 0.29, 0, 0.75, arm)
    cilindro("abajur_pe", 0.012, 0.012, 0.3, (CX1 - 0.3, CY1 - 0.18, 0.95), metal, "sala")
    cilindro("abajur_cupula", 0.13, 0.08, 0.16, (CX1 - 0.3, CY1 - 0.18, 1.15), material("abajur", (250, 232, 196), 0.6), "sala", tampa=False).modifiers.new("s", "SOLIDIFY").thickness = 0.005
    cilindro("cabideiro", 0.015, 0.015, 1.7, (CX0 + 0.2, CY1 - 0.25, 0.85), arm, "sala")
    esfera("cabideiro_chapeu", 0.14, (CX0 + 0.2, CY1 - 0.25, 1.72), material("chapeu", (150, 70, 60), 0.7), "sala", escala=(1, 1, 0.45))
    massa("casaco", [capsula_el((CX0 + 0.2, CY1 - 0.18, 1.55), (CX0 + 0.22, CY1 - 0.12, 0.95), 0.11)], material("casaco", (92, 110, 150), 0.8), "sala")
    # mesa com toalha xadrez e cadeiras, sob a janela; o pote de iogurte vazio é a "prova"
    mx, my = MESA; mw, md, mh = 0.45, 0.35, 0.76
    madeira_mesa = material("mesa", (176, 128, 86), 0.5)
    for sx in (-1, 1):
        for sy in (-1, 1):
            caixa(f"mesa_pe{sx}{sy}", mx + sx * (mw - 0.06) - 0.025, mx + sx * (mw - 0.06) + 0.025, my + sy * (md - 0.06) - 0.025, my + sy * (md - 0.06) + 0.025, 0, mh - 0.03, madeira_mesa)
    caixa("mesa_tampo", mx - mw, mx + mw, my - md, my + md, mh - 0.03, mh, madeira_mesa, bevel=0.006)
    toalha = material("toalha", (220, 60, 60), 0.85)
    caixa("toalha", mx - mw - 0.04, mx + mw + 0.04, my - md - 0.04, my + md + 0.04, mh, mh + 0.006, toalha)
    for nome, x0, x1, y0, y1 in (("toalha_f", mx - mw - 0.04, mx + mw + 0.04, my - md - 0.045, my - md - 0.04),
                                 ("toalha_t", mx - mw - 0.04, mx + mw + 0.04, my + md + 0.04, my + md + 0.045),
                                 ("toalha_e", mx - mw - 0.045, mx - mw - 0.04, my - md - 0.04, my + md + 0.04),
                                 ("toalha_d", mx + mw + 0.04, mx + mw + 0.045, my - md - 0.04, my + md + 0.04)):
        caixa(nome, x0, x1, y0, y1, mh - 0.2, mh + 0.006, toalha)
    cadeira = material("cadeira", (200, 84, 70), 0.55)
    for lado in (-1, 1):
        cx = mx + lado * (mw + 0.22)
        caixa(f"cadeira_assento{lado}", cx - 0.21, cx + 0.21, my - 0.21, my + 0.21, 0.43, 0.47, cadeira, bevel=0.008)
        for sx in (-1, 1):
            for sy in (-1, 1):
                caixa(f"cadeira_pe{lado}{sx}{sy}", cx + sx * 0.17 - 0.02, cx + sx * 0.17 + 0.02, my + sy * 0.17 - 0.02, my + sy * 0.17 + 0.02, 0, 0.43, cadeira)
        ex = cx + lado * 0.19                                         # encosto do lado de fora
        for sy in (-1, 1): caixa(f"cadeira_poste{lado}{sy}", ex - 0.02, ex + 0.02, my + sy * 0.17 - 0.02, my + sy * 0.17 + 0.02, 0.47, 0.95, cadeira)
        for zz in (0.68, 0.85): caixa(f"cadeira_ripa{lado}{zz}", ex - 0.015, ex + 0.015, my - 0.17, my + 0.17, zz, zz + 0.07, cadeira, bevel=0.006)
    pote = material("pote_iogurte", (250, 248, 240), 0.35)
    cilindro("pote_iogurte", 0.042, 0.034, 0.1, (mx - 0.1, my - 0.12, mh + 0.056), pote, "sala")
    cilindro("pote_rotulo", 0.0425, 0.036, 0.05, (mx - 0.1, my - 0.12, mh + 0.06), material("rotulo_iogurte", (240, 120, 150), 0.5), "sala", tampa=False)
    caixa("colher", mx - 0.02, mx + 0.11, my - 0.16, my - 0.15, mh + 0.006, mh + 0.012, inox, bevel=0.003)
    cilindro("garrafa_termica", 0.055, 0.055, 0.28, (mx + 0.22, my + 0.12, mh + 0.146), material("garrafa", (220, 70, 60), 0.3, coat=0.5), "sala")
    cilindro("garrafa_tampa", 0.03, 0.04, 0.05, (mx + 0.22, my + 0.12, mh + 0.31), material("preto_fosco", (40, 40, 40), 0.5), "sala")
    cilindro("vasinho", 0.045, 0.035, 0.1, (mx - 0.02, my + 0.15, mh + 0.056), material("vaso_azul", (70, 110, 170), 0.3, coat=0.4), "sala")
    for i, (dx, dz) in enumerate(((0, 0.17), (-0.04, 0.15), (0.04, 0.155))):
        cilindro(f"flor_haste{i}", 0.004, 0.004, 0.12, (mx - 0.02 + dx * 0.5, my + 0.15, mh + 0.15), folha, "sala")
        esfera(f"flor{i}", 0.026, (mx - 0.02 + dx, my + 0.15, mh + dz + 0.06), material(f"flor{i}", ((250, 200, 60), (240, 110, 130), (250, 250, 245))[i], 0.6), "sala")
    # luminária pendente em cima da mesa
    lx, ly = LUMINARIA
    cilindro("fio", 0.006, 0.006, 0.7, (lx, ly, 2.6), material("fio", (40, 40, 40), 0.5), "sala")
    cupula = material("cupula", (70, 122, 112), 0.35)
    cp = cilindro("cupula", 0.24, 0.07, 0.22, (lx, ly, 2.15), cupula, "sala", tampa=False)
    cp.modifiers.new("s", "SOLIDIFY").thickness = 0.01
    esfera("lampada", 0.05, (lx, ly, 2.08), mat_emissao("lampada", (255, 236, 190), 25.0), "sala")
    # bancada: pia com escorredor, fogão com coifa, azulejos decorados atrás
    BX1 = 5.18
    caixa("balcao", BX0, BX1, 0.95, 1.6, 0.0, 0.88, arm, bevel=0.01)
    caixa("rodape_balcao", BX0 + 0.02, BX1, 0.99, 1.6, 0.0, 0.08, material("rodape_escuro", (70, 52, 40), 0.6))
    PX0, PX1 = 3.0, 3.6                                                       # cuba
    for nome, x0, x1, y0, y1 in (("tampo", BX0 - 0.05, PX0, 0.9, 1.6), ("tampo2", PX1, BX1, 0.9, 1.6),
                                 ("tampo_f", PX0, PX1, 0.9, 1.0), ("tampo_t", PX0, PX1, 1.48, 1.6)):
        caixa(nome, x0, x1, y0, y1, 0.88, 0.94, tampo, bevel=0.006)
    cuba = material("cuba", (170, 176, 184), 0.3, metal=1.0)
    caixa("cuba_fundo", PX0, PX1, 1.0, 1.48, 0.74, 0.75, cuba)
    for nome, x0, x1, y0, y1 in (("cuba_f", PX0, PX1, 1.0, 1.01), ("cuba_t", PX0, PX1, 1.47, 1.48), ("cuba_e", PX0, PX0 + 0.01, 1.0, 1.48), ("cuba_d", PX1 - 0.01, PX1, 1.0, 1.48)):
        caixa(nome, x0, x1, y0, y1, 0.74, 0.94, cuba)
    tm = (PX0 + PX1) / 2
    cilindro("torneira", 0.016, 0.016, 0.28, (tm, 1.54, 1.08), inox, "sala")
    cilindro("torneira_bico", 0.013, 0.013, 0.18, (tm, 1.46, 1.21), inox, "sala", rot=(math.radians(90), 0, 0))
    cilindro("torneira_registro", 0.02, 0.02, 0.05, (tm + 0.07, 1.54, 0.97), inox, "sala")
    caixa("escorredor", 3.68, 4.0, 1.12, 1.46, 0.94, 0.95, inox)
    for k in range(5): caixa(f"escorredor_grade{k}", 3.68, 4.0, 1.12 + k * 0.08, 1.125 + k * 0.08, 0.95, 1.06, inox)
    prato = material("prato", (248, 248, 244), 0.2, coat=0.6)
    for k, x in enumerate((3.74, 3.8, 3.86)):
        pr = cilindro(f"prato{k}", 0.11, 0.11, 0.012, (x, 1.29, 1.06), prato, "sala", rot=(0, math.radians(75), 0))
    cilindro("copo_escorredor", 0.035, 0.03, 0.1, (3.95, 1.4, 1.0), material("copo", (180, 210, 230), 0.1, coat=0.8), "sala")
    FX0, FX1 = 4.2, 4.8                                                       # fogão (cooktop + forno)
    caixa("cooktop", FX0, FX1, 0.98, 1.55, 0.94, 0.95, preto)
    for k, (bx, by, r) in enumerate(((FX0 + 0.15, 1.12, 0.07), (FX0 + 0.43, 1.12, 0.06), (FX0 + 0.15, 1.4, 0.06), (FX0 + 0.43, 1.4, 0.08))):
        toro(f"boca{k}", r, 0.008, (bx, by, 0.955), material("boca", (70, 70, 74), 0.4), "sala")
    caixa("forno", FX0, FX1, 0.93, 0.95, 0.12, 0.82, preto)
    caixa("forno_vidro", FX0 + 0.06, FX1 - 0.06, 0.925, 0.93, 0.22, 0.6, material("vidro_forno", (20, 22, 26), 0.05, coat=1.0))
    caixa("forno_puxador", FX0 + 0.08, FX1 - 0.08, 0.89, 0.91, 0.66, 0.68, inox, bevel=0.004)
    for k in range(4): cilindro(f"botao_fogao{k}", 0.018, 0.018, 0.025, (FX0 + 0.12 + k * 0.12, 0.915, 0.76), inox, "sala", rot=(math.radians(90), 0, 0))
    panela = material("panela", (200, 60, 50), 0.3, coat=0.5)
    cilindro("panela", 0.1, 0.1, 0.12, (FX0 + 0.15, 1.12, 1.015), panela, "sala")
    esfera("panela_tampa", 0.1, (FX0 + 0.15, 1.12, 1.075), panela, "sala", escala=(1, 1, 0.25))
    cilindro("chaleira", 0.08, 0.06, 0.13, (FX0 + 0.43, 1.4, 1.02), inox, "sala")
    caixa("coifa", FX0 - 0.05, FX1 + 0.05, 1.15, 1.6, 1.68, 1.82, inox, bevel=0.01)
    caixa("coifa_chamine", FX0 + 0.15, FX1 - 0.15, 1.35, 1.6, 1.82, 2.95, inox)
    caixa("azulejo_dec", BX0 - 0.05, BX1, 1.594, 1.6, 0.94, 1.55, material("azulejo_dec", (230, 236, 244), 0.25))
    for i, x in enumerate([BX0 + 0.04 + 0.52 * k for k in range(3)]):     # portas de baixo (até a cuba)
        caixa(f"porta{i}", x, x + 0.48, 0.92, 0.95, 0.1, 0.82, arm, bevel=0.012)
        caixa(f"pux{i}", x + 0.19, x + 0.29, 0.9, 0.92, 0.72, 0.74, metal, bevel=0.004)
    caixa("porta3", FX1 + 0.03, BX1 - 0.02, 0.92, 0.95, 0.1, 0.82, arm, bevel=0.012)
    caixa("armario_alto", BX0, FX0 - 0.1, 1.25, 1.6, 1.62, 2.35, arm, bevel=0.01)
    for i, x in enumerate([BX0 + 0.04 + 0.52 * k for k in range(3)]):
        caixa(f"porta_a{i}", x, x + 0.48, 1.22, 1.25, 1.66, 2.31, arm, bevel=0.012)
        caixa(f"pux_a{i}", x + (0.42 if i % 2 == 0 else 0.04), x + (0.44 if i % 2 == 0 else 0.06), 1.2, 1.22, 1.68, 1.8, metal, bevel=0.004)
    # coisas em cima da bancada: cafeteira, caneca, potes, tábua
    caixa("cafeteira", BX0 + 0.08, BX0 + 0.3, 1.3, 1.5, 0.94, 1.26, material("cafeteira", (40, 40, 44), 0.3), bevel=0.02)
    cilindro("cafeteira_jarra", 0.06, 0.07, 0.12, (BX0 + 0.19, 1.25, 1.0), material("jarra", (120, 80, 50), 0.1, coat=1.0), "sala")
    caneca = material("caneca", (222, 88, 70), 0.3, coat=0.5)
    cilindro("caneca", 0.045, 0.045, 0.1, (BX0 + 0.42, 1.15, 0.99), caneca, "sala")
    toro("caneca_alca", 0.03, 0.01, (BX0 + 0.475, 1.15, 0.995), caneca, "sala", rot=(math.radians(90), 0, 0))
    for k, (c, h) in enumerate((((240, 236, 226), 0.2), ((236, 200, 120), 0.17), ((210, 230, 236), 0.14))):
        cilindro(f"pote{k}", 0.06, 0.06, h, (BX0 + 0.12 + k * 0.14, 1.52, 0.94 + h / 2), material(f"pote{k}", c, 0.3, coat=0.4), "sala")
        cilindro(f"pote_tampa{k}", 0.062, 0.062, 0.02, (BX0 + 0.12 + k * 0.14, 1.52, 0.95 + h), material("tampa_madeira", (150, 104, 70), 0.5), "sala")
    caixa("tabua", 4.02, 4.17, 1.05, 1.42, 0.94, 0.96, material("tabua", (196, 150, 100), 0.6), bevel=0.004)
    # parede da esquerda: quadro grande, telefone de parede e planta (aparece nos closes da Clara)
    plano("quadro_esq", 0.9, 0.65, (-4.585, -0.1, 1.68), (math.radians(90), 0, math.radians(90)), material("pintura1", (200, 200, 200), 0.6))
    caixa("quadro_esq_moldura", -4.6, -4.59, -0.6, 0.4, 1.31, 2.05, material("moldura_madeira", (90, 60, 40), 0.5))
    caixa("telefone", -4.6, -4.52, 1.0, 1.14, 1.3, 1.52, material("telefone", (230, 220, 200), 0.35), bevel=0.015)
    massa("telefone_fone", [capsula_el((-4.5, 1.03, 1.47), (-4.5, 1.03, 1.33), 0.022)], material("telefone", (230, 220, 200), 0.35), "sala")
    cilindro("planta_vaso", 0.17, 0.13, 0.36, (-4.25, 0.95, 0.18), material("vaso_grande", (230, 226, 216), 0.5), "sala")
    folha_g = material("folha_grande", (60, 128, 70), 0.55)
    for k in range(9):
        a = math.radians(k * 40); r = 0.28 + 0.06 * (k % 3); h = 0.55 + 0.12 * (k % 4)
        esfera(f"planta_folha{k}", 0.14, (-4.25 + r * math.cos(a) * 0.7, 0.95 + r * math.sin(a) * 0.7, 0.36 + h), folha_g, "sala",
               escala=(1.0, 0.1, 0.42)).rotation_euler = (math.radians(35), 0, a + math.radians(90))
        cilindro(f"planta_caule{k}", 0.006, 0.006, h, (-4.25 + r * math.cos(a) * 0.3, 0.95 + r * math.sin(a) * 0.3, 0.36 + h / 2), folha_g, "sala",
                 rot=(math.radians(14) * math.sin(a), math.radians(14) * math.cos(a), 0))

# ------------------------------------------------------------------ adereços (geladeira)
ETIQ = [(-2.92, 1.02, "CLARA"), (-2.86, 0.82, "CLARA"), (-2.93, 0.6, "CLARA"), (-2.75, 0.38, "beto")]
QUADRO = (-2.95, -2.5, 1.43, 1.8)      # x0, x1, z0, z1 na porta do freezer
def aderecos():
    papel = material("etiqueta", (255, 248, 196), 0.6); papel_b = material("etiqueta_b", (206, 232, 255), 0.6)
    for i, (x, z, txt) in enumerate(ETIQ):
        w = 0.19 if txt != "beto" else 0.12
        caixa(f"etiq{i}", x, x + w, 0.885, 0.9, z - 0.035, z + 0.035, papel if txt != "beto" else papel_b, col=f"prop_etiq{i}", bevel=0.004)
        bpy.ops.object.text_add(location=(x + w / 2, 0.882, z), rotation=(math.radians(90), 0, 0))
        t = bpy.context.object; t.name = f"etiq_txt{i}"; t.data.body = txt; t.data.align_x = "CENTER"; t.data.align_y = "CENTER"
        t.data.size = 0.045 if txt != "beto" else 0.035
        try: t.data.font = bpy.data.fonts.load(os.path.join(DIR, "fontes", "Poppins-Bold.ttf"))
        except Exception: pass
        t.data.materials.append(material("tinta", (80, 60, 60), 0.6))
        for c in t.users_collection: c.objects.unlink(t)
        ligar(t, f"prop_etiq{i}")
    # cadeado + corrente
    metal = material("corrente", (130, 132, 140), 0.3, metal=1.0); ouro = material("cadeado", (220, 172, 56), 0.3, metal=0.8)
    for k in range(17):
        x = -3.02 + k * 0.045
        toro(f"elo{k}", 0.02, 0.006, (x, 0.875, 1.3), metal, "prop_cadeado", rot=(math.radians(90), 0, math.radians(90) * (k % 2)))
    caixa("cadeado_corpo", -2.47, -2.37, 0.86, 0.89, 1.14, 1.24, ouro, col="prop_cadeado", bevel=0.015)
    toro("cadeado_arco", 0.035, 0.009, (-2.42, 0.875, 1.26), metal, "prop_cadeado", rot=(math.radians(90), 0, 0))
    # quadro branco
    x0, x1, z0, z1 = QUADRO
    caixa("quadro", x0, x1, 0.885, 0.9, z0, z1, material("quadro", (252, 252, 250), 0.35), col="prop_quadro", bevel=0.006)
    caixa("quadro_moldura", x0 - 0.012, x1 + 0.012, 0.893, 0.902, z0 - 0.012, z1 + 0.012, material("moldura", (160, 165, 175), 0.3, metal=0.6), col="prop_quadro")
    for mx in (x0 + 0.05, x1 - 0.05): esfera("ima", 0.018, (mx, 0.875, z1 - 0.01), material("ima", (230, 80, 80), 0.3), "prop_quadro")

# ------------------------------------------------------------------ personagens
PERS = {
    "clara": dict(x=-1.0, dz=0.0, pele=(232, 180, 140), roupa=(70, 150, 120), cabelo=(72, 42, 32), calca=(60, 70, 110), sapato=(70, 56, 52)),
    "beto":  dict(x=0.75, dz=0.0, pele=(158, 102, 70), roupa=(236, 140, 50), cabelo=(34, 28, 28), calca=(80, 82, 94), sapato=(60, 52, 52)),
    "neide": dict(x=1.95, dz=-0.09, pele=(224, 172, 136), roupa=(126, 80, 152), cabelo=(196, 196, 202), calca=(92, 60, 112), sapato=(70, 50, 60)),
}
R_CAB = 0.233
POSES = {  # (cotovelo, mão) para o lado +x; y negativo = para a frente
    "repouso": ((0.295, 0.0, 0.68), (0.3, -0.03, 0.49)),
    "aponta": ((0.38, -0.08, 0.72), (0.48, -0.2, 0.89)),
    "ombros": ((0.38, -0.04, 0.68), (0.49, -0.12, 0.75)),
    "cintura": ((0.43, 0.02, 0.7), (0.285, -0.07, 0.57)),
}
HZ = 1.2
POSES_DE = {"clara": ["repouso", "aponta+1", "ombros", "cintura"],
            "beto": ["repouso", "aponta-1", "aponta+1", "ombros", "cintura"],
            "neide": ["repouso", "aponta-1", "ombros", "cintura"]}

def personagem(nome):
    p = PERS[nome]; x, dz = p["x"], p["dz"]; col = f"pers_{nome}"
    pele = material(f"pele_{nome}", p["pele"], 0.5); roupa = material(f"roupa_{nome}", p["roupa"], 0.7, sheen=0.3)
    cab = material(f"cabelo_{nome}", p["cabelo"], 0.45, spec=0.6); calca = material(f"calca_{nome}", p["calca"], 0.75, sheen=0.2)
    sap = material(f"sapato_{nome}", p["sapato"], 0.35)
    obs = []
    # pernas e sapatos
    for s in (-1, 1):
        if nome == "neide":
            obs.append(massa(f"perna{s}_{nome}", [capsula_el((x + s * 0.07, 0, 0.07 + dz * 0), (x + s * 0.07, 0, 0.3), 0.05)], material("meia", (200, 160, 130), 0.6), col))
        else:
            obs.append(massa(f"perna{s}_{nome}", [capsula_el((x + s * 0.075, 0, 0.08), (x + s * 0.075, 0, 0.42), 0.07)], calca, col))
        obs.append(massa(f"sapato{s}_{nome}", [dict(tipo="CUBE", co=(x + s * 0.08, -0.04, 0.045), r=0.04, size_x=0.04, size_y=0.08, size_z=0.008)], sap, col))
    if nome == "neide":
        obs.append(cilindro(f"saia_{nome}", 0.3, 0.22, 0.26, (x, 0, 0.3 + 0.12), calca, col, seg=48))
    # tronco e pescoço
    obs.append(massa(f"tronco_{nome}", [dict(tipo="CUBE", co=(x, 0, 0.66 + dz), r=0.11, size_x=0.13, size_y=0.06, size_z=0.17)], roupa, col))
    obs.append(massa(f"pescoco_{nome}", [capsula_el((x, 0, 0.9 + dz), (x, 0, 1.02 + dz), 0.068)], pele, col))
    # cabeça, orelhas, nariz
    hz = HZ + dz
    obs.append(esfera(f"cabeca_{nome}", R_CAB, (x, 0, hz), pele, col, escala=(1, 0.94, 1.0)))
    if nome != "clara":
        for s in (-1, 1): obs.append(esfera(f"orelha{s}_{nome}", 0.05, (x + s * 0.225, 0.02, hz - 0.01), pele, col, escala=(0.5, 0.7, 0.95)))
    obs.append(esfera(f"nariz_{nome}", 0.034, (x, -0.218, hz - 0.035), pele, col, escala=(1, 0.8, 0.9)))
    # cabelo
    if nome == "clara":
        tr = massa(f"cabelo_tras_{nome}", [dict(tipo="CUBE", co=(x, 0.13, hz - 0.03), r=0.1, size_x=0.165, size_y=0.07, size_z=0.14)], cab, col)
        obs.append(tr)
        cp = esfera(f"cabelo_topo_{nome}", 0.253, (x, 0.0, hz + 0.012), cab, col, escala=(1.0, 0.96, 1.0))
        a = math.radians(32); cortar(cp, Vector((x, -0.25, hz + 0.105)), Vector((0, math.sin(a), math.cos(a))))
        cp.modifiers.new("s", "SOLIDIFY").thickness = 0.014; obs.append(cp)
    elif nome == "beto":
        cp = esfera(f"cabelo_topo_{nome}", 0.246, (x, 0.008, hz + 0.01), cab, col)
        a = math.radians(38); cortar(cp, Vector((x, -0.25, hz + 0.135)), Vector((0, math.sin(a), math.cos(a))))
        cp.modifiers.new("s", "SOLIDIFY").thickness = 0.012; obs.append(cp)
    else:
        cp = esfera(f"cabelo_topo_{nome}", 0.25, (x, 0.01, hz + 0.01), cab, col)
        a = math.radians(30); cortar(cp, Vector((x, -0.25, hz + 0.1)), Vector((0, math.sin(a), math.cos(a))))
        cp.modifiers.new("s", "SOLIDIFY").thickness = 0.014; obs.append(cp)
        obs.append(esfera(f"coque_{nome}", 0.105, (x, 0.04, hz + 0.27), cab, col))
        for s in (-1, 1): obs.append(esfera(f"lateral{s}_{nome}", 0.08, (x + s * 0.2, 0.03, hz - 0.03), cab, col, escala=(0.8, 1, 1.1)))
    # detalhes da roupa
    if nome == "beto":
        me = bpy.data.meshes.new("estrela"); bm = bmesh.new()
        vs = [bm.verts.new((0.07 * (1 if k % 2 == 0 else 0.45) * math.sin(math.radians(k * 36)), 0,
                            0.07 * (1 if k % 2 == 0 else 0.45) * math.cos(math.radians(k * 36)))) for k in range(10)]
        bm.faces.new(list(reversed(vs))); bm.to_mesh(me); bm.free()
        ob = bpy.data.objects.new(f"estrela_{nome}", me); ob.location = (x, -0.176, 0.62 + dz)
        me.materials.append(material("estrela", (255, 222, 150), 0.5)); ligar(ob, col); obs.append(ob)
    elif nome == "clara":
        me = bpy.data.meshes.new("gola"); bm = bmesh.new()
        f = bm.faces.new([bm.verts.new(v) for v in ((-0.07, 0, 0.0), (0.07, 0, 0.0), (0, 0, -0.1))]); bm.to_mesh(me); bm.free()
        ob = bpy.data.objects.new(f"gola_{nome}", me); ob.location = (x, -0.165, 0.93 + dz); ob.rotation_euler = (math.radians(-12), 0, 0)
        me.materials.append(material("gola", (48, 112, 88), 0.7)); ligar(ob, col); obs.append(ob)
    else:
        for z in (0.5, 0.62, 0.74):
            obs.append(esfera(f"botao{z}_{nome}", 0.018, (x, -0.172, z + dz), material("botao", (236, 222, 242), 0.4), col, escala=(1, 0.5, 1)))
    for ob in list(obs):
        if not any(k in ob.name for k in ("estrela", "gola", "botao")): contorno(ob)
    # braços (um conjunto por pose; todos escondidos, liga-se o da pose na hora)
    for pose in POSES_DE[nome]:
        for s in (-1, 1):
            base = pose.split("+")[0].split("-")[0] if pose.startswith("aponta") else pose
            if pose.startswith("aponta"):
                lado = 1 if pose.endswith("+1") else -1; base = "aponta" if s == lado else "repouso"
            (cx, cy, cz), (mx, my, mz) = POSES[base]
            ombro = (x + s * 0.25, 0, 0.87 + dz); cot = (x + s * cx, cy, cz + dz); mao = (x + s * mx, my, mz + dz)
            colp = f"pose_{nome}_{pose}"
            a = massa(f"braco{s}_{nome}_{pose}", [capsula_el(ombro, cot, 0.052), capsula_el(cot, mao, 0.047)], roupa, colp)
            hnd = esfera(f"mao{s}_{nome}_{pose}", 0.055, mao, pele, colp)
            contorno(a); contorno(hnd)


# ------------------------------------------------------------------ fachada (vinheta "minutos depois")
def fachada():
    X = 45.0; col = "fachada"
    chao = material("grama", (110, 168, 92), 0.8); calc = material("calcada", (196, 192, 186), 0.7)
    plano("grama", 60, 40, (X, 6, 0), (0, 0, 0), chao, col); caixa("calcada", X - 30, X + 30, -6, -3.5, 0, 0.04, calc, col=col)
    parede = material("fachada_cor", (226, 150, 112), 0.75); faixa = material("faixa", (172, 100, 80), 0.6)
    caixa("predio", X - 5, X + 5, 0, 8, 0, 13, parede, col=col, bevel=0.05)
    caixa("platibanda", X - 5.3, X + 5.3, -0.2, 8.2, 13, 13.5, faixa, col=col, bevel=0.03)
    vidro_a = mat_emissao("janela_acesa", (255, 226, 150), 2.2); vidro = material("vidro", (150, 190, 220), 0.08, coat=1.0)
    for andar in range(5):
        for c in range(5):
            x0 = X - 4.2 + c * 1.75; z0 = 1.6 + andar * 2.3
            caixa(f"jan{andar}_{c}", x0 - 0.06, x0 + 1.06, -0.08, 0.02, z0 - 0.06, z0 + 1.36, material("caixilho", (250, 246, 238), 0.4), col=col)
            caixa(f"vid{andar}_{c}", x0, x0 + 1.0, -0.1, -0.02, z0, z0 + 1.3, vidro_a if (andar * 5 + c) % 3 == 0 else vidro, col=col)
            caixa(f"peit{andar}_{c}", x0 - 0.12, x0 + 1.12, -0.25, 0.0, z0 - 0.14, z0 - 0.06, faixa, col=col)
    caixa("porta", X - 0.7, X + 0.7, -0.1, 0.05, 0.04, 1.4, material("porta_pr", (110, 76, 58), 0.5), col=col, bevel=0.02)
    caixa("marquise", X - 1.3, X + 1.3, -0.9, 0.0, 1.5, 1.62, faixa, col=col, bevel=0.02)
    copa = material("copa", (84, 150, 82), 0.7); tronco = material("tronco", (110, 76, 52), 0.8)
    for tx in (X - 7.5, X + 7.5):
        cilindro(f"tronco{tx}", 0.18, 0.14, 2.4, (tx, -2.0, 1.2), tronco, col)
        for dx, dz, r in ((0, 3.2, 1.3), (-0.8, 2.7, 0.9), (0.8, 2.8, 0.95)): esfera(f"copa{tx}{dx}", r, (tx + dx, -2.0, dz), copa, col)
    ceu = mat_ceu(); plano("ceu_fachada", 120, 60, (X, 30, 10), (math.radians(90), 0, 0), ceu, col)
    for i, (nx, nz, r) in enumerate(((X - 9, 16, 1.6), (X - 7.5, 16.4, 2.0), (X - 6, 16, 1.5), (X + 6, 18, 1.8), (X + 7.8, 18.3, 2.2))):
        esfera(f"nuvem{i}", r, (nx, 20, nz), mat_emissao(f"nuvem{i}", (255, 255, 255), 1.6), col, escala=(1.4, 0.6, 0.8))

# ------------------------------------------------------------------ câmeras e luz
CAMERAS = {   # local, alvo, lente(mm), foco (None = sem desfoque)
    "geral2": ((-0.12, -5.6, 1.22), (-0.12, 0.6, 0.96), 45, None),
    "geral3": ((0.55, -6.2, 1.25), (0.55, 0.6, 0.97), 42, None),
    "dois": ((-0.12, -3.4, 1.28), (-0.12, 0.6, 1.08), 45, 3.4),
    "close_clara": ((-1.0, -2.0, 1.3), (-1.0, 0.6, 1.07), 42, 2.0),
    "close_beto": ((0.75, -2.0, 1.3), (0.75, 0.6, 1.07), 42, 2.0),
    "close_neide": ((1.95, -2.0, 1.21), (1.95, 0.6, 0.98), 42, 2.0),
    "geladeira": ((-2.35, -3.3, 1.02), (-2.55, 0.9, 0.95), 45, None),
    "abertura": ((0.0, -5.6, 1.15), (0.0, 0.6, 0.92), 45, None),
    "fachada": ((45.0, -27.0, 3.0), (45.0, 0.0, 6.4), 30, None),
}
def camera(nome):
    loc, alvo, lente, foco = CAMERAS[nome]
    cd = bpy.data.cameras.get("cam") or bpy.data.cameras.new("cam")
    ob = bpy.data.objects.get("cam") or bpy.data.objects.new("cam", cd)
    if ob.name not in bpy.context.scene.collection.objects: bpy.context.scene.collection.objects.link(ob)
    ob.location = loc; d = Vector(alvo) - Vector(loc); ob.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    cd.lens = lente; cd.sensor_width = 36
    cd.dof.use_dof = foco is not None
    if foco: cd.dof.focus_distance = foco; cd.dof.aperture_fstop = 2.2
    bpy.context.scene.camera = ob; bpy.context.view_layer.update(); return ob

def luzes():
    def area(nome, loc, alvo, energia, tam, cor):
        ld = bpy.data.lights.new(nome, "AREA"); ld.energy = energia; ld.size = tam; ld.color = cor
        ob = bpy.data.objects.new(nome, ld); ob.location = loc
        ob.rotation_euler = (Vector(alvo) - Vector(loc)).to_track_quat("-Z", "Y").to_euler(); ligar(ob, "luz")
    area("chave", (-2.6, -4.2, 3.4), (0, 0, 1.0), 2000, 5.0, (1.0, 0.93, 0.84))
    area("preenche", (3.4, -3.6, 2.2), (0.5, 0, 1.0), 650, 3.5, (0.86, 0.92, 1.0))
    area("recorte", (0.4, 1.2, 2.7), (0.4, -0.5, 1.2), 420, 2.5, (1.0, 0.84, 0.66))
    sd = bpy.data.lights.new("sol", "SUN"); sd.energy = 2.6; sd.angle = math.radians(4); sd.color = (1.0, 0.88, 0.7)
    so = bpy.data.objects.new("sol", sd); so.rotation_euler = Vector((-0.3, -1.0, -0.75)).to_track_quat("-Z", "Y").to_euler(); ligar(so, "luz")
    w = bpy.data.worlds.new("mundo"); bpy.context.scene.world = w; w.use_nodes = True
    bg = w.node_tree.nodes["Background"]; bg.inputs[0].default_value = (0.62, 0.68, 0.76, 1); bg.inputs[1].default_value = 0.35

def configurar(amostras=160, limiar=0.02):
    sc = bpy.context.scene; sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"
    sc.cycles.samples = amostras; sc.cycles.use_adaptive_sampling = True; sc.cycles.adaptive_threshold = limiar
    sc.cycles.use_denoising = False; sc.cycles.max_bounces = 4; sc.cycles.diffuse_bounces = 2; sc.cycles.glossy_bounces = 2
    sc.cycles.use_fast_gi = True; sc.cycles.fast_gi_method = "ADD"; sc.cycles.ao_bounces_render = 1
    sc.world.light_settings.distance = 1.2
    vl = sc.view_layers[0]; vl.cycles.denoising_store_passes = True
    sc.use_nodes = True; nt = sc.node_tree; nt.nodes.clear()
    rl = nt.nodes.new("CompositorNodeRLayers"); cp = nt.nodes.new("CompositorNodeComposite"); cp.use_alpha = True
    nt.links.new(rl.outputs["Image"], cp.inputs["Image"]); nt.links.new(rl.outputs["Alpha"], cp.inputs["Alpha"])
    fo = nt.nodes.new("CompositorNodeOutputFile"); fo.name = "aux"; fo.format.file_format = "OPEN_EXR"; fo.format.color_depth = "16"
    fo.file_slots.clear(); fo.file_slots.new("alb"); fo.file_slots.new("nrm")
    nt.links.new(rl.outputs["Denoising Albedo"], fo.inputs["alb"]); nt.links.new(rl.outputs["Denoising Normal"], fo.inputs["nrm"])
    sc.cycles.transmission_bounces = 2; sc.cycles.transparent_max_bounces = 12; sc.cycles.caustics_reflective = False
    sc.cycles.caustics_refractive = False; sc.cycles.sample_clamp_indirect = 4.0
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = W, H, 100
    sc.render.use_persistent_data = True; sc.render.image_settings.file_format = "PNG"; sc.render.image_settings.color_mode = "RGBA"
    try:
        sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Punchy"
    except Exception:
        try: sc.view_settings.view_transform = "Filmic"; sc.view_settings.look = "Medium High Contrast"
        except Exception: pass
    sc.view_settings.exposure = -0.25

def construir():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    global CONTORNO; CONTORNO = mat_contorno()
    sala(); aderecos(); fachada(); luzes()
    for n in PERS: personagem(n)
    configurar()

# ------------------------------------------------------------------ visibilidade e render
def mostrar(sala_on=True, sombra=False, pers=(), poses=None, props=(), mover=None, fachada=False):
    """sala_on: cenário visível. sombra: cenário vira 'shadow catcher' (para sprites)."""
    sc = bpy.context.scene
    for nome, col in COL.items():
        if nome in ("sala", "luz"): continue
        vis = False
        if nome.startswith("pers_"): vis = nome[5:] in pers
        elif nome.startswith("pose_"):
            _, quem, pose = nome.split("_", 2); vis = quem in pers and (poses or {}).get(quem) == pose
        elif nome.startswith("prop_"): vis = nome[5:] in props
        elif nome == "fachada": vis = fachada
        col.hide_render = not vis
    colecao("sala").hide_render = not sala_on
    for ob in colecao("sala").objects:
        apanha = ob.name.split(".")[0] in APANHA_SOMBRA
        ob.is_shadow_catcher = sombra and apanha
        ob.hide_render = sombra and not apanha
    sc.render.film_transparent = sombra or not sala_on

APANHA_SOMBRA = {"piso", "p_esq", "p_dir", "p_dir2", "p_porta_cima", "p_baixo", "p_cima", "azulejos", "azulejos2", "rodape", "rodape2",
                 "friso", "friso2", "balcao", "tampo", "tampo2", "aparador", "mesa_tampo", "toalha", "parede_e", "lambri_e",
                 "gel_corpo", "gel_freezer"}

def mover_personagens(pos):
    """pos: {nome: dx} desloca o personagem inteiro (todas as poses)."""
    for nome in PERS:
        dx = pos.get(nome, 0.0)
        for cn, col in COL.items():
            if cn == f"pers_{nome}" or cn.startswith(f"pose_{nome}_"):
                for ob in col.objects:
                    if "x0" not in ob: ob["x0"] = ob.location.x
                    ob.location.x = ob["x0"] + dx
    bpy.context.view_layer.update()

def projetar(cam, co):
    sc = bpy.context.scene; v = world_to_camera_view(sc, cam, Vector(co))
    return (v.x * W, (1 - v.y) * H, v.z)

def borda(cam, pontos, margem=40):
    xs, ys = [], []
    for p in pontos:
        px, py, z = projetar(cam, p)
        if z > 0: xs.append(px); ys.append(py)
    if not xs: return None
    x0, x1 = max(0, min(xs) - margem), min(W, max(xs) + margem); y0, y1 = max(0, min(ys) - margem), min(H, max(ys) + margem)
    if x1 <= x0 or y1 <= y0: return None
    return (x0 / W, x1 / W, 1 - y1 / H, 1 - y0 / H)

def pontos_personagem(nome, dx=0.0):
    p = PERS[nome]; x = p["x"] + dx; pts = []
    for X in (x - 0.7, x + 1.5):
        for Y in (-0.35, 1.6):
            for Z in (0.0, 1.62 + p["dz"] + (0.14 if nome == "neide" else 0)): pts.append((X, Y, Z))
    return pts

def render(saida, borda_norm=None, amostras=None):
    sc = bpy.context.scene
    if amostras: sc.cycles.samples = amostras
    if borda_norm:
        sc.render.use_border = True; sc.render.use_crop_to_border = False
        sc.render.border_min_x, sc.render.border_max_x, sc.render.border_min_y, sc.render.border_max_y = borda_norm
    else: sc.render.use_border = False
    os.makedirs(os.path.dirname(saida), exist_ok=True); tmp = saida + ".tmp.png"
    base = os.path.splitext(os.path.basename(saida))[0]; fo = sc.node_tree.nodes["aux"]
    fo.base_path = os.path.dirname(saida); fo.file_slots[0].path = base + "_alb_"; fo.file_slots[1].path = base + "_nrm_"
    sc.frame_set(1)
    sc.render.filepath = tmp; t = time.time(); bpy.ops.render.render(write_still=True)
    for k in ("alb", "nrm"):
        f = os.path.join(os.path.dirname(saida), f"{base}_{k}_0001.exr")
        if os.path.exists(f): os.replace(f, os.path.join(os.path.dirname(saida), f"{base}_{k}.exr"))
    os.replace(tmp, saida)
    return time.time() - t

def projecoes():
    dados = {}
    for setup in CAMERAS:
        cam = camera(setup); d = {}
        if setup == "abertura": mover_personagens(ABERTURA_DX)
        else: mover_personagens({})
        for nome, p in PERS.items():
            dx = ABERTURA_DX.get(nome, 0) if setup == "abertura" else 0
            x = p["x"] + dx; hz = HZ + p["dz"]
            cx, cy, z = projetar(cam, (x, 0, hz)); rx, _, _ = projetar(cam, (x + R_CAB, 0, hz))
            ch, chy, _ = projetar(cam, (x, 0, 0))
            d[nome] = dict(cx=cx, cy=cy, r=abs(rx - cx), pe_x=ch, pe_y=chy, prof=z)
        x0, x1, z0, z1 = QUADRO
        d["quadro"] = [projetar(cam, c)[:2] for c in ((x0, 0.88, z1), (x1, 0.88, z1), (x1, 0.88, z0), (x0, 0.88, z0))]
        dados[setup] = d
    mover_personagens({})
    json.dump(dados, open(os.path.join(OUT, "projecoes.json"), "w"), indent=1)

ABERTURA_DX = {"clara": 0.15, "neide": -1.95, "beto": 0.1}   # clara -0.85, neide 0, beto 0.85

def visibilidade(cam, nome, dx):
    p = PERS[nome]; x = p["x"] + dx; hz = HZ + p["dz"]
    cx, cy, z = projetar(cam, (x, 0, hz))
    if 0.05 * W < cx < 0.95 * W and 0 < cy < H: return "total"
    for X in (x - 0.55, x + 0.55):
        for Z in (0.0, hz + 0.25):
            px, py, _ = projetar(cam, (X, 0, Z))
            if 0 <= px <= W and 0 <= py <= H: return "parcial"
    return None

def planejar():
    placas, sprites, props = [], [], []
    for setup in CAMERAS:
        cam = camera(setup)
        if setup != "abertura": placas.append(dict(tipo="placa", setup=setup, saida=f"{setup}/placa.png", amostras=16))
        for nome in PERS:
            dx = ABERTURA_DX.get(nome, 0) if setup == "abertura" else 0
            v = visibilidade(cam, nome, dx)
            if not v: continue
            poses = POSES_DE[nome] if v == "total" and setup not in ("geladeira", "abertura") else ["repouso"]
            for pose in poses:
                sprites.append(dict(tipo="sprite", setup=setup, quem=nome, pose=pose, saida=f"{setup}/{nome}_{pose}.png", amostras=16))
        if setup in ("geral2", "geral3", "geladeira"):
            for pr in ("etiq0", "etiq1", "etiq2", "etiq3", "cadeado", "quadro"):
                props.append(dict(tipo="prop", setup=setup, prop=pr, saida=f"{setup}/prop_{pr}.png", amostras=16))
    jobs = placas + sprites + props
    json.dump(jobs, open(os.path.join(OUT, "jobs.json"), "w"), indent=1)
    print("PLANO", len(placas), "placas", len(sprites), "sprites", len(props), "adereços")

def executar_jobs(lista):
    jobs = json.load(open(lista)); feitos = 0
    for j in jobs:
        saida = os.path.join(OUT, j["saida"])
        if os.path.exists(saida): continue
        cam = camera(j["setup"])
        mover_personagens(ABERTURA_DX if j["setup"] == "abertura" else {})
        if j["tipo"] == "placa":
            mostrar(sala_on=j["setup"] != "fachada", sombra=False, fachada=j["setup"] == "fachada")
            dt = render(saida, None, j.get("amostras", 192))
        elif j["tipo"] == "sprite":
            quem = j["quem"]; dx = ABERTURA_DX.get(quem, 0) if j["setup"] == "abertura" else 0
            mostrar(sala_on=j["setup"] != "abertura", sombra=True, pers=(quem,), poses={quem: j["pose"]})
            dt = render(saida, borda(cam, pontos_personagem(quem, dx)), j.get("amostras", 128))
        elif j["tipo"] == "prop":
            mostrar(sala_on=True, sombra=True, props=(j["prop"],))
            obs = [o for o in colecao(f"prop_{j['prop']}").objects]
            pts = [o.matrix_world @ Vector(c) for o in obs for c in o.bound_box]
            dt = render(saida, borda(cam, pts, 25), j.get("amostras", 96))
        feitos += 1; print(f"JOB {j['saida']} {dt:.1f}s", flush=True)
    print("FIM", feitos, flush=True)

if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    construir()
    if not argv or argv[0] == "teste":
        sc = bpy.context.scene; sc.render.resolution_percentage = 100
        cam = camera("geral2"); mostrar(sala_on=True, sombra=False)
        if not os.path.exists(os.path.join(DIR, "teste", "placa.png")): print("placa", render(os.path.join(DIR, "teste", "placa.png"), None, 24))
        for quem, pose in (("clara", "repouso"), ("beto", "aponta-1")):
            mostrar(sala_on=True, sombra=True, pers=(quem,), poses={quem: pose})
            print("sprite", quem, render(os.path.join(DIR, "teste", f"{quem}.png"), borda(cam, pontos_personagem(quem)), 24))
    elif argv[0] == "cor":
        sc = bpy.context.scene; sc.render.resolution_percentage = 40; camera("geral2")
        mostrar(sala_on=True, sombra=False, pers=("clara", "beto"), poses={"clara": "repouso", "beto": "aponta-1"})
        for nome, vt, look, ex in (("agx", "AgX", "AgX - Punchy", -0.25), ("std", "Standard", "Medium High Contrast", -0.55),
                                   ("filmic", "Filmic", "Medium High Contrast", -0.1)):
            sc.view_settings.view_transform = vt
            try: sc.view_settings.look = look
            except Exception as e: print("look", e); sc.view_settings.look = "None"
            sc.view_settings.exposure = ex
            print("cor", nome, render(os.path.join(DIR, "teste", f"cor_{nome}.png"), None, 16))
    elif argv[0] == "projecoes": projecoes()
    elif argv[0] == "planejar": planejar(); projecoes()
    elif argv[0] == "jobs": executar_jobs(argv[1])
    elif argv[0] == "salvar": bpy.ops.wm.save_as_mainfile(filepath=os.path.join(DIR, "cena.blend"))
