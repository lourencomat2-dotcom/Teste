---
name: novelinha-dark
description: Cria e produz episódios de mininovela para canal dark do YouTube (histórias de vingança/virada, ex. "humilharam o CEO achando que ele era ninguém") no estilo Narak Novelas — vídeo 16:9 fotorrealista, 100% diálogo encenado, sem narrador e sem texto na tela. Use quando o usuário pedir um novo episódio, roteiro, história, novelinha, mininovela, vídeo do canal dark, ou para produzir/renderizar um roteiro.json existente. Escreve o roteiro (lista de planos) e roda novelinhas/mininovela.py para gerar referências de personagem, quadros, vozes, vídeos com boca sincronizada, efeitos, trilha, card final e o vídeo pronto.
---

# Mininovela — do tema ao vídeo pronto

Referência obrigatória de estilo: canal Narak Novelas (ex.: https://youtu.be/vsV8anviiAg).
Você escreve o roteiro como **lista de planos**; `novelinhas/mininovela.py` faz o resto.
Tudo que o público ouve é **português do Brasil**, natural, falado.

## Diretrizes de qualidade (obrigatórias em todo episódio)

1. **Continuidade sem falhas.** Nada de objeto, roupa ou acessório que some e reaparece, nem cena bizarra. Fixe acessórios na descrição do personagem ("sunglasses always pushed up on top of her head") e nunca peça no movimento uma ação que mude o estado deles sem mostrar a transição. Use `continuidade` para que cada plano herde cenário, mesa, posição e objetos do plano anterior do mesmo ambiente. Confira mesa, xícaras, objetos na mão: a fala tem que bater com o que está em cena.
2. **Coerência espacial.** Quem fala está a uma distância compatível com o tom da fala. Diálogo normal = personagens próximos (garçom em pé ao lado da mesa, não do outro lado do salão). Descreva no `imagem` onde cada um está e para onde olha ("looking up at the waiter standing right beside her"). Plano/contraplano com olhares que se cruzam.
3. **Cortes só quando necessários.** Nada de cortes rápidos ou desnecessários. Cada plano tem uma função (estabelecer o lugar, mostrar quem fala, mostrar a reação que importa). Prefira menos planos e mais longos a muitos planos picados; um plano de ação só existe se o movimento conta algo.
4. **Som de abertura coerente com a cena.** O primeiro som tem que combinar com a imagem (porta com sininho e burburinho de café, não motor de carro velho). Escreva `sfx` específico e realista para cada plano de ação.
5. **Vozes naturais e agradáveis.** Uma voz por personagem, pt-BR, sem instrução de tom no texto (a instrução pode ser lida em voz alta); a emoção vem da pontuação e da própria frase. Se o usuário reclamar de uma voz, troque-a e anote em `historico.md`. Vozes já reprovadas: `Achird` (herói calmo).
6. **Foco no centro da história.** Toda cena serve ao conflito principal (a humilhação e a virada). Corte personagens e planos que não empurram o conflito.

## Formato

- 16:9, 4 a 8 min, 100% diálogo encenado. **Sem narrador. Zero texto na tela** durante a história (sem legenda, nome ou letreiro); só texto diegético (placa, logo) e o card final.
- 4 a 6 personagens com voz própria e consistente (vilã arrogante, herói calmo, marido arrogante, figura mais velha afável…).
- Estrutura: abertura in medias res (humilhação nos primeiros 5 s, sem vinheta) → contexto do problema → 1ª reviravolta (o "humilde" é o dono) → vilão humilhado → 2ª reviravolta (sacrifício secreto do herói) → 3ª reviravolta (ele já seguiu em frente) → lição/arrependimento → fade, plano aberto, card final de ~8 s (ASSISTA TAMBÉM / INSCREVA-SE / ATIVA O SININHO, gerado pela ferramenta).
- Visual: fotorrealista, cara de novela de TV, luz quente, profundidade de campo curta. Planos de 1 a 5 s (mediana ~2,7 s), plano/contraplano e closes nas falas.
- Áudio: trilha dramática por baixo, subindo nos picos (`"pico": true`); efeitos de ambiente; -14 LUFS estéreo (a ferramenta faz).
- Título: injustiça + PALAVRA EM MAIÚSCULAS + reticências + virada. Ex.: "Ela humilhou o EX-NAMORADO por ser pobre... mas não imaginava quem ele havia se tornado!"
- Thumb sem texto: tableau de contraste (humilhado de cabeça baixa, vilã apontando e rindo) em `youtube.thumbnail`.

## Passo a passo

1. Leia `novelinhas/episodios/historico.md` e não repita arquétipo, cenário, nomes ou reviravolta. Ideias em [references/formula.md](references/formula.md).
2. Escreva `novelinhas/episodios/epNNN-slug/roteiro.json` (esquema abaixo) aplicando as diretrizes.
3. Confira o roteiro contra as 6 diretrizes antes de gastar.
4. Gere só imagens e vozes primeiro e **olhe os quadros** (contato) checando continuidade e distância:
   `python3 novelinhas/mininovela.py produzir <roteiro.json> --so-quadros --limite <US$>`
5. Corrija o roteiro se preciso e rode o resto: `python3 novelinhas/mininovela.py produzir <roteiro.json> --limite <US$>`.
   **Sempre** passe `--limite` com o orçamento aprovado pelo usuário; nunca gaste além dele. Use `--ate N` para testar só os N primeiros planos.
6. Registre em `historico.md` e entregue: caminho do vídeo, custo real (saldo antes/depois) e 1–2 observações.

Custos medidos (Runware): quadro ~US$ 0,03–0,04; voz ~US$ 0,02; fala com boca sincronizada ~US$ 0,045/s; plano de ação ~US$ 0,05/s; efeito US$ 0,03; trilha US$ 0,15. Episódio de 6 min ≈ US$ 25–30. Vídeo de fala leva ~5 min para gerar; o Runware reserva crédito por pedido, então com saldo baixo só 2 vídeos rodam ao mesmo tempo.

## Esquema do roteiro.json

```json
{
  "titulo": "Ela humilhou o EX-NAMORADO por ser pobre... mas não imaginava quem ele havia se tornado!",
  "estilo_visual": "cinematic still from a Brazilian TV telenovela, photorealistic, warm golden light, shallow depth of field, 35mm lens, subtle film grain, 16:9",
  "personagens": {
    "vanessa": {"nome": "Vanessa", "genero": "f", "voz": "Kore",
                "visual": "brazilian woman, 30 years old, ..., designer sunglasses always pushed up on top of her head, white silk blouse, gold jewelry"},
    "lucas": {"nome": "Lucas", "genero": "m", "voz": "Charon", "visual": "..."}
  },
  "musica": "slow dramatic telenovela underscore, tense low strings, soft piano, emotional, cinematic, no vocals",
  "planos": [
    {"tipo": "acao", "duracao": 3, "personagens": ["vanessa", "diego"],
     "imagem": "wide shot, cozy cafe interior, the couple walking in through the glass door",
     "movimento": "the couple walks in and looks around; she keeps her sunglasses on top of her head",
     "sfx": "glass door opening with a small shop bell chime, footsteps on tile, soft cafe chatter"},
    {"tipo": "fala", "quem": "vanessa", "continuidade": [1], "personagens": ["vanessa"],
     "texto": "Olha só, esse lugar aqui só tem pé-rapado, né?", "tom": "disgusted, mocking",
     "imagem": "medium shot of the woman standing just inside the cafe entrance, looking around with disgust"}
  ],
  "card_final": {"duracao": 8},
  "youtube": {"titulos": ["..."], "thumbnail": "tableau prompt, no text"}
}
```

Plano: `tipo` (`fala` | `acao`), `imagem` (inglês, sem texto/marcas/pessoas reais), `personagens` (quem aparece → foto de referência), `continuidade` (nºs de planos do mesmo ambiente cujo quadro vira referência), `pico`. Fala: `quem`, `texto` (pt-BR, curto, natural), `tom` (só orienta a atuação do vídeo; não vai para a voz). Ação: `duracao` (2–15 s), `movimento`, `sfx`.

Vozes (Gemini 3.1 TTS, pt-BR): femininas `Gacrux` (madura), `Kore` (firme), `Leda` (jovem), `Achernar` (suave), `Sulafat` (calorosa), `Despina`, `Autonoe`, `Vindemiatrix` (gentil); masculinas `Charon` (sério/calmo), `Orus` (firme), `Algenib` (rouca), `Iapetus` (clara), `Puck` (animada), `Schedar`, `Sadaltager`. Dois personagens em cena nunca com a mesma voz.

## Regras de conteúdo

- Histórias fictícias e originais; nada de pessoas, marcas ou empresas reais.
- Humilhação dura, mas sem violência gráfica, sexo ou ataque a grupos — o vilão é arrogante por status/dinheiro.
- Vingança "justa" (demissão, exposição, perder o contrato); o herói vence com classe; o aliado é recompensado.

(O pipeline antigo de imagens paradas, `novelinhas/novelinha.py`, continua no repositório só como biblioteca de funções; não use o formato slideshow.)
