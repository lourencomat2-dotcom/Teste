"""Limpa o ruído de todos os renders novos em render/ (gera *_limpo.png)."""
import os, glob, sys
os.environ.setdefault("OPENCV_IO_ENABLE_OPENEXR", "1")
MOTOR = os.path.dirname(os.path.abspath(__file__)); RAIZ = os.path.dirname(MOTOR)
sys.path.insert(0, MOTOR)
import denoise
n = 0
for p in sorted(glob.glob(os.path.join(RAIZ, "render", "*", "*.png"))):
    if p.endswith("_limpo.png") or p.endswith(".tmp.png"): continue
    out = p[:-4] + "_limpo.png"
    if os.path.exists(out) and os.path.getmtime(out) >= os.path.getmtime(p): continue
    if not (os.path.exists(p[:-4] + "_alb.exr") and os.path.exists(p[:-4] + "_nrm.exr")): continue
    denoise.limpar(p, out); n += 1
print("limpos", n)
