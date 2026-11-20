# Geladeira Dividida — contexto do projeto

Série de humor curta no formato sitcom (episódios de ~3 min), criada pelo **Lucas** (Brasil).
Objetivo: produzir episódios com **custo baixo** e **coerência visual** total (mesmos personagens,
mesmo cenário, objetos que não "derretem" entre planos), para um canal no YouTube.
Este arquivo resume a conversa em que o projeto nasceu, para continuar daqui.

## Como o Lucas gosta de trabalhar
- Prefere **avaliação honesta de obstáculos** a otimismo; aponte limites reais antes de empolgar.
- Respostas diretas, em português; ele costuma ler no celular (mensagens curtas).
- Gosta de ver resultado (vídeo/quadro) cedo e iterar a partir dele.
- Piadas: pediu **simplicidade** (estrutura clara, falas curtas, piadas que voltam no final).
- Visual: quer algo **mais próximo de jogo** (citou GTA 6 como referência de ambição);
  a versão atual é 3D estilizada (tipo The Sims/Roblox), não realista.
- Duração-alvo: ~3 min por episódio.

## O que já foi tentado (e por quê mudou)
1. **Vídeo de IA de ponta a ponta** (Flow do Google, Seedance via Runware): falhou na coerência —
   personagens e detalhes mudam entre clipes ("efeito Will Smith comendo espaguete"), mesmo com
   imagens de referência. Custo de ~US$ 110+ por 3 min em 1080p no Seedance.
2. **Animação limitada por código (2D)**: personagens/cenário sempre iguais; só mudam expressão,
   boca, pose e câmera. Resolveu a coerência com custo zero. Versões 1–4 (`motor/episodio.py`).
3. **Vozes**: espeak → MBROLA/Piper → **Kokoro** (neural, offline). Conferência automática de
   pronúncia com Whisper: erro de palavras caiu de 37,5% (v2) para ~4% (atual).
4. **Risada de plateia**: sintetizada do zero (fonte-filtro), parâmetros escolhidos por busca
   automática maximizando a nota "Laughter" de um classificador de sons (CED/AudioSet).
   Nota ~0,5 (semelhante a uma risada real de referência). Ninguém ouviu ainda com atenção —
   pode soar artificial; para tirar, apague as linhas `(risada)` do roteiro.
5. **3D com técnica de jogo (atual)**: cozinha + 3 personagens modelados no Blender (Cycles),
   **sprites pré-renderizados** (técnica do Donkey Kong Country) por câmera e pose, sombras por
   shadow catcher, contorno toon (inverted hull), correção de cor AgX, filtro de ruído Intel OIDN.
   Rostos desenhados em 2D por cima da cabeça 3D (troca de textura, como em Animal Crossing).
6. Caminho realista considerado (não feito): imagens no Seedream + lip-sync/OmniHuman 1.5 no
   Runware (~US$ 0,13/s de fala → ~US$ 12–20 por episódio). Exige o Lucas rodar a geração.

## Estado atual
- Roteiro atual: `roteiro.txt` (Ep. 1 "O Iogurte", versão de piadas simples, ~2min45s).
- Saídas: `saida/Geladeira_Dividida_3D.mp4` (3D) e `saida/Geladeira_Dividida_2D.mp4` (2D).
- Renders 3D prontos (já sem ruído) em `render/<câmera>/*_limpo.png` + `render/projecoes.json`.
  Câmeras: geral2, geral3, dois, close_clara, close_beto, close_neide, geladeira, abertura, fachada.
- Vozes geradas em `cache_falas/` (não precisa regenerar se o texto da fala não mudar).

## Como rodar
```bash
./setup.sh                                   # instala dependências e baixa modelos (~1,5 GB)
python3 motor/episodio3d.py                  # monta o episódio 3D -> saida/
python3 motor/episodio3d.py preview 12 40    # salva quadros de checagem prev_12.png, prev_40.png
python3 motor/episodio.py vozes              # gera/confere as vozes e mostra o relatório de pronúncia
python3 motor/episodio.py                    # versão 2D
# re-renderizar o 3D (só se mudar modelos/cenário/câmeras; ~1h15 em 2 núcleos de CPU):
blender -b -noaudio -P motor/cena3d.py -- planejar
blender -b -noaudio -P motor/cena3d.py -- jobs render/jobs.json   # retomável
python3 motor/lote_denoise.py
```

## Arquitetura
- `roteiro.txt`: formato próprio (explicado no topo do arquivo): falas com expressão, plano,
  reação, insertos com eventos (etiquetas, cadeado, quadro, sai_neide), risadas e blocos de cena.
- `motor/episodio.py`: parser do roteiro, linha do tempo, vozes (Kokoro + conferência Whisper),
  mixagem (ambiente, efeitos, música sintetizada, risadas com ducking, loudnorm -16 LUFS),
  sincronia labial por envelope/centroide espectral, legendas, cartelas, render paralelo em 2D.
- `motor/cena3d.py` (roda dentro do Blender): modelos procedurais (metaballs, bisect, bevel),
  materiais procedurais, luzes, câmeras, contorno, planejamento e execução dos renders.
- `motor/episodio3d.py`: reaproveita `episodio.py` e troca o desenho 2D pela composição 3D
  (placa do cenário + sprites + rosto 2D projetado + adereços + texto do quadro por homografia).
- `vozes/`: Kokoro em pt-BR direto no onnxruntime (`kokoro_pt.py`), Whisper (`asr.py`),
  risada (`riso_sintese.py`, `busca_riso.py`, `melhor_riso.json`), classificador (`classificar.py`).
- Elenco/vozes: `ELENCO` em `motor/episodio.py`; aparência 3D: `PERS` em `motor/cena3d.py`.

## Limitações conhecidas
- Movimento limitado: poses discretas com transição curta; Dona Neide "desliza" ao entrar.
- Rostos com aspecto de adesivo sobre a cabeça 3D (escolha de estilo).
- Vozes claras mas sem emoção; com visual mais realista isso fica mais evidente.
- Sem GPU no ambiente original: render 3D lento (~50–100 s por sprite).

## Próximos passos discutidos
1. Teste em **three.js** (tempo real, técnica de jogo) para ter movimento de verdade: câmera
   passeando, cabeça virando, personagem andando — comparar com a versão Blender.
   (Há skills prontas, ex. github.com/cloudai-x/threejs-skills; o Lucas viu um vídeo sobre isso.)
2. Caprichar nos modelos 3D: cabelo com volume, mãos com dedos, roupas com detalhes.
3. Vozes com emoção (serviço pago) quando o formato estiver validado.
4. Episódio 2 reaproveitando cozinha e personagens (montagem leva minutos).

## Cuidados
- Não usar logos/personagens de GTA ou de outras marcas (risco no YouTube); só inspiração de estilo.
- Fontes em `fontes/` são SIL Open Font License; modelos de voz/reconhecimento vêm das releases
  públicas do sherpa-onnx (k2-fsa).
