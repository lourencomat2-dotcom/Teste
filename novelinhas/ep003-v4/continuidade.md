# Relatório de continuidade e áudio — ep003, teste v4

Vídeo: `novelinhas/teste/ep003-ex-namorado-cafe-v4.mp4` — 39,1 s (31,1 s de história + 8 s de card), 1920×1080, H.264 + AAC estéreo 48 kHz.
Pares de quadros de cada corte: `continuidade.jpg`. Números da checagem: `checagem/relatorio.json`.

## Modelos usados
- Falas: **OmniHuman 1.5** (sincronia labial a partir da imagem-mestra + áudio), ~US$ 0,12/s.
- Ação: **Kling 2.6 Pro**, imagem → vídeo, 5 s, sem áudio nativo (cortado na duração do plano), US$ 0,07/s.
- Vozes: **MiniMax Speech 2.8** com emoção por trecho (`disgusted`, `calm`, `surprised` → `disgusted`, `happy`), reforço de idioma `pt`, 12% mais rápido e pausas internas limitadas a 0,25 s.
- Referências e imagens-mestras: as mesmas da v3 (reaproveitadas, custo zero).

## Checagem automática (5 quadros por plano)

| Plano | Resultado | Tentativas | Observação |
|---|---|---|---|
| 1 — aberto, casal | ✅ | 1 | Vanessa e Diego batem com a referência em 4/5 quadros (1 inconclusivo) |
| 2 — close Vanessa | ✅ | 1 | 5/5 |
| 3 — aberto, Lucas entra | ✅ | 1 | casal ok no início; depois o tronco do Lucas entra no quadro e o detector conta 1 rosto (inconclusivo, não reprova) |
| 4 — close Lucas | ✅ | 1 | 5/5 |
| 5 — close Vanessa | ✅ | 1 | 5/5 |
| 6 — close Diego | ✅ | 1 | 3/5 detectados (cabeça virada para cima nos outros 2), todos dentro do limiar |
| 7 — close Lucas, reação | ✅ | 1 | 5/5 |

**Cor entre cortes (ΔE Lab, limite 12):** 4,0 · 8,7 · 5,4 · 9,6 · 4,6 · 2,3, todos dentro do limite.
Nenhuma nova tentativa foi necessária (US$ 0 de retentativas).

## Revisão visual dos cortes (pares em `continuidade.jpg`)

**Bate:**
- Posições fixas (regra dos 180°): Vanessa à esquerda e Diego à direita; Lucas entra pela direita e fica ao lado do Diego; fundo sempre a janela.
- Olhares de acordo com o eixo: Vanessa e Diego olham para a direita e para cima; Lucas olha para a esquerda e para baixo.
- Correção da v3 aplicada: no plano 3, **o casal levanta o olhar para o garçom** (o Diego para de ler o cardápio).
- Plano 3 encadeado no último quadro real do plano 1 (mesma pose: Diego com a mão no quadril); plano 7 encadeado no último quadro do plano 4.
- Figurino e cabelo estáveis: rabo de cavalo e blusa branca com colar fino (Vanessa); blazer azul-marinho e camisa branca (Diego); camiseta branca, avental bege e bloquinho com caneta (Lucas). Sem celular, sem joias extras. Sem figurantes dentro do café.
- Nenhum letreiro inventado nos 54 quadros revisados.

**Não bate (erros encontrados):**
1. **~9–14 s (dentro do plano 3): o cardápio do Diego muda de cor**, de papel branco para amarelado ou laranja, quando ele o levanta. Falha do Kling 2.6 Pro dentro do plano, não no corte.
2. **~4,0 s (corte 1):** no plano aberto a Vanessa olha para baixo e à direita, para o Diego; no close ela olha para a direita mas na altura do rosto. Pequena diferença de altura do olhar.
3. **Avental do Lucas** com um pequeno emblema no peito nos closes (planos 4 e 7) que não aparece no plano 3 (só tronco, outro ângulo). Consistente entre os closes; mínimo.
4. **Expressão da Vanessa no plano 2:** o OmniHuman fez deboche sorridente, mais do que nojo. Combina com a fala, mas é menos agressivo que o pedido.

## Áudio
- Volume integrado **-14,4 LUFS** (meta -14), pico **-1,3 dBFS** (limite -1,5 dB de true peak no normalizador; o medidor mostra -1,3 dBFS após o AAC), variação de volume (LRA) de 5,7 LU, estéreo 48 kHz.
- Nível médio: trecho com fala -16,9/-17,0 dB RMS; card final (só trilha subindo) -17,9 dB RMS. A trilha fica por baixo da fala (sidechain) e sobe nos picos (planos 5 e 7) e no card.
- Abertura: 0–4 s ambiente de café (efeito gerado a partir do vídeo do plano 1), primeira fala (humilhação) começa em **4,0 s**.
- Efeitos: plano 1 ambiente de café, plano 3 passos se aproximando, plano 7 caneta no papel (gerados pelo Mirelo a partir do próprio vídeo, sincronizados).
- **Não verificado (preciso do ouvido do Lucas):** sotaque das vozes MiniMax (o modelo só tem "português", sem distinguir pt-BR de pt-PT), naturalidade da emoção e se a sincronia labial está perfeita. Eu não consigo ouvir áudio.

## Custo real
Saldo do Runware antes: **US$ 7,58** → depois: **US$ 4,03** = **US$ 3,54**
(vídeo de fala US$ 2,15 · vídeo de ação US$ 1,05 · efeitos US$ 0,15 · vozes ~US$ 0,04 · o restante são as cobranças de imagem/upload e arredondamentos do Runware).
