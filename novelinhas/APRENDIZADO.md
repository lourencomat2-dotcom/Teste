# Aprendizado — novelinhas com IA (pausado em 16/11/2026)

Projeto pausado pelo Lucas: os modelos ainda erram demais para o esforço. Este arquivo guarda o que foi aprendido,
para retomar quando os modelos evoluírem. Detalhes técnicos para a skill: `seedance-skill-adicoes.md`.

## Onde paramos

- Série **Edifício Sossego** (sitcom anos 90, portaria, elenco fixo + papagaio): `serie-portaria/`.
  Bíblia em `biblia.md`, roteiro do ep. 1 em `ep01-a-caixa/roteiro_v2.md`.
- Ep. 1 não foi concluído. Existem: 5 tomadas do Valdir e 3 do Sigilo (`ep01-a-caixa/tomadas/`), 13 tomadas
  individuais dos visitantes com cenário travado (`ep01-a-caixa/tomadas2/`), rascunho antigo `ep01_montagem.mp4`.
- Faltava: planos de conjunto (os três visitantes juntos no balcão), abertura nova, entrada do Juninho, plateia.
- Gasto no Runware com a série: cerca de **US$ 17,40**. Saldo ao parar: **US$ 6,59**.
- Antes da série: ep003/ep004 (novela de virada), ver `ep003-*`, `ep004-senhora-do-cafe/`.

## O que funcionou

1. **Planejar no barato antes do vídeo**: bíblia → roteiro → fichas → piloto de 3 clipes → levas pequenas com teto.
2. **Seedance 2.5 Flash 480p** no Runware: US$ 0,068/s com áudio; rosto e figurino estáveis com 1 foto de referência.
3. **Cenário travado por imagem-base sem rosto**: uma foto do contraplano (balcão, abajur, ombro do porteiro de
   costas, entrada ao fundo) usada como "set exato a copiar" + ficha do personagem. 5 de 5 tomadas saíram no mesmo
   cenário. Foi o único método que deu coerência de cenário (`referencias/contra_base.jpg`, `ep01-a-caixa/leva_v2.py`).
4. **Tempos em segundos no prompt** ("0 to 2 s: ... says ..."): a fala começa em ~0,5 s em vez de 1,5–2,6 s.
5. **Nomes escritos como soam**: "Nêidji" (Neide), "Sijilo" (Sigilo), "condumínio".
6. **Voz de personagem caricato**: descrição fixa no prompt ("cartoon parrot puppet voice performed by a man:
   gravelly, nasal, squeaky, fast and mocking"), escolhida de ouvido entre amostras de TTS baratas.
7. **Conferência grátis local**: transcrição (Whisper via sherpa-onnx) contra o roteiro; impressão digital de voz
   entre tomadas (corte 0,55); folha com 1 quadro por segundo do vídeo montado (`conferir_fala.py`,
   `ep01-a-caixa/conferir_ep01.py`).

## O que não funcionou (e custou dinheiro)

1. **Uma foto só do cenário para todos os ângulos**: cada tomada reconstrói a sala diferente (cor do balcão, abajur,
   personagem do lado errado). Corrigir tomada por tomada troca um erro por outro.
2. **Conferir só 1 quadro por plano**: aprovei tomadas com erro visível. Só a revisão segundo a segundo pega.
3. **Cada personagem sozinho no quadro** numa cena em que estão juntos: não faz sentido. Faltou definir posição fixa
   de cada um e planos de conjunto desde o roteiro.
4. **Roteiro telegráfico** (uma fala de até 8 palavras por plano, sem apresentar regra/personagens): história corrida.
5. **Quadro por plano gerado do zero + imagem-para-vídeo** (ep004/ep005): cada quadro sai de um jeito.
6. **Filtro da ByteDance**: recusa voz como áudio de entrada e recusa rosto fotorrealista como primeiro quadro
   ou, às vezes, como referência ("may contain real person"). Não dá para fixar voz por áudio nem travar quadro com rosto.
7. **Voz muda entre tomadas** do mesmo personagem (pior em cochicho e em tomada longa); só dá para detectar e refazer.
8. **Plateia de sitcom** pelo Mirelo SFX: som ruim. Usar banco de áudio livre (Pixabay) e mixar.
9. **Objeto citado na fala aparece em cena** ("pizza"); fala sem preposição soa comida ("desci pegar").
10. **Filtros de ffmpeg para "voz de papagaio"**: reprovado.

## Limites que ainda travam o projeto (o que precisa evoluir)

- Coerência de cenário entre gerações separadas sem travar por imagem.
- Voz idêntica do mesmo personagem entre gerações (ou aceitar voz de referência).
- Cena com 3 ou mais pessoas falando, cada uma no seu lugar, com a fala certa.
- Pronúncia de nomes próprios em português.
- 480p é pouco para YouTube; 720p custa 2,2× e o Seedance 2.5 normal mais ainda.

## Se retomar

1. Reler este arquivo e `seedance-skill-adicoes.md`; reconferir preços.
2. Escrever o roteiro já com: posição fixa de cada personagem, planos de conjunto, fala lida em voz alta.
3. Gerar uma imagem-base sem rosto para cada ângulo de câmera e travar o cenário por ela.
4. Piloto de 3 clipes (um com duas falas, um de conjunto) antes de qualquer leva.
5. Revisar cada leva segundo a segundo antes de mostrar; nunca gastar sem teto e sem "pode".
