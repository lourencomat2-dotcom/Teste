#!/usr/bin/env python3
"""conferir_fala.py — transcreve o áudio de um vídeo, trecho a trecho, para achar fala errada (grátis, roda local).

Uso:  python conferir_fala.py <pasta do modelo> <video.mp4> <cortes em segundos...>
Ex.:  python conferir_fala.py modelos/sherpa-onnx-whisper-small final.mp4 0 7.6 15.7 20.3

Preparar uma vez:
  pip install sherpa-onnx soundfile
  curl -L -O https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-whisper-small.tar.bz2
  tar xjf sherpa-onnx-whisper-small.tar.bz2
Cada trecho precisa ter menos de 30 s. O transcritor também erra: use como filtro, não como juiz.
"""
import subprocess
import sys
import tempfile

import sherpa_onnx
import soundfile as sf

m, video = sys.argv[1], sys.argv[2]
cortes = [float(x) for x in sys.argv[3:]]
r = sherpa_onnx.OfflineRecognizer.from_whisper(
    encoder=f"{m}/small-encoder.onnx", decoder=f"{m}/small-decoder.onnx", tokens=f"{m}/small-tokens.txt",
    language="pt", task="transcribe", num_threads=4)
with tempfile.NamedTemporaryFile(suffix=".wav") as t:
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", video, "-ac", "1", "-ar", "16000", t.name], check=True)
    x, sr = sf.read(t.name, dtype="float32")
if len(cortes) < 2:
    cortes = [0.0, len(x) / sr]
for a, b in zip(cortes, cortes[1:]):
    s = r.create_stream()
    s.accept_waveform(sr, x[int(a * sr):int(b * sr)])
    r.decode_stream(s)
    print(f"{a:5.1f}-{b:5.1f} s | {s.result.text.strip()}")
