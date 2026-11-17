#!/usr/bin/env python3
"""
PyroprintDamir - generator cjenika (NN 132/2026, Pravilnik o načinu objave cjenika proizvoda).

Radi na Linuxu (GitHub Actions) i Windowsu. Samo standardna biblioteka Pythona (3.9+). Bez vanjskih servisa.
Nema lokalnih putanja: sve se zadaje argumentima.

  python3 generiraj_cjenike.py generiraj --repo <kopija main grane> [--izvor <mapa s cjenik.csv>]
  python3 generiraj_cjenike.py provjeri  --repo <kopija main grane> [--izvor <mapa s cjenik.csv>]

  generiraj: provjeri izvor (cjenik.csv), a tek zatim zapisuje cjenik.html (tablica + poveznice), CSV cjenike u cjenici/,
             arhivu cjenici/arhiva/ + arhiva.json (evidencija zamjena) i _redirects (stabilne adrese).
             Ako išta u izvoru ne valja, NIŠTA se ne zapisuje (izlaz 1).
  provjeri:  provjerava izvor i već generirane izlazne datoteke (format, redoslijed stupaca, arhiva, stabilne adrese).

Ništa ne radi git commit / push. Vrijeme je uvijek Europe/Zagreb. Opcija --sada je samo za testove.
"""
import argparse, csv, html, json, re, subprocess, sys, unicodedata
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parent
TZ = ZoneInfo("Europe/Zagreb")
REFERENTNI_DATUM = datetime(2026, 9, 10)
ARHIVA_ZADRZAVANJE_DANA = 30   # odluka vlasnika; pravilnik (čl. 3. st. 6.) traži najmanje 15 dana od zamjene
ARHIVA_MINIMUM_DANA = 15
STABILNE = {"roba": "roba.csv", "usluga": "usluge.csv"}

# Redoslijed stupaca točno prema čl. 3. st. 2. i 3. (čl. 3. st. 4. traži taj redoslijed)
ZAGLAVLJE = {
    "roba": ["naziv robe", "šifra robe", "marka robe", "neto količina", "jedinica mjere robe",
             "maloprodajna cijena robe", "posebni oblik prodaje", "cijena za jedinicu mjere robe",
             "barkod robe", "EAN barkod robe", "bazna cijena robe"],
    "usluga": ["naziv usluge", "maloprodajna cijena usluge", "posebni oblik prodaje", "bazna cijena usluge"],
}
# iz kojih stupaca izvora se puni svaki stupac CSV-a
IZVOR_STUPCI = {
    "roba": ["naziv", "sifra", "marka", "neto_kolicina", "jedinica_mjere", "maloprodajna_cijena",
             "posebni_oblik_prodaje", "cijena_za_jedinicu_mjere", "barkod", "ean_barkod", "bazna_cijena"],
    "usluga": ["naziv", "maloprodajna_cijena", "posebni_oblik_prodaje", "bazna_cijena"],
}
# JAVNI izvor smije imati točno ove stupce (nikakvih internih napomena)
DOZVOLJENI_STUPCI = ["vrsta", "naziv", "naziv_web", "sifra", "marka", "neto_kolicina", "jedinica_mjere", "prefiks",
                     "maloprodajna_cijena", "posebni_oblik_prodaje", "cijena_za_jedinicu_mjere", "barkod",
                     "ean_barkod", "bazna_cijena", "datum_bazne_cijene"]
CIJENA_RE = re.compile(r"^\d+,\d{2}$")
DATUM_RE = re.compile(r"^(\d{2})\.(\d{2})\.(\d{4})\.$")
IME_RE = re.compile(r"^(?P<mb>[A-Za-z0-9\-]+)_(?P<mjesto>ZA_SVA_PRODAJNA_MJESTA|[A-Za-z0-9\-]+_[A-Za-z0-9\-]+_[A-Za-z0-9\-]+)"
                    r"_(?P<vrsta>ROBA|USLUGA)_(?P<broj>\d+)_(?P<ts>\d{8}_\d{4})\.csv$")


def sada_zagreb(arg=None):
    if arg:
        return datetime.fromisoformat(arg).replace(tzinfo=TZ)
    return datetime.now(TZ)


def ucitaj_postavke(izvor):
    return json.loads((izvor / "postavke.json").read_text(encoding="utf-8"))


def zaglavlje_izvora(izvor):
    with open(izvor / "cjenik.csv", encoding="utf-8-sig", newline="") as f:
        return next(csv.reader(f, delimiter=";"), [])


def ucitaj_podatke(izvor):
    with open(izvor / "cjenik.csv", encoding="utf-8-sig", newline="") as f:
        return [r for r in csv.DictReader(f, delimiter=";") if (r.get("vrsta") or "").strip()]


def datum(s):
    m = DATUM_RE.match(s or "")
    return datetime(int(m[3]), int(m[2]), int(m[1])) if m else None


def prikaz_datuma(s):
    d = datum(s)
    return f"{d.day}. {d.month}. {d.year}." if d else ""


def prikazni_naziv(r):
    return r.get("naziv_web") or r["naziv"]


def nerijeseno(postavke, redovi):
    """Popis podataka koji nedostaju - sa svakim se mora riješiti prije objave."""
    n = []
    if not postavke.get("maticni_broj", "").strip():
        n.append("postavke.json: maticni_broj (matični broj obrta - čl. 6. st. 3. cjenika)")
    if not postavke.get("za_sva_prodajna_mjesta", False):
        for k in ("vrsta_prodajnog_mjesta", "adresa", "oznaka_prodajnog_mjesta"):
            if not postavke.get(k, "").strip():
                n.append(f"postavke.json: {k}")
    for r in redovi:
        if r["vrsta"] == "ponuda":
            continue
        if not CIJENA_RE.match(r.get("bazna_cijena", "").strip()):
            n.append(f"{r['naziv']}: nema bazne cijene")
        if not datum(r.get("datum_bazne_cijene", "").strip()):
            n.append(f"{r['naziv']}: nema datuma bazne cijene (npr. 17.11.2026.)")
    return n


# ---------------------------------------------------------------- git / objavljeno stanje
def git(repo, *args):
    r = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, encoding="utf-8")
    return r.returncode, r.stdout


def objavljeno_stanje(repo):
    """Što je TRENUTNO objavljeno na main (HEAD): bazne cijene (CSV) i datumi (cjenik.html). Prazno ako ništa."""
    cijene, datumi, imena = {}, {}, set()
    rc, popis = git(repo, "ls-tree", "-r", "--name-only", "HEAD", "cjenici/")
    if rc != 0:
        return cijene, datumi, imena
    for f in popis.split():
        if f.endswith(".csv") and "/arhiva/" not in f:
            _, tekst = git(repo, "show", f"HEAD:{f}")
            redovi = list(csv.reader(tekst.splitlines(), delimiter=";"))
            vrsta = "roba" if "_ROBA_" in f else "usluga"
            for r in redovi[1:]:
                if r:
                    imena.add(r[0])
                    cijene[r[0]] = r[len(ZAGLAVLJE[vrsta]) - 1]
    rc, stranica = git(repo, "show", "HEAD:cjenik.html")
    if rc == 0:
        for m in re.finditer(r'<th scope="row"[^>]*>(.*?)</th>.*?\(cijena na dan(?: uvođenja u ponudu:)? (\d{1,2}\. \d{1,2}\. \d{4}\.)\)',
                             stranica, re.S):
            datumi[html.unescape(m[1])] = m[2]
    return cijene, datumi, imena


def provjeri_izvor(repo, izvor, postavke, redovi, sada):
    """Sve što mora vrijediti PRIJE bilo kakve objave. Vraća popis grešaka."""
    g = []
    zagl = zaglavlje_izvora(izvor)
    if zagl != DOZVOLJENI_STUPCI:
        extra = [z for z in zagl if z not in DOZVOLJENI_STUPCI]
        manjka = [z for z in DOZVOLJENI_STUPCI if z not in zagl]
        g.append(f"cjenik.csv: stupci nisu točno javni skup (višak: {extra or '-'}, manjak: {manjka or '-'}, redoslijed mora biti isti)")
    for i, r in enumerate(redovi, start=2):
        for k, v in r.items():
            v = v or ""
            if len(v) > 140 or "@" in v or re.search(r"intern|račun|racun", v, re.I):
                g.append(f"cjenik.csv redak {i}: polje '{k}' izgleda kao interni/privatni podatak (nije dopušteno u javnom izvoru)")
    g += [f"nerješeno: {n}" for n in nerijeseno(postavke, redovi)]
    danas = sada.date()
    pub_cijene, pub_datumi, pub_imena = objavljeno_stanje(repo)
    for r in redovi:
        if r["vrsta"] == "ponuda":
            continue
        naziv, b, ds = r["naziv"], r.get("bazna_cijena", "").strip(), r.get("datum_bazne_cijene", "").strip()
        d = datum(ds)
        if not d:
            continue
        if d.date() > danas:
            g.append(f"{naziv}: datum bazne cijene {ds} je u budućnosti (danas je {danas:%d.%m.%Y.})")
        if d < REFERENTNI_DATUM:
            g.append(f"{naziv}: datum bazne cijene {ds} je prije referentnog datuma 10.09.2026.")
        if naziv in pub_imena:
            if pub_cijene.get(naziv) != b:
                g.append(f"{naziv}: bazna cijena ({b}) razlikuje se od objavljene ({pub_cijene.get(naziv)}). Bazna se cijena ne mijenja naknadno")
            pd = pub_datumi.get(prikazni_naziv(r))
            if pd and pd != prikaz_datuma(ds):
                g.append(f"{naziv}: datum bazne cijene ({prikaz_datuma(ds)}) razlikuje se od objavljenog ({pd})")
        elif d > REFERENTNI_DATUM:
            if d.date() != danas:
                g.append(f"{naziv}: još nije objavljen, a datum prvog nuđenja je {ds}, danas je {danas:%d.%m.%Y.}. Uskladi datum sa stvarnim datumom objave")
            if r.get("maloprodajna_cijena", "").strip() != b:
                g.append(f"{naziv}: pri prvom nuđenju bazna cijena ({b}) mora biti jednaka cijeni na taj dan ({r.get('maloprodajna_cijena')})")
    return g


# ---------------------------------------------------------------- HTML tablica
def html_tablice(redovi, prefiks_baze=True):
    def red(r):
        cijena = f"{r['prefiks'].strip()} {r['maloprodajna_cijena']} €".strip()
        naziv = html.escape(r.get("naziv_web") or r["naziv"])
        b, d = r.get("bazna_cijena", "").strip(), r.get("datum_bazne_cijene", "").strip()
        if CIJENA_RE.match(b) and datum(d):
            kasnije = datum(d) > REFERENTNI_DATUM
            opis = f"cijena na dan uvođenja u ponudu: {prikaz_datuma(d)}" if kasnije else f"cijena na dan {prikaz_datuma(d)}"
            baza = f'<span class="v">{r["prefiks"].strip()} {b} € <span class="baza-datum">({opis})</span></span>'
        else:
            baza = '<span class="v"><span class="todo">[NERIJEŠENO: bazna cijena i datum]</span></span>'
        return (f'<tr><th scope="row" data-label="Proizvod ili usluga">{naziv}</th>'
                f'<td data-label="Cijena"><span class="v">{html.escape(cijena)}</span></td>'
                f'<td data-label="Bazna cijena">{baza}</td></tr>')

    def tablica(naslov, vrste):
        rr = [r for r in redovi if r["vrsta"] in vrste]
        if not rr:
            return ""
        telo = "\n".join("            " + red(r) for r in rr)
        return (f'      <h2 class="text-dark" style="margin-top:28px">{naslov}</h2>\n'
                f'      <div class="table-scroll"><table class="price-table">\n'
                f'        <thead><tr><th scope="col">Proizvod ili usluga</th><th scope="col">Cijena</th>'
                f'<th scope="col">Bazna cijena</th></tr></thead>\n        <tbody>\n{telo}\n        </tbody>\n      </table></div>\n')

    out = tablica("Proizvodi", {"roba"}) + tablica("Usluge", {"usluga"})
    for r in redovi:
        if r["vrsta"] == "ponuda":
            out += (f'      <p class="price-individual"><strong>{html.escape(r["naziv"])}</strong>: '
                    f'{html.escape(r["maloprodajna_cijena"] or "prema individualnoj ponudi")}.</p>\n')
    return out


def zamijeni_blok(tekst, oznaka, sadrzaj):
    a, b = f"<!-- {oznaka}:START -->", f"<!-- {oznaka}:END -->"
    i, j = tekst.find(a), tekst.find(b)
    if i < 0 or j < 0:
        raise ValueError(f"cjenik.html: nedostaju oznake {a} / {b}")
    return tekst[:i + len(a)] + "\n" + sadrzaj + "      " + tekst[j:]



# ---------------------------------------------------------------- CSV
def bez_dijakritika(s):
    s = unicodedata.normalize("NFKD", s)
    return re.sub(r"[^A-Za-z0-9]+", "-", "".join(c for c in s if not unicodedata.combining(c))).strip("-")


def naziv_datoteke(postavke, vrsta, broj, sada):
    mb = postavke.get("maticni_broj", "").strip() or "MATICNI-BROJ-NERIJESEN"
    if postavke.get("za_sva_prodajna_mjesta", False):
        mjesto = ["ZA_SVA_PRODAJNA_MJESTA"]
    else:
        mjesto = [bez_dijakritika(postavke.get(k, "")) or k.upper() + "-NERIJESENO"
                  for k in ("vrsta_prodajnog_mjesta", "adresa", "oznaka_prodajnog_mjesta")]
    oznaka = "ROBA" if vrsta == "roba" else "USLUGA"
    return "_".join([mb, *mjesto, oznaka, str(broj), sada.strftime("%Y%m%d_%H%M")]) + ".csv"


def csv_tekst(redovi, vrsta):
    from io import StringIO
    buf = StringIO()
    w = csv.writer(buf, delimiter=";", lineterminator="\r\n", quoting=csv.QUOTE_MINIMAL)
    w.writerow(ZAGLAVLJE[vrsta])
    for r in redovi:
        if r["vrsta"] == vrsta:
            w.writerow([(r.get(k) or "").strip() for k in IZVOR_STUPCI[vrsta]])
    return buf.getvalue()


def zapisi_csv(tekst, putanja):
    with open(putanja, "w", encoding="utf-8", newline="") as f:  # UTF-8 bez BOM-a, čl. 6. st. 6.
        f.write(tekst)




# ---------------------------------------------------------------- arhiva, brojevi, stabilne adrese
def ucitaj_manifest(arhiva):
    p = arhiva / "arhiva.json"
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return {"zadrzavanje_dana": ARHIVA_ZADRZAVANJE_DANA, "datoteke": {}}


def zapisi_manifest(arhiva, m):
    m["zadrzavanje_dana"] = ARHIVA_ZADRZAVANJE_DANA
    m["datoteke"] = dict(sorted(m["datoteke"].items()))
    (arhiva / "arhiva.json").write_bytes((json.dumps(m, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))


def sljedeci_broj(cilj, arhiva, manifest, token):
    imena = [p.name for p in cilj.glob("*.csv")] + [p.name for p in arhiva.glob("*.csv")] + list(manifest["datoteke"])
    brojevi = [int(m["broj"]) for n in imena if (m := IME_RE.match(n)) and m["vrsta"] == token]
    return (max(brojevi) if brojevi else 0) + 1


def generiraj_izlaz(repo, postavke, redovi, sada):
    cilj, arhiva = repo / "cjenici", repo / "cjenici" / "arhiva"
    cilj.mkdir(exist_ok=True)
    arhiva.mkdir(exist_ok=True)
    manifest = ucitaj_manifest(arhiva)
    novi = {}
    for vrsta in ("roba", "usluga"):
        if not any(r["vrsta"] == vrsta for r in redovi):
            continue
        token = "ROBA" if vrsta == "roba" else "USLUGA"
        tekst = csv_tekst(redovi, vrsta)
        trenutne = [p for p in cilj.glob("*.csv") if f"_{token}_" in p.name]
        if len(trenutne) == 1 and trenutne[0].read_bytes() == tekst.encode("utf-8"):
            print(f"[{vrsta}] bez promjene ({trenutne[0].name})")
            novi[vrsta] = trenutne[0].name
            continue
        broj = sljedeci_broj(cilj, arhiva, manifest, token)
        ime = naziv_datoteke(postavke, vrsta, broj, sada)
        zapisi_csv(tekst, cilj / ime)
        for p in trenutne:  # zamijenjena verzija ide u arhivu; datum zamjene se BILJEŽI u arhiva.json (ne oslanjamo se na git)
            p.replace(arhiva / p.name)
            manifest["datoteke"][p.name] = {"zamijenjeno": sada.isoformat(timespec="minutes"), "zamijenjena_s": ime}
            print(f"[{vrsta}] u arhivu: {p.name}")
        novi[vrsta] = ime
        print(f"[{vrsta}] objavljeno: cjenici/{ime}")
    for ime, e in manifest["datoteke"].items():  # čišćenje: samo datoteke starije od 30 dana OD ZAMJENE
        if "obrisano" in e:
            continue
        if sada - datetime.fromisoformat(e["zamijenjeno"]) >= timedelta(days=ARHIVA_ZADRZAVANJE_DANA):
            p = arhiva / ime
            if p.exists():
                p.unlink()
            e["obrisano"] = sada.isoformat(timespec="minutes")
            print(f"[arhiva] isteklo {ARHIVA_ZADRZAVANJE_DANA} dana od zamjene, uklonjeno: {ime}")
    zapisi_manifest(arhiva, manifest)
    return novi, manifest


def sadrzaj_redirects(novi):
    redovi = ["# Generirano skriptom generiraj_cjenike.py - ne uređivati ručno.",
              "# Stabilne adrese aktualnih cjenika (rewrite, bez preusmjeravanja)."]
    for vrsta, ime in novi.items():
        redovi.append(f"/cjenici/{STABILNE[vrsta]}  /cjenici/{ime}  200")
    return ("\n".join(redovi) + "\n").encode("utf-8")


def html_veze(novi, manifest):
    ul = "      <ul class=\"csv-links\">\n"
    for vrsta, ime in novi.items():
        ul += (f'      <li><strong>{"Roba" if vrsta == "roba" else "Usluge"}</strong>: '
               f'<a href="cjenici/{STABILNE[vrsta]}">cjenici/{STABILNE[vrsta]}</a> '
               f'(stalna adresa, uvijek aktualni cjenik)<br>'
               f'<span class="baza-datum">datoteka: <a href="cjenici/{ime}">{ime}</a></span></li>\n')
    ul += "      </ul>\n"
    arh = sorted((n for n, e in manifest["datoteke"].items() if "obrisano" not in e), reverse=True)
    if arh:
        ul += (f"      <p class=\"text-gray\" style=\"margin-top:14px\">Arhiva zamijenjenih cjenika "
               f"(čuvamo {ARHIVA_ZADRZAVANJE_DANA} dana od zamjene):</p>\n      <ul class=\"csv-links\">\n")
        ul += "".join(f'      <li><a href="cjenici/arhiva/{n}">{n}</a></li>\n' for n in arh)
        ul += "      </ul>\n"
    return ul


def ocekivani_izlaz(repo):
    """Trenutno stanje izlaza iz datotečnog sustava: ime aktualne ROBA/USLUGA datoteke."""
    novi = {}
    for vrsta, token in (("roba", "ROBA"), ("usluga", "USLUGA")):
        p = [x.name for x in (repo / "cjenici").glob("*.csv") if f"_{token}_" in x.name]
        if len(p) == 1:
            novi[vrsta] = p[0]
    return novi


# ---------------------------------------------------------------- provjera izlaza
def provjeri_izlaz(repo, postavke, redovi, sada):
    g, upoz = [], []
    cilj, arhiva = repo / "cjenici", repo / "cjenici" / "arhiva"
    vrste = [v for v in ("roba", "usluga") if any(r["vrsta"] == v for r in redovi)]
    novi = ocekivani_izlaz(repo)
    for v in vrste:
        if v not in novi:
            g.append(f"cjenici/: mora postojati točno jedna aktualna {v} datoteka")
    csvovi = sorted(cilj.glob("*.csv")) + sorted(arhiva.glob("*.csv"))
    for p in csvovi:
        m = IME_RE.match(p.name)
        if not m:
            g.append(f"{p.name}: naziv ne odgovara predlošku (čl. 6. st. 3./4.)")
            continue
        if m["mb"] != postavke["maticni_broj"].strip():
            g.append(f"{p.name}: matični broj u nazivu nije {postavke['maticni_broj']}")
        vrsta = "roba" if m["vrsta"] == "ROBA" else "usluga"
        sirovo = p.read_bytes()
        if sirovo.startswith(b"\xef\xbb\xbf"):
            g.append(f"{p.name}: ima UTF-8 BOM")
        try:
            tekst = sirovo.decode("utf-8")
        except UnicodeDecodeError:
            g.append(f"{p.name}: nije valjani UTF-8")
            continue
        rr = list(csv.reader(tekst.splitlines(), delimiter=";"))
        if rr[0] != ZAGLAVLJE[vrsta]:
            g.append(f"{p.name}: zaglavlje/redoslijed stupaca nije prema čl. 3. st. 2./3.")
        for i, r in enumerate(rr[1:], start=2):
            if len(r) != len(ZAGLAVLJE[vrsta]):
                g.append(f"{p.name} redak {i}: {len(r)} stupaca umjesto {len(ZAGLAVLJE[vrsta])}")
                continue
            d = dict(zip(IZVOR_STUPCI[vrsta], r))
            for k in ("naziv", "maloprodajna_cijena", "posebni_oblik_prodaje", "bazna_cijena"):
                if not d[k].strip():
                    g.append(f"{p.name} redak {i}: prazno obvezno polje '{k}'")
            for k in ("maloprodajna_cijena", "bazna_cijena", "cijena_za_jedinicu_mjere"):
                if d.get(k) and not CIJENA_RE.match(d[k]):
                    g.append(f"{p.name} redak {i}: '{k}' nije u obliku 45,00")
            if d["posebni_oblik_prodaje"] not in ("DA", "NE"):
                g.append(f"{p.name} redak {i}: posebni oblik prodaje mora biti DA/NE")
    for vrsta, ime in novi.items():  # aktualni CSV mora biti točno ono što izvor daje
        if (cilj / ime).read_bytes() != csv_tekst(redovi, vrsta).encode("utf-8"):
            g.append(f"cjenici/{ime}: sadržaj ne odgovara izvoru (cjenik.csv)")
        else:
            print(f"ok  {ime}  ({sum(1 for r in redovi if r['vrsta'] == vrsta)} stavki)")
    # arhiva i evidencija zamjena (arhiva.json), neovisno o git povijesti
    man = ucitaj_manifest(arhiva)
    for p in sorted(arhiva.glob("*.csv")):
        e = man["datoteke"].get(p.name)
        if not e:
            g.append(f"arhiva/{p.name}: nema zapisa o datumu zamjene u arhiva.json")
        elif "obrisano" in e:
            g.append(f"arhiva/{p.name}: u arhiva.json označena obrisanom, a datoteka postoji")
    for ime, e in man["datoteke"].items():
        z = datetime.fromisoformat(e["zamijenjeno"])
        starost = sada - z
        if "obrisano" in e:
            if starost < timedelta(days=ARHIVA_MINIMUM_DANA):
                g.append(f"arhiva/{ime}: uklonjena prije isteka {ARHIVA_MINIMUM_DANA} dana od zamjene (čl. 3. st. 6.)")
            elif starost < timedelta(days=ARHIVA_ZADRZAVANJE_DANA):
                g.append(f"arhiva/{ime}: uklonjena prije isteka {ARHIVA_ZADRZAVANJE_DANA} dana od zamjene")
        else:
            if not (arhiva / ime).exists():
                g.append(f"arhiva/{ime}: nedostaje, a rok čuvanja nije istekao")
            elif starost >= timedelta(days=ARHIVA_ZADRZAVANJE_DANA):
                g.append(f"arhiva/{ime}: starija od {ARHIVA_ZADRZAVANJE_DANA} dana, treba je ukloniti (pokreni generiraj)")
        zs = e.get("zamijenjena_s")
        if zs and not ((cilj / zs).exists() or (arhiva / zs).exists() or zs in man["datoteke"]):
            g.append(f"arhiva/{ime}: zamjenska verzija {zs} ne postoji")
    # stabilne adrese
    rd = repo / "_redirects"
    if not rd.exists():
        g.append("_redirects ne postoji")
    elif rd.read_bytes() != sadrzaj_redirects(novi):
        g.append("_redirects ne odgovara aktualnim CSV datotekama")
    else:
        for stabilna, ime in ((STABILNE[v], novi[v]) for v in novi):
            print(f"ok  /cjenici/{stabilna} -> /cjenici/{ime}")
    # stranica
    stranica = repo / "cjenik.html"
    if not stranica.exists():
        g.append("cjenik.html ne postoji")
    else:
        s = stranica.read_text(encoding="utf-8")
        if 'class="todo"' in s:
            g.append("cjenik.html: ima neriješenih oznaka (class=\"todo\")")
        if "noindex" in s:
            g.append("cjenik.html: ima noindex")
        try:
            if zamijeni_blok(s, "TABLICA", html_tablice(redovi)) != s:
                g.append("cjenik.html: tablica ne odgovara izvoru")
            if zamijeni_blok(s, "CSVLINKS", html_veze(novi, man)) != s:
                g.append("cjenik.html: poveznice (stabilne adrese/arhiva) ne odgovaraju datotekama")
        except ValueError as e:
            g.append(str(e))
        if '<div class="featured-grid">' in s and "€" in s.split('<div class="featured-grid">')[1].split("</section>")[0]:
            g.append("cjenik.html: cijene unutar galerije")
    return g, upoz


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("naredba", choices=["generiraj", "provjeri"])
    ap.add_argument("--repo", required=True, help="radna kopija main grane (sadrži cjenik.html)")
    ap.add_argument("--izvor", default=str(HERE), help="mapa s cjenik.csv i postavke.json (zadano: mapa skripte)")
    ap.add_argument("--sada", help="SAMO ZA TESTOVE: lažno vrijeme (ISO, Europe/Zagreb)")
    a = ap.parse_args()
    repo, izvor = Path(a.repo).resolve(), Path(a.izvor).resolve()
    sada = sada_zagreb(a.sada)
    postavke = ucitaj_postavke(izvor)
    redovi = ucitaj_podatke(izvor)
    if not (repo / "cjenik.html").exists():
        sys.exit("GREŠKA: --repo ne sadrži cjenik.html")

    greske = provjeri_izvor(repo, izvor, postavke, redovi, sada)
    if greske:
        print("STOP - izvor nije valjan, ništa nije zapisano:")
        for x in greske:
            print("  -", x)
        sys.exit(1)
    print("ok  izvor (cjenik.csv): podaci, datumi i bazne cijene")

    if a.naredba == "generiraj":
        novi, manifest = generiraj_izlaz(repo, postavke, redovi, sada)
        (repo / "_redirects").write_bytes(sadrzaj_redirects(novi))
        stranica = repo / "cjenik.html"
        s = stranica.read_text(encoding="utf-8")
        s = zamijeni_blok(s, "TABLICA", html_tablice(redovi))
        s = zamijeni_blok(s, "CSVLINKS", html_veze(novi, manifest))
        stranica.write_bytes(s.encode("utf-8"))
        print("ok  generirano: cjenici/, arhiva, _redirects, cjenik.html")

    greske, upoz = provjeri_izlaz(repo, postavke, redovi, sada)
    for u in upoz:
        print("UPOZORENJE:", u)
    if greske:
        print("PROVJERA NEUSPJELA:")
        for x in greske:
            print("  -", x)
        sys.exit(1)
    print("REZULTAT: uspjeh")


if __name__ == "__main__":
    main()
