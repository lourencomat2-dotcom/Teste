import subprocess, json, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
sys.path.insert(0, "/home/user/Teste/novelinhas")
import novelinha as nv
def r(*a): subprocess.run(a, check=True, capture_output=True)
CORTES = [("1",0.0,8.0),("2",0.4,5.9),("3",0.2,6.0),("4",0.0,6.0),("5",0.0,5.9),("6",0.0,7.9),("7",0.0,3.9),("8",0.2,5.8),("9",0.0,4.0)]
VIRADA = "6"; CARD = 4.0
GRADE = open("../grade_suave.txt").read().strip().replace(",format=yuv420p","")
def luma(n, t):
    r("ffmpeg","-v","error","-y","-ss",str(t),"-i",f"clipe_{n}.mp4","-frames:v","1","-vf","scale=320:-1","l.png")
    return np.asarray(Image.open("l.png").convert("L"),dtype=float).mean()
L = {n: np.mean([luma(n,a+0.2), luma(n,(a+b)/2), luma(n,b-0.3)]) for n,a,b in CORTES}
alvo = float(np.median(list(L.values())))
segs, t, ini = [], 0.0, {}
for k,(n,a,b) in enumerate(CORTES):
    d=b-a; ini[n]=t; g=float(np.clip(alvo/L[n],0.88,1.12))
    r("ffmpeg","-v","error","-y","-ss",f"{a}","-t",f"{d}","-i",f"clipe_{n}.mp4",
      "-vf",f"scale=1280:720,setsar=1,fps=24,colorchannelmixer=rr={g:.3f}:gg={g:.3f}:bb={g:.3f},format=yuv420p",
      "-af",f"aresample=48000,aformat=channel_layouts=stereo,adeclick,afade=t=in:d=0.03,afade=t=out:st={d-0.04:.2f}:d=0.04",
      "-c:v","libx264","-preset","veryfast","-crf","14","-c:a","pcm_s16le",f"s{k}.mov")
    segs.append(f"s{k}.mov"); t+=float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",f"s{k}.mov"],capture_output=True,text=True).stdout)
    print(f"plano {n}: luma {L[n]:.1f} ganho {g:.3f} início {ini[n]:.2f}s dur {d:.2f}s")
historia=t
r("ffmpeg","-v","error","-y","-sseof","-0.1","-i","clipe_9.mp4","-update","1","-frames:v","1","card_base.png")
img=ImageEnhance.Brightness(Image.open("card_base.png").convert("RGB").resize((1280,720)).filter(ImageFilter.GaussianBlur(14))).enhance(0.5)
dr=ImageDraw.Draw(img); f1,f2=nv.fonte(54),nv.fonte(42)
def c(txt,y,f,cor=(255,255,255)): dr.text(((1280-dr.textlength(txt,font=f))/2,y),txt,font=f,fill=cor,stroke_width=3,stroke_fill=(0,0,0))
c("ASSISTA TAMBÉM",90,f1)
for x in (170,700): dr.rounded_rectangle((x,190,x+410,421),radius=14,outline=(255,255,255),width=4)
dr.rounded_rectangle((440,480,840,560),radius=16,fill=(204,0,0)); c("INSCREVA-SE",497,f2); c("ATIVA O SININHO",590,f2,(255,214,0))
img.save("card.png")
r("ffmpeg","-v","error","-y","-loop","1","-framerate","24","-i","card.png","-f","lavfi","-i","anullsrc=r=48000:cl=stereo","-t",f"{CARD}",
  "-vf","fade=t=in:st=0:d=0.6,format=yuv420p","-c:v","libx264","-preset","veryfast","-crf","14","-c:a","pcm_s16le","-shortest","card.mov")
segs.append("card.mov"); total=historia+CARD
Path("lista.txt").write_text("".join(f"file '{s}'\n" for s in segs))
r("ffmpeg","-v","error","-y","-f","concat","-safe","0","-i","lista.txt","-c","copy","junto.mov")
trilha=sorted(Path("/home/user/Teste/novelinhas/ep003").glob("trilha_*.mp3"))[0]
v0=ini[VIRADA]
fc=(f"[0:a]asplit=2[dial][sc];"
    f"[1:a]aresample=48000,aformat=channel_layouts=stereo,aloop=loop=-1:size=480000,atrim=duration={total:.2f},volume=0.35,afade=t=in:d=0.5,afade=t=out:st={historia-0.5:.2f}:d=1.0[amb];"
    f"[2:a]aresample=48000,aformat=channel_layouts=stereo,atrim=duration={total:.2f},"
    f"volume='0.09+0.10*between(t,{v0:.2f},{historia:.2f})+0.22*gte(t,{historia:.2f})':eval=frame,afade=t=in:d=1.5,afade=t=out:st={total-1.5:.2f}:d=1.5[mus];"
    f"[mus][sc]sidechaincompress=threshold=0.02:ratio=6:attack=25:release=450[duck];"
    f"[dial][amb][duck]amix=inputs=3:normalize=0:duration=first[pre]")
r("ffmpeg","-v","error","-y","-i","junto.mov","-i","amb_v2.mp3","-stream_loop","-1","-i",str(trilha),"-filter_complex",fc,"-map","[pre]","-c:a","pcm_s16le","-ar","48000","pre.wav")
m=subprocess.run(["ffmpeg","-hide_banner","-i","pre.wav","-af","loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json","-f","null","-"],capture_output=True,text=True).stderr
j=json.loads(m[m.rindex("{"):m.rindex("}")+1])
ln=(f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={j['input_i']}:measured_TP={j['input_tp']}:measured_LRA={j['input_lra']}:"
    f"measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true,aresample=48000")
r("ffmpeg","-v","error","-y","-i","pre.wav","-af",ln,"-c:a","pcm_s16le","final.wav")
out=Path("../ep003-v2-final.mp4")
r("ffmpeg","-v","error","-y","-i","junto.mov","-i","final.wav","-map","0:v","-map","1:a","-vf",f"{GRADE},format=yuv420p",
  "-c:v","libx264","-preset","slow","-crf","22","-c:a","aac","-b:a","160k","-ac","2","-movflags","+faststart",str(out))
json.dump({"historia":round(historia,2),"total":round(total,2),"inicios":ini},open("tempos.json","w"))
print("história %.2f s, total %.2f s"%(historia,total))
