"""Gera o mapa do site a partir dos polígonos municipais do IBGE (pacote npm ibge-cidades-com-poligonos):
   - estados: contorno de cada UF, juntando os municípios (bordas compartilhadas simplificadas juntas);
   - municípios por UF, com a chave = código do TSE.
   Projeção: Mercator ajustada ao mapa anterior do site (mesmas coordenadas, viewBox 0 0 613 639)."""
import json, math, sys, os
import shapely
from shapely.geometry import shape, Polygon, MultiPolygon
from shapely.ops import unary_union
ibge = json.load(open(sys.argv[1], encoding="utf-8")); liga = json.load(open(sys.argv[2])); fit = json.load(open(sys.argv[3])); out = sys.argv[4]
(ax, bx), (ay, by) = fit["cx"], fit["cy"]
merc = lambda lat: math.degrees(math.log(math.tan(math.pi/4 + math.radians(lat)/2)))
def proj(poly):
    parts = []
    for p in poly["coordinates"]:
        ext = p[0]
        if max(lon for lon, _ in ext) > -34.7: continue          # ilhas oceânicas (Noronha, Trindade)
        rings = [[(ax*lon+bx, ay*merc(lat)+by) for lon, lat in r] for r in p]
        g = Polygon(rings[0], rings[1:])
        if not g.is_valid: g = shapely.make_valid(g)
        parts.append(g)
    if not parts: return None
    g = unary_union(parts)
    return g if g.area > 0 else None
def path(g, nd, min_part=0.0, min_hole=0.0):
    polys = [g] if isinstance(g, Polygon) else [x for x in getattr(g, "geoms", []) if isinstance(x, Polygon)]
    out = []
    for p in polys:
        if p.area < min_part: continue                       # restos minúsculos da união dos municípios
        holes = [r for r in p.interiors if Polygon(r).area >= min_hole]
        for ring in [p.exterior, *holes]:
            pts = list(ring.coords)[:-1]
            if len(pts) < 3: continue
            f = lambda v: f"{round(v, nd):.{nd}f}".rstrip("0").rstrip(".") if nd else str(round(v))
            x0, y0 = pts[0]; s = f"M{f(x0)} {f(y0)}"; px, py = round(x0, nd), round(y0, nd)
            for x, y in pts[1:]:
                rx, ry = round(x, nd), round(y, nd)
                dx, dy = round(rx-px, nd), round(ry-py, nd)
                if dx == 0 and dy == 0: continue
                s += f"l{f(dx)} {f(dy)}"; px, py = rx, ry
            out.append(s + "z")
    return "".join(out)
por_uf = {}
for m in ibge:
    g = proj(m["poligono"])
    if g is None: continue
    por_uf.setdefault(m["ufSigla"], []).append((liga.get(m["municipioCodigo"]), m["municipioNome"], g))
os.makedirs(os.path.join(out, "mun"), exist_ok=True)
estados = {}
for uf, lst in sorted(por_uf.items()):
    geoms = [g for _, _, g in lst]
    simp = shapely.coverage_simplify(geoms, tolerance=0.06)
    d = {}
    for (cod, nome, _), g in zip(lst, simp):
        if cod and not g.is_empty: d[cod] = path(g, 2, 0.0005, 0.02)
    json.dump(d, open(os.path.join(out, "mun", uf + ".json"), "w"), separators=(",", ":"))
    r = 0.2
    estados[uf] = unary_union([shapely.make_valid(g) for g in geoms]).buffer(r, join_style="mitre").buffer(-r, join_style="mitre")   # fecha frestas entre municípios
ufs = sorted(estados); simp = shapely.coverage_simplify([estados[u] for u in ufs], tolerance=0.35)
est = {u: path(g, 1, 0.15, 1.0 if u == "GO" else 1e9) for u, g in zip(ufs, simp)}   # só GO tem buraco de verdade (o DF); os demais seriam frestas entre municípios
json.dump(est, open(os.path.join(out, "estados.json"), "w"), separators=(",", ":"))
tot = sum(os.path.getsize(os.path.join(out, "mun", f)) for f in os.listdir(os.path.join(out, "mun")))
print("estados.json", os.path.getsize(os.path.join(out, "estados.json")), "bytes; municípios", tot, "bytes")
