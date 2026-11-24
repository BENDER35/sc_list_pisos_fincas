# Step-by-step tutorial (English)

Learn `sc-list-pisos-fincas` from scratch. Estimated time: 20-30 minutes.

## Goals

By the end you will be able to:

1. List flats filtered by province, town and street.
2. Add your own listings to the local catalogue.
3. Build search links for the websites in the catalogue.
4. Export results and run the automated tests.
5. Build the zip and deb packages and understand the GitHub ⇄ GitLab mirror.

## 0. Requirements

- Linux, macOS or Windows with **Python 3.8+**.
- For the `.deb`: Debian/Ubuntu with `dpkg` (or `apt`).
- Optional: `git`, `gh` and `glab` for the mirror.

```bash
python3 --version
```

## 1. Get the program

```bash
git clone https://github.com/BENDER35/sc_list_pisos_fincas.git
cd sc_list_pisos_fincas
```

Or install the release `.deb`:

```bash
sudo apt install ./sc-list-pisos-fincas_0.1.0_all.deb
pisos-fincas --version
```

From source use `python3 -m pisos_fincas`; from the `.deb` use `pisos-fincas`. The examples below use the short form. To create an alias:

```bash
alias pisos-fincas='python3 -m pisos_fincas'
```

## 2. Understand the data

`data/pisos.json` holds listings. Each one describes a location and a few details:

```json
{
  "id": "p001",
  "provincia": "Madrid",
  "localidad": "Alcalá de Henares",
  "calle": "Calle Mayor, 12",
  "portal": "Idealista",
  "operacion": "venta",
  "precio": 215000,
  "habitaciones": 3,
  "m2": 88,
  "url": "https://ejemplo.es/anuncios/p001",
  "fecha": "2026-11-18",
  "notas": "Fictional sample data"
}
```

The bundled data is **fictional** and exists to learn and verify the tool.

Exercise 1 — count the listings:

```bash
pisos-fincas stats
```

You should see `Anuncios: 18`.

## 3. Your first search

Search every flat in a town:

```bash
pisos-fincas list --localidad "Alcalá de Henares"
```

Now add the street:

```bash
pisos-fincas list --localidad "Alcalá de Henares" --calle Mayor
```

Four listings on Calle Mayor appear (`p001`, `p002`, `p003`, `p018`).

Notes:

- Accents do not matter: `--localidad "Alcala de Henares"` works too.
- Street format does not matter: `Mayor`, `Calle Mayor` and `Calle Mayor, 12` all match.
- Matching is partial: `Mayor` also matches `Calle Mayorazgo`.

Exercise 2 — search by province:

```bash
pisos-fincas list --provincia Barcelona
```

## 4. Add a province, town or street

The tool queries the local catalogue. To extend it, add a listing:

```bash
pisos-fincas add \
  --provincia Madrid \
  --localidad Getafe \
  --calle "Calle Nueva, 1" \
  --precio 123000 --habitaciones 2 --m2 70 \
  --portal manual
```

Then query it:

```bash
pisos-fincas list --localidad Getafe --calle Nueva
```

To experiment safely, copy the JSON and use `--datos`:

```bash
cp data/pisos.json /tmp/my-flats.json
pisos-fincas --datos /tmp/my-flats.json add --provincia Valencia \
  --localidad Gandia --calle "Calle San Francisco, 3" --precio 90000
pisos-fincas --datos /tmp/my-flats.json list --localidad Gandia
```

## 5. Filtering and export

```bash
# Rentals in Barcelona under 1300 with at least 60 m2
pisos-fincas list --provincia Barcelona --operacion alquiler --precio-max 1300 --m2-min 60

# Sort by surface
pisos-fincas list --provincia Barcelona --orden m2

# JSON (easy for other programs)
pisos-fincas list --calle Colon --formato json

# CSV (easy for spreadsheets)
pisos-fincas list --calle Colon --formato csv > colon.csv
```

Exercise 3 — count the listings on Mallorca Street and export them to CSV.

## 6. The website catalogue

`data/webs.json` is the portal catalogue. Edit it to add your own sites or change search templates.

```bash
pisos-fincas webs
pisos-fincas webs --provincia Madrid --localidad "Alcalá de Henares" --calle Mayor
pisos-fincas webs --formato json > urls.json
```

Each entry uses placeholders such as `{provincia_slug}` or `{calle}`; the tool replaces them with your filters. Example:

```text
https://ejemplo.test/pisos?localidad=alcala-de-henares&calle=calle-mayor
```

URLs are indicative: sites change their format. Adjust the templates to your needs.

## 7. Optional web lookup

```bash
pisos-fincas fetch --web demo-local --localidad Valencia --allow-network
```

Without `--allow-network` the tool refuses to access the network. With it:

1. It reads the portal's `robots.txt`.
2. If the query is disallowed, nothing is downloaded.
3. If allowed, it extracts listing links from the HTML.

Many portals render with JavaScript and expose no listings in the initial HTML: you will see a notice, not a crash. Always check the portal's terms of use.

## 8. Verify everything works

```bash
python3 -m unittest discover -s tests -v
bash scripts/verify.sh
```

The 20 tests cover normalisation, searching, adding, URL generation, CLI and output formats.

## 9. Build zip and deb

```bash
bash scripts/build_release.sh
ls -lh dist/
```

- The **zip** contains the whole project: code, data, docs and tests.
- The **deb** installs the `pisos-fincas` executable and data in `/usr/share/sc-list-pisos-fincas/`.

Test the deb without installing:

```bash
dpkg-deb -x dist/sc-list-pisos-fincas_0.1.0_all.deb /tmp/deb-test
SC_PISOS_HOME=/tmp/deb-test/usr/share/sc-list-pisos-fincas \
  /tmp/deb-test/usr/bin/pisos-fincas stats
```

## 10. Automatic GitHub ⇄ GitLab mirror

1. Create empty repositories with the same name on GitHub and GitLab.
2. On GitHub → *Settings → Secrets and variables → Actions*, add `GITLAB_REPO_URL`:
   `https://oauth2:YOUR_TOKEN@gitlab.com/BENDER_5000/sc_list_pisos_fincas.git`
3. On GitLab → *Settings → CI/CD → Variables*, add `GH_TOKEN` with a GitHub token that has the `repo` scope.
4. Push to `main`. GitHub Actions mirrors to GitLab; the GitLab pipeline mirrors back.

To avoid loops, the scripts compare commit hashes and honour `[skip mirror]` in the commit message.

Exercise 4 — make a small README change, push, and check *Actions* and *CI/CD → Pipelines* to confirm both sides synchronise.

## 11. Troubleshooting

| Symptom | Fix |
| --- | --- |
| `No se han encontrado anuncios` | Check the town spelling; try only `--calle`. |
| `Error: no such file` for data | Pass the path with `--datos` or reinstall the deb. |
| `Web desconocida` in `fetch` | List valid ids with `pisos-fincas webs`. |
| `robots.txt no permite...` | Expected behaviour: use the local catalogue only. |
| Mirror does not trigger | Check secrets, token scopes and that Actions/CI are enabled. |

## Exercises

1. Add three new flats in your town and list them sorted by price.
2. Create a new portal in `data/webs.json` with your templates and check `pisos-fincas webs`.
3. Export all rentals of a province to CSV and open it in a spreadsheet.
4. Create a new release by bumping `VERSION` and running the build script.
