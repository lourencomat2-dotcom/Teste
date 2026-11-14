# Novelinhas — fábrica de vídeos para canal dark

Histórias narradas de vingança/virada ("humilharam o CEO achando que ele era ninguém"),
do roteiro ao vídeo pronto para subir.

## Como funciona

1. **Roteiro** — no Claude Code, peça: *"faz um episódio novo de novelinha"* (ou dê um tema).
   A skill `novelinha-dark` (`.claude/skills/novelinha-dark/`) escreve `episodios/epNNN-.../roteiro.json`
   seguindo a fórmula de retenção, sem repetir histórias do `episodios/historico.md`.
2. **Produção** — `novelinha.py` gera tudo:
   - voz (Edge TTS grátis ou ElevenLabs), uma voz por personagem se quiser;
   - imagens por cena (Replicate/Flux ou OpenAI), com personagens consistentes;
   - movimento de câmera (zoom/pan), legendas grandes estilo Shorts, música com *ducking*;
   - volume em -14 LUFS (padrão do YouTube);
   - `saida/`: vídeo `.mp4`, `thumbnail.jpg`, `legendas.srt` e `youtube.txt` (títulos, descrição, capítulos, tags).

## Instalação (no seu computador)

```bash
# precisa de Python 3.10+ e ffmpeg no PATH
pip install -r requirements.txt

# imagens (escolha um, conforme "imagens.provedor" no config.json)
export REPLICATE_API_TOKEN=...   # flux-schnell: ~US$0,003 por imagem
export OPENAI_API_KEY=...        # gpt-image-1: mais caro, mais caprichado
# voz premium (opcional; o padrão Edge TTS é grátis)
export ELEVENLABS_API_KEY=...
```

Ajustes pessoais vão em `config.local.json` (fica fora do git), ex.:
```json
{ "imagens": { "provedor": "openai" }, "tts": { "provedor": "elevenlabs", "elevenlabs": { "vozes": { "narrador": "SEU_VOICE_ID" } } } }
```

## Comandos

```bash
python novelinha.py validar  episodios/ep001-mecanico-concessionaria/roteiro.json
python novelinha.py produzir episodios/ep001-mecanico-concessionaria/roteiro.json --teste  # grátis: sem voz, imagens provisórias
python novelinha.py produzir episodios/ep001-mecanico-concessionaria/roteiro.json          # pra valer
```

- Tudo fica em cache: mudou uma frase? Só aquela cena é refeita.
- Não gostou de uma imagem? Salve a sua como `imagens/cena_005.png` na pasta do episódio e rode de novo.
- Música: coloque arquivos sem direitos autorais em `musica/` (uma é sorteada por episódio).
- Short x vídeo longo: `"formato": "vertical"` ou `"horizontal"` no roteiro.

## Custo aproximado por vídeo de 10 min (~100 cenas)
- Edge TTS + Flux schnell: **~US$ 0,30**
- ElevenLabs + gpt-image-1 (medium): ~US$ 5–8

## Atenção para monetizar
O YouTube recusa monetização de conteúdo "inautêntico" (produzido em massa, repetitivo).
Varie histórias, vozes, ritmo e thumbnails; revise cada roteiro antes de publicar e marque
"conteúdo alterado ou sintético" quando as imagens parecerem pessoas reais.
