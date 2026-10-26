"""Acrescenta municípios que faltam no pacote ibge-cidades-com-poligonos, a partir do kml-brasil (MIT).
Uso: python completar.py municipios-poligonos.json liga.json <pasta kml-brasil/lib/2010/municipios> saida.json"""
import json, sys, os
FALTANDO = [("RN", "ASSU", "Assú", "16039"), ("RN", "BOA_SAUDE", "Boa Saúde", "17035"), ("RN", "CAMPO_GRANDE", "Campo Grande", "16250")]
mun = json.load(open(sys.argv[1], encoding="utf-8")); liga = json.load(open(sys.argv[2])); base = sys.argv[3]
for uf, arq, nome, cod in FALTANDO:
    g = json.load(open(os.path.join(base, uf, "geojson", arq + ".geojson"), encoding="utf-8"))
    rings = []
    for f in g["features"]:
        geo = f["geometry"]; cs = geo["coordinates"]
        if geo["type"] == "LineString": rings.append(cs)
        elif geo["type"] == "Polygon": rings.append(cs[0])
        elif geo["type"] == "MultiLineString": rings += cs
    chave = "kml-" + cod
    mun.append({"ufSigla": uf, "municipioNome": nome, "municipioCodigo": chave, "poligono": {"type": "MultiPolygon", "coordinates": [[r] for r in rings]}})
    liga[chave] = cod
json.dump(mun, open(sys.argv[4], "w")); json.dump(liga, open(sys.argv[2], "w"))
print("acrescentados:", [n for _, _, n, _ in FALTANDO])
