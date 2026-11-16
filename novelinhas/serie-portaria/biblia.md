# Edifício Sossego — bíblia da série (rascunho para aprovação)

Etapa 1 do plano. Nada aqui custa dinheiro. Só vira produção depois do "pode" do Lucas.

## Premissa

A portaria de um edifício pequeno e antigo, onde ninguém tem sossego. Todo mundo passa pelo balcão do
Seu Valdir, todo mundo tem um segredo, e o papagaio da portaria repete tudo na pior hora.

Comédia de situação com cara de sitcom de TV dos **anos 90**, horizontal (16:9), episódios independentes de
cerca de 2 minutos, elenco e cenário fixos. A história se passa nos anos 90: sem celular, sem aplicativo, sem internet.

## Elenco fixo

| Personagem | Quem é | Defeito que gera a piada | Visual que nunca muda | Voz | Bordão |
|---|---|---|---|---|---|
| **Seu Valdir**, 58 | porteiro | sabe da vida de todos e jura que é discreto | homem negro, cabelo grisalho curto, bigode grisalho, camisa **azul-clara** de manga curta, gravata azul-marinho, óculos de leitura pendurados no pescoço | grave, mansa, sem pressa | "Eu não sou de comentar..." |
| **Dona Neide**, 62 | síndica | inventa uma regra por dia e quebra todas escondido | mulher branca, cabelo loiro curto armado, blazer **vermelho**, colar de pérolas, prancheta na mão | aguda, firme, rápida | "É regra." |
| **Soraia**, 40 | moradora do trezentos e dois | fofoqueira que finge não querer saber | mulher morena, **roupão rosa-choque** de cetim, bobes no cabelo, chinelo | rouca, arrastada, debochada | "Não que eu queira saber..." |
| **Juninho**, 22 | entregador da pizzaria | sincero demais, fala a verdade na hora errada | rapaz pardo e magro, jaqueta **laranja**, capacete preto com a viseira levantada, mochila térmica laranja | jovem, acelerada | "Só vim entregar." |
| **Sigilo** | papagaio da portaria | repete o que ouviu, sempre na pior hora | papagaio **verde** de cara amarela e **bico claro, cor de marfim**, num poleiro de galho na ponta do balcão | esganiçada, de papagaio | repete a última frase comprometedora |

Cada personagem tem uma cor só. O cenário é neutro e quente para as cores saltarem.

## Voz fixa do Sigilo (escolhida pelo Lucas em 16/11, versão M)

Gerada fora do vídeo, no Gemini 3.1 Flash TTS (Runware `google:gemini@3.1-flash-tts`), voz **Fenrir**, idioma pt-BR,
com a marcação no começo do texto:
`[cartoon parrot puppet voice: gravelly, nasal, squeaky, fast and mocking, carioca accent]` + fala + ` [laughs]`.
Amostra: `voz_sigilo/M.mp3`. Cada fala custa cerca de US$ 0,002. As falas do Sigilo são geradas assim primeiro,
e o vídeo dele é feito em cima do áudio.

## Cenário único: a portaria

Hall de edifício nos anos 90: balcão de madeira escura, painel de interfone com botões, telefone de mesa
com fio, TV de tubo pequena e rádio de pilha no balcão, ventilador de pé, parede de escaninhos de metal,
samambaia grande, sofá de couro gasto, porta de vidro para a rua, porta do elevador com moldura dourada,
abajur aceso. Visual de sitcom dos anos 90: luz quente de estúdio, cor saturada, fundo desfocado, grão leve
de filme. Figurino e cabelo da época.

### Seis posições de câmera, sempre as mesmas

| Câmera | O que mostra | Uso |
|---|---|---|
| C1 | hall inteiro, aberto | abre o episódio, entradas e saídas |
| C2 | Seu Valdir atrás do balcão, close | falas e reações dele |
| C3 | quem está na frente do balcão, close | Neide, Soraia ou Juninho, um por vez |
| C4 | Sigilo no poleiro, close | comentários e piada de fecho |
| C5 | dois personagens de perfil, frente a frente | confronto |
| C6 | o objeto do episódio, sem gente | pausa cômica |

C2, C3 e C4 (um personagem só) devem somar pelo menos dois terços dos planos.

## Fórmula do episódio (cerca de 2 min, 25 a 30 planos)

| Trecho | Tempo | O que acontece |
|---|---|---|
| Gancho | 0 a 5 s | situação absurda já em andamento, com a primeira piada |
| Problema | até 30 s | alguém quer algo do Seu Valdir, ou surge um segredo |
| Complicação | 30 a 90 s | entra o segundo personagem; a mentira cresce |
| Virada | 90 a 110 s | a verdade aparece, quase sempre pelo Sigilo |
| Fecho | últimos 10 s | o Sigilo repete mais uma coisa; reação de quem foi entregue |

## Regras de roteiro

- Um segredo por episódio. No máximo dois humanos no mesmo plano.
- Uma fala por plano, de até 8 palavras. Quem leva a piada sempre ganha um plano de reação.
- A graça vem do defeito do personagem, não de ofensa.
- Nenhum objeto que mude de estado, nada que dependa de mão esquerda ou direita, nenhum texto legível em cena.
- Números por extenso ("trezentos e dois"), sem sigla, sem palavra estrangeira.
- Palavras proibidas por pronúncia (a lista cresce a cada erro achado): **prédio** (usar "aqui", "o condomínio"); **Marlene** (o Seedance fala "Mariu"; a síndica passou a se chamar **Neide**).
- Palavras testadas e aprovadas: **karaokê**.
- Objeto citado numa fala aparece em cena (a fala "Pizza desse tamanho" gerou uma pizza no balcão). Quando a fala cita
  algo que não está ali, o prompt diz que aquilo não aparece ("there is NO pizza anywhere").

## Três episódios possíveis

1. **A caixa.** Juninho entrega uma caixa enorme para a Dona Neide. Soraia precisa saber o que tem dentro.
   Seu Valdir "não é de comentar". O Sigilo entrega: é um karaokê, e foi a Neide que proibiu barulho depois das oito.
2. **A regra nova.** Dona Neide proíbe bicho na portaria. Todos escondem o Sigilo. No fim, o Sigilo repete a
   voz da própria Neide: é ela que dá biscoito para ele escondido toda noite.
3. **O bilhete.** Aparece no elevador um bilhete anônimo falando mal da síndica. Neide investiga no balcão.
   O Sigilo repete o Seu Valdir ditando o bilhete.
