"""Montador de episódios em animação limitada — v3.

    python3 episodio.py                 # render completo
    python3 episodio.py preview 12 40   # salva quadros de checagem nesses segundos
    python3 episodio.py vozes           # só gera e confere as vozes (relatório de pronúncia)
    python3 episodio.py --roteiro outro.txt

Roteiro em roteiro.txt (formato no topo dele). Vozes: Kokoro (neural, offline), com
conferência automática de pronúncia por reconhecimento de fala (Whisper). Risada de
plateia sintetizada (sem gravações), calibrada com um classificador de sons.
"""
import hashlib, json, math, os, re, subprocess, sys, wave, shutil
from multiprocessing import Pool
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from scipy.signal import resample_poly, fftconvolve, butter, sosfilt

MOTOR = os.path.dirname(os.path.abspath(__file__))
DIR = os.path.dirname(MOTOR)                      # raiz do projeto
VOZES_DIR = os.path.join(DIR, "vozes")
sys.path.insert(0, VOZES_DIR)

# ======================= SAÍDA =======================
W, H, FPS, SS = 1920, 1080, 30, 2
K = W / 1280
SR = 44100
FONTES = {k: os.path.join(DIR, "fontes", v) for k, v in {
    "titulo": "ArchivoBlack-Regular.ttf", "bold": "Poppins-Bold.ttf", "medio": "Poppins-Medium.ttf",
    "regular": "Poppins-Regular.ttf", "marcador": "ComicRelief-Bold.ttf"}.items()}
_fonts = {}
def font(size, tipo="bold"):
    k = (int(size), tipo)
    if k not in _fonts:
        try: _fonts[k] = ImageFont.truetype(FONTES[tipo], max(6, int(size)))
        except OSError: _fonts[k] = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", max(6, int(size)))
    return _fonts[k]

# ======================= ELENCO =======================
ELENCO = {
    "clara": dict(nome="Clara", cor_nome=(120, 230, 190), x=430, dy=0,
                  pele=(232, 180, 140), roupa=(70, 150, 120), cabelo=(70, 40, 30), calca=(60, 70, 110),
                  voz=dict(voz="pf_dora", vel=1.05)),
    "beto": dict(nome="Beto", cor_nome=(255, 190, 110), x=850, dy=0,
                 pele=(180, 120, 85), roupa=(235, 140, 50), cabelo=(30, 25, 25), calca=(80, 80, 90),
                 voz=dict(voz="pm_alex", vel=1.1)),
    "neide": dict(nome="Dona Neide", cor_nome=(210, 170, 255), x=1130, dy=26,
                  pele=(222, 170, 135), roupa=(125, 80, 150), cabelo=(190, 190, 196), calca=(90, 60, 110),
                  voz=dict(voz={"pf_dora": 0.7, "ef_dora": 0.3}, vel=0.95, envelhecer=dict(formante=0.93, pitch=160, faixa=1.4))),
}
LINHA = (58, 40, 40)
GAP = 0.28
PAUSA_RISO = {"risadinha": 0.9, "risada": 1.35, "forte": 1.9}

# ======================= ROTEIRO =======================
def kv(s):
    a, _, b = s.partition("="); return a.strip().lower(), b.strip().lower()

def ler_roteiro(path):
    meta, blocos, cena = {}, [], None
    rx = re.compile(r"^(\w+)\s*(?:\[(\w+)\])?\s*(?:\(([\w_]+)\))?\s*(?:\{([^}]*)\})?\s*(?:<([^>]*)>)?\s*:\s*(.+)$")
    for n, raw in enumerate(open(path, encoding="utf-8"), 1):
        s = raw.strip()
        if not s or s.startswith("#"): continue
        if s.startswith("=="):
            partes = [p.strip() for p in s[2:].split("|")]; cab = partes[0]
            if cab.upper().startswith("CENA"):
                cena = dict(kind="cena", nome=cab[4:].strip() or f"cena{len(blocos)}", elenco=[], inicio={},
                            pre=1.2, post=1.4, falas=[], bigode=["beto"])
                for p in partes[1:]:
                    k, _, v = p.partition(":") if ":" in p else p.partition("=")
                    k, v = k.strip().lower(), v.strip()
                    if k == "elenco": cena["elenco"] = [x.strip().lower() for x in v.split(",")]
                    elif k == "inicio": cena["inicio"] = dict(kv(x) for x in v.split(","))
                    elif k in ("pre", "post"): cena[k] = float(v)
                    elif k == "entra": cena["entra_quem"] = v.lower()
                    elif k == "bigode": cena["bigode"] = [x.strip().lower() for x in v.split(",") if x.strip()]
                blocos.append(cena)
            elif cab.upper().startswith("ABERTURA"): blocos.append(dict(kind="card", nome="abertura", dur=7.8)); cena = None
            elif cab.upper().startswith("VINHETA"):
                blocos.append(dict(kind="card", nome="vinheta", dur=2.4, texto=cab[7:].strip() or "Mais tarde...")); cena = None
            elif cab.upper().startswith("CREDITOS"): blocos.append(dict(kind="card", nome="creditos", dur=8.5)); cena = None
            continue
        if cena is None and ":" in s and s.split(":")[0].strip().upper() in ("TITULO", "EPISODIO", "CRIACAO"):
            k, _, v = s.partition(":"); meta[k.strip().upper()] = v.strip(); continue
        mr = re.fullmatch(r"\((risadinha|risada|risada forte)\)", s.lower())
        if mr:
            if cena is None or not cena["falas"]: sys.exit(f"roteiro linha {n}: risada sem fala antes")
            cena["falas"][-1]["riso"] = {"risadinha": "risadinha", "risada": "risada", "risada forte": "forte"}[mr.group(1)]
            continue
        m = rx.match(s)
        if not m or cena is None: sys.exit(f"roteiro linha {n}: não entendi -> {s}")
        who = m.group(1).lower()
        if who not in ELENCO: sys.exit(f"roteiro linha {n}: personagem desconhecido {who}")
        ins = None
        if m.group(5):
            a = m.group(5).split(None, 2)
            evs = []
            for e in (a[2].split(";") if len(a) > 2 else []):
                e = e.strip()
                if e: nome, _, arg = e.partition(" "); evs.append((nome.strip(), arg.strip()))
            ins = (a[0], float(a[1]), evs)
        cena["falas"].append(dict(who=who, ex=m.group(2) or "neutro", shot=m.group(3) or f"close_{who}",
                                  react=dict(kv(x) for x in m.group(4).split(",")) if m.group(4) else {},
                                  insert=ins, text=m.group(6).strip(), riso=None))
    return meta, blocos

# ======================= ÁUDIO =======================
def para_sr(a, sr):
    if sr == SR: return a.astype(np.float32)
    g = math.gcd(sr, SR); return resample_poly(a, SR // g, sr // g).astype(np.float32)

def filtro(a, tipo, f, ordem=2):
    return sosfilt(butter(ordem, f, btype=tipo, fs=SR, output="sos"), a).astype(np.float32)

IR_SALA = None
def reverb_sala(a, wet=0.09):
    global IR_SALA
    if IR_SALA is None:
        t = np.arange(int(0.35 * SR)) / SR
        IR_SALA = filtro(np.random.default_rng(3).standard_normal(len(t)).astype(np.float32) * np.exp(-t / 0.07), "low", 4000)
        IR_SALA /= np.abs(IR_SALA).sum() ** 0.5 * 4
    r = fftconvolve(a, IR_SALA)[: len(a) + len(IR_SALA)]
    out = np.zeros_like(r); out[: len(a)] = a; return out + wet * r

def envelhecer(a, sr, formante, pitch, faixa, dur=1.0):
    import parselmouth
    from parselmouth.praat import call
    s = parselmouth.Sound(a.astype(np.float64), sampling_frequency=sr)
    s2 = call(s, "Change gender", 75, 600, formante, pitch, faixa, dur)
    return s2.values[0].astype(np.float32)

def aparar(a, sr):
    nz = np.nonzero(np.abs(a) > 0.01 * np.abs(a).max())[0]
    return a[max(0, nz[0] - int(0.01 * sr)): nz[-1] + int(0.06 * sr)] if len(nz) else a

RELATORIO = []
def gerar_voz(i, who, text):
    os.makedirs(f"{DIR}/cache_falas", exist_ok=True)
    v = ELENCO[who]["voz"]; h = hashlib.md5((text + json.dumps(v, sort_keys=True)).encode()).hexdigest()[:10]
    path, meta = f"{DIR}/cache_falas/{i:03d}_{who}_{h}.wav", f"{DIR}/cache_falas/{i:03d}_{who}_{h}.json"
    if not os.path.exists(path):
        import kokoro_pt as KK
        try:
            import asr; tem_asr = os.path.exists(asr.D)      # conferência de pronúncia é opcional
        except Exception: tem_asr = False
        melhor = None
        for vel in (v["vel"], v["vel"] * 0.93, v["vel"] * 1.05, v["vel"] * 0.88):
            a, ps = KK.falar(text, v["voz"], vel); a = aparar(a, KK.SR)
            if v.get("envelhecer"): a = envelhecer(a, KK.SR, **v["envelhecer"])
            if tem_asr: hyp = asr.transcrever(a, KK.SR); erro = asr.wer(text, hyp)
            else: hyp, erro = "(sem conferência)", 0.0
            if melhor is None or erro < melhor[0]: melhor = (erro, a, hyp, vel)
            if erro <= 0.08: break
        erro, a, hyp, vel = melhor
        with wave.open(path, "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(KK.SR)
            w.writeframes((np.clip(a / (np.abs(a).max() + 1e-9) * 0.95, -1, 1) * 32000).astype(np.int16).tobytes())
        json.dump(dict(texto=text, ouvido=hyp, erro=erro, vel=vel), open(meta, "w"), ensure_ascii=False)
    info = json.load(open(meta)); RELATORIO.append((i, who, info))
    with wave.open(path) as w:
        sr = w.getframerate(); a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    a = para_sr(a, sr)
    a = filtro(a, "high", 85)
    a = np.tanh(a / (np.abs(a).max() + 1e-9) * 1.6) / np.tanh(1.6)
    a = a * (0.12 / (np.sqrt(np.mean(a ** 2)) + 1e-9))
    return np.clip(a, -0.98, 0.98).astype(np.float32)

def mix(buf, t, s, pan=0.0, vol=1.0):
    i = int(t * SR); j = min(len(buf), i + len(s))
    if j <= i: return
    s = s[: j - i] * vol
    if s.ndim == 1:
        ang = (pan + 1) * math.pi / 4
        buf[i:j, 0] += s * math.cos(ang) * 1.41; buf[i:j, 1] += s * math.sin(ang) * 1.41
    else: buf[i:j] += s

# ---------- música e efeitos ----------
def tom(midi, dur, vol=1.0, timbre="marimba"):
    f = 440 * 2 ** ((midi - 69) / 12); t = np.arange(int(dur * SR)) / SR
    if timbre == "baixo":
        s = np.sin(2 * np.pi * f * t) + 0.3 * np.sin(4 * np.pi * f * t) * np.exp(-t * 8); env = np.exp(-t * 4)
    elif timbre == "pad":
        s = sum(np.sin(2 * np.pi * f * n * t * (1 + 0.002 * (n % 3))) / n for n in range(1, 7))
        env = np.minimum(1, t / 0.25) * np.minimum(1, (dur - t) / 0.3).clip(0)
    else:
        s = (np.sin(2 * np.pi * f * t) + 0.4 * np.sin(2 * np.pi * 4 * f * t) * np.exp(-t * 20)
             + 0.2 * np.sin(2 * np.pi * 2 * f * t) + 0.08 * np.sin(2 * np.pi * 10 * f * t) * np.exp(-t * 40))
        env = np.exp(-t * 5.5)
    return (s * env * np.minimum(1, t / 0.003) * vol).astype(np.float32)

def ruido(dur, seed=0): return np.random.default_rng(seed).standard_normal(int(dur * SR)).astype(np.float32)
def palma():
    t = np.arange(int(0.18 * SR)) / SR; n = filtro(ruido(0.18, 1), "band", [900, 5000])
    return n * (np.exp(-t * 35) + 0.6 * np.exp(-((t - 0.012) * 300) ** 2)) * 0.5
def chocalho(seed):
    t = np.arange(int(0.06 * SR)) / SR; return filtro(ruido(0.06, seed), "high", 6000) * np.exp(-t * 60) * 0.25

def tema(final=False):
    beat = 60 / 140; n = int((16 * beat + 2.4) * SR); L = np.zeros((n, 2), np.float32)
    mel = [72, 76, 79, 76, 74, 72, 74, 76, 76, 72, 69, 72, 76, 77, 76, 74,
           72, 77, 81, 77, 76, 74, 72, 69, 71, 74, 79, 77, 76, 74, 71, 74]
    for k, m in enumerate(mel): mix(L, k * beat / 2, tom(m, 0.7, 0.5), pan=0.25)
    acordes = [[60, 64, 67], [57, 60, 64], [53, 57, 60], [55, 59, 62]]; raizes = [(48, 55), (45, 52), (41, 48), (43, 50)]
    for b in range(4):
        for m in acordes[b]: mix(L, b * 4 * beat, tom(m, 4 * beat, 0.10, "pad"), pan=-0.4 + 0.4 * (m % 3))
        for k in range(4):
            r, q = raizes[b]; mix(L, (b * 4 + k) * beat, tom(r if k % 2 == 0 else q, beat * 0.95, 0.75, "baixo"))
            if k % 2 == 1: mix(L, (b * 4 + k) * beat, palma(), pan=0.1)
        for k in range(8): mix(L, (b * 4) * beat + k * beat / 2, chocalho(b * 8 + k), pan=-0.3)
    for m in (60, 64, 67, 72, 76): mix(L, 16 * beat, tom(m, 2.4, 0.4), pan=(m - 66) / 20)
    mix(L, 16 * beat, palma())
    if final: L *= (np.linspace(1, 0, n) ** 0.6)[:, None]
    return L / np.abs(L).max() * 0.5

def vinheta_som():
    L = np.zeros((int(2.7 * SR), 2), np.float32); st = 0.12
    for k, m in enumerate([72, 76, 79, 84]): mix(L, k * st, tom(m, 0.6, 0.55), pan=-0.3 + 0.2 * k)
    for m in (60, 67, 72, 76, 79): mix(L, 4 * st, tom(m, 2.2, 0.35), pan=(m - 70) / 20)
    mix(L, 4 * st, palma()); return L / np.abs(L).max() * 0.45

def sfx_pop():
    t = np.arange(int(0.09 * SR)) / SR; f = 1100 * np.exp(-t * 18) + 380
    return (np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 45) * 0.35).astype(np.float32)
def sfx_cadeado():
    t = np.arange(int(0.25 * SR)) / SR
    s = (np.sin(2 * np.pi * 1850 * t) + 0.6 * np.sin(2 * np.pi * 2730 * t)) * np.exp(-t * 28) * 0.25
    s[: int(0.02 * SR)] += filtro(ruido(0.02, 5), "high", 2000) * 0.6; return s.astype(np.float32)
def sfx_corrente():
    s = np.zeros(int(0.5 * SR), np.float32); rng = np.random.default_rng(9)
    for k in range(9):
        t0 = int(rng.uniform(0, 0.42) * SR); tt = np.arange(int(0.05 * SR)) / SR
        c = (np.sin(2 * np.pi * rng.uniform(2500, 4200) * tt) * np.exp(-tt * 90) * 0.15).astype(np.float32); s[t0:t0 + len(c)] += c
    return s
def sfx_passo(seed):
    t = np.arange(int(0.12 * SR)) / SR
    return (filtro(ruido(0.12, seed), "low", 500) * 0.8 + np.sin(2 * np.pi * 95 * t) * 0.6) * np.exp(-t * 40) * 0.35
def sfx_batida():
    t = np.arange(int(0.18 * SR)) / SR
    return ((np.sin(2 * np.pi * 160 * t) + 0.5 * np.sin(2 * np.pi * 330 * t)) * np.exp(-t * 30)
            + filtro(ruido(0.18, 8), "band", [400, 2500]) * np.exp(-t * 80) * 0.6).astype(np.float32) * 0.5
def sfx_marcador(dur, seed):
    n = int(dur * SR); rng = np.random.default_rng(seed); t = np.arange(n) / SR
    mod = np.abs(np.sin(2 * np.pi * rng.uniform(5, 8) * t + rng.uniform(0, 3))) ** 0.5
    return filtro(ruido(dur, seed), "band", [2500, 7000]) * mod * np.minimum(1, np.minimum(t, dur - t) / 0.03) * 0.09
def sfx_whoosh():
    t = np.arange(int(0.6 * SR)) / SR; return filtro(ruido(0.6, 7), "band", [600, 4000]) * np.sin(np.pi * t / 0.6) ** 2 * 0.25
def ambiente(dur):
    n = int(dur * SR); b = np.cumsum(ruido(dur, 11)); b = filtro(b - np.mean(b), "high", 30)
    b = b / (np.abs(b).max() + 1e-9) * 0.006; t = np.arange(n) / SR
    hum = (np.sin(2 * np.pi * 50 * t) + 0.5 * np.sin(2 * np.pi * 100 * t)) * 0.0015
    return ((b + hum) * np.minimum(1, np.minimum(t / 0.4, (dur - t) / 0.4))).astype(np.float32)

_riso_ok = False
def risada(intensidade, seed):
    global _riso_ok
    import riso_sintese as RS, busca_riso as BR
    if not _riso_ok:
        p = json.load(open(f"{VOZES_DIR}/melhor_riso.json")); p = {k: tuple(v) if isinstance(v, list) else v for k, v in p.items()}
        BR.configurar(p); RS.pessoa = BR.pessoa; _riso_ok = p
    return para_sr(RS.plateia(intensidade, seed, molhado=_riso_ok["molhado"]), RS.SR) if RS.SR != SR else \
        RS.plateia(intensidade, seed, molhado=_riso_ok["molhado"])

# ======================= LINHA DO TEMPO =======================
def montar(roteiro_path):
    meta, blocos = ler_roteiro(roteiro_path)
    falas, planos, eventos, sons, cenas, risos = [], [], [], [], [], []
    t, idx = 0.0, 0
    for b in blocos:
        if b["kind"] == "card":
            planos.append(dict(t0=t, t1=t + b["dur"], tipo="card", card=b))
            if b["nome"] == "abertura": sons += [(t, tema()), (t + 0.9, sfx_whoosh())]
            elif b["nome"] == "vinheta": sons.append((t, vinheta_som()))
            else: sons.append((t, tema(final=True)))
            t += b["dur"]; continue
        cena = dict(b, t0=t); cenas.append(cena)
        if b.get("entra_quem"):
            cena["entra"] = (t + 1.0, t + 2.2)
            for k in range(3): sons.append((t + 0.15 + k * 0.22, sfx_batida()))
        cortes = [(t, "geral")]; t += b["pre"]
        for fl in b["falas"]:
            a = gerar_voz(idx, fl["who"], fl["text"]); idx += 1
            fl = dict(fl, t0=t, t1=t + len(a) / SR, audio=a, cena=cena)
            falas.append(fl); cortes.append((t - 0.2, fl["shot"]))
            t = fl["t1"] + GAP
            if fl["riso"] and not fl["insert"]:
                risos.append((fl["t1"] + 0.1, fl["riso"])); t += PAUSA_RISO[fl["riso"]]
            if fl["insert"]:
                nome, dur, evs = fl["insert"]; cortes.append((t - 0.1, nome)); te = t - 0.1 + 0.45
                ultimo = te
                for k, (ev, arg) in enumerate(evs):
                    eventos.append(dict(t=te + k * 0.9, nome=ev, arg=arg)); ultimo = te + k * 0.9
                    if ev.startswith("sai_"): cena["sai"] = (t, t + 1.3)
                    if ev == "quadro": ultimo += 0.55 * len(linhas_quadro(arg))
                if fl["riso"]:
                    t_riso = (ultimo + 0.5) if evs else (te + 0.6)
                    risos.append((t_riso, fl["riso"])); t = max(t + dur, t_riso + PAUSA_RISO[fl["riso"]])
                else:
                    t += dur
        if falas[-1]["insert"]:          # cena termina no próprio inserto
            t = t - GAP + 0.3
        else:
            cortes.append((falas[-1]["t1"] + 0.35 + (PAUSA_RISO[falas[-1]["riso"]] if falas[-1]["riso"] else 0), "geral"))
            t = max(t, falas[-1]["t1"] + b["post"])
        cena["t1"] = t
        limpos = []
        for c in sorted(cortes, key=lambda c: c[0]):
            if limpos and limpos[-1][1] == c[1]: continue
            if limpos and c[0] - limpos[-1][0] < 0.4: limpos[-1] = (limpos[-1][0], c[1]); continue
            limpos.append(c)
        for k, (c0, nome) in enumerate(limpos):
            c1 = limpos[k + 1][0] if k + 1 < len(limpos) else t
            if c1 - c0 > 0.05: planos.append(dict(t0=c0, t1=c1, tipo="cena", shot=nome, cena=cena))
    return meta, falas, planos, eventos, sons, cenas, risos, t

def mixar_audio(falas, eventos, sons, cenas, risos, total, path):
    n = int((total + 1) * SR)
    dial = np.zeros((n, 2), np.float32); fx = np.zeros((n, 2), np.float32); plat = np.zeros((n, 2), np.float32)
    for c in cenas: mix(fx, c["t0"], ambiente(c["t1"] - c["t0"]))
    for fl in falas:
        mix(dial, fl["t0"], reverb_sala(fl["audio"]), pan=(ELENCO[fl["who"]]["x"] - 700) / 700 * 0.45)
    for t0, s in sons: mix(fx, t0, s)
    for k, (t0, intens) in enumerate(risos):
        r = risada(intens, 100 + k); r = r * (0.075 / (np.sqrt(np.mean(r[: int(1.0 * SR)] ** 2)) + 1e-9))
        mix(plat, t0, r)
    for e in eventos:
        if e["nome"] == "etiquetas":
            for k in range(4): mix(fx, e["t"] + k * 0.3, sfx_pop(), pan=-0.5)
        elif e["nome"] == "cadeado":
            mix(fx, e["t"] - 0.15, sfx_corrente(), pan=-0.5); mix(fx, e["t"] + 0.22, sfx_cadeado(), pan=-0.5)
        elif e["nome"] == "quadro":
            n_l = len(linhas_novas(e));
            for k in range(n_l): mix(fx, e["t"] + k * 0.55, sfx_marcador(0.45, k + int(e["t"])), pan=-0.5)
    for c in cenas:
        for chave in ("entra", "sai"):
            if chave in c:
                a, b = c[chave]; k = 0
                while a + k * 0.32 < b: mix(fx, a + k * 0.32, sfx_passo(k), pan=0.6); k += 1
    # plateia abaixa quando alguém fala (ducking)
    vad = np.abs(dial).max(1); w = int(0.05 * SR); vad = np.convolve(vad, np.ones(w) / w, "same")
    vad = np.clip(vad / 0.05, 0, 1); duck = 1 - 0.55 * np.convolve(vad, np.ones(int(0.2 * SR)) / int(0.2 * SR), "same")
    buf = dial + fx + plat * duck[:, None]
    buf = np.clip(buf, -1, 1)
    with wave.open(path, "wb") as wv:
        wv.setnchannels(2); wv.setsampwidth(2); wv.setframerate(SR); wv.writeframes((buf * 32000).astype(np.int16).tobytes())

def analisar_boca(fl):
    a = fl["audio"]; n = SR // FPS; env, cen = [], []; freqs = np.fft.rfftfreq(n, 1 / SR)
    for i in range(0, len(a), n):
        seg = a[i:i + n]
        if len(seg) < n: seg = np.pad(seg, (0, n - len(seg)))
        env.append(np.sqrt(np.mean(seg ** 2))); sp = np.abs(np.fft.rfft(seg * np.hanning(n)))
        cen.append((sp * freqs).sum() / (sp.sum() + 1e-9))
    env = np.convolve(np.array(env), [0.25, 0.5, 0.25], "same")
    fl["env"] = env / (env.max() + 1e-9); fl["cen"] = np.array(cen)

# ======================= ESTADO =======================
def ease(u): u = max(0.0, min(1.0, u)); return u * u * (3 - 2 * u)

def linhas_quadro(arg): return [l.strip() for l in arg.split("|")] if arg else []
_QD = []
def linhas_novas(e):
    ant = []
    for q in _QD:
        if q["t"] < e["t"]: ant = linhas_quadro(q["arg"])
    novas = linhas_quadro(e["arg"]); return [i for i, l in enumerate(novas) if i >= len(ant) or ant[i] != l]

class Estado:
    def __init__(s, falas, eventos, cenas):
        s.falas, s.eventos = falas, eventos
        s.por_cena = {id(c): [f for f in falas if f["cena"] is c] for c in cenas}
    def da(s, cena): return s.por_cena[id(cena)]
    def fala_de(s, cena, who, tt):
        for fl in s.da(cena):
            if fl["who"] == who and fl["t0"] - 0.3 <= tt < fl["t1"] + 0.35: return fl
    def boca(s, cena, who, tt):
        for fl in s.da(cena):
            if fl["who"] == who and fl["t0"] <= tt < fl["t1"]:
                k = min(int((tt - fl["t0"]) * FPS), len(fl["env"]) - 1); v, c = fl["env"][k], fl["cen"][k]
                if v < 0.16: return "fechada", 0
                if v < 0.45: return ("larga" if c > 2300 else "pequena"), v
                return ("redonda" if c < 1200 else "larga" if c > 2600 else "aberta"), v
        return "fechada", 0
    def expressao(s, cena, who, tt):
        ex = cena["inicio"].get(who, "neutro")
        for fl in s.da(cena):
            if fl["who"] == who and fl["t0"] - 0.3 <= tt: ex = fl["ex"]
            elif who in fl["react"] and fl["t0"] + 0.4 <= tt: ex = fl["react"][who]
        return ex
    def falante(s, cena, tt):
        atual, ant = None, None
        for fl in s.da(cena):
            if fl["t0"] - 0.2 <= tt:
                if atual and atual["who"] != fl["who"]: ant = atual
                atual = fl
        return atual, ant
    def posicao(s, cena, who, tt):
        x = ELENCO[who]["x"]
        if cena.get("entra_quem") == who:
            a, b = cena["entra"]
            if tt < a: return None, False
            x = 1470 + (x - 1470) * ease((tt - a) / (b - a)); anda = tt < b
            if "sai" in cena:
                a2, b2 = cena["sai"]
                if tt >= b2: return None, False
                if tt >= a2: x = ELENCO[who]["x"] + (1490 - ELENCO[who]["x"]) * ease((tt - a2) / (b2 - a2)); anda = True
            return x, anda
        return x, False
    def olhar(s, cena, who, x, tt, presentes):
        at, ant = s.falante(cena, tt); alvo = None
        if at and at["who"] != who: alvo = at["who"]
        elif ant and ant["who"] != who: alvo = ant["who"]
        if alvo not in presentes:
            outros = [o for o in presentes if o != who]
            alvo = min(outros, key=lambda o: abs(presentes[o] - x)) if outros else None
        return 0 if alvo is None else (1 if presentes[alvo] > x else -1)
    def legenda(s, cena, tt):
        for fl in s.da(cena):
            if fl["t0"] - 0.1 <= tt < fl["t1"] + 0.25: return fl
    def primeiro(s, nome):
        for e in s.eventos:
            if e["nome"] == nome: return e["t"]
    def quadro(s, tt):
        atual, ant = None, None
        for e in s.eventos:
            if e["nome"] == "quadro" and e["t"] <= tt: ant, atual = atual, e
        return atual, ant

# ======================= CÂMERA =======================
class Cam:
    def __init__(s, c, z, oy=0.0): s.cx, s.cy, s.z, s.oy = c[0], c[1], z * SS * K, oy
    def p(s, x, y): return ((x - s.cx) * s.z + W * SS / 2, (y + s.oy - s.cy) * s.z + H * SS / 2)
    def r(s, v): return v * s.z
    def w(s, v): return max(1, int(round(v * s.z)))
    def box(s, x0, y0, x1, y1):
        a, b = s.p(x0, y0), s.p(x1, y1); return [min(a[0], b[0]), min(a[1], b[1]), max(a[0], b[0]), max(a[1], b[1])]
    def mais_oy(s, oy): c = Cam((s.cx, s.cy), 1, s.oy + oy); c.z = s.z; return c
    def mundo(s, px, py): return ((px - W * SS / 2) / s.z + s.cx, (py - H * SS / 2) / s.z + s.cy - s.oy)

def camera(shot, cena):
    tres = len(cena["elenco"]) >= 3
    if shot == "geral": return Cam((770, 360), 0.98) if tres else Cam((640, 360), 1.0)
    if shot == "dois": return Cam((640, 345), 1.45)
    if shot == "geladeira": return Cam((205, 336), 1.6)
    who = shot.split("_", 1)[1]; return Cam((ELENCO[who]["x"], 330 + ELENCO[who]["dy"]), 2.1)

DESFOQUE = {"dois": 7, "close": 12}
APROXIMA = {"dois": 0.025, "close": 0.04}       # aproximação lenta da câmera durante o plano

# ======================= CENÁRIO =======================
def cenario(cam):
    im = Image.new("RGB", (W * SS, H * SS)); d = ImageDraw.Draw(im); P, B, w = cam.p, cam.box, cam.w
    d.rectangle(B(-3000, -3000, 5000, 520), fill=(244, 225, 196))
    d.rectangle(B(-3000, 300, 5000, 520), fill=(238, 216, 184))
    for x in range(-600, 2200, 60): d.line([P(x, 302), P(x, 510)], fill=(226, 204, 170), width=w(2))
    d.rectangle(B(-3000, 296, 5000, 304), fill=(214, 186, 150))
    d.rectangle(B(-3000, 520, 5000, 3000), fill=(176, 120, 86))
    for k, x in enumerate(range(-2000, 4000, 140)):
        d.polygon([P(x, 520), P(x + 140, 520), P((x + 140) * 1.25 - 160, 760), P(x * 1.25 - 160, 760)],
                  fill=(176, 120, 86) if k % 2 else (168, 114, 82))
        d.line([P(x, 520), P(x * 1.25 - 160, 760)], fill=(150, 98, 70), width=w(2))
    d.rectangle(B(-3000, 506, 5000, 522), fill=(250, 244, 232), outline=LINHA, width=w(1.5))
    d.rectangle(B(560, 90, 760, 250), fill=(160, 210, 238)); d.rectangle(B(560, 190, 760, 250), fill=(185, 222, 242))
    for bx, bh in ((575, 70), (612, 105), (660, 60), (700, 120), (735, 80)): d.rectangle(B(bx, 250 - bh, bx + 34, 250), fill=(150, 170, 195))
    d.rounded_rectangle(B(556, 86, 764, 254), radius=cam.r(8), outline=(255, 255, 255), width=w(10))
    d.rounded_rectangle(B(550, 80, 770, 260), radius=cam.r(10), outline=LINHA, width=w(2))
    d.line([P(660, 90), P(660, 250)], fill=(255, 255, 255), width=w(8))
    d.rectangle(B(545, 258, 775, 268), fill=(250, 244, 232), outline=LINHA, width=w(1.5))
    for s in (-1, 1):
        cx0 = 660 + s * 118
        d.polygon([P(cx0 - 22, 70), P(cx0 + 22, 70), P(cx0 + 30 * s + 16, 270), P(cx0 + 30 * s - 16, 270)], fill=(232, 120, 100), outline=LINHA)
    d.rectangle(B(520, 64, 800, 72), fill=(120, 82, 60))
    d.line([P(640, -200), P(640, 20)], fill=LINHA, width=w(2))
    d.polygon([P(615, 20), P(665, 20), P(690, 55), P(590, 55)], fill=(70, 120, 110), outline=LINHA)
    d.ellipse(B(628, 50, 652, 64), fill=(255, 240, 180))
    d.rectangle(B(345, 150, 525, 160), fill=(140, 96, 66), outline=LINHA, width=w(1.5))
    for bx, cor, bh in ((360, (200, 80, 70), 46), (376, (80, 110, 170), 52), (392, (230, 190, 80), 40)):
        d.rectangle(B(bx, 150 - bh, bx + 15, 150), fill=cor, outline=LINHA, width=w(1.2))
    d.polygon([P(470, 150), P(500, 150), P(505, 120), P(465, 120)], fill=(200, 110, 70), outline=LINHA)
    for ang in (-60, -30, 0, 30, 60):
        a = math.radians(ang - 90); d.ellipse(B(485 + 30 * math.cos(a) - 9, 118 + 30 * math.sin(a) - 9, 485 + 30 * math.cos(a) + 9, 118 + 30 * math.sin(a) + 9), fill=(90, 160, 90))
    d.ellipse(B(846, 96, 914, 164), fill=(255, 252, 245), outline=LINHA, width=w(3))
    for k in range(12):
        a = math.radians(k * 30); d.line([P(880 + 26 * math.sin(a), 130 - 26 * math.cos(a)), P(880 + 30 * math.sin(a), 130 - 30 * math.cos(a))], fill=LINHA, width=w(2))
    d.line([P(880, 130), P(880, 108)], fill=LINHA, width=w(3)); d.line([P(880, 130), P(896, 136)], fill=LINHA, width=w(3))
    d.rectangle(B(980, 110, 1600, 240), fill=(150, 105, 75), outline=LINHA, width=w(2))
    for x in range(980, 1600, 110):
        d.rectangle(B(x + 6, 116, x + 104, 234), outline=(120, 82, 58), width=w(2)); d.ellipse(B(x + 92, 168, x + 100, 176), fill=(220, 200, 150))
    d.rectangle(B(980, 400, 1600, 560), fill=(120, 82, 60), outline=LINHA, width=w(2))
    for x in range(990, 1600, 110):
        d.rectangle(B(x, 418, x + 100, 548), outline=(98, 66, 48), width=w(2)); d.rounded_rectangle(B(x + 35, 428, x + 65, 434), radius=cam.r(3), fill=(220, 200, 150))
    d.rectangle(B(970, 385, 1600, 405), fill=(226, 226, 220), outline=LINHA, width=w(2))
    d.rounded_rectangle(B(1240, 330, 1290, 390), radius=cam.r(8), fill=(220, 90, 70), outline=LINHA, width=w(2))
    d.ellipse(B(1280, 345, 1310, 375), outline=(220, 90, 70), width=w(7))
    d.chord(B(1320, 345, 1420, 395), 0, 180, fill=(240, 240, 235), outline=LINHA, width=w(2))
    for fx, fc in ((1345, (230, 70, 60)), (1370, (250, 200, 60)), (1395, (120, 180, 80))):
        d.ellipse(B(fx - 13, 350, fx + 13, 376), fill=fc, outline=LINHA, width=w(1.5))
    d.rounded_rectangle(B(95, 120, 285, 560), radius=cam.r(22), fill=(236, 240, 244), outline=LINHA, width=w(3))
    d.rounded_rectangle(B(102, 126, 116, 552), radius=cam.r(8), fill=(246, 249, 252))
    d.line([P(95, 280), P(285, 280)], fill=LINHA, width=w(3))
    for y0, y1 in ((180, 250), (310, 420)):
        d.rounded_rectangle(B(253, y0, 270, y1), radius=cam.r(6), fill=(170, 178, 190), outline=LINHA, width=w(1.5))
    return im

def luz(im, cam, desfoque):
    gw, gh = 192, 108; ys, xs = np.mgrid[0:gh, 0:gw].astype(np.float32)
    wx, wy = cam.mundo((xs + 0.5) / gw * W * SS, (ys + 0.5) / gh * H * SS)
    ganho = 1 + 0.10 * np.exp(-(((wx - 660) / 380) ** 2 + ((wy - 180) / 300) ** 2)) - 0.10 * np.clip((wy - 520) / 260, 0, 1)
    u, v = (xs + 0.5) / gw - 0.5, (ys + 0.5) / gh - 0.5; ganho *= 1 - 0.28 * np.clip((u * u + v * v) * 2.2 - 0.12, 0, 1)
    g = Image.fromarray(np.clip(ganho * 200, 0, 255).astype(np.uint8)).resize(im.size, Image.BILINEAR)
    if desfoque: im = im.filter(ImageFilter.GaussianBlur(desfoque * SS))
    arr = np.asarray(im).astype(np.uint16) * np.asarray(g).astype(np.uint16)[..., None] // 200
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))

ETIQUETAS = [(110, 335, "CLARA", (255, 250, 200)), (140, 400, "CLARA", (255, 250, 200)),
             (112, 468, "CLARA", (255, 250, 200)), (178, 528, "beto", (210, 235, 255))]
QX0, QY0, QX1, QY1 = 106, 130, 244, 270
def aderecos(d, cam, tt, E):
    te = E.primeiro("etiquetas")
    if te is not None:
        for k, (x, y, txt, cor) in enumerate(ETIQUETAS):
            u = (tt - te - k * 0.3) / 0.15
            if u < 0: continue
            sc = 1 + 0.3 * max(0, 1 - u) if u < 2 else 1; w2, h2 = (36 if txt != "beto" else 23) * sc, 13 * sc
            d.rounded_rectangle(cam.box(x + 34 - w2, y - h2, x + 34 + w2, y + h2), radius=cam.r(3), fill=cor, outline=LINHA, width=cam.w(1.5))
            d.text(cam.p(x + 34, y), txt, font=font(cam.r(14 if txt != "beto" else 10) * sc), fill=(80, 60, 60), anchor="mm")
    atual, ant = E.quadro(tt)
    if atual is not None:
        u = min(1, (tt - atual["t"]) / 0.2) if ant is None else 1
        y0 = QY0 + 30 * (1 - ease(u))
        d.rectangle(cam.box(QX0 + 3, y0 + 4, QX1 + 3, QY1 + 4 - (QY0 - y0)), fill=(200, 205, 212))
        d.rectangle(cam.box(QX0, y0, QX1, QY1 - (QY0 - y0)), fill=(252, 252, 250), outline=(150, 155, 165), width=cam.w(3))
        for mx in (QX0 + 16, QX1 - 16): d.ellipse(cam.box(mx - 7, y0 - 5, mx + 7, y0 + 9), fill=(230, 80, 80), outline=LINHA, width=cam.w(1))
        novas = linhas_quadro(atual["arg"]); velhas = linhas_quadro(ant["arg"]) if ant else []
        mudadas = [i for i, l in enumerate(novas) if i >= len(velhas) or velhas[i] != l]
        for i, txt in enumerate(novas):
            cor = (40, 80, 170) if i == 0 else (200, 50, 50)
            fs = 16 if i == 0 else 15
            if i in mudadas:
                k = mudadas.index(i); prog = (tt - atual["t"] - k * 0.55) / 0.45
                if prog <= 0: continue
                txt = txt[: max(1, int(len(txt) * min(1, prog)))]
            yy = y0 + 24 if i == 0 else y0 + 56 + (i - 1) * 28
            completo = novas[i]; fnt = font(cam.r(fs), "marcador"); larg = fnt.getlength(completo); maxw = cam.r(QX1 - QX0 - 14)
            if larg > maxw: fnt = font(cam.r(fs) * maxw / larg, "marcador")
            d.text(cam.p((QX0 + QX1) / 2, yy), txt, font=fnt, fill=cor, anchor="mm")
    tc = E.primeiro("cadeado")
    if tc is not None and tt >= tc:
        u = min(1, (tt - tc) / 0.22); cy = 300 - 40 * (1 - u) ** 2
        for x in range(92, 292, 12): d.ellipse(cam.box(x, cy - 6, x + 14, cy + 6), outline=(110, 110, 120), width=cam.w(3))
        d.arc(cam.box(246, cy - 2, 278, cy + 34), 180, 360, fill=(150, 150, 160), width=cam.w(6))
        d.rounded_rectangle(cam.box(240, cy + 14, 284, cy + 52), radius=cam.r(6), fill=(222, 178, 60), outline=LINHA, width=cam.w(2))
        d.ellipse(cam.box(258, cy + 26, 266, cy + 34), fill=(90, 70, 30))

# ======================= PERSONAGENS =======================
SOBR = {"neutro": (-18, -18), "inocente": (-30, -34), "nervoso": (-24, -33), "feliz": (-24, -27),
        "brava": (-27, -12), "surpresa": (-34, -37), "seca": (-15, -15)}
ABRE = {"seca": 5, "suspeita": 7, "brava": 9, "surpresa": 15}
POSES = {"repouso": ((66, 455), (64, 516)), "aponta": ((100, 445), (128, 400)),
         "ombros": ((96, 455), (126, 438)), "cintura": ((110, 448), (70, 486))}

def capsula(d, cam, pts, larg, cor):
    for k in range(len(pts) - 1): d.line([cam.p(*pts[k]), cam.p(*pts[k + 1])], fill=LINHA, width=cam.w(larg + 5))
    for p in pts: r = (larg + 5) / 2; d.ellipse(cam.box(p[0] - r, p[1] - r, p[0] + r, p[1] + r), fill=LINHA)
    for k in range(len(pts) - 1): d.line([cam.p(*pts[k]), cam.p(*pts[k + 1])], fill=cor, width=cam.w(larg))
    for p in pts: r = larg / 2; d.ellipse(cam.box(p[0] - r, p[1] - r, p[0] + r, p[1] + r), fill=cor)

def pose_de(ex, fala, tt):
    if not fala or ex == "seca" or fala["t1"] - fala["t0"] < 0.9: return None, 0, 0
    g = ease((tt - fala["t0"] + 0.15) / 0.3) * ease((fala["t1"] + 0.3 - tt) / 0.35)
    if ex == "brava": return "cintura", g, 0
    if ex in ("nervoso", "inocente"): return "ombros", g, 0
    return "aponta", g, 1

def personagem(d, cam0, who, ex, boca, pisca, tt, x, olha, andando=False, fala=None, bigode=None):
    c = ELENCO[who]; cam = cam0.mais_oy(c["dy"]); P, R, Bx, w = cam.p, cam.r, cam.box, cam.w
    forma, vol = boca
    bob = -abs(math.sin(tt * 11)) * 7 if andando else math.sin(tt * 2.2 + len(who)) * 2
    hy = 290 + bob + vol * 3
    enf = max(0.0, min(1.0, (vol - 0.72) / 0.28)) * 5          # sobrancelha sobe nas sílabas fortes
    d.ellipse(Bx(x - 70, 640, x + 70, 662), fill=(150, 98, 70))
    if who == "neide":
        d.polygon([P(x - 46, 520), P(x + 46, 520), P(x + 58, 642), P(x - 58, 642)], fill=c["calca"], outline=LINHA, width=w(3))
        for s in (-1, 1): d.rounded_rectangle(Bx(x + s * 26 - 14, 636, x + s * 26 + 14, 652), radius=R(6), fill=(70, 50, 60))
    else:
        for s in (-1, 1):
            d.rounded_rectangle(Bx(x + s * 20 - 19, 520, x + s * 20 + 19, 645), radius=R(10), fill=c["calca"], outline=LINHA, width=w(3))
            d.rounded_rectangle(Bx(x + s * 24 - 22, 636, x + s * 24 + 22, 656), radius=R(8), fill=(60, 50, 50), outline=LINHA, width=w(2))
    d.rounded_rectangle(Bx(x - 70, 370 + bob, x + 70, 545), radius=R(40), fill=c["roupa"], outline=LINHA, width=w(3))
    if who == "neide":
        for yb in (405, 445, 485): d.ellipse(Bx(x - 5, yb + bob, x + 5, yb + 10 + bob), fill=(235, 220, 240), outline=LINHA, width=w(1))
        d.line([P(x, 380 + bob), P(x, 540)], fill=(100, 62, 122), width=w(2))
    elif who == "beto":
        pts = [P(x + 17 * math.sin(math.radians(k * 36)) * (1 if k % 2 == 0 else 0.45),
                 455 + bob - 17 * math.cos(math.radians(k * 36)) * (1 if k % 2 == 0 else 0.45)) for k in range(10)]
        d.polygon(pts, fill=(255, 222, 150))
    else:
        d.polygon([P(x - 22, 372 + bob), P(x + 22, 372 + bob), P(x, 400 + bob)], fill=(50, 120, 96))
    nome_pose, g, unilateral = pose_de(ex, fala, tt)
    for s in (-1, 1):
        ombro = (x + s * 58, 395 + bob); (e0, h0) = POSES["repouso"]
        if nome_pose and (not unilateral or s == (olha or 1)):
            e1, h1 = POSES[nome_pose]
            e = (e0[0] + (e1[0] - e0[0]) * g, e0[1] + (e1[1] - e0[1]) * g); h = (h0[0] + (h1[0] - h0[0]) * g, h0[1] + (h1[1] - h0[1]) * g)
        else: e, h = e0, h0
        cot, mao = (x + s * e[0], e[1] + bob * 0.5), (x + s * h[0], h[1] + bob * 0.3)
        capsula(d, cam, [ombro, cot, mao], 28, c["roupa"])
        d.ellipse(Bx(mao[0] - 15, mao[1] - 15, mao[0] + 15, mao[1] + 15), fill=c["pele"], outline=LINHA, width=w(2.5))
    d.rectangle(Bx(x - 16, 350 + bob, x + 16, 382 + bob), fill=c["pele"], outline=LINHA, width=w(2.5))
    if who != "clara":
        for s in (-1, 1): d.ellipse(Bx(x + s * 66 - 12, hy - 8, x + s * 66 + 12, hy + 20), fill=c["pele"], outline=LINHA, width=w(2.5))
    if who == "clara":
        d.rounded_rectangle(Bx(x - 82, hy - 70, x + 82, hy + 72), radius=R(50), fill=c["cabelo"], outline=LINHA, width=w(3))
    d.ellipse(Bx(x - 68, hy - 72, x + 68, hy + 72), fill=c["pele"], outline=LINHA, width=w(3))
    if who == "clara":
        d.chord(Bx(x - 76, hy - 90, x + 76, hy + 16), 180, 360, fill=c["cabelo"], outline=LINHA, width=w(3))
    elif who == "beto":
        d.chord(Bx(x - 71, hy - 80, x + 71, hy + 44), 180, 360, fill=c["cabelo"], outline=LINHA, width=w(3))
        for s_ in (-1, 1): d.rectangle(Bx(x + s_ * 64 - 6, hy - 20, x + s_ * 64 + 6, hy + 8), fill=c["cabelo"])
    else:
        d.ellipse(Bx(x - 34, hy - 120, x + 34, hy - 58), fill=c["cabelo"], outline=LINHA, width=w(3))
        d.chord(Bx(x - 72, hy - 82, x + 72, hy + 30), 180, 360, fill=c["cabelo"], outline=LINHA, width=w(3))
        for s_ in (-1, 1): d.ellipse(Bx(x + s_ * 62 - 14, hy - 30, x + s_ * 62 + 14, hy + 10), fill=c["cabelo"], outline=LINHA, width=w(2))
    for s in (-1, 1):
        bc = tuple(min(255, max(0, int(v + d_))) for v, d_ in zip(c["pele"], (18, -12, -6)))
        d.ellipse(Bx(x + s * 40 - 13, hy + 14, x + s * 40 + 13, hy + 28), fill=bc)
    d.arc(Bx(x - 8 + olha * 3, hy + 4, x + 8 + olha * 3, hy + 22), 300 if olha >= 0 else 60, 120 if olha >= 0 else 240, fill=LINHA, width=w(2.5))
    ox = olha * 6
    for s in (-1, 1):
        ex0, ey = x + s * 26, hy - 5
        if pisca: d.arc(Bx(ex0 - 12, ey - 8, ex0 + 12, ey + 6), 20, 160, fill=LINHA, width=w(4))
        else:
            ab = ABRE.get(ex, 12); pr = 4 if ex == "surpresa" else 6.5
            d.ellipse(Bx(ex0 - 13, ey - ab, ex0 + 13, ey + 12), fill=(255, 255, 255), outline=LINHA, width=w(2))
            py = -4 if ex == "inocente" else (3 if ab < 10 else 1)
            d.ellipse(Bx(ex0 + ox - pr, ey + py - pr, ex0 + ox + pr, ey + py + pr), fill=(35, 28, 28))
            d.ellipse(Bx(ex0 + ox - pr * 0.2, ey + py - pr * 0.75, ex0 + ox + pr * 0.35, ey + py - pr * 0.2), fill=(255, 255, 255))
            if ab < 10:
                d.rectangle(Bx(ex0 - 15, ey - ab - 3, ex0 + 15, ey - ab + 5), fill=c["pele"])
                d.line([P(ex0 - 14, ey - ab + 5), P(ex0 + 14, ey - ab + 5)], fill=LINHA, width=w(3))
        out_, in_ = ((-17, -13) if s == -1 else (-27, -25)) if ex == "suspeita" else SOBR.get(ex, SOBR["neutro"])
        yl, yr = (ey + out_ - enf, ey + in_ - enf) if s == -1 else (ey + in_ - enf, ey + out_ - enf)
        cs = (150, 150, 155) if who == "neide" else tuple(max(0, v - 15) for v in c["cabelo"])
        d.line([P(ex0 - 14, yl), P(ex0 + 14, yr)], fill=cs, width=w(6.5))
    if who == "neide":
        for s in (-1, 1): d.ellipse(Bx(x + s * 26 - 19, hy - 22, x + s * 26 + 19, hy + 16), outline=(90, 60, 110), width=w(4))
        d.line([P(x - 8, hy - 6), P(x + 8, hy - 6)], fill=(90, 60, 110), width=w(4))
    if (who == "beto") if bigode is None else bigode:
        d.chord(Bx(x - 26, hy + 14, x + 26, hy + 36), 180, 360, fill=(252, 252, 247), outline=(215, 215, 205), width=w(1.5))
        for gx in (-14, 4, 18): d.ellipse(Bx(x + gx - 4, hy + 22, x + gx + 4, hy + 32), fill=(252, 252, 247))
    my = hy + 42; lb, ln = (110, 40, 40), (225, 110, 110)
    if forma == "fechada":
        if ex == "nervoso": d.line([P(x - 22 + i * 4, my + (3 if i % 2 else -3)) for i in range(12)], fill=LINHA, width=w(4))
        elif ex == "inocente": d.arc(Bx(x - 20, my - 14, x + 20, my + 8), 20, 160, fill=LINHA, width=w(4))
        elif ex == "feliz":
            d.chord(Bx(x - 23, my - 13, x + 23, my + 15), 0, 180, fill=lb, outline=LINHA, width=w(2.5))
            d.rectangle(Bx(x - 15, my + 1, x + 15, my + 5), fill=(255, 255, 255))
        elif ex == "brava": d.arc(Bx(x - 18, my, x + 18, my + 22), 200, 340, fill=LINHA, width=w(4))
        elif ex == "surpresa": d.ellipse(Bx(x - 7, my - 6, x + 7, my + 10), fill=lb, outline=LINHA, width=w(2))
        else: d.line([P(x - 16, my), P(x + 16, my)], fill=LINHA, width=w(4))
    else:
        tw, th = {"pequena": (14, 9), "aberta": (16, 18), "larga": (22, 10), "redonda": (10, 15)}[forma]
        d.ellipse(Bx(x - tw, my - th / 2, x + tw, my + th), fill=lb, outline=LINHA, width=w(2.5))
        if th > 9: d.ellipse(Bx(x - tw * 0.6, my + th * 0.35, x + tw * 0.6, my + th * 0.9), fill=ln)
        if forma in ("aberta", "larga"): d.rectangle(Bx(x - tw * 0.6, my - th / 2 + 1, x + tw * 0.6, my - th / 2 + 4), fill=(255, 255, 255))
    if ex == "nervoso":
        d.polygon([P(x + 74, hy - 40), P(x + 66, hy - 18), P(x + 82, hy - 18)], fill=(150, 210, 255), outline=LINHA)
        d.ellipse(Bx(x + 66, hy - 26, x + 82, hy - 10), fill=(150, 210, 255))

def piscando(who, f):
    per, off = {"clara": 96, "beto": 110, "neide": 88}.get(who, 100), len(who) * 13
    return (f + off) % per < 4

# ======================= LEGENDA =======================
_leg = {}
def legenda_img(fl):
    k = (fl["who"], fl["text"])
    if k in _leg: return _leg[k]
    fn, ft = font(34, "bold"), font(40, "medio"); tmp = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    nome = ELENCO[fl["who"]]["nome"] + "  "; wn = tmp.textlength(nome, font=fn); txt = fl["text"]; linhas = [txt]
    if wn + tmp.textlength(txt, font=ft) > W - 220:
        pal = txt.split(); best = None
        for i in range(1, len(pal)):
            a, b = " ".join(pal[:i]), " ".join(pal[i:]); m = max(wn + tmp.textlength(a, font=ft), tmp.textlength(b, font=ft))
            if best is None or m < best[0]: best = (m, a, b)
        linhas = [best[1], best[2]]
    larg = max([wn + tmp.textlength(linhas[0], font=ft)] + [tmp.textlength(l, font=ft) for l in linhas[1:]])
    lh = 56; im = Image.new("RGBA", (int(larg + 56), lh * len(linhas) + 30), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, im.width - 1, im.height - 1], radius=18, fill=(10, 10, 16, 185))
    d.text((28, 15 + 6), nome, font=fn, fill=ELENCO[fl["who"]]["cor_nome"])
    d.text((28 + wn, 15), linhas[0], font=ft, fill=(255, 255, 255))
    for i, l in enumerate(linhas[1:], 1): d.text((28, 15 + lh * i), l, font=ft, fill=(255, 255, 255))
    _leg[k] = im; return im

# ======================= CARTELAS =======================
def texto_img(txt, size, tipo="titulo", cor=(255, 255, 255), contorno=(70, 40, 30), sw=8, sombra=True):
    f = font(size, tipo); bb = f.getbbox(txt, stroke_width=sw); pad = 20
    im = Image.new("RGBA", (bb[2] - bb[0] + 2 * pad, bb[3] - bb[1] + 2 * pad), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    if sombra: d.text((-bb[0] + pad + 6, -bb[1] + pad + 8), txt, font=f, fill=(0, 0, 0, 90), stroke_width=sw, stroke_fill=(0, 0, 0, 90))
    d.text((-bb[0] + pad, -bb[1] + pad), txt, font=f, fill=cor, stroke_width=sw, stroke_fill=contorno)
    return im

def colar(im, peca, cx, cy, escala=1.0, alpha=1.0):
    if escala <= 0.02 or alpha <= 0.01: return
    p = peca if escala == 1 else peca.resize((max(1, int(peca.width * escala)), max(1, int(peca.height * escala))), Image.LANCZOS)
    if alpha < 1: p = p.copy(); p.putalpha(p.split()[3].point(lambda v: int(v * alpha)))
    im.paste(p, (int(cx - p.width / 2), int(cy - p.height / 2)), p)

class Cartelas:
    def __init__(s, meta):
        s.meta = meta; s.titulo = texto_img(meta.get("TITULO", "Minha Série"), 128)
        s.sub = texto_img(meta.get("EPISODIO", ""), 54, "bold", sw=5); s.txt = {}
    def abertura(s, lt, f):
        im = Image.new("RGB", (W * SS, H * SS), (246, 192, 74)); d = ImageDraw.Draw(im); cam = Cam((640, 360), 1.0)
        cx, cy = cam.p(640, 200)
        for k in range(18):
            a0 = math.radians(k * 20 + lt * 8); a1 = a0 + math.radians(10); Rr = W * SS * 1.2
            d.polygon([(cx, cy), (cx + Rr * math.cos(a0), cy + Rr * math.sin(a0)), (cx + Rr * math.cos(a1), cy + Rr * math.sin(a1))], fill=(240, 178, 58))
        for k, (who, x) in enumerate((("clara", 330), ("neide", 640), ("beto", 950))):
            u = ease((lt - 0.3 - k * 0.25) / 0.5)
            personagem(d, Cam((640, 360), 1.0, oy=(1 - u) * 420 + 120), who, "feliz", ("fechada", 0), piscando(who, f), lt, x, 0)
        im = im.reduce(SS); u = (lt - 1.2) / 0.5
        esc = 0 if u < 0 else (1.15 * ease(u) if u < 1 else 1.15 - 0.15 * ease((u - 1) * 2))
        colar(im, s.titulo, W / 2, 225, esc); colar(im, s.sub, W / 2, 370, 1.0, ease((lt - 2.4) / 0.5))
        return im
    def vinheta(s, lt, f, texto):
        z = 1.0 + 0.05 * lt / 2.4
        im = Image.new("RGB", (W * SS, H * SS), (150, 205, 235)); d = ImageDraw.Draw(im); cam = Cam((640, 420), z); B = cam.box
        for k in range(8): d.rectangle(B(-600, 40 + k * 60, 1900, 100 + k * 60), fill=(150 + k * 6, 205 + k * 3, 235))
        d.ellipse(B(1000, 60, 1110, 170), fill=(255, 220, 110))
        for nx in (200, 900):
            for dx, r in ((0, 40), (45, 50), (95, 38)):
                xx = nx + dx + lt * 12; d.ellipse(B(xx - r, 120 - r * 0.6, xx + r, 120 + r * 0.6), fill=(250, 252, 255))
        d.rectangle(B(-600, 640, 1900, 900), fill=(120, 180, 100))
        d.rectangle(B(470, 210, 810, 660), fill=(225, 150, 110), outline=LINHA, width=cam.w(3))
        d.rectangle(B(455, 195, 825, 220), fill=(170, 100, 80), outline=LINHA, width=cam.w(3))
        for r in range(5):
            for c in range(4):
                acesa = (r * 4 + c) % 3 == 0
                d.rectangle(B(495 + c * 80, 245 + r * 70, 545 + c * 80, 290 + r * 70), fill=(255, 235, 150) if acesa else (190, 220, 240), outline=LINHA, width=cam.w(2))
        d.rectangle(B(610, 590, 670, 660), fill=(120, 80, 60), outline=LINHA, width=cam.w(2))
        for tx in (300, 1000):
            d.rectangle(B(tx - 10, 560, tx + 10, 650), fill=(110, 75, 50), outline=LINHA, width=cam.w(2))
            d.ellipse(B(tx - 70, 450, tx + 70, 590), fill=(90, 160, 80), outline=LINHA, width=cam.w(2))
        im = im.reduce(SS)
        if texto not in s.txt: s.txt[texto] = texto_img(texto, 72, "titulo", contorno=(40, 40, 60), sw=6)
        colar(im, s.txt[texto], W / 2, 110, 1.0, ease(lt / 0.4)); return im
    def creditos(s, lt, f):
        m = s.meta
        linhas = [(m.get("TITULO", ""), "titulo", 84, (246, 192, 74)), (m.get("EPISODIO", ""), "bold", 46, (255, 255, 255)), None,
                  (f"Criação: {m.get('CRIACAO', '')}", "regular", 38, (205, 210, 230)),
                  ("Clara  ·  Beto  ·  Dona Neide", "regular", 38, (205, 210, 230)), None,
                  ("Animação montada por script, sem IA de vídeo", "regular", 34, (160, 165, 190)),
                  ("Vozes sintéticas (Kokoro)  ·  Plateia sintetizada", "regular", 34, (160, 165, 190))]
        im = Image.new("RGB", (W, H), (30, 32, 48)); d = ImageDraw.Draw(im); y = 210
        for k, it in enumerate(linhas):
            if it is None: y += 36; continue
            txt, tipo, sz, cor = it; a = ease((lt - 0.3 - k * 0.35) / 0.6); cor = tuple(int(30 + (v - 30) * a) for v in cor)
            d.text((W / 2, y + (1 - a) * 16), txt, font=font(sz, tipo), fill=cor, anchor="mm"); y += 110 if k == 0 else 72
        fim = ease((lt - 7.4) / 1.0)
        if fim > 0: im = Image.fromarray((np.asarray(im).astype(np.float32) * (1 - fim)).astype(np.uint8))
        return im

# ======================= RENDER =======================
G = {}
def preparar(pl):
    if pl["tipo"] != "cena": return None
    cam = camera(pl["shot"], pl["cena"]); pl["cam"] = cam; base = cenario(cam)
    pl["aderecos_fixos"] = pl["shot"] != "geladeira"
    if pl["aderecos_fixos"]: aderecos(ImageDraw.Draw(base), cam, pl["t0"] + 0.01, G["estado"])
    tipo = "dois" if pl["shot"] == "dois" else "close" if pl["shot"].startswith("close") else None
    pl["aprox"] = APROXIMA.get(tipo, 0)
    return luz(base, cam, DESFOQUE.get(tipo, 0))

def quadro(f, pl, base):
    tt = f / FPS
    if pl["tipo"] == "card":
        c, lt, C = pl["card"], tt - pl["t0"], G["cartelas"]
        if c["nome"] == "abertura": return C.abertura(lt, f)
        if c["nome"] == "vinheta": return C.vinheta(lt, f, c["texto"])
        return C.creditos(lt, f)
    E, cena, cam = G["estado"], pl["cena"], pl["cam"]
    im = base.copy(); d = ImageDraw.Draw(im)
    if not pl["aderecos_fixos"]: aderecos(d, cam, tt, E)
    pos = {who: E.posicao(cena, who, tt) for who in cena["elenco"]}
    presentes = {w_: p[0] for w_, p in pos.items() if p[0] is not None}
    for who in sorted(presentes, key=lambda w_: -abs(presentes[w_] - cam.cx)):
        x, anda = pos[who]
        personagem(d, cam, who, E.expressao(cena, who, tt), E.boca(cena, who, tt), piscando(who, f), tt, x,
                   E.olhar(cena, who, x, tt, presentes), anda, E.fala_de(cena, who, tt), who in cena.get("bigode", ["beto"]))
    if pl["aprox"]:
        z = 1 + pl["aprox"] * ease((tt - pl["t0"]) / max(0.5, pl["t1"] - pl["t0"]))
        cw, ch = W * SS / z, H * SS / z; x0, y0 = (W * SS - cw) / 2, (H * SS - ch) / 2
        im = im.resize((W, H), Image.BOX, box=(x0, y0, x0 + cw, y0 + ch))
    else: im = im.reduce(SS)
    fl = E.legenda(cena, tt)
    if fl: li = legenda_img(fl); im.paste(li, (int((W - li.width) / 2), H - 50 - li.height), li)
    return im

def render_plano(i):
    pl = G["planos"][i]; f0, f1 = round(pl["t0"] * FPS), round(pl["t1"] * FPS)
    fin = f"{DIR}/planos/p{i:03d}.mp4"; tmp = fin[:-4] + ".tmp.mp4"
    if f1 <= f0: return None
    base = preparar(pl)
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "17", "-preset", "veryfast",
                          "-tune", "animation", "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
    for f in range(f0, f1): p.stdin.write(quadro(f, pl, base).convert("RGB").tobytes())
    p.stdin.close()
    if p.wait() != 0: raise RuntimeError(f"ffmpeg falhou no plano {i}")
    os.replace(tmp, fin); return i

def main():
    args = sys.argv[1:]; roteiro = f"{DIR}/roteiro.txt"
    if "--roteiro" in args: k = args.index("--roteiro"); roteiro = args[k + 1]; del args[k:k + 2]
    meta, falas, planos, eventos, sons, cenas, risos, total = montar(roteiro)
    _QD[:] = [e for e in eventos if e["nome"] == "quadro"]
    print(f"duração {total:.1f}s · {len(falas)} falas · {len(risos)} risadas · {len(planos)} planos")
    erros = [(i, w_, r) for i, w_, r in RELATORIO if r["erro"] > 0.2]
    print(f"pronúncia: erro médio {np.mean([r['erro'] for _, _, r in RELATORIO]) * 100:.1f}% · falas com problema: {len(erros)}")
    for i, w_, r in erros: print(f"   [{i}] {w_}: '{r['texto']}' -> ouvido '{r['ouvido']}' ({r['erro'] * 100:.0f}%)")
    if args and args[0] == "vozes": return
    for fl in falas: analisar_boca(fl)
    G.update(planos=planos, estado=Estado(falas, eventos, cenas), cartelas=Cartelas(meta))
    if args and args[0] == "preview":
        for ts in args[1:]:
            tt = float(ts); i = next(k for k, p in enumerate(planos) if p["t0"] <= tt < p["t1"])
            quadro(int(tt * FPS), planos[i], preparar(planos[i])).save(f"{DIR}/prev_{ts}.png")
        return
    mixar_audio(falas, eventos, sons, cenas, risos, total, f"{DIR}/audio.wav")
    shutil.rmtree(f"{DIR}/planos", ignore_errors=True); os.makedirs(f"{DIR}/planos")
    ordem = sorted(range(len(planos)), key=lambda i: -(planos[i]["t1"] - planos[i]["t0"]))
    with Pool(os.cpu_count() or 2) as pool:
        for n, _ in enumerate(pool.imap_unordered(render_plano, ordem), 1):
            if n % 15 == 0: print(f"  {n}/{len(planos)} planos", flush=True)
    feitos = [f"{DIR}/planos/p{i:03d}.mp4" for i in range(len(planos)) if os.path.exists(f"{DIR}/planos/p{i:03d}.mp4")]
    with open(f"{DIR}/planos/lista.txt", "w") as fh: fh.writelines(f"file '{x}'\n" for x in feitos)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", f"{DIR}/planos/lista.txt",
                    "-c", "copy", f"{DIR}/video.mp4"], check=True)
    os.makedirs(f"{DIR}/saida", exist_ok=True)
    nome = "saida/" + re.sub(r"[^\w]+", "_", meta.get("TITULO", "episodio")).strip("_") + "_2D.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", f"{DIR}/video.mp4", "-i", f"{DIR}/audio.wav",
                    "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-af", "loudnorm=I=-16:TP=-1.5:LRA=11,alimiter=limit=0.84:level=false",
                    "-ar", "48000", "-c:a", "aac", "-b:a", "192k", "-shortest", f"{DIR}/{nome}"], check=True)
    print("pronto:", nome)

if __name__ == "__main__":
    main()
