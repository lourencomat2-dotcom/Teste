#!/usr/bin/env bash
# Instala o que o projeto precisa. Testado em Ubuntu/Debian (no Windows, use o WSL).
# No macOS: brew install ffmpeg espeak-ng  e instale o Blender pelo site (blender.org).
set -e
cd "$(dirname "$0")"
SUDO=""; [ "$(id -u)" != "0" ] && SUDO="sudo"

if command -v apt-get >/dev/null 2>&1; then
  $SUDO apt-get update
  $SUDO apt-get install -y ffmpeg espeak-ng python3-numpy   # numpy do sistema: o exportador glTF do Blender precisa
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
cd ..
# personagens realistas (MakeHuman, opcional, ~120 MB): dados oficiais via npm e alvos de forma via PyPI
if [ ! -f vendor/makehuman/targets.npz ] && command -v npm >/dev/null 2>&1; then
  T=$(mktemp -d); mkdir -p vendor/makehuman
  (cd "$T" && npm pack makehuman-data@0.0.2 --silent && tar -xzf makehuman-data-0.0.2.tgz) && rm -rf vendor/makehuman/dados && mv "$T/package/public/data" vendor/makehuman/dados
  python3 -m pip download --no-deps -d "$T" makehuman==1.3.2 && python3 -c "import zipfile,sys; open('vendor/makehuman/targets.npz','wb').write(zipfile.ZipFile(sys.argv[1]).read('makehuman/data/targets.npz'))" "$T"/makehuman-1.3.2-py3-none-any.whl
  rm -rf "$T"
fi
# versão three.js (tempo real): precisa de Node.js 18+
if command -v npm >/dev/null 2>&1; then
  (cd tempo_real && npm install --no-audit --no-fund && { npx playwright install chromium || echo "Chromium do Playwright não instalado (só é preciso para capturar o vídeo)."; })
else
  echo "npm não encontrado: instale o Node.js para usar a versão three.js (tempo_real/)."
fi
echo "Pronto. Teste com: python3 motor/episodio3d.py preview 10"
