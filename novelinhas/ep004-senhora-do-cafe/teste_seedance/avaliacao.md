# Teste Seedance 2.5 — ep004, um plano contínuo de 15 s

**Modelo:** `bytedance:seedance@2.5` · 1280×720 · 24 fps · 15,07 s · áudio nativo (`settings.audio: true`) · **uma tentativa**, envio único sem reenvio.
**Referências** (`inputs.referenceImages`, nesta ordem = @Image1..@Image5): `refs/ref_helena.jpg`, `ref_paula.jpg`, `ref_ana.jpg`, `ref_joice.jpg`, `storyboard/master.jpg`.
**Trecho:** planos 2–4 do roteiro corrigido, num plano só: PAULA "Enche aí. E não demora, tá?" → Helena serve a xícara da Paula, HELENA "Fica à vontade." → Ana se levanta, ANA "Deixa que eu ajudo a senhora. Como é o seu nome?"; Joice em silêncio no balcão.
Obs.: o pedido atribuía "Fica à vontade" à Ana, mas no roteiro corrigido essa fala é da **Helena** (plano 3); segui o roteiro.

**Arquivos:** `prompt.txt` (4.166 caracteres), `seedance_original.mp4` (14,7 MB), `seedance_leve.mp4` (2,9 MB, libx264 2 passadas 1.420k + AAC 128k, faststart), `gasto_seedance.json`, `gerar_seedance.py`.

## Avaliação (medições + quadros extraídos a cada ~1 s; não consigo ouvir o áudio)
| Item | Resultado |
|---|---|
| Plano contínuo, sem cortes | ✅ um plano só; câmera com push-in/pan lento para a direita |
| 4 personagens | ⚠️ **A Joice sai do quadro por volta de 4–5 s** (o movimento de câmera a deixa para fora) e não volta; o pedido era ela ao fundo o plano todo |
| Rostos e figurino × refs | ✅ Helena (coque grisalho, cardigã cinza, blusa creme), Ana (rabo de cavalo cacheado, camisa azul aberta, camiseta branca, calça bege, cinto), Paula (terninho azul-marinho, blusa branca) e Joice (chanel, blusa vinho) estáveis do começo ao fim, sem troca de rosto. ⚠️ Cabelo da Paula na altura dos ombros (o roteiro corrigido pede passando dos ombros) |
| Sala × master | ✅ sofá, mesinha, balcão com telefone de fio, porta da diretoria, quadros e planta iguais ao master; janela na parede esquerda como no master; porta de entrada fora de quadro. Luz natural contida, cor neutra, baixa saturação |
| Eixo 180° | ✅ candidatas sempre à esquerda, Helena sempre à direita delas |
| Objetos | ✅ garrafa na **mão direita** da Helena o plano todo; o café cai na **xícara da Paula** (7–9 s); pasta da Paula junto ao braço do sofá; pasta azul **fechada**, na mão esquerda da Ana quando ela se levanta. ⚠️ Desse ângulo não dá para confirmar que a xícara da Ana continua vazia |
| Ordem do diálogo / quem fala | ✅ fala em 3 blocos na ordem certa: 0–3 s (F0 ~180–220 Hz, boca da **Paula** se mexendo, as outras fechadas), 7–9 s (F0 ~140 Hz, mais grave, **Helena** falando enquanto serve), 10,5–13 s (F0 ~200–208 Hz, **Ana** falando de pé, Helena calada) |
| Inteligibilidade, sotaque, palavras exatas | ❓ **não verificado**: não consigo ouvir e não há transcrição automática aqui. Precisa de escuta humana (as falas podem ter palavras trocadas) |
| Vozes | ⚠️ Paula e Ana com tom médio parecido (~200 Hz); a Helena é bem distinta (~140 Hz) |
| Som | ✅ sala silenciosa: entre as falas o nível cai abaixo de −40 dB, sem música nem ruído em loop audível na medição; loudness −24,8 LUFS (precisa normalizar para −14 na montagem) |
| Atuação | ✅ contida: Paula entediada no celular, Helena calma, Ana séria e educada; sem caretas nem sorrisos |
| Artefatos | ⚠️ por volta de 9,5–10 s, quando a Ana se levanta, o rosto dela fica borrado por movimento por ~0,5 s; fora isso, sem deformações visíveis nas mãos, garrafa ou xícaras nos quadros conferidos |

**Veredito:** o Seedance 2.5 segurou bem a identidade das 4 personagens, a sala do master, o eixo, os objetos e a ordem das falas num plano contínuo de 15 s. **Não passa na regra do Lucas como está** por causa da Joice saindo de quadro, do borrão no rosto da Ana ao levantar e do cabelo da Paula; e o áudio precisa de escuta humana antes de qualquer decisão. Para um próximo teste: câmera **totalmente fixa** (sem push-in) para a Joice não sair, e uma referência da Paula com cabelo mais longo.
