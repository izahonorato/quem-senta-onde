#!/usr/bin/env python3
"""
Baixa os resultados OFICIAIS do TSE e gera os arquivos que o site lê (site/data/).

Fontes (todas do TSE):
  * 2026 (senado, Câmara, assembleias): arquivos públicos de divulgação
    https://resultados.tse.jus.br/oficial/ele2026/6259/dados/<uf>/<uf>-c<cargo>-e006259-u.json
  * Senadores eleitos em 2022 (mandato até 2031): Portal de Dados Abertos, consulta_cand_2022
  * Prefeitos e vereadores 2024: Portal de Dados Abertos, consulta_cand_2024

Uso:
  python scripts/atualizar_tse.py               # atualiza 2026 e gera 2022/2024 se ainda não existirem
  python scripts/atualizar_tse.py --forcar-base # refaz também 2022 e 2024
  python scripts/atualizar_tse.py --mock        # dados FICTÍCIOS só para testar o visual
"""
import argparse, csv, io, json, os, random, sys, time, unicodedata, urllib.request, urllib.error, zipfile
from datetime import datetime, timezone, timedelta

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(RAIZ, "site", "data")
CACHE = os.path.join(RAIZ, ".cache")
os.makedirs(os.path.join(DATA, "municipios"), exist_ok=True)
os.makedirs(CACHE, exist_ok=True)

ELEICAO = os.environ.get("TSE_ELEICAO", "6259")           # Eleições Gerais Estaduais 2026, 1º turno
BASE = os.environ.get("TSE_BASE", "https://resultados.tse.jus.br/oficial/ele2026")
CDN_CAND = "https://cdn.tse.jus.br/estatistica/sead/odsele/consulta_cand/consulta_cand_{ano}.zip"

UFS = ["ac","al","am","ap","ba","ce","df","es","go","ma","mg","ms","mt","pa","pb","pe","pi",
       "pr","rj","rn","ro","rr","rs","sc","se","sp","to"]
VAGAS_CAMARA = dict(ac=8,al=9,ap=8,am=8,ba=39,ce=22,df=8,es=10,go=17,ma=18,mt=8,ms=8,mg=53,pa=17,pb=12,
                    pr=30,pe=25,pi=10,rj=46,rn=8,rs=31,ro=8,rr=8,sc=16,sp=70,se=8,to=8)
CARGO_SENADOR, CARGO_FEDERAL, CARGO_ESTADUAL, CARGO_DISTRITAL = "0005", "0006", "0007", "0008"

# Número do partido -> sigla (usado só se o arquivo não trouxer a sigla)
NUM_PARTIDO = {"10":"REPUBLICANOS","11":"PP","12":"PDT","13":"PT","15":"MDB","16":"PSTU","18":"REDE",
  "20":"PODE","21":"PCB","22":"PL","23":"CIDADANIA","25":"PRD","27":"DC","28":"PRTB","29":"PCO",
  "30":"NOVO","33":"MOBILIZA","35":"DEMOCRATA","36":"AGIR","40":"PSB","43":"PV","44":"UNIÃO",
  "45":"PSDB","50":"PSOL","55":"PSD","65":"PCdoB","70":"AVANTE","77":"SOLIDARIEDADE","80":"UP"}
NORMALIZA = {"PC DO B":"PCdoB","PCDOB":"PCdoB","UNIAO":"UNIÃO","UNIÃO BRASIL":"UNIÃO","MISSAO":"MISSÃO",
  "PMB":"DEMOCRATA","PODEMOS":"PODE","SOLIDARIEDADE":"SOLIDARIEDADE","REPUBLICANOS":"REPUBLICANOS"}
CAPITAIS = {"AC":"RIO BRANCO","AL":"MACEIÓ","AP":"MACAPÁ","AM":"MANAUS","BA":"SALVADOR","CE":"FORTALEZA",
  "ES":"VITÓRIA","GO":"GOIÂNIA","MA":"SÃO LUÍS","MT":"CUIABÁ","MS":"CAMPO GRANDE","MG":"BELO HORIZONTE",
  "PA":"BELÉM","PB":"JOÃO PESSOA","PR":"CURITIBA","PE":"RECIFE","PI":"TERESINA","RJ":"RIO DE JANEIRO",
  "RN":"NATAL","RS":"PORTO ALEGRE","RO":"PORTO VELHO","RR":"BOA VISTA","SC":"FLORIANÓPOLIS",
  "SP":"SÃO PAULO","SE":"ARACAJU","TO":"PALMAS"}

# ---------------------------------------------------------------- utilidades
def log(*a): print(*a, flush=True)

def sem_acento(s):
    return "".join(c for c in unicodedata.normalize("NFD", s or "") if unicodedata.category(c) != "Mn").upper().strip()

MINUSC = {"de","da","do","das","dos","e","di","du"}
def titulo(s):
    s = (s or "").strip()
    if not s: return s
    out = []
    for i, w in enumerate(s.lower().split()):
        out.append(w if (i and w in MINUSC) else w[:1].upper() + w[1:])
    return " ".join(out)

def partido(sg=None, numero=None):
    if sg:
        sg = sg.strip()
        k = sem_acento(sg)
        if k in NORMALIZA: return NORMALIZA[k]
        if sg in ("PCdoB",): return sg
        return sg.upper()
    if numero:
        return NUM_PARTIDO.get(str(numero)[:2], f"Nº {str(numero)[:2]}")
    return "?"

def baixar(url, destino=None, tentativas=3):
    """Baixa uma URL. Com destino, grava em arquivo (para os zips grandes)."""
    req = urllib.request.Request(url, headers={"User-Agent": "quem-senta-onde/1.0 (+github pages)"})
    for t in range(tentativas):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                if destino:
                    with open(destino + ".part", "wb") as f:
                        while True:
                            b = r.read(1 << 20)
                            if not b: break
                            f.write(b)
                    os.replace(destino + ".part", destino)
                    return destino
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 404: return None          # não insistir em 404: o TSE bloqueia IPs que erram muito
            log(f"  HTTP {e.code} em {url} (tentativa {t+1})")
        except Exception as e:
            log(f"  erro em {url}: {e} (tentativa {t+1})")
        time.sleep(3 * (t + 1))
    return None

def salvar(nome, obj):
    caminho = os.path.join(DATA, nome)
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))

def ler(nome, padrao=None):
    try:
        with open(os.path.join(DATA, nome), encoding="utf-8") as f: return json.load(f)
    except Exception: return padrao

# ------------------------------------------------- resultados 2026 (EA20)
def candidatos_do_arquivo(js):
    """Percorre o JSON do TSE e devolve todos os candidatos, levando a sigla do partido do nível 'par'."""
    achados = []
    def walk(o, sg=None):
        if isinstance(o, dict):
            if "cand" in o and isinstance(o.get("cand"), list):
                sg_local = o.get("sg") or sg
                for c in o["cand"]:
                    if isinstance(c, dict): achados.append((c, sg_local))
                for k, v in o.items():
                    if k != "cand": walk(v, sg_local)
            else:
                for v in o.values(): walk(v, o.get("sg") or sg)
        elif isinstance(o, list):
            for v in o: walk(v, sg)
    walk(js)
    return achados

def eleitos(js):
    out = []
    for c, sg in candidatos_do_arquivo(js):
        st = str(c.get("st", "")).lower()
        if c.get("e") == "s" or st.startswith("eleito"):
            num = c.get("n")
            nome = c.get("nmu") or c.get("nm") or ""
            try: votos = int(str(c.get("vap", "0")).replace(".", ""))
            except ValueError: votos = 0
            out.append({"nome": titulo(nome), "p": partido(sg, num), "n": num, "votos": votos,
                        "st": c.get("st", "")})
    out.sort(key=lambda x: -x["votos"])
    return out

def arquivo_2026(uf, cargo):
    url = f"{BASE}/{ELEICAO}/dados/{uf}/{uf}-c{cargo}-e{int(ELEICAO):06d}-u.json"
    raw = baixar(url)
    time.sleep(0.15)                                   # bem abaixo do limite de 100 req/s do TSE
    if not raw: return None
    try: return json.loads(raw)
    except Exception: return None

def atualizar_2026():
    senado = ler("senado_2026.json", {}) or {}
    camara = ler("camara.json", {}) or {}
    assemb = ler("assembleias.json", {}) or {}
    status = ler("status.json", {}) or {}
    for uf in UFS:
        U = uf.upper()
        log(f"[2026] {U}")
        for chave, cargo, destino in (("senado", CARGO_SENADOR, senado),
                                      ("camara", CARGO_FEDERAL, camara),
                                      ("assembleia", CARGO_DISTRITAL if uf == "df" else CARGO_ESTADUAL, assemb)):
            js = arquivo_2026(uf, cargo)
            if js is None:
                log(f"   {chave}: arquivo ainda não disponível; mantém o último salvo")
                continue
            lista = eleitos(js)
            final = js.get("and") == "f" or any(isinstance(c, dict) and c.get("and") == "f" for c in js.get("carg", []) or [])
            if lista or final:
                destino[U] = lista
            status.setdefault(U, {})[chave] = {"final": bool(final), "eleitos": len(lista),
                                               "gerado": f"{js.get('dg','')} {js.get('hg','')}".strip()}
            log(f"   {chave}: {len(lista)} eleitos {'(totalização final)' if final else '(parcial)'}")
        if len(camara.get(U, [])) not in (0, VAGAS_CAMARA[uf]):
            log(f"   aviso: Câmara {U} com {len(camara[U])} de {VAGAS_CAMARA[uf]} eleitos (pode haver sub judice)")
    salvar("senado_2026.json", senado); salvar("camara.json", camara)
    salvar("assembleias.json", assemb); salvar("status.json", status)

# ------------------------------------------------ dados abertos (2022 / 2024)
def zip_candidatos(ano):
    destino = os.path.join(CACHE, f"consulta_cand_{ano}.zip")
    if not os.path.exists(destino):
        log(f"[{ano}] baixando candidatos do Portal de Dados Abertos do TSE (arquivo grande)…")
        if not baixar(CDN_CAND.format(ano=ano), destino):
            log(f"[{ano}] não foi possível baixar"); return None
    return zipfile.ZipFile(destino)

def linhas_csv(zf):
    nomes = [n for n in zf.namelist() if n.lower().endswith(".csv")]
    brasil = [n for n in nomes if "BRASIL" in n.upper()]
    for nome in (brasil or nomes):
        with zf.open(nome) as f:
            for row in csv.DictReader(io.TextIOWrapper(f, encoding="latin-1"), delimiter=";"):
                yield row

def eleito_csv(row):
    return sem_acento(row.get("DS_SIT_TOT_TURNO", "")).startswith("ELEITO")

def senado_2022():
    zf = zip_candidatos(2022)
    if not zf: return
    out, vistos = {}, set()
    for r in linhas_csv(zf):
        if r.get("CD_CARGO") != "5" or not eleito_csv(r): continue
        sq = r.get("SQ_CANDIDATO")
        if sq in vistos: continue
        vistos.add(sq)
        out.setdefault(r["SG_UF"], []).append({"nome": titulo(r.get("NM_URNA_CANDIDATO")),
                                               "p": partido(r.get("SG_PARTIDO"))})
    salvar("senado_2022.json", out)
    log(f"[2022] {sum(len(v) for v in out.values())} senadores com mandato até 2031")

def municipios_2024():
    zf = zip_candidatos(2024)
    if not zf: return
    cidades, vistos = {}, set()
    for r in linhas_csv(zf):
        cargo = r.get("CD_CARGO")
        if cargo not in ("11", "13") or not eleito_csv(r): continue
        sq = r.get("SQ_CANDIDATO")
        if sq in vistos: continue
        vistos.add(sq)
        uf, cod = r["SG_UF"], r["SG_UE"]
        c = cidades.setdefault(uf, {}).setdefault(cod, {"nome": titulo(r["NM_UE"]), "prefeito": None, "vereadores": []})
        pessoa = {"nome": titulo(r.get("NM_URNA_CANDIDATO")), "p": partido(r.get("SG_PARTIDO"))}
        if cargo == "11": c["prefeito"] = pessoa
        else: c["vereadores"].append(pessoa)
    resumo_pref, resumo_ver, capitais, indice = {}, {}, [], {}
    for uf, mapa in cidades.items():
        salvar(f"municipios/{uf}.json", mapa)
        indice[uf] = sorted([[cod, v["nome"]] for cod, v in mapa.items()], key=lambda x: sem_acento(x[1]))
        for cod, v in mapa.items():
            if v["prefeito"]: resumo_pref[v["prefeito"]["p"]] = resumo_pref.get(v["prefeito"]["p"], 0) + 1
            for x in v["vereadores"]: resumo_ver[x["p"]] = resumo_ver.get(x["p"], 0) + 1
            if sem_acento(v["nome"]) == sem_acento(CAPITAIS.get(uf, "-")) and v["prefeito"]:
                capitais.append({"cidade": v["nome"], "uf": uf, "cod": cod, **v["prefeito"]})
    capitais.sort(key=lambda x: x["uf"])
    salvar("municipios/indice.json", {"prefeitos": resumo_pref, "vereadores": resumo_ver,
                                      "capitais": capitais, "cidades": indice})
    log(f"[2024] {sum(len(v) for v in cidades.values())} municípios")

# ------------------------------------------------------------------ mock
def gerar_mock():
    """Dados FICTÍCIOS, apenas para ver o layout antes da primeira coleta."""
    random.seed(4)
    ps = ["PL","PT","UNIÃO","PSD","PP","REPUBLICANOS","MDB","PODE","PSB","PSOL","PCdoB","PSDB","NOVO","PV","PDT"]
    pesos = [24,14,9,8,8,8,7,5,3,3,2,2,2,1,1]
    pessoa = lambda i: {"nome": f"Candidato Fictício {i}", "p": random.choices(ps, pesos)[0], "votos": random.randint(20000, 300000)}
    vag_al = dict(ac=24,al=27,ap=24,am=24,ba=63,ce=46,df=24,es=30,go=41,ma=42,mt=24,ms=24,mg=77,pa=41,pb=36,pr=54,pe=49,pi=30,rj=70,rn=24,rs=55,ro=24,rr=24,sc=40,sp=94,se=24,to=24)
    k = iter(range(1, 99999))
    salvar("senado_2026.json", {u.upper(): [pessoa(next(k)) for _ in range(2)] for u in UFS})
    salvar("senado_2022.json", {u.upper(): [pessoa(next(k))] for u in UFS})
    salvar("camara.json", {u.upper(): [pessoa(next(k)) for _ in range(VAGAS_CAMARA[u])] for u in UFS})
    salvar("assembleias.json", {u.upper(): [pessoa(next(k)) for _ in range(vag_al[u])] for u in UFS})
    salvar("status.json", {u.upper(): {"senado":{"final":True},"camara":{"final":True},"assembleia":{"final":True}} for u in UFS})
    cid = {"0001": {"nome": "Cidade Fictícia", "prefeito": pessoa(1), "vereadores": [pessoa(i) for i in range(15)]}}
    salvar("municipios/SP.json", cid)
    salvar("municipios/indice.json", {"prefeitos": {"PSD": 891, "MDB": 860}, "vereadores": {"MDB": 8000},
        "capitais": [{"cidade": "Cidade Fictícia", "uf": "SP", "cod": "0001", **pessoa(2)}],
        "cidades": {"SP": [["0001", "Cidade Fictícia"]]}})

# ------------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--forcar-base", action="store_true", help="refaz senado 2022 e municípios 2024")
    ap.add_argument("--so-2026", action="store_true")
    ap.add_argument("--mock", action="store_true")
    a = ap.parse_args()
    if a.mock:
        gerar_mock(); meta(mock=True); return
    atualizar_2026()
    if not a.so_2026:
        if a.forcar_base or not os.path.exists(os.path.join(DATA, "senado_2022.json")): senado_2022()
        if a.forcar_base or not os.path.exists(os.path.join(DATA, "municipios", "indice.json")): municipios_2024()
    meta()

def meta(mock=False):
    agora = datetime.now(timezone(timedelta(hours=-3))).strftime("%d/%m/%Y %H:%M")
    salvar("meta.json", {"atualizado": agora, "eleicao": ELEICAO, "mock": mock})
    log(f"pronto: {agora}")

if __name__ == "__main__":
    main()
