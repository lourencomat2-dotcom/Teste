import numpy as np,sys
sr=48000
# pauses (s) found earlier, all >= 0.4 s of no speech
P=[(100.30,100.75),(55.30,55.65),(26.50,26.80),(117.0,117.15),(4.45,4.80)]
def stats(f,skip_end=None):
    x=np.fromfile(f,dtype=np.float32)
    if x.ndim==1 and f.endswith('st.raw'): x=x.reshape(-1,2).mean(1)
    out=[]
    for a,b in P:
        s=x[int((a+.03)*sr):int((b-.03)*sr)]
        rms=20*np.log10(np.sqrt(np.mean(s**2))+1e-12)
        S=np.abs(np.fft.rfft(s*np.hanning(len(s))))**2; fr=np.fft.rfftfreq(len(s),1/sr)
        tot=S.sum(); hi=S[fr>12000].sum()/tot*100; mid=S[(fr>4000)&(fr<12000)].sum()/tot*100
        out.append((rms,hi,mid))
    o=np.array(out); print(f"{sys.argv[2]:32s} ruído médio {o[:,0].mean():6.1f} dBFS (pior {o[:,0].max():6.1f})  energia >12kHz {o[:,1].mean():4.0f}%  4-12kHz {o[:,2].mean():4.0f}%")
stats(sys.argv[1])
