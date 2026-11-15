# ep004 — templates fixos de prompt (método de template)

**Regra:** o texto de cada bloco abaixo é colado **palavra por palavra** em todo prompt de quadro. Nenhum bloco é editado por plano.
Cada quadro = `ESTILO` + `CENARIO` + blocos das personagens que aparecem no quadro + `ATUACAO` + **uma linha de AÇÃO do plano** (a única parte que muda).
O script (`gerar_template.py`) lê os blocos direto deste arquivo, entre as marcas `<!-- BLOCO:NOME -->` e `<!-- FIM -->`, para garantir que nada seja reescrito.

Referências de imagem enviadas junto (sempre nesta ordem): **imagem 1 = `storyboard/master.jpg`** (cenário, luz, lados), depois as refs das personagens do quadro (`refs/ref_*.png`).
Posições conforme `planta_recepcao.jpg`. Se a ação tira a personagem do lugar-base (ex.: Ana de pé), a linha de AÇÃO diz isso; o bloco não muda.

## ESTILO
<!-- BLOCO:ESTILO -->
1990s TV drama scene, photorealistic, natural neutral colors, low saturation, soft contained natural daylight, realistic skin tones, subtle film texture. Same light, colors and brightness as image 1.
<!-- FIM -->

## CENARIO
<!-- BLOCO:CENARIO -->
SET (identical to image 1): small 1990s office reception; light beige walls, grey carpet, framed pictures without text, a potted plant. A window on the LEFT wall is the ONLY light source (soft overcast daylight from screen left); ceiling lights off. A grey two-seat sofa against the back wall, left of center, facing the camera. A low wooden coffee table in front of the sofa with EXACTLY TWO white cups on saucers, one in front of each seat. A closed plain wooden director door on the back wall at the right. A light wooden reception counter on the RIGHT side, near the front, with a beige corded desk phone and a low stack of plain papers. The camera is always on the open front side of the room: seated candidates on screen LEFT, Helena and the counter on screen RIGHT. No other people. No text, no signs, no logos, no captions, no watermark.
<!-- FIM -->

## HELENA
<!-- BLOCO:HELENA -->
HELENA (must match her reference image exactly): Brazilian woman about 60, light brown skin, grey hair pulled back in a low bun, no glasses, no jewelry; grey knit cardigan with a pocket on the right side, open over a cream blouse; dark grey trousers; black flat shoes. Her place: standing just to the RIGHT of the coffee table, between the table and the reception counter. Fixed object: a tall stainless steel coffee serving thermos jug with a handle and a black pour cap, held in her RIGHT hand. NO badge visible (it is inside her pocket). Calm, composed, mouth closed.
<!-- FIM -->

## PAULA
<!-- BLOCO:PAULA -->
PAULA (must match her reference image exactly): Brazilian woman about 28, fair skin, straight dark brown shoulder-length hair; navy blue 1990s pantsuit with soft shoulder pads over a white blouse; small gold stud earrings. Her place: seated on the LEFT seat of the sofa, her black leather bag on the sofa at her left side. Fixed object: a small dark 1990s mobile phone with a short antenna in her hands. Detached, bored, mouth closed.
<!-- FIM -->

## ANA
<!-- BLOCO:ANA -->
ANA (must match her reference image exactly): Brazilian woman about 24, brown skin, dark curly hair tied back in a ponytail, no jewelry; open light blue button-up shirt over a plain white crew-neck t-shirt; beige trousers with a black belt. Her place: the RIGHT seat of the sofa. Fixed object: one closed blue folder. Kind, attentive, mouth closed.
<!-- FIM -->

## JOICE
<!-- BLOCO:JOICE -->
JOICE (must match her reference image exactly): Brazilian woman about 30, medium brown skin, short black bob haircut, no jewelry; burgundy short-sleeve blouse. Her place: seated behind the reception counter on the right, facing screen left. Neutral, professional, mouth closed.
<!-- FIM -->

## ATUACAO
<!-- BLOCO:ATUACAO -->
Restrained, realistic TV drama acting. Subtle micro-expressions only. No exaggerated facial expressions, no grimaces, no smiles, no open-mouth shock, no villain smirk. Mouths relaxed and closed. Each person appears exactly once.
<!-- FIM -->

## Linhas de AÇÃO (a única parte que muda por quadro)
| Quadro | Personagens (blocos) | Refs de imagem | AÇÃO |
|---|---|---|---|
| teste p04 | ANA, PAULA, HELENA | master, ref_ana, ref_paula, ref_helena | ver `gerar_template.py` (`ACAO_P04`) |

## Resultado do teste (p04 → `storyboard/teste_template_p04.jpg`)
Prompt enviado: `storyboard/teste_template_p04_prompt.txt` (montado por `gerar_template.py`; refs: master + Ana + Paula + Helena; seed 84004). Custo registrado pela API: US$ 0,052.

**Falha de método:** o prompt montado tinha **3.264 caracteres** e `gerar_imagem` corta em 2.900, então os **últimos 364 caracteres da linha de AÇÃO não chegaram ao modelo** (pasta na mão esquerda, Paula só em parte, Helena só a borda do cardigã). `gerar_template.py` agora para sem gastar se o prompt passar de 2.900.

**Veredito:** a identidade das personagens ficou **consistente** com o template e as refs. O **quadro não serve como p04**.
| Item | Resultado |
|---|---|
| Ana: rosto, cabelo (rabo de cavalo cacheado), camisa azul aberta, camiseta branca, calça bege, cinto preto | ✅ igual à ref |
| Ana: de pé em frente ao assento direito, virada e olhando para a direita (Helena), expressão contida | ✅ |
| Ana: pasta azul fechada **na mão esquerda, ao lado do corpo** | ❌ segura a pasta com as duas mãos na frente do peito (a mesma pose da ref; essa instrução foi cortada) |
| Enquadramento **plano médio** | ❌ saiu plano aberto, praticamente o enquadramento do master (a instrução chegou e foi ignorada: o master como imagem 1 prende a câmera) |
| Paula **em parte** na borda esquerda | ❌ inteira, no centro-esquerda (instrução cortada); figurino, celular, brincos e pasta preta ✅ |
| Helena só a **borda do cardigã** à direita | ❌ inteira e de rosto visível (instrução cortada); garrafa na mão direita, sem crachá, figurino ✅ |
| Joice | ⚠️ aparece no balcão (vem do master), embora o bloco CENARIO diga "no other people" e ela não estivesse no quadro: contradição entre o bloco e o master |
| Xícaras | ❌ as duas vazias; depois do plano 3 a da Paula deveria ter café. O template não guarda o estado dos objetos por plano |
| Luz, lados, sofá, mesinha, porta, balcão (180°) | ✅ iguais ao master |

**Ajustes para o template funcionar:** (1) blocos mais curtos (~1.900 caracteres no total) para a ação caber inteira; (2) bloco de **estado dos objetos por plano** (xícara da Paula cheia a partir do 3, pasta da Ana na mão ou no colo); (3) tirar "no other people" do CENARIO e listar quem está em quadro na ação; (4) para planos fechados, não usar o master inteiro como imagem 1 (ele prende o enquadramento aberto): recortar o master na região do plano ou partir de um quadro já fechado.
