# Edifício Sossego — ep. 1 · piloto (etapa B, para aprovação)

Nada aqui foi gerado ainda. Teto do piloto: **US$ 2,50**. Saldo no Runware: US$ 3,85.

## O que o piloto precisa responder

1. Quanto o Seedance custa de verdade por segundo em 480p, no 2.5 e no 2.5 Flash.
2. Se a fala sai certa em português, inclusive "karaokê".
3. Se o papagaio fala de um jeito que funciona.
4. Se uma tomada de 8 s com duas falas e pausa sai inteira e na ordem.

## Ordem, com parada entre cada clipe

| # | Clipe | Modelo | Segundos | Para quê |
|---|---|---|---|---|
| 1 | Plano 19, Juninho | Seedance 2.5 | 4 | preço real e pronúncia de "karaokê" |
| 2 | Plano 19, Juninho (mesmo prompt) | Seedance 2.5 Flash | 4 | comparar preço e qualidade com o clipe 1 |
| 3 | Plano 26, Sigilo | o melhor entre 1 e 2 | 4 | papagaio falando |
| 4 | Tomada Valdir 2 (planos 6 e 8) | o melhor entre 1 e 2 | 8 | duas falas com pausa |

- Depois de cada clipe: confiro o custo informado pela API, passo o áudio no transcritor, olho os quadros.
- Se o custo real fizer o resto passar de US$ 2,50, o piloto para ali.
- Um envio por clipe, sem reenvio automático.
- Referências enviadas: a do personagem e a da portaria.

## Prompts (em inglês, que o modelo segue melhor; as falas ficam em português)

Trecho comum no fim de todos os prompts:

> 1990s TV sitcom look, warm studio lighting, rich saturated colors, subtle film grain, background softly out of focus.
> Static camera, one continuous shot, no cuts. Audio: only the spoken line(s) and soft room tone. No music, no laugh
> track, no other voices. No subtitles, no text on screen.

### Clipe 1 e 2 — plano 19, Juninho (4 s)

Referências: @Image1 = `juninho.jpg`, @Image2 = `portaria.jpg`.

> Close-up at eye level of the young delivery man of @Image1: same face, black motorcycle helmet with the visor raised,
> bright orange jacket, orange delivery backpack straps on his shoulders. He stands in the lobby of @Image2, seen from
> behind the doorman counter; behind him, out of focus, the glass street door, the fern and the brown leather sofa.
> He looks down at a small blank paper slip in his hand, then looks up at someone just off-screen to the left and says,
> sincere and naive, in Brazilian Portuguese with a natural São Paulo accent: "Ué. Na nota tá escrito karaokê."
> Young man's voice, light and quick. Only he speaks, once.

### Clipe 3 — plano 26, Sigilo (4 s)

Referências: @Image1 = `sigilo.jpg`, @Image2 = `portaria.jpg`.

> Close-up of the green parrot with a yellow face of @Image1, on its curved branch perch at the end of the dark wooden
> counter of @Image2; out of focus behind it, the metal mailboxes. The parrot bobs its head, flaps its wings once and
> says loudly, in a squawky parrot voice, in Brazilian Portuguese: "O segundo é do Valdir!" Its beak opens and closes
> with the words. Only the parrot speaks, once.

### Clipe 4 — tomada Valdir 2, planos 6 e 8 (8 s)

Referências: @Image1 = `valdir.jpg`, @Image2 = `portaria.jpg`.

> Close-up at eye level of the doorman of @Image1: same face, grey mustache, light blue short-sleeve shirt, navy tie,
> reading glasses hanging on a cord. He stands behind the dark wooden counter of @Image2, seen from the front; behind
> him, out of focus, the metal mailboxes and the intercom panel.
> 0 to 3 s: without looking at anyone, calm, deep, unhurried voice, in Brazilian Portuguese with a natural São Paulo
> accent: "Eu não sou de comentar."
> 3 to 5 s: silence; he keeps a straight face, then glances once to the left, as if someone is staring at him.
> 5 to 8 s: he leans a little forward and says quietly, almost whispering: "É da Dona Marlene."
> Only he speaks.

## Conta

| Preço por segundo | 20 s de piloto |
|---|---|
| US$ 0,10 (estimativa em 480p) | US$ 2,00 |
| US$ 0,19 (o que o vídeo de 42 s custou por segundo aproveitado) | US$ 3,80, para no clipe 3 |
