#!/usr/bin/env bash
# Instala o que o projeto precisa. Testado em Ubuntu/Debian (no Windows, use o WSL).
# No macOS: brew install ffmpeg espeak-ng  e instale o Blender pelo site (blender.org).
set -e
cd "$(dirname "$0")"
SUDO=""; [ "$(id -u)" != "0" ] && SUDO="sudo"

if command -v apt-get >/dev/null 2>&1; then
  $SUDO apt-get update
  $SUDO apt-get install -y ffmpeg espeak-ng
  $SUDO apt-get install -y --no-install-recommends blender || echo "Blender não instalado (só é preciso para re-renderizar o 3D)."
fi

python3 -m pip install -r requirements.txt || python3 -m pip install --break-system-packages -r requirements.txt

REL=https://github.com/k2-fsa/sherpa-onnx/releases/download
cd vozes
# voz neural (obrigatório para gerar falas novas)
[ -d kokoro-multi-lang-v1_0 ] || { curl -L -o kokoro.tar.bz2 $REL/tts-models/kokoro-multi-lang-v1_0.tar.bz2 && tar -xjf kokoro.tar.bz2 && rm kokoro.tar.bz2; }
# conferência de pronúncia (opcional, ~640 MB)
[ -d sherpa-onnx-whisper-small ] || { curl -L -o w.tar.bz2 $REL/asr-models/sherpa-onnx-whisper-small.tar.bz2 && tar -xjf w.tar.bz2 && rm w.tar.bz2; }
# classificador de sons, só para recalibrar a risada (opcional)
[ -d sherpa-onnx-ced-small-audio-tagging-2024-04-19 ] || { curl -L -o c.tar.bz2 $REL/audio-tagging-models/sherpa-onnx-ced-small-audio-tagging-2024-04-19.tar.bz2 && tar -xjf c.tar.bz2 && rm c.tar.bz2; }
echo "Pronto. Teste com: python3 motor/episodio3d.py preview 10"
