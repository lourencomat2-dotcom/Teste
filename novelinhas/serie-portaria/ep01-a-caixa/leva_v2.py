#!/usr/bin/env python3
"""Leva do roteiro v2: visitantes com cenário travado (contra_base), abertura e planos abertos (portaria como set exato).
Uma tomada por vez, um envio cada, para no teto. Uso: leva_v2.py <teto US$> [nomes...]"""
import json, sys, time, uuid
from pathlib import Path
import requests
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import mininovela as mn
B = Path(__file__).resolve().parent; OUT = B / "tomadas2"; REF = B.parent / "referencias"
API = "https://api.runware.ai/v1"; CAB = {"Authorization": "Bearer proxy-injected"}
FIM = (" Static camera, one continuous shot, no cuts. Real-time motion, no slow motion, lively sitcom timing, following the timings in "
       "seconds. Speech in Brazilian Portuguese with a natural Rio de Janeiro accent. Audio: only the spoken line(s) and soft room tone. "
       "No music, no laugh track, no other voices. No subtitles, no text.")
CONTRA = ("@Image1 is the EXACT set, camera position, framing and lighting of this shot: copy it faithfully and change nothing in it: the "
          "dark reddish-brown wooden counter along the bottom, the lit green-shade lamp and the beige phone at the left, the doorman seen "
          "from behind at the right edge (out of focus, silent, barely moving), and behind, out of focus, the glass street door, the brown "
          "sofa, the fern and one standing fan. No parrot, no TV, no elevator, no mailboxes, no extra objects on the counter. ")
UM = ("Add only one person, taken from @Image2 (identity and clothes only): standing in the center on the far side of the counter, waist "
      "up, in sharp focus, facing the doorman. ")
Q = {"neide": ("neide_3q.jpg", "She is the building manager: short voluminous teased blonde hair, bright red blazer, pearl necklace, brown clipboard against her chest. ", "Voice: high, firm, fast, bossy voice of a woman about 62."),
     "soraia": ("soraia_3q.jpg", "She is the resident: shiny hot pink satin bathrobe, pink hair curlers. ", "Voice: husky, drawling, teasing voice of a woman about 40."),
     "juninho": ("juninho.jpg", "He is the young delivery man: black motorcycle helmet with the visor raised, bright orange jacket, orange backpack straps. ", "Voice: light, quick voice of a young man about 22.")}
V_VALDIR = "Voice: deep, warm, relaxed voice of a man about 58, lively conversational rhythm."
V_SIGILO = "Voice: a cartoon parrot puppet voice performed by a man: gravelly, nasal, squeaky, fast and mocking."
PORT = ("@Image1 is the EXACT set and lighting: the 1990s lobby with the dark wooden doorman counter, green-shade lamp, small TV, beige "
        "phone, metal mailboxes, intercom, the green parrot with yellow face and PALE IVORY beak on its branch perch at the right end of "
        "the counter, the elevator with the gold frame, the glass street door, the brown sofa, the fern. ")
J = []
def vis(nome, quem, dur, acao):
    f, desc, voz = Q[quem]
    J.append((nome, dur, ["contra_base.jpg", f], CONTRA + UM + desc + acao.replace("VOZ", voz) + FIM))
vis("juninho1", "juninho", 6, '0 to 2 s: out of breath, he says: "Hoje é bico. Só vim entregar." VOZ 2 to 3 s: he catches his breath. 3 to 5 s: he says: "Mas ó: tá pesada." 5 to 6 s: he wipes his forehead, mouth closed.')
vis("soraia1", "soraia", 6, '0 to 3 s: eyes glued to something on the floor in front of the counter, pretending not to care, she says: "Não que eu queira saber... mas de quem é?" VOZ 3 to 6 s: she looks up at the doorman and stares, one eyebrow raised, mouth closed.')
vis("soraia2", "soraia", 4, '0 to 2 s: excited, leaning in, she says: "Da síndica? Pesada assim?" VOZ 2 to 4 s: she grins, mouth closed.')
vis("soraia3", "soraia", 4, '0 to 2 s: caught, pretending to be casual, glancing to screen left, she says: "Só desci pra pegar o jornal." VOZ 2 to 4 s: an innocent little smile, mouth closed.')
vis("soraia4", "soraia", 4, '0 to 2 s: suspicious, eyes narrowed, glancing to screen left, she says: "Limpeza? Desse tamanho?" VOZ 2 to 4 s: she crosses her arms, mouth closed.')
vis("neide2", "neide", 6, '0 to 2 s: very serious, she says: "É muito detergente." VOZ 2 to 6 s: a beat, then her eyes suddenly go wide in shock, mouth closed, clutching the clipboard. No bottles anywhere.')
vis("juninho2", "juninho", 8, '0 to 3 s: he looks down at a small blank paper slip in his hand, then up, sincere and naive, and says: "Ué. Na nota tá escrito karaokê." VOZ 3 to 5 s: short pause, he checks the slip again. 5 to 7 s: helpful, he says: "Com dois microfones." 7 to 8 s: he nods, mouth closed. No microphone anywhere.')
vis("soraia5", "soraia", 5, '0 to 4 s: delighted with the discovery, glancing to screen left, she says: "Karaokê? A senhora proibiu barulho depois das oito!" VOZ 4 to 5 s: a delighted smile, mouth closed.')
vis("neide3", "neide", 6, '0 to 2 s: recovering her posture, chin up, she says: "É pra reunião do condumínio." VOZ 2 to 3 s: silence. 3 to 6 s: she slowly turns her eyes to the doorman in front of her, nervous, mouth closed.')
vis("soraia6", "soraia", 5, '0 to 4 s: teasing, she says: "Reunião cantada? E o segundo microfone, é de quem?" VOZ 4 to 5 s: she raises an eyebrow, mouth closed. No microphone anywhere.')
vis("soraia7", "soraia", 4, '0 to 2 s: amazed, looking at the doorman, she says: "Seu Valdir! O senhor canta?" VOZ 2 to 4 s: she laughs silently, hand on her chest, mouth closed.')
vis("neide4", "neide", 4, '0 to 2 s: pointing past the doorman toward screen right, she says firmly: "Regra nova: papagaio, não!" VOZ 2 to 4 s: she keeps pointing, stern, mouth closed.')
vis("juninho3", "juninho", 4, '0 to 2 s: forgotten there, lifting a small blank paper slip, hesitant, he says: "E aí... alguém assina?" VOZ 2 to 4 s: he looks around, waiting, mouth closed.')
J.append(("perfil", 4, ["contra_base.jpg", "neide_3q.jpg", "soraia_3q.jpg"], CONTRA + "Add exactly two women on the far side of the counter, waist up, in sharp focus, in profile, face to face: on the RIGHT the building manager of @Image2 (teased blonde hair, red blazer, pearls, clipboard) facing left; on the LEFT the resident of @Image3 (hot pink satin bathrobe, pink curlers) facing right. 0 to 3 s: the building manager looks the bathrobe up and down and says firmly: \"De roupão? É regra: roupão, não.\" Voice: high, firm, fast, bossy voice of a woman about 62. 3 to 4 s: the resident pulls her bathrobe closed, offended, mouth closed. Only the building manager speaks." + FIM))
J.append(("sigilo0", 4, ["sigilo.jpg", "portaria.jpg"], "Close-up of the green parrot with a yellow face and a PALE IVORY BEAK of @Image1, on its curved branch perch at the end of the dark wooden counter of @Image2; behind it, out of focus, the metal mailboxes. 0 to 3 s: bobbing its head, imitating a bossy lady, the parrot says: \"Silêncio depois das oito! É regra!\" " + V_SIGILO + " 3 to 4 s: it tilts its head. Only the parrot speaks; its beak opens and closes with every syllable." + FIM))
J.append(("valdir0", 6, ["valdir.jpg", "portaria.jpg"], "Medium close-up at eye level of the doorman of @Image1: same face, short grey hair, grey mustache, light blue short-sleeve shirt, navy tie, reading glasses hanging on a cord. He stands behind the dark wooden counter of @Image2; behind him, out of focus, the metal mailboxes and the intercom panel. A small portable radio sits on the counter. 0 to 2 s: he sighs and switches off the small radio with one hand. 2 to 5 s: grumbling, half amused, he says: \"Regra da Dona Nêidji. Até o rádio ela proibiu.\" " + V_VALDIR + " 5 to 6 s: he shakes his head, mouth closed. Only he speaks." + FIM))
J.append(("hall0", 4, ["portaria.jpg", "valdir.jpg"], PORT + "Wide shot, same framing as @Image1. Add only the doorman of @Image2 (grey mustache, light blue short-sleeve shirt, navy tie) standing behind the counter, relaxed, swaying a little and humming a tune quietly to himself while a small radio on the counter plays very softly. Nobody else. Nobody speaks: only his soft humming and the faint radio." + FIM.replace("Audio: only the spoken line(s) and soft room tone. No music, no laugh track, no other voices.", "Audio: only his soft humming, a faint old radio tune and room tone. No laugh track, no other voices.")))
J.append(("hall1", 4, ["portaria.jpg", "valdir.jpg", "juninho.jpg"], PORT + "Wide shot, same framing as @Image1. The doorman of @Image2 (light blue shirt, navy tie) stands behind the counter. 0 to 3 s: the glass street door opens and the delivery man of @Image3 (orange jacket, black helmet with raised visor) walks in hugging a huge plain brown cardboard box with no text and says, out of breath: \"Entrega pra Dona Nêidji!\" Voice: light, quick voice of a young man about 22. 3 to 4 s: he puts the box down on the floor in front of the counter. Only the delivery man speaks." + FIM))
J.append(("hall2", 4, ["portaria.jpg", "neide_3q.jpg", "soraia_3q.jpg"], PORT + "Medium-wide shot toward the elevator with the gold frame. The resident of @Image3 (hot pink satin bathrobe, pink curlers) stands in the foreground at the left with her back half turned. 0 to 1 s: the elevator doors open. 1 to 4 s: the building manager of @Image2 (teased blonde hair, red blazer, pearls, clipboard) steps out and says, bossy: \"Que reunião é essa na portaria?\" Voice: high, firm, fast, bossy voice of a woman about 62. Only the building manager speaks." + FIM))

def main():
    teto = float(sys.argv[1]); so = sys.argv[2:]
    OUT.mkdir(exist_ok=True); lf = OUT / "gasto.json"; log = json.loads(lf.read_text()) if lf.exists() else {"itens": []}
    cache_f = OUT / "uploads.json"; cache = json.loads(cache_f.read_text()) if cache_f.exists() else {}
    gasto = 0.0
    for nome, dur, refs, prompt in J:
        if (so and nome not in so) or (OUT / f"{nome}.mp4").exists(): continue
        if gasto + dur * 0.068 > teto: sys.exit(f"PARADO antes de {nome}: leva em US$ {gasto:.2f}")
        ids = [mn.subir_imagem(REF / r, cache) for r in refs]; cache_f.write_text(json.dumps(cache))
        tid = str(uuid.uuid4())
        t = {"taskType": "videoInference", "taskUUID": tid, "model": "bytedance:seedance@2.5-flash", "positivePrompt": prompt, "width": 854,
             "height": 480, "duration": dur, "numberResults": 1, "outputType": "URL", "outputFormat": "MP4", "deliveryMethod": "async",
             "includeCost": True, "inputs": {"referenceImages": ids}, "settings": {"audio": True}}
        ok = False
        for _ in range(30):
            r = requests.post(API, headers=CAB, json=[t], timeout=120); j = r.json(); er = j.get("errors") or []
            if r.status_code < 300 and not er: ok = True; break
            if any(e.get("code") == "concurrentRequestLimitExceeded" for e in er): time.sleep(60); continue
            print(f"{nome}: RECUSADO, sem custo: {json.dumps(er or j, ensure_ascii=False)[:300]}", flush=True); break
        if not ok: continue
        item = {"tomada": nome, "segundos": dur, "taskUUID": tid, "custo": None}; log["itens"].append(item); lf.write_text(json.dumps(log, indent=1))
        fim = time.time() + 2700
        while time.time() < fim:
            time.sleep(10)
            try: j = requests.post(API, headers=CAB, timeout=60, json=[{"taskType": "getResponse", "taskUUID": tid}]).json()
            except Exception: continue
            res = next((d for d in j.get("data", []) if d.get("taskUUID") == tid), {})
            if res.get("videoURL"):
                mn.baixar(res["videoURL"], OUT / f"{nome}.mp4"); (OUT / f"{nome}_prompt.txt").write_text(prompt)
                item["custo"] = res.get("cost") or dur * 0.068; gasto += item["custo"]; lf.write_text(json.dumps(log, indent=1))
                print(f"{nome}: ok US$ {item['custo']:.3f} | leva US$ {gasto:.2f}", flush=True); break
            if res.get("status") in ("error", "failed") or j.get("errors"):
                item["falhou"] = json.dumps(res or j.get("errors"), ensure_ascii=False)[:300]; lf.write_text(json.dumps(log, indent=1))
                print(f"{nome}: FALHOU: {item['falhou']}", flush=True); break
main()
