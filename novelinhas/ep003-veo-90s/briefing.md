# Briefing — teste Veo 3.1 Lite, estética sitcom anos 90 (ep003, café): 3 planos com fala

Autorizado pelo Lucas: **limite US$ 1,50 no Runware, só este teste.** Nova tentativa só se couber no limite.
Saldo antes: US$ 3,60. Modelo: Veo 3.1 Lite, imagem → vídeo, 720p, áudio nativo.

## 1. Planta do cenário (fixa em todos os planos)

```
                 RUA (desfocada, carros dos anos 90)
  ┌──────────────── JANELA GRANDE DA FRENTE ─────────────────┐   ← única luz: sol de fim de tarde,
  │  [vaso]          [vaso]           [vaso]        [vaso]    │     dourado, entrando pela janela
  │                                                           │     (contraluz atrás do casal)
  │      VANESSA (sentada)   ( MESA  )   DIEGO (sentado,      │
  │      lado ESQUERDO        redonda     fora de quadro      │
  │      da mesa              madeira     nestes planos)      │
  │                          2 cardápios                      │
  │                            fechados          LUCAS (em pé,│
  │                                              lado DIREITO │
  │                                              da mesa)     │
  │                                                           │
  │   ······················ EIXO 180° ······················ │
  │                                                           │
  │            CÂMERA sempre deste lado (balcão)              │
  │   [balcão de madeira, máquina de espresso cromada antiga, │
  │    registradora mecânica, telefone de parede com fio]     │
  └───────────────────────────────────────────────────────────┘
```

- **Vanessa:** sentada no lado **esquerdo** da mesa, sempre à **esquerda da tela**. Olha **para cima e à direita** (para o Lucas).
- **Lucas:** em pé no lado **direito** da mesa, sempre à **direita da tela**. Olha **para baixo e à esquerda** (para a Vanessa).
- **Câmera:** sempre do lado do balcão; **nunca cruza o eixo**. Fundo de todos os planos: **a janela** com a rua desfocada.
- **Luz:** uma só, o sol dourado de fim de tarde vindo da janela, **atrás** da Vanessa e na **lateral esquerda/fundo** do Lucas. Sem luminárias acesas em destaque.
- **Mesa:** redonda de madeira, **só 2 cardápios de papel fechados** (sem xícaras, copos ou celular; nada muda entre os planos).
- **Figurantes:** nenhum.

## 2. Estética sitcom anos 90 (em tudo)
- **Imagem:** "cena de sitcom americana/brasileira de TV dos anos 90 filmada em 35 mm": cor quente e saturada, pele com tom âmbar, preto levemente lavado, leve suavização (halation nos realces da janela), grão de filme.
- **Café dos anos 90:** paredes creme com lambri de madeira escura, cadeiras de madeira com assento de palhinha, piso de madeira, quadros emoldurados genéricos sem texto legível, plantas em vasos de barro. **Sem letreiros legíveis.**
- **Figurino dos anos 90 (identidade igual à das referências):**
  - **Vanessa:** cabelo castanho-claro em **rabo de cavalo baixo com scrunchie de veludo bordô**, repartido no meio; **blusa de seda branca de manga longa com ombreiras leves**, abotoada; **um colar fino de ouro**. Sem brincos, sem óculos, sem bolsa.
  - **Lucas:** cabelo escuro curto e ondulado, barba curta; **camiseta branca de gola redonda, avental bege** amarrado no pescoço e na cintura; **bloquinho de papel na mão esquerda e caneta na direita**. Sem celular.
- **Acabamento único no ffmpeg (igual nos 3 planos):** cor quente (+saturação 15%), contraste suave com pretos levemente lavados, leve desfoque (σ 0,6), brilho difuso nos realces, grão animado, vinheta leve.

## 3. Voz (descrição idêntica em todo prompt da mesma personagem)
- **VOZ_VANESSA:** `female voice, early thirties, native Brazilian Portuguese with a São Paulo accent, clear medium pitch, arrogant and mocking tone, natural conversational pace`
- **VOZ_LUCAS:** `male voice, early thirties, native Brazilian Portuguese with a São Paulo accent, warm calm baritone, polite and unhurried`
- Só fala quem está de frente; quem está de costas fica calado.

## 4. Planos (sequência A → B → C)

| Plano | Duração | Enquadramento | Fala (pt-BR) | Quadro inicial |
|---|---|---|---|---|
| **A** | 6 s | Por cima do ombro do Lucas: Vanessa sentada à esquerda, de frente, olhando para cima e à direita; em primeiro plano, à direita, o ombro e o braço do Lucas de costas, desfocados | VANESSA: "Lucas? Não acredito. Você ainda tá servindo mesa?" | Seedream (refs Vanessa e Lucas + mestre do cenário v3) |
| **B** | 4 s | Contraplano por cima do ombro da Vanessa: Lucas em pé à direita, três-quartos, olhando para baixo e à esquerda, com bloquinho e caneta; em primeiro plano, à esquerda, a nuca e o rabo de cavalo da Vanessa (scrunchie bordô), desfocados | LUCAS: "Tô sim, Vanessa. E vocês, o que vão querer?" | Seedream (refs Lucas e Vanessa + **quadro A** como referência de cenário e luz) |
| **C** | 6 s | **Mesmo enquadramento do A** | VANESSA: "Um café. E capricha, viu? Pelo menos isso você sabe fazer." | **Último quadro real do vídeo A** (continuidade total de pose, luz e objetos) |

Som de cada clipe: só a fala + ambiente baixo de café (máquina de espresso antiga ao longe). **Sem música, sem legenda.**

## 5. Checagens depois de gerar
- **Continuidade:** pares de quadros em cada corte (A→B, B→C): lado de cada personagem, luz, mesa, figurino, scrunchie, colar, bloquinho.
- **Voz da Vanessa A × C (medição, já que não consigo ouvir):** frequência fundamental (mediana e faixa) e timbre (MFCC médio, centróide espectral) dos trechos com fala, comparados entre A e C, com o Lucas (B) como controle.
- **Montagem:** A+B+C, acabamento anos 90 único, -14 LUFS.

## 6. Custo estimado
| Item | US$ |
|---|---|
| 2 quadros Seedream (A, B) | ~0,09 |
| Veo 3.1 Lite 720p: 6 + 4 + 6 = 16 s × 0,05 | 0,80 |
| **Total** | **~0,89** (limite rígido 1,50; sobra para no máximo 1 nova tentativa) |
