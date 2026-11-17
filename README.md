# Cjenik PyroprintDamir - izvor i alat (grana `cjenik-izvor`)

Ova grana je JAVNA. Sadrži samo podatke koji su ionako na javnoj stranici cjenika te skripte. Ne ide na web (Netlify objavljuje samo `main`).
Interne evidencije, računi, povijesne transakcije i podaci o kupcima NIKAD ne idu ovamo (ostaju samo na vlasnikovu računalu).

| Datoteka | Uloga |
|---|---|
| `cjenik.csv` | jedini izvor cijena (samo javni stupci; skripta odbija bilo što drugo) |
| `postavke.json` | matični broj i oznaka prodajnog mjesta (`ZA_SVA_PRODAJNA_MJESTA`, pravno nepotvrđeno tumačenje) |
| `generiraj_cjenike.py` | provjerava izvor, generira `cjenik.html` (tablica), CSV cjenike, arhivu + `arhiva.json`, `_redirects` |
| `objava.py` | probni prolaz / objava na `main` / provjera javne stranice nakon deploya |

## Promjena cijene
1. Uredi `cjenik.csv` na grani `cjenik-izvor` (GitHub web editor ili lokalno). Netlify to NE objavljuje.
   - Nova stavka (nakon 10.9.2026.): `bazna_cijena` = cijena na dan prvog nuđenja, `datum_bazne_cijene` = taj dan (mora biti dan objave).
   - Bazna cijena i datum objavljene stavke se ne mijenjaju (skripta odbija).
2. GitHub: Actions -> **Cjenik** -> Run workflow (branch `main`) -> `samo-provjera`. Ništa se ne objavljuje; generirane datoteke dobiješ kao artefakt "cjenik-pregled".
3. Ako je provjera zelena: Run workflow -> `objavi`. Jedan commit na `main` (samo `cjenici/`, `cjenik.html`, `_redirects`), Netlify objavi, workflow provjeri `/cjenik`, `/cjenici/roba.csv` i `/cjenici/usluge.csv` (HTTP 200, text/csv, bez preusmjeravanja, sadržaj). Crveno = nije potvrđeno.
4. Izmjena mora biti objavljena do 11:00 na dan promjene (čl. 3. st. 5.).

## Arhiva
Zamijenjena verzija ide u `cjenici/arhiva/` i bilježi se u `cjenici/arhiva/arhiva.json` (datum zamjene s vremenskom zonom, neovisno o git povijesti). Čuva se 30 dana od zamjene (pravilnik traži najmanje 15). Starije briše sljedeća objava; `provjeri` pada ako je nešto uklonjeno prerano ili nedostaje.

## Lokalno / oporavak (računalo uključeno)
Klon `main` u mapi A, klon ove grane u mapi B:
```
python objava.py provjera --repo A --izvor B            # siguran probni prolaz (radi na kopiji)
python objava.py objavi   --repo A --izvor B --potvrdi   # commit + push na main
python objava.py live     --repo A --izvor B             # provjera javne stranice
```
Ako loša verzija ode na web: Netlify -> Deploys -> prethodni deploy -> "Publish deploy", zatim ispravi izvor.
