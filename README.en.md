# sc-list-pisos-fincas

A local **flat & property finder** that, starting from a catalogue of real-estate websites and a JSON database of listings, lets you **add a province, town or street and list every flat** that matches. It also builds ready-to-open search URLs for every configured website.

- No external dependencies (Python 3.8+ only).
- Partial, case- and accent-insensitive searches.
- Table, JSON or CSV output.
- Optional web lookup, disabled by default and `robots.txt`-aware.
- **.zip** and **.deb** artifacts attached to every release.
- Automatic **bidirectional mirror GitHub ⇄ GitLab**.

## Quick start

### From source

```bash
git clone https://github.com/BENDER35/sc_list_pisos_fincas.git
cd sc_list_pisos_fincas
python3 -m pisos_fincas list --localidad "Alcalá de Henares" --calle Mayor
```

### From the .deb package

```bash
sudo apt install ./sc-list-pisos-fincas_0.1.0_all.deb
pisos-fincas stats
```

### From the ZIP archive

```bash
unzip sc_list_pisos_fincas-0.1.0.zip
cd sc_list_pisos_fincas-0.1.0
python3 -m pisos_fincas webs --localidad Valencia --calle Colon
```

## Usage

```bash
# All listings
pisos-fincas list

# Filter by province, town and street (combinable)
pisos-fincas list --provincia Madrid --localidad "Alcalá de Henares" --calle Mayor

# Street prefix and number are ignored: "Calle Mayor, 12" == "Mayor"
pisos-fincas list --calle "calle mayor, 12"

# Extra filters and ordering
pisos-fincas list --provincia Barcelona --operacion alquiler --precio-max 1300 --m2-min 60 --orden m2

# Export
pisos-fincas list --calle Colon --formato json
pisos-fincas list --calle Colon --formato csv > colon.csv

# Add a listing to the local catalogue
pisos-fincas add --provincia Madrid --localidad Getafe --calle "Calle Nueva, 1" \
  --precio 123000 --habitaciones 2 --m2 70 --portal manual

# Show catalogued websites with prefilled search URLs
pisos-fincas webs --provincia Madrid --localidad "Alcalá de Henares" --calle Mayor
pisos-fincas webs --formato json

# Summary
pisos-fincas stats

# Optional website lookup (check robots.txt and terms of use first)
pisos-fincas fetch --web demo-local --localidad Valencia --allow-network
```

## Data format

`data/pisos.json` is a list of listings:

| Field | Meaning |
| --- | --- |
| `id`, `provincia`, `localidad`, `calle` | ID and location (the last three are required when adding). |
| `portal`, `operacion` | Source portal and `venta` / `alquiler` (sale / rent). |
| `precio`, `habitaciones`, `m2` | Optional numeric details. |
| `url`, `fecha`, `notas` | Listing URL, date and free notes. |

Use another file with `--datos path/to/pisos.json`. The `.deb` reads from `/usr/share/sc-list-pisos-fincas/data/` by default; the `SC_PISOS_HOME` environment variable overrides that base path.

## Website catalogue

`data/webs.json` holds the portals (Idealista, Fotocasa, pisos.com, enalquiler, Milanuncios, a sample agency and a `demo-local` portal for tests). Each entry defines templates:

- `inicio`, `provincia`, `localidad`, `calle`.
- Placeholders: `{provincia}`, `{localidad}`, `{calle}`, `{provincia_slug}`, `{localidad_slug}`, `{calle_slug}`, `{url}`.

The most specific template is selected from the filters you pass. URLs are **indicative**: verify the current format on each portal before using `fetch`.

> **Legal / ethical note:** `fetch` honours `robots.txt`, sends an identifiable User-Agent and never attempts to bypass blocks. Check each portal's terms before use. It is off by default; normal operation is entirely local.

## Development and tests

```bash
python3 -m unittest discover -s tests -v
bash scripts/build_release.sh
bash scripts/verify.sh
```

`build_release.sh` creates in `dist/`:

- `sc_list_pisos_fincas-0.1.0.zip` — source, documentation, data and tests.
- `sc-list-pisos-fincas_0.1.0_all.deb` — Debian/Ubuntu package (architecture `all`).

## Bidirectional mirror

```text
push on GitHub  --[GitHub Actions: scripts/mirror_to_gitlab.sh]-->  GitLab
push on GitLab  --[GitLab CI:      scripts/mirror_to_github.sh]-->  GitHub
```

Each side force-mirrors to the other. To prevent loops, the scripts compare SHAs before pushing and honour the `[skip mirror]` marker in the latest commit message.

Required secrets:

- GitHub: `GITLAB_REPO_URL` (HTTPS URL with a GitLab token allowed to `write_repository`).
- GitLab: `GH_TOKEN` (GitHub token with `repo` scope).

Default branch: `main`. See the [step-by-step tutorial](docs/TUTORIAL_EN.md).

## License

MIT. See [LICENSE](LICENSE).
