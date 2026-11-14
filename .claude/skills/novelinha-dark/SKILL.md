---
name: novelinha-dark
description: Cria e produz episódios de "novelinha" para canal dark do YouTube (histórias de vingança/virada, ex. "humilharam o CEO achando que ele era ninguém") no formato novela dublada — só os personagens falam, sem narrador. Use quando o usuário pedir um novo episódio, roteiro, história, novelinha, vídeo do canal dark, ou para produzir/renderizar um roteiro.json existente. Escreve o roteiro em JSON e roda novelinhas/novelinha.py para gerar vozes, imagens, legendas, vídeo, thumbnail e textos do YouTube.
---

# Novelinha dark — novela dublada, do tema ao vídeo pronto

Você escreve o roteiro; a ferramenta `novelinhas/novelinha.py` faz o resto.
Todos os textos que vão ao público são em **português do Brasil**, linguagem simples e falada.

## Formato: novela dublada (sem narrador)

O usuário **não quer narrador**. A história é contada só por:
- **falas dos personagens**, cada um com a própria voz (a legenda mostra o nome na cor do personagem);
- **texto na tela** (`tela`) para o que um narrador diria: tempo ("Seis meses antes"), segredos ("O que ninguém sabia: o hotel era dela"), ganchos ("Guarda o nome desse hotel") e a moral/CTA do final.

Regras do formato:
- A informação importante vem **das falas**: o vilão se revela no que diz; o passado do herói aparece numa conversa ("Ele dormia numa caixa de papelão do lado do isopor").
- `tela` curta: até ~12 palavras. No máximo ~1 em cada 4 cenas. Nunca empilhe mais de 2 telas seguidas.
- Falas curtas e naturais, do jeito que brasileiro fala ("tá", "pra", "né", "minha filha"). 1 a 3 frases por fala, no máximo 2–3 falas por cena.
- Use `tom` (em inglês, curto) para dirigir a interpretação: `"cold, arrogant"`, `"whispering"`, `"crying"`, `"laughing, mocking"`, `"calm, firm"`.

## Passo a passo

1. **Entender o pedido.** Defaults: `horizontal`, 8–12 min (≈ 90–110 cenas, ≈ 1.100–1.500 palavras de fala); `vertical` para Short (45–90 s, ≈ 12–18 cenas).
2. **Não repetir.** Leia `novelinhas/episodios/historico.md`. Escolha arquétipo, cenário, nomes e reviravolta diferentes. Combinações em [references/formula.md](references/formula.md).
3. **Escrever o roteiro** (estrutura em [references/formula.md](references/formula.md), esquema abaixo). Salve em `novelinhas/episodios/epNNN-slug/roteiro.json`.
4. **Validar:** `python3 novelinhas/novelinha.py validar <roteiro.json>` — mostra cenas, falas, minutos estimados e vozes. Corrija até passar.
5. **Produzir:** `python3 novelinhas/novelinha.py produzir <roteiro.json>` (voz e imagens pelo Runware; na nuvem do Claude a chave é injetada sozinha). `--teste` = sem APIs, só para conferir ritmo. Erro de rede/saldo: relate o erro exato, não invente que funcionou.
6. **Registrar** uma linha em `historico.md`: `| NNN | título | herói/disfarce | cenário | reviravolta | nomes |`.
7. **Entregar:** vídeo (mande uma prévia leve com SendUserFile), thumbnail, `youtube.txt`, duração e 1–2 sugestões.

## Esquema do roteiro.json

```json
{
  "titulo": "Humilharam o faxineiro na festa da empresa… sem saber que ele era o dono",
  "formato": "horizontal",
  "estilo_visual": "cinematic photo, dramatic warm lighting, shallow depth of field, Brazilian people, realistic, 35mm film look, telenovela atmosphere",
  "personagens": {
    "rafael": {"nome": "Rafael", "genero": "m", "voz": {"runware": "Achird"}, "cor_legenda": "#9BE89B",
               "visual": "brazilian man, 35 years old, short dark hair, light stubble, grey cleaner uniform"},
    "debora": {"nome": "Débora", "genero": "f", "voz": {"runware": "Kore"}, "cor_legenda": "#FF7A7A",
               "visual": "brazilian woman, 30s, sleek blonde hair, red dress, arrogant look"}
  },
  "cenas": [
    {
      "falas": [
        {"quem": "debora", "texto": "Limpa isso aí. E rápido, que hoje tem gente importante.", "tom": "cold, arrogant"},
        {"quem": "rafael", "texto": "Sim, senhora.", "tom": "calm"}
      ],
      "imagem": "elegant corporate party, arrogant woman pointing at a spill on the floor, man in cleaner uniform",
      "personagens": ["debora", "rafael"],
      "capitulo": "A festa"
    },
    {
      "tela": "Ela não fazia ideia de quem ele era.",
      "imagem": "close-up of the cleaner's calm face, faint smile",
      "personagens": ["rafael"],
      "pausa": 0.6
    }
  ],
  "youtube": {
    "titulos": ["...", "...", "..."],
    "descricao": "2–3 frases com gancho, sem spoiler. Termine com: História fictícia, criada para entretenimento.",
    "hashtags": ["#novelinha", "#historiadevinganca"],
    "tags": ["novelinha", "história de vingança", "..."],
    "thumbnail_texto": "ELE ERA O DONO",
    "thumbnail_cena": 1
  }
}
```

Por cena: `falas` e/ou `tela` (pelo menos um), `imagem` (obrigatório), e opcionais `personagens`, `capitulo` (o 1º na cena 1; só horizontal), `movimento` (`zoom_in`, `zoom_out`, `pan_direita`, `pan_esquerda`, `pan_cima`), `pausa` (s; ~1.0 antes de revelação), `tempo_tela` (s), `repetir_imagem` (nº de outra cena).

### Vozes (Gemini 3.1 TTS no Runware, idioma fixo pt-BR)
Uma voz diferente por personagem, combinando com idade e jeito. Femininas: `Gacrux` (madura), `Kore` (firme), `Leda` (jovem), `Achernar` (suave), `Sulafat` (calorosa), `Despina`, `Autonoe`, `Aoede`, `Vindemiatrix` (gentil), `Pulcherrima`. Masculinas: `Charon` (sério), `Orus` (firme), `Achird` (amigável), `Algenib` (rouca), `Iapetus` (clara), `Puck` (animada), `Fenrir`, `Alnilam`, `Schedar`, `Sadaltager`.
Dois personagens que conversam nunca têm a mesma voz.

## Regras de escrita

- **Áudio sempre em português do Brasil, sem sotaque estrangeiro.** O provedor runware força `pt-BR`. Em outros provedores, só vozes pt-BR nativas (Edge: `pt-BR-AntonioNeural`, `pt-BR-FranciscaNeural`, `pt-BR-ThalitaMultilingualNeural`; ElevenLabs: só vozes marcadas Portuguese (Brazil)).
- **Prompts de imagem em inglês**, descritivos, sem texto na imagem, sem pessoas reais, marcas ou logos. Personagens da cena em `personagens` para manter rosto e roupa.
- Falas para ouvir: sem emojis, sem parênteses, sem abreviações; números por extenso quando soar melhor.
- Histórias **fictícias e originais**. Nada de pessoas ou empresas reais.
- Humilhação dura, mas sem violência gráfica, sexo ou ataque a grupos (raça, religião, deficiência…) — o vilão é arrogante por status/dinheiro.
- A vingança é "justa": demissão, exposição, perder o contrato, cair a máscara. O herói vence com classe; o aliado é recompensado.
