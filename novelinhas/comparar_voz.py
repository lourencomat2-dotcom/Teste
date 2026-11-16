#!/usr/bin/env python3
"""comparar_voz.py — compara a voz de um personagem entre clipes (grátis, roda local).

Uso: python comparar_voz.py clipe1.mp4 clipe2.mp4 ...
Mede, só nos trechos com fala: tom médio (F0, em Hz) e brilho do timbre (centroide espectral, em Hz).
Clipes do mesmo personagem com tom muito diferente (mais de ~15%) indicam troca de voz. Confirmar de ouvido.
"""
import subprocess
import sys

import numpy as np

SR = 16000


def audio(f):
    b = subprocess.run(["ffmpeg", "-v", "error", "-i", f, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                       capture_output=True, check=True).stdout
    return np.frombuffer(b, dtype=np.float32)


def medir(x):
    w, h = 1024, 256
    q = np.hanning(w)
    f0s, cents = [], []
    nivel = 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-9)
    for i in range(0, len(x) - w, h):
        s = x[i:i + w]
        db = 20 * np.log10(np.sqrt(np.mean(s ** 2)) + 1e-9)
        if db < nivel - 6:  # fora da fala
            continue
        spec = np.abs(np.fft.rfft(s * q))
        fr = np.fft.rfftfreq(w, 1 / SR)
        cents.append((spec * fr).sum() / (spec.sum() + 1e-9))
        ac = np.correlate(s, s, "full")[w - 1:]
        lo, hi = SR // 400, SR // 70  # 70 a 400 Hz
        k = lo + np.argmax(ac[lo:hi])
        if ac[k] > 0.35 * ac[0]:
            f0s.append(SR / k)
    return (np.median(f0s) if f0s else float("nan")), (np.median(cents) if cents else float("nan")), len(f0s)


ref = None
for f in sys.argv[1:]:
    f0, c, n = medir(audio(f))
    ref = ref or f0
    print(f"{f.split('/')[-1]:28s} tom {f0:6.1f} Hz ({(f0 / ref - 1) * 100:+5.1f}%)  timbre {c:6.0f} Hz  ({n} quadros com voz)")
