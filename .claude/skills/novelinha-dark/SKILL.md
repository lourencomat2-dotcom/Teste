---
name: novelinha-dark
description: Cria e produz episódios de "novelinha" para canal dark do YouTube (histórias narradas de vingança/virada, ex. "humilharam o CEO achando que ele era ninguém"). Use quando o usuário pedir um novo episódio, roteiro, história, novelinha, vídeo do canal dark, ou para produzir/renderizar um roteiro.json existente. Escreve o roteiro em JSON e roda novelinhas/novelinha.py para gerar voz, imagens, legendas, vídeo, thumbnail e textos do YouTube.
---

# Novelinha dark — do tema ao vídeo pronto

Você escreve o roteiro; a ferramenta `novelinhas/novelinha.py` faz o resto.
Todos os textos que vão ao público são em **português do Brasil**, linguagem simples e falada.

## Passo a passo

1. **Entender o pedido.** O usuário pode dar só "faz um episódio", um tema ("garçonete humilhada que é dona do restaurante") ou um roteiro pronto. Defaults se não disser nada:
   - formato `horizontal`, 8–12 min (≈1.300–1.800 palavras) — vídeo longo monetiza melhor;
   - `vertical` quando pedir Short/Reels/TikTok: 45–90 s (≈120–220 palavras), ou série "Parte 1/2/3".
2. **Não repetir.** Leia `novelinhas/episodios/historico.md` (crie se não existir). Escolha arquétipo, cenário, nomes e reviravolta diferentes dos últimos episódios. Veja combinações em [references/formula.md](references/formula.md).
3. **Escrever o roteiro** seguindo a estrutura de [references/formula.md](references/formula.md) e o esquema abaixo. Salve em `novelinhas/episodios/epNNN-slug/roteiro.json` (NNN = próximo número).
4. **Validar:** `python3 novelinhas/novelinha.py validar <roteiro.json>` — corrija até passar e confira a duração estimada.
5. **Produzir:**
   - Se não houver chaves de API no ambiente (ou o usuário pediu rascunho): `python3 novelinhas/novelinha.py produzir <roteiro.json> --teste` (voz muda + imagens provisórias, só para conferir ritmo).
   - Senão: `python3 novelinhas/novelinha.py produzir <roteiro.json>`. Provedores ficam em `novelinhas/config.json` (sobrescreva em `config.local.json` ou na chave `"config"` do roteiro).
   - Erro de rede/chave: relate o erro exato ao usuário, não invente que funcionou.
6. **Registrar** uma linha em `historico.md`: `| NNN | título | arquétipo | cenário | reviravolta | nomes |`.
7. **Entregar:** caminho do vídeo, thumbnail, `youtube.txt`, duração, e 1–2 sugestões (ex. "cena 7 ficou longa").

## Esquema do roteiro.json

```json
{
  "titulo": "Humilharam o faxineiro na festa da empresa… sem saber que ele era o dono",
  "formato": "horizontal",
  "estilo_visual": "cinematic photo, dramatic lighting, shallow depth of field, Brazilian people, 35mm film look",
  "personagens": {
    "heroi":  {"nome": "Rafael", "visual": "brazilian man, 35 years old, short dark hair, light stubble"},
    "vila":   {"nome": "Débora", "visual": "brazilian woman, 30s, sleek blonde hair, red dress, arrogant look"}
  },
  "vozes": { "edge": { "vila": "pt-BR-FranciscaNeural" } },
  "musica": null,
  "cenas": [
    {
      "narracao": "Ela jogou o vinho na cara dele na frente de duzentas pessoas. Mal sabia que, em uma hora, ia perder tudo.",
      "imagem": "elegant corporate party, woman throwing red wine on a man in a cleaner uniform, guests shocked",
      "personagens": ["heroi", "vila"],
      "capitulo": "A humilhação"
    }
  ],
  "youtube": {
    "titulos": ["...", "...", "..."],
    "descricao": "2–3 frases com gancho, sem dar spoiler do final.",
    "hashtags": ["#novelinha", "#historia", "#vinganca"],
    "tags": ["novelinha", "história de vingança", "..."],
    "thumbnail_texto": "ELE ERA O DONO",
    "thumbnail_cena": 1
  }
}
```

Campos por cena (opcionais além de `narracao` e `imagem`):
- `personagens`: chaves de `personagens` → a descrição visual entra no prompt (mantém o rosto/roupa consistentes).
- `voz`: papel em `vozes` (padrão `narrador`). Use para falas marcantes de personagem; o resto é narrador.
- `capitulo`: vira capítulo na descrição (só em vídeo horizontal; o primeiro deve estar na cena 1).
- `movimento`: `zoom_in`, `zoom_out`, `pan_direita`, `pan_esquerda`, `pan_cima` (padrão: sorteado).
- `pausa`: segundos de respiro após a cena (padrão 0.35; use ~1.0 antes de uma revelação).
- `repetir_imagem`: número de outra cena para reaproveitar a imagem (economiza geração).

Para trocar uma imagem gerada: o usuário coloca `imagens/cena_005.png` na pasta do episódio e roda de novo — imagem manual sempre tem prioridade. Tudo fica em cache; só o que mudou é refeito.

## Regras de escrita

- **Cena = 1 a 3 frases** (≈ 5–12 s de fala). Imagem nova a cada cena mantém retenção. Longo de 10 min ≈ 80–120 cenas.
- **Prompts de imagem em inglês**, descritivos, sem texto na imagem, sem nomes de pessoas reais, marcas ou logos.
- **Áudio sempre em português do Brasil, sem sotaque estrangeiro.** Só use vozes pt-BR nativas (Edge: `pt-BR-AntonioNeural`, `pt-BR-FranciscaNeural`, `pt-BR-ThalitaMultilingualNeural`; ElevenLabs: só vozes marcadas como Portuguese (Brazil)). Nunca escolha uma voz em inglês ou de Portugal para um personagem.
- Narração escrita para ouvir: frases curtas, números por extenso quando soarem melhor, sem emojis, sem parênteses, sem abreviações.
- Histórias **fictícias e originais**. Nada de pessoas reais, empresas reais, nem "baseado em fatos reais" se não for.
- Humilhação pode ser dura, mas sem violência gráfica, sem conteúdo sexual e sem atacar grupos (raça, religião, deficiência etc.) — o vilão é arrogante por status/dinheiro. Isso protege a monetização.
- A vingança é "justa": demissão, exposição, perder o contrato, cair a máscara. O herói vence com classe.
