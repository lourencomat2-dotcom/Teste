#!/bin/bash
# Regressão por quadros de controle: gera os quadros 60, 150, 200 e 320 nas três versões da abertura
# (estilizada, ?humanos e ?humanos&mocap) e compara com os aprovados em testes/referencia/.
#   bash tempo_real/testes/regressao.sh            # gera e compara (sai com 1 se algo mudou)
#   bash tempo_real/testes/regressao.sh aprovar    # copia os gerados para referencia/ (depois de o Lucas aprovar)
# Mudança visual sem pedido é efeito colateral: corrigir ou perguntar antes do commit.
set -e
AQUI=$(cd "$(dirname "$0")" && pwd); RAIZ=$(cd "$AQUI/../.." && pwd)
GER=$RAIZ/saida/regressao; REF=$AQUI/referencia
QUADROS="60 150 200 320"
declare -A MODOS=([estilizada]='&semlegenda' [humanos]='&humanos&semlegenda' [mocap]='&humanos&mocap&semlegenda')
if [ "$1" = aprovar ]; then
  for m in "${!MODOS[@]}"; do mkdir -p "$REF/$m"; cp "$GER/$m"/rt_*.png "$REF/$m/"; done
  echo "referência atualizada em $REF"; exit 0
fi
for m in estilizada humanos mocap; do
  mkdir -p "$GER/$m"; rm -f "$GER/$m"/rt_*.png
  echo "== $m"
  PARAMS="${MODOS[$m]}" node "$RAIZ/tempo_real/capturar.cjs" "$GER/$m/x.mp4" $QUADROS 2>&1 | grep -E "^\[erro\]" || true
  for f in $QUADROS; do                        # 640x360 basta para comparar e mantém o repositório leve
    python3 -c "from PIL import Image; im = Image.open('$GER/$m/rt_$f.png'); im.convert('RGB').resize((640, 360), Image.LANCZOS).save('$GER/$m/rt_$f.png')"
  done
done
python3 "$RAIZ/motor/comparar_quadros.py" "$REF" "$GER" "$GER/prancha_mudancas.jpg"
