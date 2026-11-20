"""Kokoro (82M) em português do Brasil, rodando direto no onnxruntime.
Fonemas pelo espeak-ng (pt-br), no mesmo esquema do pipeline oficial (misaki/EspeakG2P).
"""
import os, re, subprocess
import numpy as np
import onnxruntime as ort

D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "kokoro-multi-lang-v1_0")
SR = 24000
E2M = sorted({"a^ɪ": "I", "a^ʊ": "W", "d^z": "ʣ", "d^ʒ": "ʤ", "e^ɪ": "A", "o^ʊ": "O", "ə^ʊ": "Q",
              "s^s": "S", "t^s": "ʦ", "t^ʃ": "ʧ", "ɔ^ɪ": "Y"}.items(), key=lambda kv: -len(kv[0]))

_sess = _voices = _vocab = _names = None
def _carregar():
    global _sess, _voices, _vocab, _names
    if _sess is None:
        so = ort.SessionOptions(); so.intra_op_num_threads = 2
        _sess = ort.InferenceSession(f"{D}/model.onnx", so, providers=["CPUExecutionProvider"])
        _voices = np.fromfile(f"{D}/voices.bin", dtype=np.float32).reshape(-1, 510, 1, 256)
        _vocab = {}
        for l in open(f"{D}/tokens.txt", encoding="utf-8"):
            l = l.rstrip("\n"); sym, _, idx = l.rpartition(" ")
            if sym == "" and idx: sym = " "
            _vocab[sym] = int(idx)
        meta = _sess.get_modelmeta().custom_metadata_map
        _names = meta["speaker_names"].split(",")

def nomes():
    _carregar(); return list(_names)

def fonemas(texto):
    texto = re.sub(r"\s+", " ", texto.strip())
    partes = re.findall(r"[^.,!?;:…—]+|[.,!?;:…—]+", texto)
    out = []
    for p in partes:
        if re.fullmatch(r"[.,!?;:…—]+", p):
            out.append(p.replace("...", "…").replace("…", "…")[:2]); out.append(" "); continue
        p = p.strip()
        if not p: continue
        r = subprocess.run(["espeak-ng", "-q", "--ipa", "--tie=^", "-v", "pt-br", p], capture_output=True, text=True)
        ps = " ".join(r.stdout.split())
        ps = re.sub(r"\([a-z\-]+\)", "", ps)
        for a, b in E2M: ps = ps.replace(a, b)
        ps = ps.replace("^", "")
        if out and out[-1] != " ": out.append(" ")
        out.append(ps)
    s = "".join(out).strip()
    s = re.sub(r" ([.,!?;:…—])", r"\1", s)
    return s

def estilo(voz):
    """voz: nome ('pf_dora'), id, ou mistura {'pf_dora': .7, 'ef_dora': .3}"""
    _carregar()
    if isinstance(voz, dict):
        return sum(_voices[_names.index(k) if isinstance(k, str) else k] * w for k, w in voz.items()) / sum(voz.values())
    return _voices[_names.index(voz) if isinstance(voz, str) else voz]

def falar_ipa(ps, voz="pf_dora", velocidade=1.0):
    _carregar()
    ids = [_vocab[c] for c in ps if c in _vocab][:508]
    st = estilo(voz)[len(ids)]
    audio = _sess.run(None, {"tokens": np.array([[0, *ids, 0]], dtype=np.int64), "style": st.astype(np.float32),
                              "speed": np.array([velocidade], dtype=np.float32)})[0]
    return np.asarray(audio, dtype=np.float32).reshape(-1)

def falar(texto, voz="pf_dora", velocidade=1.0):
    _carregar()
    ps = fonemas(texto)
    ids = [_vocab[c] for c in ps if c in _vocab][:508]
    st = estilo(voz)[len(ids)]                       # (1, 256)
    audio = _sess.run(None, {"tokens": np.array([[0, *ids, 0]], dtype=np.int64),
                              "style": st.astype(np.float32),
                              "speed": np.array([velocidade], dtype=np.float32)})[0]
    return np.asarray(audio, dtype=np.float32).reshape(-1), ps

if __name__ == "__main__":
    import sys, wave
    txt = sys.argv[1] if len(sys.argv) > 1 else "Eu não comi. Eu manifestei."
    a, ps = falar(txt, sys.argv[2] if len(sys.argv) > 2 else "pf_dora")
    print(ps, len(a) / SR)
    with wave.open("kokoro_teste.wav", "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(a, -1, 1) * 32000).astype(np.int16).tobytes())
