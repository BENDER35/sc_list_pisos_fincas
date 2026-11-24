# sc-list-pisos-fincas

Consultor local de **pisos y fincas** que, a partir de un catálogo de portales inmobiliarios y de un JSON de anuncios, permite **añadir una provincia, localidad o calle y listar todos los pisos** que coinciden. También genera las URLs de búsqueda de cada web configurada.

- Sin dependencias externas (solo Python 3.8+).
- Búsquedas parciales e insensibles a mayúsculas y acentos.
- Salida en tabla, JSON o CSV.
- Consulta opcional a Internet, desactivada por defecto y con respeto a `robots.txt`.
- Paquetes **.zip** y **.deb** publicados en cada release.
- Réplica automática **bidireccional GitHub ⇄ GitLab**.

## Instalación rápida

### Desde el código fuente

```bash
git clone https://github.com/BENDER35/sc_list_pisos_fincas.git
cd sc_list_pisos_fincas
python3 -m pisos_fincas list --localidad "Alcalá de Henares" --calle Mayor
```

### Desde el paquete .deb

```bash
sudo apt install ./sc-list-pisos-fincas_0.1.0_all.deb
pisos-fincas stats
```

### Desde el ZIP

```bash
unzip sc_list_pisos_fincas-0.1.0.zip
cd sc_list_pisos_fincas-0.1.0
python3 -m pisos_fincas webs --localidad Valencia --calle Colón
```

## Uso

```bash
# Ver todos los anuncios
pisos-fincas list

# Filtrar por provincia, localidad y calle (combinables)
pisos-fincas list --provincia Madrid --localidad "Alcalá de Henares" --calle Mayor

# El prefijo de vía y el número no importan: "Calle Mayor, 12" = "Mayor"
pisos-fincas list --calle "calle mayor, 12"

# Más filtros y orden
pisos-fincas list --provincia Barcelona --operacion alquiler --precio-max 1300 --m2-min 60 --orden m2

# Exportar
pisos-fincas list --calle Colón --formato json
pisos-fincas list --calle Colón --formato csv > colon.csv

# Añadir un anuncio nuevo al catálogo local
pisos-fincas add --provincia Madrid --localidad Getafe --calle "Calle Nueva, 1" \
  --precio 123000 --habitaciones 2 --m2 70 --portal manual

# Ver las webs del catálogo y sus URLs de búsqueda ya rellenas
pisos-fincas webs --provincia Madrid --localidad "Alcalá de Henares" --calle Mayor
pisos-fincas webs --formato json

# Resumen
pisos-fincas stats

# Consulta opcional a un portal (revisa antes robots.txt y condiciones de uso)
pisos-fincas fetch --web demo-local --localidad Valencia --allow-network
```

Ejemplo de salida de `list`:

```text
id   | provincia | localidad         | calle           | portal    | operacion | precio | m2
-----+-----------+-------------------+-----------------+-----------+-----------+--------+---
p002 | Madrid    | Alcalá de Henares | Calle Mayor, 28 | Fotocasa  | venta     | 189500 | 71
p018 | Madrid    | Alcalá de Henares | Calle Mayor, 55 | manual    | venta     | 205000 | 74
p001 | Madrid    | Alcalá de Henares | Calle Mayor, 12 | Idealista | venta     | 215000 | 88
p003 | Madrid    | Alcalá de Henares | Calle Mayor, 40 | pisos.com | alquiler  | 950    | 65
```

## Formato de datos

`data/pisos.json` es una lista de anuncios:

| Campo | Descripción |
| --- | --- |
| `id`, `provincia`, `localidad`, `calle` | Identificador y ubicación (los tres últimos son obligatorios al dar de alta). |
| `portal`, `operacion` | Portal de origen y `venta` / `alquiler`. |
| `precio`, `habitaciones`, `m2` | Datos numéricos opcionales. |
| `url`, `fecha`, `notas` | Enlace al anuncio, fecha e información libre. |

Puedes usar otro fichero con `--datos ruta/a/pisos.json`. El `.deb` lee por defecto de `/usr/share/sc-list-pisos-fincas/data/`; la variable `SC_PISOS_HOME` permite cambiar esa base.

## Catálogo de webs

`data/webs.json` contiene los portales (Idealista, Fotocasa, pisos.com, enalquiler, Milanuncios, una inmobiliaria de ejemplo y un portal `demo-local` para pruebas). Cada entrada define plantillas:

- `inicio`, `provincia`, `localidad`, `calle`.
- Marcadores: `{provincia}`, `{localidad}`, `{calle}`, `{provincia_slug}`, `{localidad_slug}`, `{calle_slug}`, `{url}`.

La herramienta elige la plantilla más específica según los filtros que pases. Las URLs son **orientativas**: comprueba el formato real en cada portal antes de usar `fetch`.

> **Aviso legal / ético:** `fetch` respeta `robots.txt`, incluye un User-Agent identificable y nunca intenta evadir bloqueos. Verifica las condiciones de uso del portal. Por defecto está desactivado; el funcionamiento normal de la herramienta es 100 % local.

## Desarrollo y pruebas

```bash
python3 -m unittest discover -s tests -v
bash scripts/build_release.sh
bash scripts/verify.sh
```

`build_release.sh` genera en `dist/`:

- `sc_list_pisos_fincas-0.1.0.zip` — código fuente, documentación, datos y pruebas.
- `sc-list-pisos-fincas_0.1.0_all.deb` — paquete Debian/Ubuntu (arquitectura `all`).

## Réplica bidireccional

```text
push en GitHub  --[GitHub Actions: scripts/mirror_to_gitlab.sh]-->  GitLab
push en GitLab  --[GitLab CI:      scripts/mirror_to_github.sh]-->  GitHub
```

Cada lado hace `push --mirror --force` hacia el otro. Para evitar bucles, los scripts comparan los SHA antes de empujar y respetan la marca `[skip mirror]` en el mensaje del último commit.

Secretos necesarios:

- En GitHub: `GITLAB_REPO_URL` (URL HTTPS con token de GitLab con `write_repository`).
- En GitLab: `GH_TOKEN` (token de GitHub con permiso `repo`).

El branch por defecto es `main`. Consulta la [guía didáctica](docs/GUIA_DIDACTICA_ES.md) para el paso a paso.

## Licencia

MIT. Consulta [LICENSE](LICENSE).
