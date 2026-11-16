# Referência: @euadonaeogato (Instagram) — análise plano a plano

Arquivos no Drive do Lucas: `ref1-euadonaeogato-ep03.mp4`, `ref2-euadonaeogato-ep26.mp4` (compartilhados por link)
e `ref3-euadonaeogato-apoiadores.mp4` (privado, não analisado). Cortes detectados com ffmpeg (`scene > 0.30`),
um quadro por plano conferido a olho. Áudio não foi ouvido.

## Medidas

| | ep03 | ep26 |
|---|---|---|
| Formato | vertical 1080×1920, 30 fps | vertical 1080×1920, 30 fps |
| Duração | 2 min 41 s | 5 min 16 s |
| Planos | 24 | 75 |
| Duração mediana do plano | 6,3 s | 3,6 s |
| Planos de 2 a 6 s | 8 de 24 | 58 de 75 |
| Planos acima de 10 s | 5 | 3 (11 s, 17 s, 23 s) |
| Cenários | 2 (sala, porta/corredor) | 2 (sala, quintal com festa) |

## O que aparece em cada plano

| Tipo de plano | ep03 (24) | ep26 (72 conferidos) |
|---|---|---|
| Um bicho sozinho (gato, cachorro) | 14 | 16 |
| Uma pessoa sozinha (close ou plano médio) | 5 | 31 |
| Duas pessoas | 2 | 8 |
| Grupo ou plano aberto | 3 | 14 |
| Detalhe de objeto (fita, rádio) | 0 | 2 |

- Cerca de dois terços dos planos têm **um personagem só**.
- Falas de 2 a 7 palavras por plano ("agora, Carol?", "tá bom, Carol... você venceu").
- Legenda queimada em duas línguas no ep26 (português em amarelo, inglês em branco).
- Elenco fixo entre episódios: família (Frank, Carol, Lisa...) e os bichos (gato branco, gato preto Barão,
  vira-lata, golden), que comentam a cena.

## Como a consistência é obtida (leitura minha)

- **O cenário não é idêntico de um plano para outro.** No ep26 a varanda, a cerca, a árvore e as luzes mudam de
  lugar entre planos. Não incomoda porque os planos são fechados, é noite e o fundo está desfocado.
- **O que não muda é o personagem e o visual do conjunto**: figurino marcante e de cor única por personagem
  (avental xadrez vermelho, listrado com jardineira, vestido azul de bolinhas, paletó de tweed), cor quente,
  grão de filme, luzes de fundo desfocadas.
- **Os bichos são o truque de produção**: um gato branco é sempre o mesmo gato branco, e ninguém cobra
  sincronia de boca de um gato. No ep03 eles ocupam mais da metade dos planos.
- As mesmas posições de câmera se repetem (gato na poltrona florida aparece 7 vezes no ep03).
- Nada depende de mão esquerda/direita, de objeto mudando de estado ou de planta do cenário.

## Diferença para o que tentamos (ep003, ep004, ep005)

| | Referência | Nossos testes |
|---|---|---|
| Formato | vertical | horizontal |
| Cenário | varia, escondido por plano fechado e desfoque | exigido idêntico (planta, eixo 180°) |
| Personagens por plano | 1 na maioria | até 4 |
| Objetos | quase nenhum com função | xícaras, garrafa, pastas, crachá com estado |
| Visual | quente, saturado, grão, luzes de fundo | sala bege, luz chapada |
| Fala por plano | 2 a 7 palavras | até 11 palavras |

## Vídeo do Lucas feito no Seedance 2.5 em 480p (`final_v2_leve.mp4`, ep004)

854×480 horizontal, 42,6 s, 7 planos (7,6 · 8,1 · 4,6 · 3,5 · 8,0 · 3,8 · 7,0 s), mediana 7,0 s. Custo informado: ~US$ 8.

- Personagens e sala se mantêm reconhecíveis de um plano para outro (melhor que quadro por plano).
- 6 dos 7 planos têm duas ou três pessoas em plano aberto ou médio; só 1 plano tem uma pessoa sozinha (Joice ao telefone).
- Nenhum close de rosto; a Paula passa o vídeo inteiro olhando o celular, sem plano de reação.
- A geometria da sala muda entre ângulos (janela e balcão aparecem só a partir de 24 s).
- Visual: sala bege, luz chapada, cor neutra.

### Falas do vídeo, transcritas automaticamente (`novelinhas/conferir_fala.py`)

| Trecho | Roteiro | O que o transcritor ouviu |
|---|---|---|
| 0–7,6 s | Enche aí. E não demora, tá? / Fica à vontade. | igual |
| 7,6–15,7 s | Deixa que eu **ajudo** a senhora. Como é o seu nome? / Helena. **Esse aí é** o seu projeto? | Deixa que eu **ajude** a senhora. [...] **E se é eu** o seu projeto? |
| 15,7–20,3 s | Ela já está no **prédio**, sim. Pode deixar comigo. | Ela já está no **pédio**, sim. |
| 20,3–23,8 s | Diretora que atrasa **assim** nem deve ler currículo. | Diretora que atrasa **sim** nem deve ler currículo. |
| 23,8–31,8 s | Ana, pode entrar. A gente conversa lá dentro. | igual |
| 35,6–42,6 s | O café estava do seu gosto? | igual |

O "pédio" é o erro que o Lucas ouviu. Os outros três precisam de confirmação de ouvido: o transcritor também erra.
