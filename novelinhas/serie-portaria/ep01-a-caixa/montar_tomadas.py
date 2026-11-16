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
         "of focus. Static camera, one continuous shot, no cuts. Speech in Brazilian Portuguese with a natural Rio de "
         "Janeiro accent. Audio: only the spoken line(s) and soft room tone. No music, no laugh track, no other "
         "voices. No subtitles, no text on screen.")

VISUAL = {
    "valdir": ("the doorman of @Image1: same face, short grey hair, grey mustache, light blue short-sleeve shirt, navy "
               "tie, reading glasses hanging on a cord. He stands behind the dark wooden counter of @Image2; behind him, "
               "out of focus, the metal mailboxes and the intercom panel"),
    "neide": ("the building manager of @Image1: same face, short voluminous teased blonde hair, bright red blazer, pearl "
              "necklace, holding a plain brown clipboard against her chest. She stands in the lobby of @Image2; behind "
              "her, out of focus, the elevator door with the gold frame"),
    "soraia": ("the resident of @Image1: same face, shiny hot pink satin bathrobe, pink hair curlers. She stands in the "
               "lobby of @Image2 in front of the counter; behind her, out of focus, the brown leather sofa and the fern"),
    "juninho": ("the young delivery man of @Image1: same face, black motorcycle helmet with the visor raised, bright "
                "orange jacket, orange delivery backpack straps. He stands in the lobby of @Image2 in front of the "
                "counter; behind him, out of focus, the glass street door and the fern"),
    "sigilo": ("the green parrot with a yellow face and a PALE IVORY BEAK of @Image1, on its curved branch perch at the end "
               "of the dark wooden counter of @Image2; behind it, out of focus, the metal mailboxes"),
}

VOZ = {
    "valdir": "deep, calm, unhurried voice of a man about 58",
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
    partes = [f"{plano} of {VISUAL[quem]}.", olhar and OLHAR[quem] and OLHAR[quem][0].upper() + OLHAR[quem][1:] + ".", acao,
              f"Only {quem.upper()} speaks." if quem != "sigilo" else "Only the parrot speaks; its beak opens and "
              "closes with every syllable.", final, COMUM]
    return " ".join(p for p in partes if p)


T = []


def tomada(nome, quem, dur, planos, acao, olhar=True):
    T.append({"tomada": nome, "camera": "C4" if quem == "sigilo" else ("C2" if quem == "valdir" else "C3"),
              "refs": [f"{quem}.jpg", "portaria.jpg"], "segundos": dur, "planos": planos, "prompt": close(quem, acao, olhar=olhar)})


# ---- Valdir (C2)
tomada("valdir1", "valdir", 4, [2], "He looks down over the counter at something big on the floor (out of frame), raises "
       "his eyebrows, amused, and " + fala("valdir", "Que caixa é essa, Juninho?"))
tomada("valdir2", "valdir", 8, [6, 8], "0 to 3 s: without looking at anyone, straight face, " + fala("valdir", "Eu não sou de comentar.")
       + " 3 to 5 s: silence; he glances once toward screen left, as if someone is staring at him. 5 to 8 s: he leans a "
       "little forward and " + fala("valdir", "É da Dona Neidi.", "quietly, almost whispering"), olhar=False)
tomada("valdir3", "valdir", 4, [11], "He turns his head toward screen RIGHT, toward the parrot at the end of the counter, "
       "and " + fala("valdir", "Sijilo! Fica quieto.", "in a scolding whisper"), olhar=False)
tomada("valdir4", "valdir", 4, [15], "Helpful and polite, he gestures down toward the floor in front of the counter (out of frame) and "
       + fala("valdir", "Chegou uma caixa pra senhora.") + " No box is visible in this shot; the counter top holds only the phone, the lamp and the small TV.")
tomada("valdir5", "valdir", 6, [25, 27], "0 to 3 s: he looks up at the ceiling, innocent, and " + fala("valdir", "Eu não sou de comentar...")
       + " 3 to 6 s: silence; he freezes, then straightens his tie with both hands, embarrassed, mouth closed.", olhar=False)
# ---- Soraia (C3)
tomada("soraia1", "soraia", 6, [5, 7], "0 to 3 s: her eyes are glued to something on the floor; pretending not to care, "
       + fala("soraia", "Não que eu queira saber...") + " 3 to 6 s: silence; she looks up toward screen RIGHT and stares, one eyebrow raised, mouth closed.", olhar=False)
tomada("soraia2", "soraia", 4, [9], "Excited, leaning in, " + fala("soraia", "Da síndica? Pesada assim?"))
tomada("soraia3", "soraia", 4, [13], "Caught, pretending to be casual, " + fala("soraia", "Só desci pegar o jornal."))
tomada("soraia4", "soraia", 4, [17], "Suspicious, eyes narrowed, " + fala("soraia", "Limpeza? Desse tamanho?"))
tomada("soraia5", "soraia", 4, [22], "Delighted with the discovery, " + fala("soraia", "A senhora proibiu barulho depois das oito!"))
tomada("soraia6", "soraia", 4, [24], "Teasing, " + fala("soraia", "Reunião cantada? E o segundo microfone?") + " No microphone anywhere in the scene.")
# ---- Neide (C3)
tomada("neide1", "neide", 4, [16], "She freezes for a moment, then " + fala("neide", "É... material de limpeza.", "with forced calm") + " No cleaning products anywhere in the scene.")
tomada("neide2", "neide", 6, [18, 20], "0 to 3 s: very serious, " + fala("neide", "É muito detergente.") + " No detergent or bottles anywhere in the scene."
       + " 3 to 6 s: silence; her eyes go wide in shock, mouth closed, clutching the clipboard.")
tomada("neide3", "neide", 4, [23], "She recovers her posture, chin up, " + fala("neide", "É pra reunião do condomínio."))
tomada("neide4", "neide", 4, [29], "She points toward screen RIGHT at the parrot and " + fala("neide", "Regra nova: papagaio, não!", "firmly"), olhar=False)
# ---- Juninho (C3)
tomada("juninho1", "juninho", 4, [3], "Out of breath, " + fala("juninho", "Hoje é bico. Só vim entregar."))
# plano 19 ("Ué. Na nota tá escrito karaokê.") reaproveita o clipe 2 do piloto (piloto/clipe2_flash.mp4), aprovado
tomada("juninho2", "juninho", 4, [21], "He holds a small blank paper slip in his hand and, helpful and naive, "
       + fala("juninho", "Com dois microfones.") + " No microphone anywhere in the scene.")
tomada("juninho3", "juninho", 4, [31], "Forgotten there, he lifts the blank paper slip and " + fala("juninho", "E aí... alguém assina?", "hesitantly"))
# ---- Sigilo (C4)
tomada("sigilo1", "sigilo", 4, [10], "The parrot bobs its head and " + fala("sigilo", "Pesada assim! Pesada assim!", "fast and mocking"))
tomada("sigilo2", "sigilo", 4, [26], "The parrot bobs its head and " + fala("sigilo", "O segundo é do Valdir!", "fast and mocking")
       + " Then a short cackling laugh.")
tomada("sigilo3", "sigilo", 8, [28, 30], "0 to 3 s: the parrot flaps its wings once and " + fala("sigilo", "Ensaio às nove! Ensaio às nove!", "fast and mocking")
       + " 3 to 5 s: silence, head tilted. 5 to 8 s: " + fala("sigilo", "É regra! É regra!", "mocking"))
# ---- planos com mais gente
T.append({"tomada": "hall1", "camera": "C1", "refs": ["juninho.jpg", "valdir.jpg", "portaria.jpg"], "segundos": 4, "planos": [1],
          "prompt": "Wide shot of the lobby of @Image3, camera at eye level, the whole counter visible. The doorman of @Image2 "
          "(grey mustache, light blue shirt, navy tie) stands behind the counter. The glass street door opens and the delivery "
          "man of @Image1 (orange jacket, black helmet) walks in hugging a huge plain brown cardboard box with no text that "
          "hides his face, and puts it down on the floor in front of the counter. " + fala("juninho", "Entrega pra Dona Neidi!", "out of breath")
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
