import numpy as np, json, sys
import riso_sintese as R
import classificar as C

def configurar(p):
    R.BWS = tuple(b * p["bw"] for b in (90, 110, 170, 250))
    R.P = p

# versão parametrizada de pessoa()
def pessoa(rng, feminino=None, n_sil=None):
    p = R.P
    fem = rng.random() < 0.5 if feminino is None else feminino
    base = rng.uniform(*p["f0_f"]) if fem else rng.uniform(*p["f0_m"])
    n_sil = n_sil or int(rng.integers(4, 10))
    out = []
    for k in range(n_sil):
        q = k / max(1, n_sil - 1)
        vogal = rng.choice(list(R.VOGAIS), p=[0.45, 0.2, 0.15, 0.1, 0.1]) if rng.random() < p["troca_vogal"] or k == 0 else vogal
        F = R.VOGAIS[vogal]; F = tuple(f * (1.12 if fem else 1) for f in F)
        intervalo = rng.uniform(*p["intervalo"]) * (1 + p["desacel"] * q)
        f_ini = base * (1.2 - 0.3 * q) * rng.uniform(1 - p["salto"], 1 + p["salto"]); f_fim = f_ini * rng.uniform(0.72, 0.9)
        dv = intervalo * rng.uniform(0.5, 0.7); dh = intervalo * rng.uniform(0.1, 0.22)
        s = R.silaba(f_ini, f_fim, dv, dh, rng.uniform(*p["sopro"]), F, rng) * (1 - 0.5 * q) * rng.uniform(0.7, 1.15)
        gap = np.zeros(max(0, int(intervalo * SR) - len(s)))
        out += [s, gap]
    y = np.concatenate(out)
    from scipy.signal import sosfilt, butter
    y = sosfilt(butter(2, 90, btype="high", fs=SR, output="sos"), y)
    return y / (np.abs(y).max() + 1e-9)
SR = R.SR

def avaliar(p, seeds=(1, 2)):
    configurar(p); R.pessoa = pessoa
    notas = []
    for s in seeds:
        a = R.plateia("risada", s, molhado=p["molhado"]); riso, fala, mus, mult, top = C.notas(a, R.SR)
        eco = dict(top).get("Echo", 0)
        notas.append(riso)
    return float(np.mean(notas))

if __name__ == "__main__":
    rng = np.random.default_rng(int(sys.argv[1]) if len(sys.argv) > 1 else 0)
    melhor = None
    for it in range(int(sys.argv[2]) if len(sys.argv) > 2 else 30):
        p = dict(bw=float(rng.uniform(1.0, 2.5)), f0_f=(float(rng.uniform(220, 300)), float(rng.uniform(340, 480))),
                 f0_m=(float(rng.uniform(130, 170)), float(rng.uniform(200, 300))), troca_vogal=float(rng.uniform(0, 0.5)),
                 intervalo=(float(rng.uniform(0.11, 0.16)), float(rng.uniform(0.17, 0.26))), desacel=float(rng.uniform(0, 0.6)),
                 salto=float(rng.uniform(0.04, 0.25)), sopro=(float(rng.uniform(0.1, 0.4)), float(rng.uniform(0.5, 1.2))),
                 molhado=float(rng.uniform(0.05, 0.35)))
        nota = avaliar(p)
        if melhor is None or nota > melhor[0]: melhor = (nota, p); print(f"{it:3d} nova melhor {nota:.3f}", flush=True)
    json.dump(melhor[1], open("melhor_riso.json", "w")); print("final", melhor[0], melhor[1])
