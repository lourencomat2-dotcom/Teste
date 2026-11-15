# ep003 — Roteiro v2 (Veo 3.1, ~50 s)

**"Ela humilhou o EX-NAMORADO por ser pobre... mas não imaginava quem ele havia se tornado!"**
16:9 · 720p · Veo 3.1 Lite com áudio nativo · sem narrador · sem texto na tela (só card final).

## O que mudou em relação ao episódio parcial (feedback do Lucas)
| Problema | Causa | Correção no v2 |
|---|---|---|
| (a) Barulho estranho no áudio | A cama de ambiente foi feita com o som do **plano 8 (Lucas escrevendo)**, que tem **cliques periódicos ~10/s** da caneta; em loop sob o episódio inteiro virou um tique-tique constante | **Nenhum som de ação vira cama.** Nos prompts do Veo: "quiet room tone, no rhythmic sounds, no writing or clicking sounds, no music". Ninguém escreve no bloquinho enquanto alguém fala. A cama de ambiente é gerada à parte (sala silenciosa, sem cliques) e **verificada no espectro** antes de entrar; a trilha só na edição. |
| (b) Erros de fala ("pé-rapado" separado) | Palavras com hífen e gírias curtas o Veo quebra ou pronuncia mal | Falas reescritas **sem hífen, sem siglas, sem números em algarismo**, frases curtas e de ritmo natural; lidas em voz alta antes de fechar |
| (c) Roteiro mal planejado | Diálogo picado, Diego quase sem papel, fim abrupto (o plano do Diego não foi gerado) | Arco em 3 atos com começo (humilhação), virada (Dona Marta) e fecho (Diego desiste, eles saem de cena); 9 planos, cada um com função |
| (d) Coisas estranhas na mudança de ângulo (cardápios numa mesinha lateral) | O contraplano não descrevia **onde está a mesa** nem **que as outras mesas estão vazias** | Planta fixa + em todo prompt: "a mesa redonda deles na parte de baixo do quadro, com os 2 cardápios na frente da Vanessa e do Diego; **as outras mesas estão vazias, sem nada em cima**" |
| Voz da Dona Marta parecida com a da Vanessa (213 × 222–229 Hz) | Descrições de voz próximas ("female, warm…") | Vozes com **idade, altura e ritmo opostos** (ver abaixo) |

## Personagens e vozes (texto idêntico em todo prompt)
| Personagem | Visual fixo (MUST NOT CHANGE) | Voz |
|---|---|---|
| **Vanessa** (30, vilã) | ref `ep003/refs/vanessa_*`; rabo de cavalo baixo com **scrunchie de veludo bordô**, repartido no meio; **blusa de seda branca manga longa com ombreiras leves**; **colar fino de ouro**; sem brincos, óculos ou bolsa | `young woman about 30, HIGH bright voice, fast sharp delivery, mocking and arrogant, native Brazilian Portuguese (São Paulo accent)` |
| **Diego** (35, marido) | ref `ep003/refs/diego_*`; cabelo preto penteado para trás; **blazer azul-marinho de ombros largos** sobre camisa branca aberta; sem relógio/joias | `man about 35, nasal tenor voice, quick smug delivery with a short laugh, native Brazilian Portuguese (São Paulo accent)` |
| **Lucas** (32, herói) | ref `ep003/refs/lucas_*`; cabelo escuro curto ondulado, barba curta; **camiseta branca gola redonda, avental bege**; **bloquinho na mão esquerda, caneta na direita**; nunca celular | `man about 32, deep calm baritone, slow and polite, native Brazilian Portuguese (São Paulo accent)` |
| **Dona Marta** (65, gerente) | **ref nova** (seed fixa); cabelo grisalho curto e cacheado, óculos de leitura num cordão, **cardigã vinho** sobre blusa creme, crachá sem texto | `ELDERLY woman about 65, LOW husky alto voice, slow warm grandmotherly pace, native Brazilian Portuguese (São Paulo accent)` |

## Espaço (ver `planta_cafe.jpg`)
- Mesa redonda **T1** encostada na **janela da frente** (fundo). **Vanessa** sentada à **esquerda** de T1, **Diego** à **direita** de T1, ambos de frente para o balcão. **2 cardápios fechados** sobre T1, um na frente de cada um. Mais nada na mesa o episódio inteiro (os cafés nunca chegam).
- **Lucas** vem do balcão (frente/direita) e fica **em pé do lado direito de T1, encostado na mesa, ao lado do Diego**, de frente para o casal.
- **Dona Marta** vem do balcão pela direita e para **à direita do Lucas** (mais perto do balcão).
- **Outras mesas (T2, T3):** vazias, sem nada em cima. Sem outros clientes. Porta de entrada na parede esquerda (ninguém usa nesta cena).
- **Eixo 180°:** linha casal ↔ Lucas. **A câmera fica sempre do lado do balcão.** Vanessa e Diego olham **para cima e à direita**; Lucas e Marta olham **para baixo e à esquerda**.
- **Luz:** uma só, luz natural de fim de tarde pela janela (atrás do casal), **neutra e contida**, preenchimento suave do lado do balcão.
- **Visual:** cor neutra, saturação reduzida, só um toque de anos 90 (figurino, telefone de fio e registradora no balcão, carros antigos lá fora); acabamento `grade_suave.txt` na edição.

## Planos (9 planos · 54 s gerados → ~49 s usados + card 4 s)
| # | Dur. | Enquadramento (câmera) | Quem fala / fala exata | Em quadro e onde | Mãos / mesa | Quadro inicial |
|---|---|---|---|---|---|---|
| **1** | 8 s | **MESTRE** aberto frontal (C1): mesa T1 inteira, janela atrás | **VANESSA** (olhando o café, depois para o Diego): *"Nossa, amor... que lugar mais simples, hein? Só tem gente sem dinheiro aqui."* — no fim, o Lucas chega pela direita e para ao lado do Diego (só do peito para baixo; cabeça sai pelo topo) | Vanessa (esq.), Diego (dir.), Lucas entrando (dir.) | Diego segura o cardápio dele; o da Vanessa na mesa. Lucas com bloquinho e caneta | Seedream |
| **2** | 6 s | **Over-the-shoulder do Lucas** (C2): Vanessa de frente; costas/ombro do Lucas à direita; Diego visível entre os dois, meio encoberto | **VANESSA** (reconhece, deboche): *"Lucas? Não acredito! Você ainda trabalha servindo mesa?"* | Vanessa (esq.), Diego (centro, parcial), Lucas de costas (dir., primeiro plano) | Cardápios em T1 na frente dela | Seedream |
| **3** | 6 s | **Contraplano over-the-shoulder da Vanessa** (C3): nuca/ombro da Vanessa à esquerda; **T1 na parte de baixo** com os cardápios; Diego sentado de perfil; Lucas em pé encostado na mesa | **LUCAS** (calmo): *"Trabalho, sim. Boa tarde, Vanessa. O que vocês vão querer?"* | Vanessa de costas (esq.), Diego (centro), Lucas (dir.) | Lucas segura bloquinho e caneta **parados** (não escreve) | Seedream |
| **4** | 6 s | **Close do Diego** (C4): Diego de frente, olhando para cima e à direita; **ombro da Vanessa** na borda esquerda | **DIEGO** (risadinha): *"Então esse é o ex? Olha só o avental, amor."* | Diego (centro), ombro da Vanessa (esq.); Lucas fora de quadro à direita (em pé, acima do enquadramento) | Diego segura o cardápio | Seedream |
| **5** | 6 s | Igual ao **2** (C2) | **VANESSA** (de cima para baixo): *"Traz dois cafés. E capricha, viu? Pelo menos isso você sabe fazer."* | igual ao 2 | igual ao 2 | **último quadro do 2** (Seedream só como referência) |
| **6** | 8 s | Igual ao **3** (C3) | **DONA MARTA** entra pela direita, toca o braço do Lucas: *"Seu Lucas, o contador ligou. As doze lojas bateram recorde este mês!"* Lucas sorri, calado | Vanessa de costas (esq.), Diego (centro), Lucas (dir.), Marta entra e para à direita do Lucas | Lucas com bloquinho parado | **último quadro do 3** |
| **7** | 4 s | Igual ao **2** (C2); Marta aparece **em parte** na borda direita (manga do cardigã vinho), ao lado das costas do Lucas | **VANESSA** (baixinho, chocada): *"Seu Lucas? Doze lojas?"* | Vanessa (esq.), Diego (centro, parcial), Lucas de costas (dir.), manga da Marta (borda dir.) | — | **último quadro do 5** |
| **8** | 6 s | Igual ao **3/6** (C3) | **LUCAS** (sorriso tranquilo): *"Pois é. Esta aqui foi a primeira. Os cafés de vocês são por conta da casa."* | Vanessa de costas, Diego, Lucas, Marta ao lado dele sorrindo | Lucas guarda a caneta no bolso do avental | **último quadro do 6** |
| **9** | 4 s | Igual ao **4** (C4) | **DIEGO** (sem graça, abaixa o cardápio): *"Amor... vamos embora."* | Diego, ombro da Vanessa (esq.) | Diego larga o cardápio na mesa | **último quadro do 4** |

Card final 4 s (ASSISTA TAMBÉM / INSCREVA-SE / ATIVA O SININHO) sobre o último quadro desfocado.

### Leitura em voz alta (checagem de fala)
Todas as falas foram lidas em voz alta pensando no Veo: sem hífen ("pé-rapado" saiu), sem número em algarismo ("doze" por extenso), sem sigla, sem palavra de 1 sílaba isolada no fim ("Rede?" virou "Doze lojas?"), pontuação marcando a respiração. Nenhuma fala passa de ~4 s falada dentro de um plano de 6–8 s.

## Áudio (como evitar o barulho)
1. **Prompt do Veo em todo plano:** `Audio: only this character's spoken line, in a quiet room with very soft room tone. No music. No rhythmic sounds, no clicking, no writing sounds, no clinking. Everyone else is silent.`
2. **Ninguém escreve** enquanto alguém fala (o bloquinho fica parado).
3. **Cama de ambiente separada**, gerada só como som de sala calma (sem cliques, sem conversa inteligível), **checada no espectro** (sem picos periódicos) antes de entrar; volume baixo e contínuo.
4. **Trilha só na edição**, leve, com ducking sob as falas, subindo na virada (planos 6–8).
5. Junções de 30–40 ms entre clipes; -14 LUFS; pico ≤ -1 dBFS.

## Custo previsto (vídeo, NÃO nesta etapa)
54 s × US$ 0,05 = **US$ 2,70** (Veo 3.1 Lite 720p) + cama de ambiente ~US$ 0,03 + trilha já paga; reserva para 2 refações ~US$ 0,60.

## Storyboard (etapa 2) — `storyboard_v2.jpg`, `planta_cafe.jpg`, `storyboard/p01…p09.jpg`
Quadros iniciais gerados no Seedream 5.5 com as referências fixas (Vanessa, Diego, Lucas da v3 + **Dona Marta nova**, `storyboard/ref_marta.jpg`, seed 71000) e o plano mestre/ângulos como referência de cenário. Seeds fixas 72001–72014.

**Checagem de continuidade feita antes de entregar:**
- **Corrigidos:** `p01` (saíram **3 cardápios** — um a mais na frente do Diego) e `p04` (saiu plano médio com o **rosto da Vanessa**, não close do Diego). Refeitos com contagem explícita de cardápios e enquadramento fechado; versões descartadas em `storyboard/descartados/` (não versionadas).
- **C2 (2, 5, 7):** Vanessa à esquerda olhando para cima/direita, Diego parcial atrás do braço do Lucas, Lucas de costas à direita, 2 cardápios na mesa; no 7 a manga do cardigã vinho da Marta aparece na borda direita (ela está ao lado do Lucas). ✅
- **C3 (3, 6, 8):** nuca/scrunchie da Vanessa à esquerda, mesa T1 embaixo com os 2 cardápios, Diego de perfil no centro, Lucas colado à mesa; no 8 a Marta à direita do Lucas com a mão no braço dele. ✅
- **C4 (4, 9):** close do Diego; ombro da Vanessa na borda esquerda e avental do Lucas na borda direita (coerente: ele está em pé ao lado). ✅
- Luz neutra pela janela, sempre do mesmo lado; figurino e cabelo iguais às referências. ✅
- **Pendências conhecidas:** nos quadros C2 o Lucas aparece com a caneta encostada no bloquinho (o prompt de vídeo diz "não escreve"); nas mesas vazias do fundo aparecem saleiros pequenos (não são cardápios nem xícaras).

**Uso na geração de vídeo:** planos 1–4 partem destes quadros; os planos 5–9 partem do **último quadro real** do vídeo anterior do mesmo ângulo (5←2, 6←3, 7←5, 8←6, 9←4). Os quadros 5–9 do storyboard servem de referência visual e de reserva caso um encadeamento saia errado.

Custo desta etapa: US$ 0,56 registrados (12 imagens, incluindo 2 refeitas); saldo Runware US$ 20,26 → US$ 19,72.
