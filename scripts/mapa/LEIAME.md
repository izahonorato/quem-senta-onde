# Mapa de estados e cidades

Os contornos ficam em `site/data/mapa/` e só precisam ser refeitos se os municípios mudarem.

- `estados.json`: contorno de cada UF (união dos municípios), usado no mapa nacional.
- `mun/<UF>.json`: contorno de cada município, com a chave igual ao código do TSE.

Como refazer:

```bash
npm pack ibge-cidades-com-poligonos && tar xzf ibge-cidades-com-poligonos-*.tgz   # polígonos do IBGE (via kml-brasil)
pip install "shapely>=2.1" numpy
python scripts/mapa/casar.py package/municipios-poligonos.json site/data/municipios liga.json   # IBGE -> código do TSE, pelo nome
git clone --depth 1 https://github.com/eduardo-veras/kml-brasil.git                          # 3 cidades do RN que faltam no pacote (MIT)
python scripts/mapa/completar.py package/municipios-poligonos.json liga.json kml-brasil/lib/2010/municipios mun_completo.json
python scripts/mapa/gerar_mapa.py mun_completo.json liga.json scripts/mapa/projecao.json site/data/mapa
```

`projecao.json` é a projeção de Mercator ajustada às coordenadas do mapa do site (viewBox 0 0 613 639).
Municípios sem par (o script lista) ficam sem contorno próprio. Em out/2026: Iporá (GO, falta nos dados do TSE do site)
e Boa Esperança do Norte (MT, criado depois das malhas usadas).
