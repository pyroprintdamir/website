#!/usr/bin/env python3
"""
PyroprintDamir - sigurna objava cjenika na main (Netlify objavljuje svaki push na main).

Radi na Linuxu (GitHub Actions) i Windowsu, bez lokalnih putanja. Samo standardna biblioteka.

  python3 objava.py provjera --repo <kopija main grane>
        Generira i provjerava SVE u radnoj kopiji, ali NIŠTA ne commita (siguran probni prolaz).
  python3 objava.py objavi --repo <kopija main grane> --potvrdi
        Isto, a tek ako SVE prođe: jedan commit samo s generiranim datotekama i push na main.
        Bez --potvrdi ponaša se kao 'provjera'.
        --prva-objava (samo lokalno, prva objava): u commit ulaze SVE trenutne promjene u repozitoriju.
  python3 objava.py live --repo <kopija main grane> [--cekaj 600] [--site https://pyroprintdamir.hr]
        Nakon deploya: čeka Netlify pa provjerava /cjenik, /cjenici/roba.csv i /cjenici/usluge.csv
        (HTTP status, MIME, bez preusmjeravanja, sadržaj identičan) te arhivu.

Svaka provjera koja ne prođe prekida postupak (izlaz 1) i NIŠTA se ne objavljuje.
"""
import argparse, atexit, os, re, shutil, subprocess, sys, tempfile, time, urllib.error, urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
GEN = [sys.executable, str(HERE / "generiraj_cjenike.py")]
GENERIRANO = ("cjenici", "cjenik.html", "_redirects")
BOT = ["-c", "user.name=github-actions[bot]", "-c", "user.email=41898282+github-actions[bot]@users.noreply.github.com"]


def stani(poruka):
    print("\nSTOP - NIŠTA NIJE OBJAVLJENO ILI NIJE POTVRĐENO:\n  " + poruka.replace("\n", "\n  "), flush=True)
    sys.exit(1)


def ok(poruka):
    print("ok  " + poruka, flush=True)


def git(repo, *args, check=True, ci=False):
    cmd = ["git", *(BOT if ci else []), "-C", str(repo), *args]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if check and r.returncode != 0:
        stani(f"git {' '.join(args)} nije uspio:\n{r.stdout}{r.stderr}")
    return r


def generiraj_i_provjeri(repo, izvor, sada):
    arg = ["--repo", str(repo), "--izvor", str(izvor)] + (["--sada", sada] if sada else [])
    for naredba in ("generiraj", "provjeri"):
        r = subprocess.run(GEN + [naredba] + arg, capture_output=True, text=True, encoding="utf-8")
        print(r.stdout, end="")
        if r.returncode != 0:
            stani(f"'{naredba}' nije prošlo:\n{r.stderr}")
    ok("generiranje i sve provjere prošli (izvor, datumi, bazne cijene, CSV, stabilne adrese, arhiva)")


def objavi(a):
    repo, izvor = Path(a.repo).resolve(), Path(a.izvor).resolve()
    ci = os.environ.get("GITHUB_ACTIONS") == "true"
    if a.sada and (a.potvrdi or ci):
        stani("--sada je dopušteno samo u probnom prolazu bez --potvrdi")
    if not a.potvrdi:  # probni prolaz radi na KOPIJI: stvarna radna kopija ostaje netaknuta
        privremena = Path(tempfile.mkdtemp(prefix="cjenik-probni-"))
        atexit.register(shutil.rmtree, privremena, True)  # kopija se uvijek briše (i nakon STOP-a)
        radna = privremena / "kopija"
        # lagana kopija: dijeljeni git objekti + samo datoteke cjenika (bez slika i ostatka stranice)
        git(repo, "rev-parse", "--git-dir")
        subprocess.run(["git", "clone", "--shared", "--no-checkout", "--quiet", str(repo), str(radna)], check=True, capture_output=True)
        git(radna, "sparse-checkout", "set", "--no-cone", "/cjenik.html", "/_redirects", "/_headers", "/cjenici/")
        git(radna, "checkout", "--quiet", "main", check=False)
        for ime in ("cjenik.html", "_redirects", "_headers", "cjenici"):
            src = repo / ime
            if src.is_dir():
                shutil.copytree(src, radna / ime, dirs_exist_ok=True, copy_function=shutil.copyfile)
            elif src.exists():
                shutil.copyfile(src, radna / ime)
        repo = radna
    grana = git(repo, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
    if grana != "main":
        stani(f"aktivna grana je '{grana}', objava ide samo s 'main'")
    ok("grana je main")
    if a.potvrdi:
        git(repo, "fetch", "origin", "main")
        zaostaje = git(repo, "rev-list", "--count", "HEAD..origin/main").stdout.strip()
        if zaostaje != "0":
            stani(f"lokalni main zaostaje {zaostaje} commit(a) za origin/main - povuci promjene i pokreni ponovno")
        ok("main nije iza origin/main")
    status = git(repo, "status", "--porcelain").stdout.splitlines()
    if status and not a.prva_objava and a.potvrdi:
        stani("radna kopija nije čista prije generiranja (osim --prva-objava):\n" + "\n".join(status))

    # Neobjavljene (untracked) generirane CSV datoteke iz ranijih probnih generiranja su nacrti: uklanjaju se
    # da se nova verzija generira s vremenskom oznakom stvarne objave (npr. prva objava nakon lokalnog testa).
    for f in git(repo, "ls-files", "--others", "--exclude-standard", "cjenici/").stdout.splitlines():
        if f.endswith(".csv") or f.endswith("arhiva.json"):
            (repo / f).unlink()
            print(f"nacrt uklonjen (nikad objavljen): {f}")

    generiraj_i_provjeri(repo, izvor, a.sada)

    promjene = git(repo, "status", "--porcelain").stdout.splitlines()
    if not a.prva_objava:
        tudje = [s for s in promjene if not s[3:].startswith(GENERIRANO)]
        if tudje:
            stani("neočekivane promjene izvan generiranih datoteka:\n" + "\n".join(tudje))
    if not promjene:
        print("\nNema promjena u cjeniku - nema ništa za objaviti.")
        return
    print("\nPromjene koje bi se objavile:\n" + "\n".join(promjene))
    if not a.potvrdi:
        if a.izlaz:  # generirane datoteke za pregled (npr. artefakt u GitHub Actionsu)
            izlaz = Path(a.izlaz)
            for ime in GENERIRANO:
                src = repo / ime
                if src.is_dir():
                    shutil.copytree(src, izlaz / ime, dirs_exist_ok=True)
                elif src.exists():
                    izlaz.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, izlaz / ime)
        print("\nPROBNI PROLAZ je prošao. Ništa nije commitano ni pushano. Za stvarnu objavu dodaj --potvrdi.")
        return

    git(repo, "add", "-A" if a.prva_objava else "--", *([] if a.prva_objava else list(GENERIRANO)))
    poruka = a.poruka or "Cjenik: objava"
    git(repo, "commit", "-m", poruka, ci=ci)
    git(repo, "push", "origin", "main")  # bez --force; odbija se ako je main u međuvremenu pomaknut
    lokalni = git(repo, "rev-parse", "HEAD").stdout.strip()
    udaljeni = git(repo, "ls-remote", "origin", "refs/heads/main").stdout.split()[0]
    if lokalni != udaljeni:
        stani("push nije potvrđen: origin/main nije jednak lokalnom commitu")
    ok(f"commit {lokalni[:10]} pushan na main. Netlify sada objavljuje - slijedi 'live' provjera")


class _BezPreusmjeravanja(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def dohvati(url):
    otvarac = urllib.request.build_opener(_BezPreusmjeravanja)
    zahtjev = urllib.request.Request(url, headers={"User-Agent": "cjenik-provjera", "Cache-Control": "no-cache"})
    try:
        with otvarac.open(zahtjev, timeout=20) as r:
            return r.status, r.headers.get("content-type", ""), r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.headers.get("content-type", ""), b""


def live(a):
    repo = Path(a.repo).resolve()
    site = a.site.rstrip("/")
    rd = (repo / "_redirects").read_text(encoding="utf-8")
    ciljevi = dict(re.findall(r"^(/cjenici/\S+\.csv)\s+(/cjenici/\S+\.csv)\s+200", rd, re.M))
    if len(ciljevi) != 2:
        stani("_redirects nema dvije stabilne adrese")
    ocekivano = {}
    for stabilna, cilj in ciljevi.items():
        p = repo / cilj.lstrip("/")
        if not p.exists():
            stani(f"_redirects pokazuje na nepostojeću datoteku: {cilj}")
        ocekivano[stabilna] = p.read_bytes()
    # 1) čekaj da Netlify objavi NOVI sadržaj (stabilne adrese moraju vratiti očekivani sadržaj)
    kraj = time.time() + a.cekaj
    while True:
        spremno = all(dohvati(site + s)[0:3][2] == b for s, b in ocekivano.items())
        if spremno:
            ok("Netlify je objavio novi sadržaj")
            break
        if time.time() > kraj:
            stani(f"Netlify deploy nije stigao u {a.cekaj} s: stabilne adrese još ne vraćaju novi sadržaj. "
                  "Provjeri Netlify (Deploys) - objava NIJE potvrđena.")
        print("... čekam Netlify deploy", flush=True)
        time.sleep(15)
    # 2) puna provjera
    greske = []

    def provjeri(url, tijelo_ocekivano=None):
        st, ct, tijelo = dohvati(url)
        if st != 200 or "text/csv" not in ct:
            greske.append(f"{url}: HTTP {st}, {ct or 'bez Content-Type'} (očekivano 200 i text/csv, bez preusmjeravanja)")
        elif tijelo_ocekivano is not None and tijelo != tijelo_ocekivano:
            greske.append(f"{url}: sadržaj se razlikuje od generirane datoteke")
        else:
            ok(f"{url}: {st} {ct}" + (", sadržaj identičan" if tijelo_ocekivano is not None else ""))

    for stabilna, cilj in ciljevi.items():
        provjeri(site + stabilna, ocekivano[stabilna])
        provjeri(site + cilj, ocekivano[stabilna])
    for f in sorted((repo / "cjenici" / "arhiva").glob("*.csv")):
        provjeri(f"{site}/cjenici/arhiva/{f.name}", f.read_bytes())
    st, ct, tijelo = dohvati(site + "/cjenik")
    t = tijelo.decode("utf-8", "replace")
    if st != 200 or "text/html" not in ct:
        greske.append(f"/cjenik: HTTP {st}, {ct}")
    elif "noindex" in t:
        greske.append("/cjenik: ima noindex")
    else:
        ok(f"/cjenik: {st} {ct}, bez noindex")
        for stabilna in ciljevi:
            if f'href="{stabilna.lstrip("/")}"' not in t:
                greske.append(f"/cjenik ne sadrži poveznicu na {stabilna}")
    if greske:
        print("\nPROBLEMI NA ŽIVOJ STRANICI - OBJAVA NIJE USPJELA:\n  " + "\n  ".join(greske), flush=True)
        sys.exit(1)
    print("\nLive provjera prošla: stranica i oba CSV-a su objavljeni i ispravni.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("naredba", choices=["provjera", "objavi", "live"])
    ap.add_argument("--repo", required=True)
    ap.add_argument("--izvor", default=str(HERE))
    ap.add_argument("--potvrdi", action="store_true")
    ap.add_argument("--prva-objava", action="store_true")
    ap.add_argument("--poruka")
    ap.add_argument("--izlaz", help="mapa u koju probni prolaz kopira generirane datoteke (za pregled)")
    ap.add_argument("--sada", help="SAMO ZA TESTOVE (lažno vrijeme, Europe/Zagreb)")
    ap.add_argument("--cekaj", type=int, default=600)
    ap.add_argument("--site", default="https://pyroprintdamir.hr")
    a = ap.parse_args()
    if a.naredba == "live":
        live(a)
    else:
        if a.naredba == "provjera":
            a.potvrdi = False
        objavi(a)
