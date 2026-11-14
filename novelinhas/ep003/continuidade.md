# Relatório de continuidade — ep003, teste v3

Vídeo montado **localmente** (`ep003/saida/video.mp4`, 40,0 s, -13,9 LUFS). **Ainda não foi publicado**: pela regra do briefing, plano reprovado na checagem automática interrompe a entrega.
Pares de quadros de cada corte: `continuidade.jpg` (antes → depois, com ΔE de cor).

## Checagem automática

| Plano | Resultado | Tentativas | Detalhe |
|---|---|---|---|
| 1 (aberto, casal) | ✅ | 1 | Vanessa e Diego batem com a referência; último quadro inconclusivo (o detector contou 4 rostos, incluindo pessoas na rua) |
| 2 (close Vanessa) | ✅ | 1 | 3 de 3 quadros ok |
| 3 (aberto, Lucas entra) | ✅ | 1 | último quadro ok para Vanessa e Diego; o Lucas entra só do pescoço para baixo, como planejado |
| 4 (close Lucas) | ✅ | 1 | 3 de 3 quadros ok |
| 5 (close Vanessa) | ✅ | 1 | 3 de 3 quadros ok |
| 6 (close Diego) | ❌ | 2 (limite) | início e meio ok; último quadro "sem rosto detectado" |
| 7 (close Lucas, reação) | ❌ | 2 (limite) | início e fim ok; quadro do meio "sem rosto detectado" |

**Cor entre cortes (limite ΔE 12):** 5,5 · 5,0 · 4,9 · 5,5 · 2,5 · 10,9, todos dentro do limite.

## Revisão visual (humana) dos reprovados

- **Plano 6:** o rosto do Diego é o mesmo da referência em todos os quadros. Ele inclina a cabeça para cima e para a direita, olhando para o Lucas como pede o eixo, e o detector frontal/de perfil perde o rosto nesse ângulo. Provável **falso negativo**.
- **Plano 7:** mesmo caso. O Lucas olha para baixo, para o bloquinho, e o detector perde o rosto no quadro do meio. Na **tentativa 1** o gerador de vídeo **inventou um letreiro ("Flubcko") na janela**. A tentativa 2, usada na montagem, não tem letreiro. A checagem automática não detecta texto; isso precisa entrar na ferramenta.

## Continuidade observada nos cortes

- Posições fixas respeitadas: Vanessa à esquerda e Diego à direita no plano aberto; Lucas à direita, ao lado do Diego; fundo sempre a janela.
- Olhares de acordo com o eixo: Vanessa e Diego olham para cima e à direita; Lucas olha para baixo e à esquerda (close espelhado).
- Figurino estável: rabo de cavalo e blusa branca com colar fino (Vanessa); blazer azul-marinho e camisa branca (Diego); camiseta branca, avental e bloquinho com caneta (Lucas). Nenhum celular, nenhuma joia extra.
- Mesa: só os cardápios, coerente com "O que vocês vão querer?".
- Ponto de atenção: no fim do plano 3, o Diego continua lendo o cardápio em vez de olhar para o Lucas (o prompt pedia que o casal olhasse para ele).
- A sincronia labial não dá para verificar só por quadros; nos closes, a boca abre e fecha durante as falas.

## Custo real

Saldo antes: US$ 10,38 → depois: US$ 7,58 = **US$ 2,80** (teto de US$ 3). Sobram US$ 0,20, insuficiente para refazer qualquer plano dentro do teto.
