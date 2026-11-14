# Fecha o silêncio de 0,31 s em "o computador | de outra pessoa" (1:39.1)
# e devolve o mesmo tempo na pausa seguinte (1:40.45), mantendo a sincronia.
# Entrada: leveled.wav (saída de 2_nivelar_voz.py)  Saída: leveled2.wav
import numpy as np, wave
w=wave.open('leveled.wav'); sr=w.getframerate(); y=np.frombuffer(w.readframes(w.getnframes()),'<i2').astype(np.float32)/32767; w.close()
N=len(y)
c0,c1=int(99.15*sr),int(99.39*sr)      # remove 0.24 s inside the hole
ins=int(100.45*sr)                      # pause before "E aqui está o pulo do gato"
xf=int(0.008*sr)
def splice(a,b):  # crossfade end of a into start of b
    r=np.linspace(0,1,xf); m=a[-xf:]*(1-r)+b[:xf]*r
    return np.concatenate([a[:-xf],m,b[xf:]])
z=splice(y[:c0+xf//2], y[c1-xf//2:])
shift=len(y)-len(z)
p=ins-shift
tone=y[int(100.30*sr):int(100.30*sr)+shift+xf]  # real room tone from the same pause
z=splice(splice(z[:p+xf//2],tone),z[p-xf//2:])
z=z[:N] if len(z)>=N else np.pad(z,(0,N-len(z)))
with wave.open('leveled2.wav','wb') as o:
    o.setnchannels(1);o.setsampwidth(2);o.setframerate(sr);o.writeframes((np.clip(z,-1,1)*32767).astype('<i2').tobytes())
