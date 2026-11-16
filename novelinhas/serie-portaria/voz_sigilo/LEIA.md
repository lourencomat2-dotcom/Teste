# Voz do Sigilo — teste 2 (papagaio de verdade), 16/11

Script: `../voz_sigilo.py`. Fala: "O segundo é do Valdir!". Custo total: US$ 0,0037.
Comparação em cima do clipe 3 do piloto: `../sigilo_vozes_v2.mp4`.

| Versão | Modelo | Direção | Duração da fala | Transcritor |
|---|---|---|---|---|
| A | Qwen3-TTS VoiceDesign | papagaio imitando gente: agudo, nasal, metálico, picotado | 5,9 s | O segundo é do Valbir! |
| B | Qwen3-TTS VoiceDesign | papagaio imitando um homem: espremido, estridente, rouco, assobiado | 4,8 s | O segundo é do Valdir! |
| C | Gemini 3.1 Flash TTS, voz Puck | tag: papagaio de verdade, estridente, rouco, nasal | 2,8 s | O segundo é do Valdir. |
| D | Gemini 3.1 Flash TTS, voz Fenrir | tag: imitação estridente de papagaio | 2,4 s | O segundo é do Valdir. |

Descrições completas em `testes.json`. Teste 1 (filtros sobre a voz do Seedance) reprovado pelo Lucas.

# Teste 3 (papagaio de programa de TV, voz original), 16/11

Direção do Lucas: algo na linha de papagaio de programa de TV (boneco). Voz original, sem copiar personagem ou ator.
Custo: US$ 0,0044. Escuta: `../sigilo_vozes_v3.mp4`. Descrições em `testes_r3.json`.

| Versão | Modelo | Fala dura | Transcritor |
|---|---|---|---|
| E | Qwen3-TTS VoiceDesign | 3,0 s | O segundo é do Valtir! |
| F | Qwen3-TTS VoiceDesign | 2,0 s | Ah, segundo é do Valdear! |
| G | Gemini 3.1 Flash TTS, voz Puck | 1,9 s | O segundo é do Faldir. |
| H | Gemini 3.1 Flash TTS, voz Algenib | 3,5 s | O segundo é do Valdir! |
