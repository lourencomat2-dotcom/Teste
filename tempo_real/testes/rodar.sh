#!/usr/bin/env bash
# Roda todos os testes automáticos da versão three.js (Node). Sai com erro se algum falhar.
cd "$(dirname "$0")/.." || exit 1
falhas=0; total=0
for t in testes/*.test.mjs; do
  total=$((total + 1)); echo "== $t"
  node "$t" || falhas=$((falhas + 1))
done
echo "-- $((total - falhas)) de $total arquivos de teste passaram"
[ "$falhas" -eq 0 ]
