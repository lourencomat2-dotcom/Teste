# Geladeira Dividida — rumo à qualidade "GTA 6" (design)

Data: 21/11/2026 · Método: Superpowers (brainstorming → design → plano → execução com verificação)

## Objetivo
Episódios de sitcom (~3 min) com personagens e cenário que pareçam reais, movimento crível e
coerência total entre planos e episódios — o mais perto possível da qualidade visual de GTA 6.
Avaliação honesta: GTA 6 é feito por milhares de artistas; "perto" aqui significa humanos realistas
(pele, cabelo, roupa), luz de cinema, animação capturada de gente de verdade e boca sincronizada,
em cenas curtas e controladas. Igualar o jogo não é a meta.

## Decisões do Lucas (brainstorming de 21/11/2026)
| Tema | Decisão |
|---|---|
| Caminho principal | **Unreal Engine 5** (MetaHumans, Lumen, Movie Render Queue) |
| Hardware | **GPU alugada** na produção; testes curtos nesta máquina (nuvem do Claude), mesmo que lentos |
| Serviços pagos | **Sem Seedance por enquanto** |
| Efeito colateral a corrigir | **"A cabeça deforma"** (versão com mocap) |

## Obstáculos reais (ditos antes de gastar tempo)
1. **O Unreal não roda nesta máquina.** Não há GPU, e baixar o motor exige login na Epic, cujo site
   é bloqueado aqui. Tudo que é Unreal roda na GPU alugada. Aqui eu preparo dados, roteiros de
   automação (Python do Unreal) e o "animatic" em three.js, que continua sendo o teste rápido e grátis.
2. **Os scripts do Unreal não podem ser executados aqui.** Eles serão escritos e testados contra
   dados e simulações, e validados de verdade no primeiro uso na GPU alugada. Conte com 1 ou 2 rodadas
   de correção nessa hora.
3. **GPU alugada:** máquina Windows com placa NVIDIA de 16–24 GB de memória de vídeo, 32 GB de RAM e
   ~200 GB de disco (motor + MetaHuman + Fab). Ordem de grandeza: US$ 0,5–1,5 por hora. Instalar
   tudo leva 2–4 h na primeira vez; vale manter o disco salvo entre sessões.
4. **Licenças a confirmar antes de publicar:** o Unreal é gratuito para vídeo linear (royalties só
   valem para jogos e produtos). Os MetaHumans e os assets do Fab/Megascans têm termos próprios;
   confiro o texto atual na fase 1.
5. **A boca precisa de captura facial ou de áudio→rosto.** O MetaHuman Animator gera animação
   facial a partir do áudio, o que serve para as nossas vozes Kokoro. A qualidade com voz sintética
   precisa ser testada.

## Arquitetura (alvo)
```
roteiro.txt ──► motor/episodio.py (vozes, tempos, legendas) ──► linha do tempo JSON
                                                         │
             mocap CMU (BVH→FBX)  cozinha (Blender→FBX)  │
                     │                     │             ▼
                     └──────────► Unreal Engine 5 (na GPU alugada)
                                   unreal/montar_sequencia.py: Level Sequence com câmeras,
                                   MetaHumans, mocap reaproveitado, rostos a partir do áudio, luz
                                   ──► Movie Render Queue ──► quadros ──► ffmpeg + áudio + legendas
three.js (tempo_real/) = animatic: o mesmo JSON, para conferir câmera e marcação em minutos, de graça
```
- **Fonte única da verdade:** o roteiro e a linha do tempo JSON. Unreal e three.js leem o mesmo arquivo,
  então o animatic aprovado é o que o Unreal renderiza.
- **Coerência:** personagens (MetaHumans salvos como asset) e cenário (um nível só) nunca mudam
  entre planos ou episódios.
- **Movimento:** mocap da CMU (livre para uso comercial) reaproveitado no esqueleto do MetaHuman
  com o IK Retargeter do Unreal; travamento dos pés pelo IK do próprio Unreal.

## Fases (marcos)
| Fase | Onde roda | Entrega | Critério de pronto |
|---|---|---|---|
| 0. Corrigir efeitos colaterais e criar testes de regressão | aqui | cabeça sem deformar; gestos sem mãos juntas; testes automáticos | testes passam; quadros de controle aprovados pelo Lucas |
| 1. Preparar o piloto Unreal | aqui | linha do tempo JSON; FBX de mocap e cozinha; scripts Python do Unreal; roteiro de aluguel da GPU | arquivos validados por testes; roteiro passo a passo revisado |
| 2. Piloto Unreal (abertura de 13 s) | GPU alugada | Clara e Beto MetaHuman; cozinha realista; abertura renderizada em 1080p | vídeo aprovado; tempo e custo de render medidos |
| 3. Episódio inteiro | GPU alugada | Dona Neide; adereços da geladeira; entradas e saídas; ep. 1 completo | ep. 1 aprovado; custo por episódio conhecido |
| 4. Vozes com emoção | aqui + serviço | vozes melhores; ajuste da risada | escuta aprovada pelo Lucas |
| 5. Episódio 2 | ambos | reaproveita tudo | montagem em horas, não dias |

## Fora de escopo (por enquanto)
- Seedance/Runware (decisão do Lucas).
- Re-renderizar a versão Blender (sprites): fica congelada como referência.
- Personagens estilizados: continuam funcionando, mas não recebem melhorias.

## Como verificar cada passo (verification-before-completion)
- Nada é dado como pronto sem evidência: teste automático passando **e** quadro ou vídeo mostrado.
- Cada mudança roda os testes de regressão das três versões (estilizada, realista e mocap) para
  pegar efeitos colaterais antes do Lucas.
- Gasto em serviço pago só com OK explícito e valor estimado antes.
