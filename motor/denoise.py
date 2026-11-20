"""Limpa o ruído dos renders (OIDN) usando albedo e normal; trata alfa separadamente."""
import os, sys, numpy as np, cv2, pyoidn
os.environ.setdefault("OPENCV_IO_ENABLE_OPENEXR", "1")
from PIL import Image

def s2l(c): return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
def l2s(c): c = np.clip(c, 0, 1); return np.where(c <= 0.0031308, c * 12.92, 1.055 * np.power(c, 1 / 2.4) - 0.055)

def ler_exr(p):
    a = cv2.imread(p, cv2.IMREAD_UNCHANGED)
    if a is None: return None
    return a[..., :3][..., ::-1].astype(np.float32)

def limpar(png, saida):
    im = np.asarray(Image.open(png).convert("RGBA")).astype(np.float32) / 255
    base = png[:-4]; alb, nrm = ler_exr(base + "_alb.exr"), ler_exr(base + "_nrm.exr")
    cor = s2l(im[..., :3]).astype(np.float32); a = im[..., 3:4]
    ys, xs = np.nonzero(a[..., 0] > 0.001)
    if len(xs) == 0: Image.fromarray((im * 255).astype(np.uint8)).save(saida); return
    y0, y1, x0, x1 = max(0, ys.min() - 8), ys.max() + 9, max(0, xs.min() - 8), xs.max() + 9
    c = cor[y0:y1, x0:x1]; aa = a[y0:y1, x0:x1]
    if alb is not None and nrm is not None:
        al = np.clip(alb[y0:y1, x0:x1], 0, 1).astype(np.float32); nr = np.clip(nrm[y0:y1, x0:x1], -1, 1).astype(np.float32)
        d = pyoidn.denoise(np.ascontiguousarray(c), np.ascontiguousarray(al), np.ascontiguousarray(nr))
    else:
        d = pyoidn.denoise(np.ascontiguousarray(c))
    if aa.min() < 0.999:   # alfa (sombras) também tem ruído
        a3 = np.ascontiguousarray(np.repeat(aa, 3, axis=2)); ad = pyoidn.denoise(a3)[..., :1]
        ad = np.where(aa > 0.98, aa, np.clip(ad, 0, 1))
    else: ad = aa
    out = np.zeros_like(im); out[y0:y1, x0:x1, :3] = l2s(d); out[y0:y1, x0:x1, 3:] = ad
    Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)).save(saida)

if __name__ == "__main__":
    for p in sys.argv[1:]:
        limpar(p, p.replace(".png", "_limpo.png")); print("ok", p)
