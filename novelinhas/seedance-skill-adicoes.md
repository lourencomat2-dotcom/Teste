# Proposta de acréscimo à skill `seedance-video`

Para colar como seção nova da skill ("Diálogo, ritmo e elenco fixo"). Primeira parte: testado no Runware na série
Edifício Sossego, 16/11/2026. Segunda parte: dicas de guias de terceiros, ainda não testadas por nós.

## Testado por nós (Runware, Seedance 2.5 Flash, 480p)

**Preço e limites**
- Seedance 2.5 Flash 480p com áudio no Runware: **US$ 0,068/s** (medido em 11 clipes; 4 s = US$ 0,27, 8 s = US$ 0,54).
- 480p no Runware é **854×480** exato; 864×480 é recusado (sem custo).
- O Seedance 2.5 normal exige **saldo mínimo de cerca de US$ 7,43** para aceitar o pedido. Pedidos em andamento
  reservam cerca de 2 créditos; com saldo baixo o segundo envio é recusado até a cobrança do primeiro entrar.
- Recusas antes da geração (tamanho, saldo, moderação) não são cobradas.

**Voz**
- Áudio de referência com voz humana, mesmo sintética, é **recusado pela moderação da ByteDance** ("input audio may
  contain sensitive information"). Para fixar a voz de um personagem: descreva a voz no prompt com **o mesmo texto,
  palavra por palavra, em todo clipe** dele.
- Voz caricata (papagaio, boneco): descrição que funcionou, escolhida de ouvido: "a cartoon parrot puppet voice
  performed by a man: gravelly, nasal, squeaky, fast and mocking". Filtro de ffmpeg por cima de voz humana não convenceu.
- Duas falas com pausa no mesmo clipe de 6 a 8 s saem na ordem certa.

**Pronúncia**
- Nomes próprios saem errados com frequência: "Marlene" saiu "Mariu", "Sigilo" saiu "segui-lo", "Neide" soou estranho.
  - Prefira nomes curtos e comuns e teste o nome no primeiro clipe.
  - Escreva como se fala, com letras que o modelo não tem como ler errado: "Neidi" ainda saiu "Neida", mas
    **"Nêidji"** saiu "Neide"; "Sigilo" saiu "Siguelho" mesmo com explicação, mas **"Sijilo"** saiu "Sigilo"
    (transcrição automática; confirmar de ouvido).
  - Explicar fora das aspas que o nome é uma palavra comum ("Sigilo is the Portuguese word 'sigilo'") não funcionou.
- Palavra estrangeira ("karaokê") saiu certa. "Prédio" saiu "pédio".

**O que aparece em cena**
- **Objeto citado na fala aparece em cena**: "Pizza desse tamanho?" gerou uma pizza no balcão. Troque a fala, ou
  escreva que o objeto não está em cena (negativas nem sempre funcionam; trocar a fala é mais seguro).
- Detalhe pequeno varia entre clipes (bico do papagaio claro num, escuro no outro): escreva o detalhe em maiúsculas
  no bloco do personagem ("PALE IVORY BEAK").
- Personagem que fala de outro pode trazê-lo para o quadro (o papagaio apareceu na tomada do porteiro): bom ou ruim,
  decida no prompt.

**Ritmo (o "robótico")**
- **Marcar tempos em segundos funciona; pedir "comece logo" não.** Em clipes de 4 s sem marcação, a fala começou entre
  1,5 e 2,6 s (o personagem fica "esperando"); com "0 to 3 s: ... says", começou em 0,8 s. Escrever a fala no começo
  ("0 to 2 s: ... says ...") e a reação depois ("2 to 4 s: ...").
- Na montagem, usar só o trecho da fala e da reação; a espera antes da fala é cortada.
- Voz "calma, sem pressa", "cara séria", pausas de 2 a 3 s e clipe de 4 s para fala de 1 s deixam o personagem lento,
  "parecendo que está esperando alguma coisa" (avaliação do Lucas).
- Corrigir com: ritmo de sitcom em tempo real, fala começando no primeiro meio segundo, gestos em velocidade normal,
  pausas viram olhares rápidos, duração do clipe próxima da duração da fala.

**Elenco e cenário**
- **Uma foto de cenário para cada lado da câmera.** Com uma foto só do cenário inteiro, o modelo põe o personagem
  em qualquer lugar (a síndica apareceu do lado de dentro do balcão em 4 de 4 tomadas). Com uma foto do contraplano
  (vista de trás do balcão) + ficha 3/4 com fundo cinza + "ombro desfocado do outro personagem na borda", o primeiro
  teste saiu certo.
- Diga o que NÃO aparece naquele lado ("the counter, the phone, the lamp, the TV ... are NOT visible in this shot").
- Uma imagem de referência do personagem + uma do cenário mantêm rosto e figurino iguais entre clipes.
- O cenário varia entre ângulos (posição de móveis, lâmpada, TV). Esconda com plano fechado e fundo desfocado,
  como fazem as séries de referência no Instagram.
- O olhar (esquerda/direita da tela) às vezes sai invertido: defina um eixo fixo para a série e escreva em todo prompt.

**Conferência grátis**
- Voz do mesmo personagem entre clipes: impressão digital de locutor (sherpa-onnx, modelo 3D-Speaker eres2net). Mesmo
  personagem ficou entre 0,58 e 0,76; a tomada que o Lucas ouviu como "voz diferente" ficou entre 0,05 e 0,30.
  Usar 0,55 como corte.
- Fala: transcrever o trecho cortado e comparar palavra por palavra com o roteiro; transcrever também uma janela
  maior para saber se o corte comeu palavra.
- Ler a fala do roteiro em voz alta antes de gerar: falta de preposição ("desci pegar") soa como fala comida.
- Transcrever o áudio localmente (Whisper small via sherpa-onnx) pega nome errado e palavra trocada. Erra em voz
  caricata e em cochicho; confirme de ouvido.
- Comparar o tom (F0) entre clipes do mesmo personagem só funciona em voz normal, não em cochicho.

## Dicas de guias de terceiros (não testadas; busca de 16/11/2026)

- Escrever "real-time motion, no slow motion"; palavras moles ("slowly", "glides", "calm", "unhurried") puxam câmera lenta.
- No 2.5, marcações de tempo em segundos inteiros; uma ação principal por bloco de tempo.
- Dizer o papel de cada referência: "@Image1 defines only the identity; do not copy its framing, pose or lighting."
- Interpretação específica em vez de genérica: "the eyes move first, then the head"; reações meio tempo atrasadas;
  piscar natural.
- Fala sempre entre aspas, curta; em cena com duas pessoas, dizer quem fala e que a boca do outro fica fechada.
- Não pule para o vídeo sem fichas fixas de personagem, cenário e objetos (Higgsfield, curso "AI ad 3-step").

Fontes: higgsfield.ai/blog/seedance-2-5-prompting-guide, grailogic.com/articles/seedance-2-5-prompt-guide,
seedance.tv/blog/seedance-2-5-prompt-guide, venice.ai/blog/seedance-2-5-prompt-tips,
github.com/Anil-matcha/awesome-seedance-2.5-api-prompts, higgsfield.ai/academy/how-to-use/how-to-make-ultra-realistic-ai-ads.

## Acréscimos do fim do projeto (16/11/2026)

- **Travar cenário**: imagem-base do ângulo SEM rosto como @Image1 com "is the EXACT set, camera position, framing and
  lighting: copy it faithfully" + ficha do personagem como @Image2. 5 de 5 tomadas no mesmo cenário.
- Imagem com rosto fotorrealista como **primeiro quadro** é recusada pela moderação; como referência passa na maioria
  das vezes (uma ficha 3/4 foi recusada, a foto original do mesmo personagem passou).
- Com `frameImages` o Runware não aceita `width`/`height`; usar `resolution: "480p"`.
- Recusas de moderação parecem gerar cobrança parcial (saldo caiu ~US$ 0,19 além do somado).
- Cena com vários personagens presentes: definir posição fixa e gerar planos de conjunto; tomada individual com o
  personagem sozinho no meio do cenário quebra a lógica da cena.
- Revisão visual: 1 quadro por SEGUNDO do vídeo montado, não 1 por plano.

