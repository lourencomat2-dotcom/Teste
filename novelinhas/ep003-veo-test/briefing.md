# Briefing — teste Veo 3.1 Lite (ep003, café): 2 planos com fala

Autorizado pelo Lucas: **só este teste, até ~US$ 1,00 no Runware.** Nenhuma nova tentativa, nada além destes 2 planos.
Mesmo roteiro, cenário e fichas do ep003 (ver `novelinhas/ep003/briefing.md`). Referências e cenário reaproveitados da v3/v4.

## Personagens (o que NÃO pode mudar, repetido em todo prompt)

- **Vanessa** (ref: `ep003/refs/vanessa_*.png`): brasileira, 30 anos, pele clara, cabelo castanho-claro liso em **rabo de cavalo baixo repartido no meio**, **blusa de seda branca de manga longa abotoada**, **um colar fino de ouro**, sem brincos, sem óculos, sem bolsa.
- **Lucas** (ref: `ep003/refs/lucas_*.png`): brasileiro, 32 anos, pele morena clara, cabelo escuro curto e ondulado, barba curta, **camiseta branca de gola redonda, avental bege**, **bloquinho de papel na mão esquerda e caneta na direita**, nunca celular.
- **Diego** está à mesa (à direita da Vanessa), mas **fica fora do quadro** nestes 2 planos.

## Voz (descrição idêntica em todo prompt; só fala quem está de frente)
- **VOZ_VANESSA:** `female voice, early thirties, native Brazilian Portuguese with a São Paulo accent, clear medium pitch, arrogant and mocking tone, natural conversational pace`
- **VOZ_LUCAS:** `male voice, early thirties, native Brazilian Portuguese with a São Paulo accent, warm calm baritone, polite and unhurried`

## Cenário e luz (iguais aos da v4)
Café de bairro pequeno, paredes creme e madeira; mesa redonda de madeira **encostada na janela da frente**; fim de tarde (~17h); **uma única luz**: sol dourado entrando pela janela atrás dos personagens (contraluz suave); rua desfocada lá fora; vasinhos no parapeito; **nenhum outro cliente**. Na mesa: **só dois cardápios de papel fechados**.

## Eixo (180°)
Vanessa sentada à **esquerda**, Lucas em pé do lado **direito** da mesa. A câmera nunca cruza o eixo: a Vanessa olha **para cima e à direita**, o Lucas olha **para baixo e à esquerda**.

## Plano A — Vanessa fala, por cima do ombro do Lucas (6 s)
- **Enquadramento:** plano médio-close da Vanessa sentada, de frente, olhando para cima e à direita. Em primeiro plano, à **direita** da tela, **o ombro e o braço do Lucas de costas** (camiseta branca, alça do avental bege), desfocados. A boca do Lucas não aparece.
- **Fala (pt-BR):** VANESSA: "Lucas? Não acredito. Você ainda tá servindo mesa?"
- **Atuação:** reconhece, ergue as sobrancelhas, sorriso de deboche.
- **Som:** fala + ambiente baixo de café (máquina de espresso ao longe). **Sem música, sem legenda.**

## Plano B — contraplano: Lucas responde (4 s)
- **Enquadramento:** plano médio do Lucas em pé, três-quartos, olhando para baixo e à esquerda, segurando o bloquinho e a caneta na altura do peito. Em primeiro plano, à **esquerda** da tela, **a nuca e o rabo de cavalo da Vanessa de costas**, desfocados. A boca da Vanessa não aparece.
- **Fala (pt-BR):** LUCAS: "Tô sim, Vanessa. E vocês, o que vão querer?"
- **Atuação:** calmo, educado, leve sorriso, sem se abalar.
- **Som:** fala + o mesmo ambiente de café. **Sem música, sem legenda.**

## Geração
1. Quadro inicial de cada plano: **Seedream 5.5** com as referências da Vanessa e do Lucas + a imagem-mestra do cenário (`ep003/mestres/m01_*`), seed fixa (41001 e 41002).
2. **Veo 3.1 Lite**, imagem → vídeo, **720p**, `generateAudio: true`, A = 6 s, B = 4 s.
3. Montagem A+B em sequência (sem trilha, sem correção extra; só o volume normalizado para -14 LUFS para ouvir).

## Custo estimado
| Item | US$ |
|---|---|
| 2 quadros Seedream | ~0,07 |
| Veo 3.1 Lite: 10 s × US$ 0,05 (720p) | ~0,50 (até 0,80 se cobrado a US$ 0,08/s) |
| **Total** | **~0,57 (máximo ~0,87)**, limite rígido de 1,00 |
