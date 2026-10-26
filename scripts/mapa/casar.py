"""Liga cada município do IBGE (polígonos) ao código do TSE (dados do site), pelo nome dentro da UF."""
import json, sys, unicodedata, re, difflib, glob, os
ibge = json.load(open(sys.argv[1], encoding="utf-8"))
mundir = sys.argv[2]
def norm(s):
    s = unicodedata.normalize("NFD", s or "").encode("ascii", "ignore").decode().lower()
    s = re.sub(r"[’'`´\-]", " ", s); s = re.sub(r"\b(d|de|da|do|das|dos|e)\b", " ", s)
    return re.sub(r"\s+", "", s)
tse = {}
for f in glob.glob(os.path.join(mundir, "[A-Z][A-Z].json")):
    uf = os.path.basename(f)[:2]
    for cod, v in json.load(open(f, encoding="utf-8")).items():
        tse.setdefault(uf, {})[cod.zfill(5)] = v["nome"]
MANUAL = {("PB", "São Domingos de Pombal"): "19429", ("RN", "Arês"): "16233", ("TO", "Fortaleza do Tabocão"): "73199"}
liga, sem = {}, []
for uf in sorted(tse):
    t = {norm(n): c for c, n in tse[uf].items()}
    usados = set()
    pend = []
    for m in [m for m in ibge if m["ufSigla"] == uf]:
        k = norm(m["municipioNome"])
        man = MANUAL.get((uf, m["municipioNome"]))
        if man: liga[m["municipioCodigo"]] = man; usados.add(man); continue
        if k in t and t[k] not in usados: liga[m["municipioCodigo"]] = t[k]; usados.add(t[k])
        else: pend.append(m)
    for m in pend:
        livres = {k: c for k, c in t.items() if c not in usados}
        best = difflib.get_close_matches(norm(m["municipioNome"]), list(livres), n=1, cutoff=0.82)
        if best: liga[m["municipioCodigo"]] = livres[best[0]]; usados.add(livres[best[0]]); print(f"aproximado {uf}: {m['municipioNome']} -> {tse[uf][livres[best[0]]]}")
        else: sem.append(f"IBGE sem par {uf}: {m['municipioNome']}")
    for c, n in tse[uf].items():
        if c not in usados: sem.append(f"TSE sem polígono {uf}: {n} ({c})")
json.dump(liga, open(sys.argv[3], "w"))
print(len(liga), "ligados"); print("\n".join(sem))
