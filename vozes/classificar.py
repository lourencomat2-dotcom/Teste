"""Classificador de sons (CED, AudioSet): diz o quanto um áudio parece risada, fala, música..."""
import os, sys, wave, numpy as np, sherpa_onnx
from scipy.signal import resample_poly
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sherpa-onnx-ced-small-audio-tagging-2024-04-19")
_t = None
def tagger():
    global _t
    if _t is None:
        cfg = sherpa_onnx.AudioTaggingConfig(model=sherpa_onnx.AudioTaggingModelConfig(ced=f"{D}/model.int8.onnx", num_threads=2),
                                             labels=f"{D}/class_labels_indices.csv", top_k=50)
        _t = sherpa_onnx.AudioTagging(cfg)
    return _t

RISO = ("Laughter", "Giggle", "Belly laugh", "Chuckle, chortle", "Snicker", "Baby laughter")
def notas(a, sr):
    if a.ndim > 1: a = a.mean(1)
    if sr != 16000:
        from math import gcd; g = gcd(sr, 16000); a = resample_poly(a, 16000 // g, sr // g)
    s = tagger().create_stream(); s.accept_waveform(16000, a.astype(np.float32))
    ev = tagger().compute(s, top_k=50)
    d = {e.name: e.prob for e in ev}
    riso = max([d.get(k, 0) for k in RISO])
    return riso, d.get("Speech", 0), d.get("Music", 0), d.get("Crowd", 0), [(e.name, round(e.prob, 2)) for e in ev[:5]]

def ler(path):
    with wave.open(path) as w:
        sr, ch = w.getframerate(), w.getnchannels()
        a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    return (a.reshape(-1, ch) if ch > 1 else a), sr

if __name__ == "__main__":
    for p in sys.argv[1:]:
        a, sr = ler(p); r, sp, mu, cr, top = notas(a, sr)
        print(f"{p.split('/')[-1]:28s} risada {r:.2f}  fala {sp:.2f}  música {mu:.2f}  multidão {cr:.2f}  {top}")
