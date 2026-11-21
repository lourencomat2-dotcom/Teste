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
6. **three.js em tempo real (teste, nov/2026)**: só a abertura fria (13 s) refeita com os mesmos modelos
   (exportados do Blender em GLB), cores, rostos, vozes e legendas. Movimento de verdade: grua/câmera
   passeando, Beto andando do balcão até o lugar (pernas, braços, passos no áudio), cabeças virando para
   quem fala (molas), gestos articulados, câmera sobe para a lâmpada na piada. Esqueleto simples por
   pivôs (quadril/pernas/tronco/braços/cabeça), sem rig de ossos. Sem GPU no ambiente: o vídeo é
   capturado quadro a quadro no Chromium (SwiftShader, ~2–3 s/quadro); num PC comum roda ao vivo.
7. **Personagens realistas (teste, nov/2026)**: Clara e Beto refeitos com o **MakeHuman** (corpo
   paramétrico, pele, olhos, cabelo e roupas; esqueleto de 163 ossos; 16 unidades de expressão
   facial como morphs). Os sites do MakeHuman/Blender são bloqueados no ambiente; os dados oficiais
   vêm do pacote npm `makehuman-data` e do PyPI `makehuman` (setup.sh). A direção da cena é a mesma:
   o boneco de massinha vira "marionete" invisível e os ossos copiam caminhada, olhar e gestos.
   Ajustes: camisa do Beto lisa (tirado o logo do MakeHuman), bigode de iogurte 3D, Clara de rabo de
   cavalo (os chanéis do MakeHuman cobrem um olho). Limites: texturas de pele 512 px (closes ficam
   moles), mãos/expressões mais duras que o desenho 2D, voz robótica destoa mais.
8. **Cenário de sitcom (nov/2026)**: cozinha refeita em `sala()` (cena3d.py) — porta com corredor ao fundo
   atrás da marca da Dona Neide (entradas), mesa com toalha xadrez, cadeiras e o pote de iogurte vazio
   ("prova do crime") sob a janela, bancada com pia/escorredor/fogão/coifa e azulejos decorados, aparador
   com filtro de barro, calendário, quadros, telefone de parede, planta, relógio fora do varão da cortina,
   vista pintada da cidade na janela. Paredes amarelo-manteiga, lambri branco, ladrilho hidráulico.
   Texturas pintadas em canvas e luz de estúdio (clara, sombras suaves) em `tempo_real/cenario.js`.
   **Decisão do Lucas: a versão three.js é a principal.** A versão Blender (sprites) ficou com o cenário
   antigo (os renders em `render/` não foram refeitos; refazer custa ~2 h de CPU).
9. **Passada de IA vídeo→vídeo no Runware (teste, nov/2026)**: abertura sem legenda (720p, 13 s) enviada ao
   Seedance 2.0 Fast (`motor/runware_v2v.py`). Custo real US$ 1,69 (+ US$ 1,69 perdidos num pedido de teste
   aceito por engano). Resultado: visual de sitcom real muito convincente e personagens coerentes dentro do
   clipe (Clara de verde, Beto de laranja com bigode de iogurte), MAS o modelo usou o vídeo só como
   referência: inventou os planos, inverteu as posições, deixou a câmera parada e criou falas próprias em
   português (não as do roteiro). Saldo da conta abaixo do mínimo do Seedance 2.5 (7,43) e 2.0 (6);
   o 2.0 Fast aceita só 720p (854/864×480 recusados).
   **Seedance 2.5 em modo edição** (480p, `--modelo bytedance:seedance@2.5 --res 480p --auto`, prompt em
   `prompts/abertura_seedance25.txt`, US$ 1,63): manteve 100% a estrutura (planos, cortes, câmera, posições,
   caminhada, cenário) e refez as VOZES com as falas exatas do roteiro, com atuação. Mas o ganho de realismo
   foi pequeno: o visual continua o nosso 3D (roupas ficaram mais reais; rostos e cenário quase iguais).
   No 2.5, a API usa `resolution` (não width/height) e, em edição, duração "auto". Correção: as vozes NÃO
   foram refeitas — ele imitou o áudio que estava no vídeo de entrada (mesmo timbre e ritmo da Kokoro).
   **Teste 3 (Seedance 2.5 + atores de referência, US$ 1,63)**: vídeo de entrada SEM áudio + fotos dos atores
   "reais" do teste 2.0 (`prompts/refs/`, viram @Image1/@Image2) + falas com tempos no prompt
   (`prompts/abertura_seedance25_atores.txt`). Resultado: estrutura 100% mantida, rostos e roupas de atores
   reais, bigode de iogurte em todos os planos, vozes NOVAS com atuação (pequenas variações: "Eu, não",
   "É, é protetor solar"). O cenário ainda tem cara de cenário pintado (janela, filtro). Melhor resultado
   até agora. Gasto total no Runware: US$ 6,64.
10. Caminho realista considerado (não feito): imagens no Seedream + lip-sync/OmniHuman 1.5 no
   Runware (~US$ 0,13/s de fala → ~US$ 12–20 por episódio). Exige o Lucas rodar a geração.

## Mocap real (versão ?humanos&mocap, nov/2026)
- Dados: base da CMU em BVH (conversão 2010 de Bruce Hahne; "free for use in research and commercial
  projects") vinda de raw.githubusercontent.com/una-dinosauria/cmu-mocap (único caminho liberado na rede).
  Em `tempo_real/mocap/`: `16_34` ("slow walk, stop": entra andando e para em ~2 m) e `113_21` ("Standing
  Still", idle). Descartada: `133_11` (a pessoa anda curvada 25–38°). Mixamo: exige login da Adobe.
- `tempo_real/mocap.js`: `SkeletonUtils.retargetClip` com ajustes por osso calculados na T-pose do quadro 0
  (a "pose zero" da CMU não é ereta) e alinhando o osso inteiro (direção + frente), senão o cotovelo dobra
  no plano errado. Translação do quadril vira root motion (encaixa a caminhada para terminar na marca).
  O IK de `locomocao.js` só trava os pés apoiados; no fim, dois passinhos para virar para a Clara.
- Teste: `QUADROS=0-105 PARAMS='&humanos&mocap&semlegenda' node tempo_real/capturar.cjs saida/entrada_mocap.mp4`
  (QUADROS=a-b grava só um trecho).
- Gestos de fala no mocap: `tempo_real/gestos.js` (tarefa A4). Cada gesto (aponta, ombros, cintura) é um alvo
  para punho, cotovelo e palma no referencial do tronco do mocap, resolvido por IK de duas articulações. A mistura
  com o mocap é feita nos alvos, e o peso do gesto tem mola. Antes, rotações locais pensadas para a marionete davam
  braços esticados no "não sei".
- Pegadinha do three.js: o AnimationMixer só reescreve um osso quando o valor do clipe muda. Quem mexe nos ossos
  depois do mixer (olhar, gestos, IK dos pés) precisa que o `pose()` devolva o último valor do mocap antes de
  atualizar (já feito em `mocap.js`), senão o gesto do quadro anterior "sobra" e acumula.

## Vozes geradas pelo Seedance (falas no prompt)
- Escrever as falas já no formato da pronúncia, com a tônica marcada quando a IA erra
  (ex.: "bigóde" — no teste 3 saiu sem a tônica no "gó"). Manter a lista aqui:
  bigode → "bigóde".
- Mandar o vídeo esqueleto SEM áudio (senão ele imita as vozes da Kokoro).

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

- Versão three.js da abertura: `saida/abertura_threejs.mp4`; comparação `saida/abertura_comparacao.mp4`;
  realista `saida/abertura_realista.mp4`; com o cenário novo `saida/abertura_cenario_novo.mp4`.
- Ainda em aberto: personagens estilizados (padrão) ou realistas (`?humanos`) como versão oficial.

## Versão three.js (tempo_real/)
```bash
blender -b -noaudio -P motor/exportar_glb.py   # modelos -> tempo_real/cena.glb (só se mudar cena3d.py)
python3 motor/tempo_real.py 0                  # linha do tempo, rostos, legendas e áudio da cena 0 -> tempo_real/dados/
node tempo_real/capturar.cjs                    # vídeo -> saida/abertura_threejs.mp4 (sem GPU ~15 min)
python3 motor/comparar_cena.py 0               # versão Blender da mesma cena + vídeo comparativo
# ao vivo: cd tempo_real && python3 -m http.server  -> http://localhost:8000
# personagens realistas: python3 motor/humanos.py -> tempo_real/humanos/ ; página com ?humanos
# inspecionar o cenário: ?cam=x,y,z,alvo_x,alvo_y,alvo_z,mm (coordenadas do Blender)
PARAMS='&humanos' node tempo_real/capturar.cjs saida/abertura_realista.mp4
```
- `motor/humanos.py`: monta cada personagem (ELENCO: idade, gênero, peso, etnia, pele, cabelo, roupas
  com tingimento) e exporta malhas + ossos + morphs; `tempo_real/humano.js` carrega no three.js.
- `tempo_real/cena.js`: carrega o GLB, refaz texturas procedurais (piso, azulejo, parede, madeira) em
  canvas, contorno toon (casca invertida), rosto = calota esférica com a textura do desenho 2D,
  direção da cena (caminho do Beto, olhares, gestos) e câmeras por plano (`PLANOS`).
- Hoje a direção (câmeras, caminhada) está escrita à mão em `cena.js` só para a cena 0; para o
  episódio inteiro, o próximo passo é tirar isso do roteiro (ex.: `(plano)` virar câmera 3D).

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

## Plano atual (21/11/2026, método Superpowers)
- Decisões do Lucas: caminho principal **Unreal Engine 5** (MetaHumans), **GPU alugada** para produção
  (testes curtos aqui), **sem Seedance por enquanto**, corrigir "a cabeça deforma".
- Design: `docs/plans/2026-11-21-rumo-gta6-design.md`. Execução: `docs/plans/2026-11-21-fase0-fase1.md`.
- Causa da cabeça deformada: no idle `113_21` a pessoa capturada tomba a cabeça até 59° (pescoço 23–26°, e o
  osso da cabeça gira mais), e na caminhada `16_34` o pescoço entorta 28° para trás; a malha do MakeHuman estica.
- **Corrigido (tarefa A3):** no mocap, pescoço e cabeça não copiam mais a CMU (`mocap.js`, `olhar()`): a cabeça
  fica nivelada no mundo e recebe só o olhar da cena (35% no pescoço, 65% na cabeça). `?cabecacmu` volta ao
  jeito antigo (diagnóstico); `?semolhar` desliga o olhar.
- Idle: `113_21` segue o melhor dos 11 candidatos medidos (`node tempo_real/escolher_idle.mjs <pasta>`; tronco
  até 8° para o lado e 3° para a frente, mãos caídas). Trechos que emendam: Beto 0,5–10,7 s, Clara 2,4–10,53 s,
  com 0,8 s de mistura na emenda (antes a Clara dava um pulo aos 5,7 s: coxa 34°, quadril 15 cm).
- Testes sem gráficos (Node): `bash tempo_real/testes/rodar.sh` (cabeça, pescoço, olhar, emenda do idle).
  Rodar antes de cada commit que mexa em animação.

## Próximos passos discutidos
1. ~~Teste em three.js~~ feito para a abertura (ver acima). Se aprovado: levar para o episódio todo
   (câmeras/movimentos a partir do roteiro, entrada/saída da Neide andando, adereços da geladeira).
2. Caprichar nos modelos 3D: cabelo com volume, mãos com dedos, roupas com detalhes.
3. Vozes com emoção (serviço pago) quando o formato estiver validado.
4. Episódio 2 reaproveitando cozinha e personagens (montagem leva minutos).

## Cuidados
- Não usar logos/personagens de GTA ou de outras marcas (risco no YouTube); só inspiração de estilo.
- Fontes em `fontes/` são SIL Open Font License; modelos de voz/reconhecimento vêm das releases
  públicas do sherpa-onnx (k2-fsa).
