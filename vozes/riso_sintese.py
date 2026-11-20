"""Síntese de risada por fonte-filtro (sem amostras gravadas).
Pulso glotal de Rosenberg + sopro sincronizado + trato vocal em cascata (tipo Klatt),
em sílabas 'ha/he/ho' a ~5-6 por segundo, com tom caindo ao longo da risada."""
import numpy as np
from scipy.signal import lfilter, butter, sosfilt, fftconvolve

SR = 44100
VOGAIS = {"a": (850, 1350, 2600, 3500), "ɛ": (620, 1800, 2650, 3500), "ə": (560, 1450, 2500, 3500),
          "o": (560, 1000, 2550, 3400), "æ": (780, 1650, 2650, 3500)}
BWS = (90, 110, 170, 250)

def cascata(x, F, bws=BWS):
    for f, bw in zip(F, bws):
        r = np.exp(-np.pi * bw / SR); c = 2 * r * np.cos(2 * np.pi * f / SR)
        x = lfilter([1 - c + r * r], [1, -c, r * r], x)
    return x

def fonte_glotal(f0, rng, tp=0.42, tn=0.16):
    fase_acum = np.cumsum(f0 / SR); fase = fase_acum % 1.0
    g = np.where(fase < tp, 0.5 * (1 - np.cos(np.pi * fase / tp)),
                 np.where(fase < tp + tn, np.cos(np.pi * (fase - tp) / (2 * tn)), 0.0))
    per = np.floor(fase_acum); amp = 1 + 0.06 * rng.standard_normal(int(per[-1]) + 2)   # shimmer
    g = g * amp[per.astype(int)]
    return g, np.diff(g, prepend=0) * SR / 2000.0      # fluxo e derivada (radiação)

def silaba(f0_ini, f0_fim, dur_voz, dur_h, sopro, F, rng):
    nh, nv = int(dur_h * SR), int(dur_voz * SR)
    t = np.arange(nv) / SR
    f0 = f0_ini * (f0_fim / f0_ini) ** (t / max(t[-1], 1e-3))
    f0 = f0 * (1 + 0.015 * np.sin(2 * np.pi * rng.uniform(5, 8) * t) + 0.01 * rng.standard_normal(nv).cumsum() / np.sqrt(np.arange(1, nv + 1)))
    fluxo, exc = fonte_glotal(f0, rng)
    env = np.minimum(1, t / 0.012) * np.exp(-t / (dur_voz * 0.6))
    nz = rng.standard_normal(nv); nz = sosfilt(butter(1, 1500, btype="high", fs=SR, output="sos"), nz)
    voz = exc / (np.abs(exc).max() + 1e-9) * env + nz * (0.15 + fluxo) * sopro * 0.35 * env
    h = rng.standard_normal(nh) * np.linspace(0.15, 0.6, nh) * 0.5 if nh else np.zeros(0)
    sinal = np.concatenate([h, voz])
    return cascata(sinal, [f * rng.uniform(0.95, 1.05) for f in F])

def pessoa(rng, feminino=None, n_sil=None):
    fem = rng.random() < 0.5 if feminino is None else feminino
    base = rng.uniform(250, 400) if fem else rng.uniform(150, 240)
    n_sil = n_sil or int(rng.integers(4, 10))
    vogal = rng.choice(list(VOGAIS), p=[0.45, 0.2, 0.15, 0.1, 0.1]); F = VOGAIS[vogal]
    if fem: F = tuple(f * 1.12 for f in F)
    intervalo = rng.uniform(0.15, 0.2); sopro = rng.uniform(0.2, 0.6)
    out = []
    for k in range(n_sil):
        q = k / max(1, n_sil - 1)
        f_ini = base * (1.2 - 0.3 * q) * rng.uniform(0.94, 1.06); f_fim = f_ini * rng.uniform(0.75, 0.9)
        dv = intervalo * rng.uniform(0.5, 0.68); dh = intervalo * rng.uniform(0.12, 0.22)
        s = silaba(f_ini, f_fim, dv, dh, sopro, F, rng) * (1 - 0.5 * q) * rng.uniform(0.85, 1.1)
        gap = np.zeros(max(0, int((intervalo * rng.uniform(0.95, 1.1 + 0.3 * q)) * SR) - len(s)))
        out += [s, gap]
    if rng.random() < 0.5:   # inspiração no fim
        n = int(rng.uniform(0.2, 0.4) * SR); env = np.sin(np.linspace(0, np.pi, n)) ** 2
        out.append(cascata(rng.standard_normal(n) * env * 0.15, (700, 1500, 2700, 3600), (300, 300, 400, 500)))
    y = np.concatenate(out); y = sosfilt(butter(2, 90, btype="high", fs=SR, output="sos"), y)
    return y / (np.abs(y).max() + 1e-9)

def _hall(n_s=1.4, seed=4):
    rng = np.random.default_rng(seed); t = np.arange(int(n_s * SR)) / SR
    ir = rng.standard_normal((len(t), 2)) * np.exp(-t / 0.28)[:, None]
    sos = butter(2, 5000, fs=SR, output="sos"); ir = np.stack([sosfilt(sos, ir[:, c]) for c in range(2)], 1)
    return ir / np.sqrt((ir ** 2).sum(0)) * 0.5

def plateia(intensidade="risada", seed=0, molhado=0.35):
    n, dur = {"risadinha": (14, 1.7), "risada": (24, 2.3), "forte": (42, 3.1)}[intensidade]
    rng = np.random.default_rng(seed); out = np.zeros((int((dur + 2.0) * SR), 2))
    for p in range(n):
        y = pessoa(rng)
        if dur > 2 and rng.random() < 0.35: y = np.concatenate([y, np.zeros(int(0.08 * SR)), pessoa(rng) * 0.6])
        atraso = rng.gamma(2.0, 0.08) + (rng.uniform(0.2, dur * 0.4) if rng.random() < 0.2 else 0)
        g = rng.uniform(0.35, 1.0) * (0.55 if atraso > 0.5 else 1); pan = rng.uniform(-0.85, 0.85); ang = (pan + 1) * np.pi / 4
        i = int(atraso * SR); j = min(len(out), i + len(y))
        out[i:j, 0] += y[: j - i] * g * np.cos(ang); out[i:j, 1] += y[: j - i] * g * np.sin(ang)
    ir = _hall(); wet = np.stack([fftconvolve(out[:, c], ir[:, c])[: len(out)] for c in range(2)], 1)
    out = out + wet * molhado
    t = np.arange(len(out)) / SR; env = np.minimum(1, t / 0.05) * np.clip(1 - (t - dur * 0.6) / (dur * 0.7), 0, 1) ** 1.2
    out *= env[:, None]; fim = np.nonzero(env > 0.001)[0][-1] + int(0.3 * SR)
    out = out[:fim]
    return (out / (np.abs(out).max() + 1e-9) * 0.9).astype(np.float32)

if __name__ == "__main__":
    import wave
    def salvar(p, a):
        a = a if a.ndim == 2 else np.stack([a, a], 1)
        with wave.open(p, "wb") as w:
            w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((a * 30000).astype(np.int16).tobytes())
    rng = np.random.default_rng(7)
    salvar("ps_homem.wav", pessoa(rng, False, 8) * 0.9); salvar("ps_mulher.wav", pessoa(rng, True, 8) * 0.9)
    for k in ("risadinha", "risada", "forte"): salvar(f"ps_{k}.wav", plateia(k, 3))
