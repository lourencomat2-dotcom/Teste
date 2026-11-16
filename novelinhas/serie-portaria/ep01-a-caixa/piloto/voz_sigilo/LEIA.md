# Voz do Sigilo, tratada na edição (sem custo de geração)

O vídeo é gerado com a fala normal; na montagem o áudio do Sigilo passa por um filtro do ffmpeg.
O bico continua sincronizado porque a duração não muda.

| Versão | Filtro | Transcritor ouviu |
|---|---|---|
| original | nenhum | O segundo é do Valdir. |
| A | rubberband=pitch=1.6:formant=shifted,highpass=f=600,lowpass=f=5500,equalizer=f=2500:t=q:w=1.2:g=6,vibrato=f=18:d=0.25,asoftclip=type=tanh | O segundo é do maldito! |
| B | rubberband=pitch=1.45:formant=shifted,highpass=f=500,lowpass=f=6000,equalizer=f=3000:t=q:w=1:g=8,acrusher=bits=8:mix=0.25:mode=log,tremolo=f=30:d=0.35 | O segundo é do Valdir. |
| C | rubberband=pitch=1.9:formant=shifted,highpass=f=900,lowpass=f=7000,equalizer=f=3500:t=q:w=1:g=6,vibrato=f=12:d=0.3 | O segundo é do Audi! |

Comparação: `../sigilo_vozes_comparar.mp4` (original, A, B, C em sequência).
