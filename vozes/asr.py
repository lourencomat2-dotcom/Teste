"""Transcreve com Whisper small (offline) e mede taxa de erro de palavras."""
import os, sys, wave, re, unicodedata, numpy as np, sherpa_onnx
from scipy.signal import resample_poly

D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sherpa-onnx-whisper-small")
_rec = None
def rec():
    global _rec
    if _rec is None:
        _rec = sherpa_onnx.OfflineRecognizer.from_whisper(
            encoder=f"{D}/small-encoder.int8.onnx", decoder=f"{D}/small-decoder.int8.onnx",
            tokens=f"{D}/small-tokens.txt", language="pt", task="transcribe", num_threads=2)
    return _rec

def ler(path):
    with wave.open(path) as w:
        sr = w.getframerate(); a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
        if w.getnchannels() > 1: a = a.reshape(-1, w.getnchannels()).mean(1)
    return a, sr

def transcrever(a, sr):
    if sr != 16000:
        from math import gcd; g = gcd(sr, 16000); a = resample_poly(a, 16000 // g, sr // g)
    s = rec().create_stream(); s.accept_waveform(16000, a.astype(np.float32)); rec().decode_stream(s)
    return s.result.text.strip()

def norm(t):
    t = unicodedata.normalize("NFKD", t.lower()); t = "".join(c for c in t if not unicodedata.combining(c))
    t = re.sub(r"[^a-z0-9 ]", " ", t)
    nums = {"42": "quarenta e dois", "1": "um", "2": "dois", "3": "tres", "4": "quatro", "5": "cinco", "7": "sete",
            "42 mil": "quarenta e dois mil", "pra": "para", "pro": "para o", "ta": "esta", "to": "estou"}
    t = " ".join(nums.get(w, w) for w in t.split())
    return t.split()

def wer(ref, hyp):
    r, h = norm(ref), norm(hyp); d = np.zeros((len(r) + 1, len(h) + 1), int)
    d[:, 0] = range(len(r) + 1); d[0, :] = range(len(h) + 1)
    for i in range(1, len(r) + 1):
        for j in range(1, len(h) + 1):
            d[i, j] = min(d[i - 1, j] + 1, d[i, j - 1] + 1, d[i - 1, j - 1] + (r[i - 1] != h[j - 1]))
    return d[-1, -1] / max(1, len(r))

if __name__ == "__main__":
    for p in sys.argv[1:]:
        a, sr = ler(p); print(p, "->", transcrever(a, sr))
