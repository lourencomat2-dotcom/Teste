import numpy as np,subprocess
W,H=640,360
p=subprocess.run(['ffmpeg','-v','error','-i','../dl5/video.mp4','-vf',f'scale={W}:{H}','-f','rawvideo','-pix_fmt','rgb24','-'],capture_output=True).stdout
f=np.frombuffer(p,np.uint8).reshape(-1,H,W,3).astype(np.int16)
res=[]
for i in range(len(f)):
    r,g,b=f[i,...,0],f[i,...,1],f[i,...,2]
    o=(r>190)&(g>120)&(g<200)&(b<120)
    t=(r<120)&(g>160)&(b>160)
    adj=np.zeros_like(o)
    for k in range(1,4):
        adj[:,:-k]|=(o[:,:-k]&t[:,k:])|(t[:,:-k]&o[:,k:])
    rows=np.where(adj.any(1))[0]
    # diagonal line spans many rows with ~1 hit per row
    if len(rows)>40: res.append((i,len(rows),int(adj.sum())))
for i,n,s in res: print(f"{i/24:7.3f} f{i} rows={n} px={s}")
