#!/usr/bin/env python3
"""Monta os prompts das 24 tomadas do ep. 1 a partir de blocos fixos (grátis, não chama API).

Saída: tomadas.json (para o gerador) e tomadas.md (para o Lucas revisar).
Cada personagem tem um bloco de visual e um de voz que nunca mudam entre tomadas.
"""
import json
from pathlib import Path

B = Path(__file__).resolve().parent
PRECO_S = 0.068  # Seedance 2.5 Flash 480p com áudio, medido no piloto

COMUM = ("1990s TV sitcom look, warm studio lighting, rich saturated colors, subtle film grain, background softly out "
         "of focus. Static camera, one continuous shot, no cuts. PACE: lively sitcom timing in real time; the "
         "character starts talking within the first half second, moves, turns and gestures at normal everyday speed "
         "(real-time motion, no slow motion), with natural blinking, following the timings in seconds exactly, "
         "with lively intonation; no slow motion, no long silent pauses, nobody stands still waiting. Speech in Brazilian Portuguese with a natural Rio de "
         "Janeiro accent. Audio: only the spoken line(s) and soft room tone. No music, no laugh track, no other "
         "voices. No subtitles, no text on screen.")

ENTRADA = ("; behind, out of focus, exactly the lobby of @Image2 (the glass street door, the brown leather sofa, the "
           "fern, the standing fan). At the RIGHT edge of the frame, in the near foreground and very out of focus, the "
           "back of the shoulder and grey head of the doorman of @Image3 (light blue shirt), facing the speaker")
VISITANTES = ("neide", "soraia", "juninho")

VISUAL = {
    "valdir": ("the doorman of @Image1: same face, short grey hair, grey mustache, light blue short-sleeve shirt, navy "
               "tie, reading glasses hanging on a cord. He stands behind the dark wooden counter of @Image2; behind him, "
               "out of focus, the metal mailboxes and the intercom panel"),
    "neide": ("the building manager of @Image1: same face, short voluminous teased blonde hair, bright red blazer, pearl "
              "necklace, holding a plain brown clipboard against her chest. She stands in front of the doorman counter, "
              "seen from behind the counter" + ENTRADA),
    "soraia": ("the resident of @Image1: same face, shiny hot pink satin bathrobe, pink hair curlers. She stands in front of the doorman counter, "
               "seen from behind the counter" + ENTRADA),
    "juninho": ("the young delivery man of @Image1: same face, black motorcycle helmet with the visor raised, bright "
                "orange jacket, orange delivery backpack straps. He stands in front of the doorman counter, "
                "seen from behind the counter" + ENTRADA),
    "sigilo": ("the green parrot with a yellow face and a PALE IVORY BEAK of @Image1, on its curved branch perch at the end "
               "of the dark wooden counter of @Image2; behind it, out of focus, the metal mailboxes"),
}

VOZ = {
    "valdir": "deep, warm, relaxed voice of a man about 58, lively conversational rhythm",
    "neide": "high, firm, fast, bossy voice of a woman about 62",
    "soraia": "husky, drawling, teasing voice of a woman about 40",
    "juninho": "light, quick voice of a young man about 22",
    "sigilo": "a cartoon parrot puppet voice performed by a man: gravelly, nasal, squeaky, fast and mocking",
}

OLHAR = {  # eixo fixo: quem está na frente do balcão olha para a DIREITA da tela; quem está atrás, para a ESQUERDA
    "valdir": "looking toward screen LEFT, at the person in front of the counter just off-screen",
    "neide": "looking toward screen LEFT, at the woman in the pink bathrobe just off-screen",
    "soraia": "looking toward screen RIGHT, at the person just off-screen",
    "juninho": "looking toward screen RIGHT, at the doorman just off-screen",
    "sigilo": "",
}


def fala(quem, texto, jeito=""):
    return f'{quem.upper()} says{(" " + jeito) if jeito else ""}: "{texto}" Voice: {VOZ[quem]}.'


def close(quem, acao, final="", olhar=True):
    plano = "Close-up" if quem == "sigilo" else "Medium close-up at eye level"
    papel = ("@Image1 defines only the identity (face, hair, clothes); @Image2 defines only the place. Do not copy "
             "their framing, poses or lighting.")
    if quem in VISITANTES:
        papel = ("@Image1 defines only the identity (face, hair, clothes); @Image2 defines only the background behind "
                 "the speaker; @Image3 is the doorman, seen only as an out-of-focus shoulder at the frame edge. Do not "
                 "copy their framing, poses or lighting. The counter top, the phone, the lamp, the TV, the mailboxes, "
                 "the elevator and the parrot are NOT visible in this shot.")
    partes = [f"{plano} of {VISUAL[quem]}.", papel, olhar and OLHAR[quem] and OLHAR[quem][0].upper() + OLHAR[quem][1:] + ".", acao,
              f"Only {quem.upper()} speaks." if quem != "sigilo" else "Only the parrot speaks; its beak opens and "
              "closes with every syllable.", final, COMUM]
    return " ".join(p for p in partes if p)


T = []


def tomada(nome, quem, dur, planos, acao, olhar=True):
    T.append({"tomada": nome, "camera": "C4" if quem == "sigilo" else ("C2" if quem == "valdir" else "C3"),
              "refs": [f"{quem}_3q.jpg", "entrada.jpg", "valdir.jpg"] if quem in VISITANTES else [f"{quem}.jpg", "portaria.jpg"],
              "segundos": dur, "planos": planos, "prompt": close(quem, acao, olhar=olhar)})


# Tempos marcados em segundos inteiros: o modelo segue (fala começa ~0,8 s); sem eles a fala começa só em 1,5-2,6 s.
REACAO = "a small natural reaction right after the line (a nod or a glance), mouth closed"
SIGILO_NOME = " (Sigilo, the parrot's name, is the Portuguese word 'sigilo', meaning secrecy, pronounced like that word.)"


def curta(antes, linha, depois=REACAO):
    """Tomada de 4 s com uma fala: fala nos 2 primeiros segundos, reação depois."""
    return f"0 to 2 s: {antes} {linha} 2 to 4 s: {depois}."


# ---- Valdir (C2)
tomada("valdir1", "valdir", 4, [2], curta("glancing down over the counter at something big on the floor (out of frame), "
       "eyebrows raised, amused,", fala("valdir", "Que caixa é essa, Juninho?")))
tomada("valdir2", "valdir", 6, [6, 8], "0 to 2 s: not looking at anyone, playing innocent, " + fala("valdir", "Eu não sou de comentar.")
       + " 2 to 3 s: a quick glance toward screen left, as if someone is staring at him. 3 to 5 s: he leans forward and "
       + fala("valdir", "É da Dona Nêidji.", "quietly, almost whispering") + " 5 to 6 s: he straightens up, mouth closed.", olhar=False)
tomada("valdir3", "valdir", 4, [11], curta("turning his head toward screen RIGHT, toward the parrot at the end of the counter,",
       fala("valdir", "Sijilo! Fica quieto.", "in a scolding whisper"), "he turns back toward screen left, mouth closed"),
       olhar=False)
tomada("valdir4", "valdir", 4, [15], curta("helpful and polite, gesturing down toward the floor in front of the counter (out of frame),",
       fala("valdir", "Chegou uma caixa pra senhora.")) + " No box is visible in this shot; the counter top holds only the phone, the lamp and the small TV.")
tomada("valdir5", "valdir", 6, [25, 27], "0 to 2 s: looking up at the ceiling, innocent, " + fala("valdir", "Eu não sou de comentar...")
       + " 2 to 6 s: he freezes for a beat, then quickly straightens his tie with both hands, embarrassed, mouth closed.", olhar=False)
# ---- Soraia (C3)
tomada("soraia1", "soraia", 6, [5, 7], "0 to 3 s: eyes glued to something on the floor, pretending not to care, "
       + fala("soraia", "Não que eu queira saber...") + " 3 to 6 s: she looks up toward screen RIGHT and stares, one eyebrow raised, mouth closed.", olhar=False)
tomada("soraia2", "soraia", 4, [9], curta("excited, leaning in,", fala("soraia", "Da síndica? Pesada assim?")))
tomada("soraia3", "soraia", 4, [13], curta("caught, pretending to be casual,", fala("soraia", "Só desci pra pegar o jornal.")))
tomada("soraia4", "soraia", 4, [17], curta("suspicious, eyes narrowed,", fala("soraia", "Limpeza? Desse tamanho?")))
tomada("soraia5", "soraia", 4, [22], "0 to 3 s: delighted with the discovery, " + fala("soraia", "A senhora proibiu barulho depois das oito!")
       + " 3 to 4 s: a delighted little smile, mouth closed.")
tomada("soraia6", "soraia", 4, [24], "0 to 3 s: teasing, " + fala("soraia", "Reunião cantada? E o segundo microfone?")
       + " 3 to 4 s: she raises an eyebrow, mouth closed. No microphone anywhere in the scene.")
# ---- Neide (C3)
tomada("neide1", "neide", 4, [16], curta("after a split-second hesitation, with forced calm,", fala("neide", "É... material de limpeza."))
       + " No cleaning products anywhere in the scene.")
tomada("neide2", "neide", 6, [18, 20], "0 to 2 s: very serious, " + fala("neide", "É muito detergente.")
       + " 2 to 6 s: a beat, then her eyes suddenly go wide in shock, mouth closed, clutching the clipboard. No detergent or bottles anywhere in the scene.")
tomada("neide3", "neide", 4, [23], curta("recovering her posture, chin up,", fala("neide", "É pra reunião do condumínio.")))
tomada("neide4", "neide", 4, [29], curta("pointing toward screen RIGHT at the parrot,", fala("neide", "Regra nova: papagaio, não!", "firmly"),
       "she keeps pointing, stern, mouth closed"), olhar=False)
# ---- Juninho (C3)
tomada("juninho1", "juninho", 4, [3], curta("out of breath,", fala("juninho", "Hoje é bico. Só vim entregar.")))
# plano 19 ("Ué. Na nota tá escrito karaokê.") reaproveita o clipe 2 do piloto (piloto/clipe2_flash.mp4), aprovado
tomada("juninho2", "juninho", 4, [21], curta("holding a small blank paper slip, helpful and naive,", fala("juninho", "Com dois microfones."))
       + " No microphone anywhere in the scene.")
tomada("juninho3", "juninho", 4, [31], curta("forgotten there, lifting the blank paper slip, hesitant,", fala("juninho", "E aí... alguém assina?")))
# ---- Sigilo (C4)
tomada("sigilo1", "sigilo", 4, [10], curta("bobbing its head,", fala("sigilo", "Pesada assim! Pesada assim!", "fast and mocking"),
       "it bobs its head once more"))
tomada("sigilo2", "sigilo", 4, [26], "0 to 3 s: bobbing its head, " + fala("sigilo", "O segundo é do Valdir!", "fast and mocking")
       + " 3 to 4 s: a short cackling laugh.")
tomada("sigilo3", "sigilo", 6, [28, 30], "0 to 3 s: it flaps its wings once and " + fala("sigilo", "Ensaio às nove! Ensaio às nove!", "fast and mocking")
       + " 3 to 4 s: a quick head tilt. 4 to 6 s: " + fala("sigilo", "É regra! É regra!", "mocking"))
# ---- planos com mais gente
T.append({"tomada": "hall1", "camera": "C1", "refs": ["juninho.jpg", "valdir.jpg", "portaria.jpg"], "segundos": 4, "planos": [1],
          "prompt": "Wide shot of the lobby of @Image3, camera at eye level, the whole counter visible. The doorman of @Image2 "
          "(grey mustache, light blue shirt, navy tie) stands behind the counter. The glass street door opens and the delivery "
          "man of @Image1 (orange jacket, black helmet) walks in hugging a huge plain brown cardboard box with no text that "
          "hides his face, and puts it down on the floor in front of the counter. " + fala("juninho", "Entrega pra Dona Nêidji!", "out of breath")
          + " Only JUNINHO speaks. " + COMUM})
T.append({"tomada": "hall2", "camera": "C1", "refs": ["neide.jpg", "soraia.jpg", "portaria.jpg"], "segundos": 4, "planos": [12],
          "prompt": "Wide shot of the lobby of @Image3, camera facing the elevator door with the gold frame; the counter is out "
          "of frame. The resident of @Image2 (hot pink satin bathrobe, pink curlers) stands in the foreground on screen left, "
          "her back half turned. The elevator doors open and the building manager of @Image1 (teased blonde hair, red blazer, "
          "pearls, clipboard) steps out and " + fala("neide", "Que reunião é essa na portaria?", "bossy")
          + " Only NEIDE speaks. " + COMUM})
T.append({"tomada": "perfil", "camera": "C5", "refs": ["neide.jpg", "soraia.jpg", "portaria.jpg"], "segundos": 4, "planos": [14],
          "prompt": "Medium two-shot in profile in the lobby of @Image3: the building manager of @Image1 (teased blonde hair, red "
          "blazer, pearls, clipboard) on screen RIGHT facing left, and the resident of @Image2 (hot pink satin bathrobe, pink "
          "curlers) on screen LEFT facing right, face to face. NEIDE looks the bathrobe up and down and "
          + fala("neide", "De roupão? É regra: roupão, não.", "firmly") + " Soraia stays silent. Only NEIDE speaks. " + COMUM})

seg = sum(t["segundos"] for t in T)
for t in T:
    t["caracteres"] = len(t["prompt"])
(B / "tomadas.json").write_text(json.dumps(T, indent=1, ensure_ascii=False))
linhas = ["# Ep. 1 — 24 tomadas, prompts para revisão", "",
          f"Total: {len(T)} tomadas, {seg} s de vídeo. Custo previsto: {seg} × US$ {PRECO_S} = **US$ {seg * PRECO_S:.2f}**, "
          f"com 30% de refação **US$ {seg * PRECO_S * 1.3:.2f}**. Mais a imagem da caixa (plano 4), cerca de US$ 0,02.", "",
          "Eixo fixo: quem está na frente do balcão olha para a direita da tela; o Valdir e a Neide, para a esquerda.",
          "O plano 19 reaproveita o clipe 2 do piloto (Juninho, karaokê), já aprovado.",
          "Sotaque carioca para todos, igual ao do Sigilo.", "",
          "| Tomada | Câm. | Planos | s | Referências | Prompt |", "|---|---|---|---|---|---|"]
for t in T:
    linhas.append(f"| {t['tomada']} | {t['camera']} | {', '.join(map(str, t['planos']))} | {t['segundos']} | "
                  f"{', '.join(t['refs'])} | {t['prompt']} |")
(B / "tomadas.md").write_text("\n".join(linhas) + "\n")
print(f"{len(T)} tomadas, {seg} s, US$ {seg * PRECO_S:.2f} (com 30%: US$ {seg * PRECO_S * 1.3:.2f}); "
      f"maior prompt {max(t['caracteres'] for t in T)} caracteres")
