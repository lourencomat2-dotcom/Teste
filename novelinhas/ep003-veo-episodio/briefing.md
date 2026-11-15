# Briefing — ep003 completo no Veo 3.1 Lite (café, toque anos 90)

**"Ela humilhou o EX-NAMORADO por ser pobre... mas não imaginava quem ele havia se tornado!"**
Formato: 16:9, 720p, ~50 s de história + card final curto. Sem narrador, sem texto na tela (só o card final).
Base aprovada: testes `ep003-veo-test` e `ep003-veo-90s` (cortes, continuidade e voz da Vanessa entre clipes).

## Ajuste do Lucas (estética)
- **Um toque de anos 90, sem carregar.** Cor **natural e neutra** nos prompts (nada de "warm saturated Kodak"); o anos 90 vem do **figurino, dos objetos e do cenário** e de um acabamento **suave** no ffmpeg.
- Acabamento final único (`grade_suave`): saturação +4%, leve calor (≈1,5%), pretos quase intactos, brilho difuso de 6% nos realces, desfoque σ 0,35, grão leve (3), vinheta discreta.
- **Manter** a dinâmica de cortes (plano/contraplano por cima do ombro) e a continuidade (último quadro → primeiro quadro nos planos contínuos; referências fixas).

## Personagens (o que NÃO pode mudar; repetido em todo prompt)
| Personagem | Visual fixo | Voz (descrição idêntica em todo prompt) |
|---|---|---|
| **Vanessa** (vilã) | ref `ep003/refs/vanessa_*`; rabo de cavalo baixo com **scrunchie de veludo bordô**, repartido no meio; **blusa de seda branca de manga longa com ombreiras leves**; **colar fino de ouro**; sem brincos, óculos ou bolsa | `female voice, early thirties, native Brazilian Portuguese with a São Paulo accent, clear medium pitch, arrogant and mocking tone, natural conversational pace` |
| **Diego** (marido arrogante) | ref `ep003/refs/diego_*`; cabelo preto penteado para trás; **blazer azul-marinho de ombros largos (anos 90)** sobre camisa branca de gola aberta; sem relógio/joias | `male voice, mid thirties, native Brazilian Portuguese with a São Paulo accent, slightly nasal, smug and condescending, relaxed pace` |
| **Lucas** (herói, "garçom") | ref `ep003/refs/lucas_*`; cabelo escuro curto ondulado, barba curta; **camiseta branca de gola redonda, avental bege**; **bloquinho na mão esquerda, caneta na direita**; nunca celular | `male voice, early thirties, native Brazilian Portuguese with a São Paulo accent, warm calm baritone, polite and unhurried` |
| **Dona Marta** (gerente, figura mais velha afável) | **nova referência** (seed fixa): brasileira, ~65 anos, pele morena, cabelo grisalho curto e cacheado, óculos de leitura pendurados num cordão, **cardigã vinho sobre blusa creme**, crachá sem texto legível | `female voice, mid sixties, native Brazilian Portuguese with a São Paulo accent, warm, gentle, slightly husky` |

## Planta do cenário (igual aos testes)
```
                 RUA (desfocada, carros dos anos 90)
  ┌──────────────── JANELA GRANDE DA FRENTE ─────────────────┐  ← única luz: sol de fim de tarde
  │      VANESSA (sentada,   ( MESA  )   DIEGO (sentado,      │
  │      ESQUERDA da tela)    redonda     DIREITA do casal)   │
  │                          2 cardápios                      │
  │                            fechados        LUCAS (em pé,  │
  │                                            DIREITA, ao    │
  │                                            lado do Diego) │
  │   ······················ EIXO 180° ······················ │
  │  CÂMERA sempre deste lado (balcão: máquina de espresso    │
  │  cromada antiga, registradora mecânica, telefone de fio)  │
  │  DONA MARTA chega pela DIREITA da tela, vindo do balcão   │
  └───────────────────────────────────────────────────────────┘
```
- Olhares: Vanessa e Diego olham **para cima e à direita** (Lucas/Marta em pé); Lucas e Marta olham **para baixo e à esquerda**.
- Luz: uma só, sol de fim de tarde pela janela, **sempre do mesmo lado** (fundo/direita da tela), cor **neutra-quente natural**.
- Mesa: **só 2 cardápios fechados** o episódio inteiro (eles não chegam a pedir nada).
- Figurantes: nenhum. Sem letreiros legíveis.

## Planos (13 planos; durações do Veo 4/6/8 s, cortados na montagem)
| # | Gerar | Usar | Enquadramento | Ação / fala (pt-BR) | Quadro inicial |
|---|---|---|---|---|---|
| 1 | 6 s | ~5 s | Plano aberto frontal do casal sentado | VANESSA olha em volta: "Olha só, esse lugar aqui só tem pé-rapado, né?" | Seedream (refs V, D + mestre v3) |
| 2 | 4 s | ~3 s | Close do Diego, olhando para ela (esquerda) | DIEGO, debochado: "Foi você que quis parar aqui, amor." | Seedream (ref D + quadro 1) |
| 3 | 6 s | ~4 s | Mesmo plano aberto do 1 | Lucas entra pela direita (só do pescoço para baixo) e para ao lado do Diego; o casal levanta o olhar. Sem fala | **último quadro do 1** |
| 4 | 6 s | ~5 s | Por cima do ombro do Lucas → Vanessa | VANESSA: "Lucas? Não acredito. Você ainda tá servindo mesa?" | Seedream (refs V, L + quadro 1) |
| 5 | 4 s | ~3,5 s | Contraplano por cima do ombro da Vanessa → Lucas, **perto da mesa** | LUCAS: "Tô sim, Vanessa. E vocês, o que vão querer?" | Seedream (refs L, V + quadro 4) |
| 6 | 4 s | ~3,5 s | Close do Diego olhando para cima e à direita | DIEGO: "Então esse é o ex? Olha o avental dele." | Seedream (ref D + quadro 1) |
| 7 | 6 s | ~5 s | Mesmo enquadramento do 4 | VANESSA: "Um café. E capricha, viu? Pelo menos isso você sabe fazer." | **último quadro do 4** |
| 8 | 4 s | ~3 s | Close do Lucas (mesmo eixo do 5), calmo, anota | Sem fala; leve sorriso | **último quadro do 5** |
| 9 | 6 s | ~5 s | Plano médio: Dona Marta chega pela direita até o Lucas | MARTA, carinhosa: "Seu Lucas, o contador ligou. A rede fechou o melhor mês do ano!" | Seedream (refs M, L + quadro 5) |
| 10 | 4 s | ~3 s | Close da Vanessa, chocada, olhando para cima e à direita | VANESSA, baixinho: "Seu Lucas? Rede?" | Seedream (ref V + quadro 4) |
| 11 | 6 s | ~5 s | Por cima do ombro da Vanessa → Lucas (mesmo do 5) | LUCAS, calmo: "Pois é. Esse café foi o primeiro de doze. O de vocês é por conta da casa." | **último quadro do 8** |
| 12 | 4 s | ~3 s | Close do Diego, sem graça, abaixa o cardápio | DIEGO, envergonhado: "Amor... vamos embora." | **último quadro do 6** |
| 13 | 4 s | ~3,5 s | Plano aberto (mesmo do 1/3): Lucas se afasta pela direita com a Dona Marta; o casal fica parado | Sem fala; fade | Seedream (refs V, D + último quadro do 3) |

História ≈ 51 s + card final de 4 s ("INSCREVA-SE / ATIVA O SININHO").
Som: fala + ambiente de café em cada clipe (Veo); **trilha leve** de sitcom/novela por baixo (MiniMax Music, instrumental), subindo na revelação (planos 9–11); -14 LUFS estéreo.

## Checagens antes de entregar
- Pares de quadros em todos os cortes (lado, luz, mesa, figurino, objetos, distância).
- Voz de cada personagem comparada entre os clipes em que ela fala (F0 e MFCC), como no teste anterior.
- Sem letreiros inventados (revisão visual).

## Custo estimado
| Item | US$ |
|---|---|
| Referência nova (Dona Marta) | 0,04 |
| Quadros Seedream (9) | ~0,40 |
| Veo 3.1 Lite 720p: 6+4+6+6+4+4+6+4+6+4+6+4+4 = **64 s × 0,05** | **3,20** |
| Trilha MiniMax Music | ~0,15 |
| **Base** | **~3,80** |
| Reserva para refazer até ~2 planos | ~0,60 |
| **Máximo** | **~4,40** |

Saldo no Runware no momento do briefing: **US$ 2,81** → **não cobre o episódio.**
