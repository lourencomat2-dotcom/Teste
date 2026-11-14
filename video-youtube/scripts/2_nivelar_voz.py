import numpy as np, wave
x=np.fromfile('a.raw',dtype=np.float32); sr=48000
hop=480; n=len(x)//hop
e=20*np.log10(np.sqrt(np.mean(x[:n*hop].reshape(n,hop)**2,1))+1e-9)
act=e>-40
# silence runs >=0.25s split chunks
chunks=[];start=None;sil=0
for i,a in enumerate(act):
    if a:
        if start is None: start=i
        sil=0; last=i
    else:
        if start is not None:
            sil+=1
            if sil>=25: chunks.append((start,last+1)); start=None
if start is not None: chunks.append((start,last+1))
def lvl(a,b):
    s=x[a*hop:b*hop]; fr=s[:len(s)//hop*hop].reshape(-1,hop); r=np.sqrt(np.mean(fr**2,1))
    r=r[20*np.log10(r+1e-9)>-35]; return 20*np.log10(np.sqrt(np.mean(r**2))+1e-9)
L=np.array([lvl(a,b) for a,b in chunks]); tgt=np.median(L)
g=np.clip(tgt-L,-6,6)
print("target",round(tgt,1))
for (a,b),l,gg in zip(chunks,L,g):
    if abs(gg)>1: print(f"{a*hop/sr:7.2f}-{b*hop/sr:7.2f} level {l:6.1f} gain {gg:+.1f}")
# gain curve per frame: hold chunk gain, ramp in silences
gc=np.zeros(n)
mids=[0]+[ (chunks[i][1]+chunks[i+1][0])//2 for i in range(len(chunks)-1)]+[n]
for i,(a,b) in enumerate(chunks): gc[mids[i]:mids[i+1]]=g[i]
k=np.ones(15)/15; gc=np.convolve(np.pad(gc,7,mode='edge'),k,'valid')
gs=np.interp(np.arange(len(x)),np.arange(n)*hop+hop/2,gc)
y=x*10**(gs/20)
y=np.clip(y,-1,1)
with wave.open('leveled.wav','wb') as w:
    w.setnchannels(1);w.setsampwidth(2);w.setframerate(sr);w.writeframes((y*32767).astype('<i2').tobytes())
