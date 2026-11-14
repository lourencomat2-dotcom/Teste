#!/usr/bin/env bash
# Pipeline usado para gerar ep01-fazsense-youtube-final.mp4 a partir do original.
# Requer: ffmpeg, python3 + numpy. Rodar numa pasta de trabalho com:
#   ../dl5/video.mp4    (original: ep01-v5.14-fazsense.mp4)
#   ../dl5/legenda.srt  (ep01-v5.14-completo.srt, usado na análise)
set -euo pipefail
SRC=../dl5/video.mp4

# 0) Áudio do original em float mono 48 kHz (usado pelos scripts Python)
ffmpeg -v error -y -i "$SRC" -ac 1 -ar 48000 -f f32le a.raw

# 1) Detectar as faixas diagonais (transições). A de 1:13.79 (quadros 1771-1774)
#    passa sobre o cachorro sem trocar de cena -> substituir por interpolação.
python3 -I 1_detectar_faixas.py

# 1b) Gerar 4 quadros interpolados entre o quadro 1770 e o 1775
mkdir -p ip fill
ffmpeg -v error -y -i "$SRC" -vf "select='eq(n\,1770)+eq(n\,1775)'" -vsync 0 ip/k%d.png
cp ip/k1.png ip/s1.png; cp ip/k1.png ip/s2.png; cp ip/k2.png ip/s3.png; cp ip/k2.png ip/s4.png; cp ip/k2.png ip/s5.png
ffmpeg -v error -y -framerate 1 -i ip/s%d.png \
  -vf "minterpolate=fps=5:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1" -fps_mode passthrough ip/o%02d.png
for i in 07 08 09 10; do cp ip/o$i.png fill/; done

# 2) Nivelar o volume da voz por trecho (inícios de bloco até +4 dB) -> leveled.wav
python3 -I 2_nivelar_voz.py

# 3) Fechar o buraco de áudio em 1:39 -> leveled2.wav
python3 -I 3_fechar_buraco_1m39.py

# 4) Vídeo: troca dos 4 quadros, corte do final em 146 s, fade-out
#    (o áudio desta etapa é substituído no passo 6)
END=146.0; FS=144.8
ffmpeg -v error -y -i "$SRC" -framerate 24 -start_number 7 -i fill/o%02d.png -i leveled2.wav -filter_complex "\
[0:v]trim=end_frame=1771,setpts=PTS-STARTPTS,format=yuv420p[a];\
[1:v]format=yuv420p,setsar=1,setpts=PTS-STARTPTS[b];\
[0:v]trim=start_frame=1775,setpts=PTS-STARTPTS,format=yuv420p[c];\
[a][b][c]concat=n=3:v=1:a=0,trim=duration=$END,fade=t=out:st=$FS:d=1.2[v]" \
 -map "[v]" -map 2:a -r 24 -c:v libx264 -preset slow -crf 17 -profile:v high -level 4.1 \
 -c:a aac -b:a 320k -movflags +faststart v3.mp4

# 5) Áudio final: redução de ruído leve + passa-baixa suave + ganho fixo + limitador true peak
#    (sem loudnorm dinâmico, que aumentava o chiado nas pausas)
PRE="highpass=f=80,afftdn=nr=10:nf=-62:tn=1,acompressor=threshold=-20dB:ratio=1.6:attack=15:release=250:makeup=1,lowpass=f=13000:p=2,pan=stereo|c0=c0|c1=c0"
ffmpeg -v error -y -i leveled2.wav -af "atrim=duration=$END,$PRE,volume=4.2dB,aresample=192000,\
alimiter=limit=0.84:attack=1:release=60:level=disabled,aresample=48000,afade=t=out:st=$FS:d=1.2" -c:a pcm_f32le new.wav

# 6) Montagem final
ffmpeg -v error -y -i v3.mp4 -i new.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 320k -ar 48000 \
  -movflags +faststart ep01-fazsense-youtube-final.mp4

# 7) Trechos de comparação 1:36-1:46
ffmpeg -v error -y -ss 96 -t 10 -i v3.mp4 -c:v libx264 -preset medium -crf 18 -c:a aac -b:a 320k -movflags +faststart trecho-1m36-ANTES.mp4
ffmpeg -v error -y -ss 96 -t 10 -i v3.mp4 -ss 96 -t 10 -i new.wav -map 0:v -map 1:a -c:v libx264 -preset medium -crf 18 \
  -c:a aac -b:a 320k -movflags +faststart trecho-1m36-DEPOIS.mp4
# Nota: o trecho ANTES foi gerado a partir da versão anterior de v3.mp4, cujo áudio usava
# "acompressor(ratio=2,makeup=1.5) + loudnorm=I=-14:TP=-1.5:LRA=7" (modo dinâmico).

# 8) Verificação: volume/true peak e ruído nas pausas
ffmpeg -nostats -i ep01-fazsense-youtube-final.mp4 -af ebur128=peak=true -f null - 2>&1 | grep -E "^\s+(I|Peak):"
ffmpeg -v error -y -i ep01-fazsense-youtube-final.mp4 -ac 1 -ar 48000 -f f32le fin.raw
python3 -I medir_ruido.py fin.raw "Final"
