# Guía didáctica (español)

Aprende a usar `sc-list-pisos-fincas` desde cero. Duración estimada: 20-30 minutos.

## Objetivos

Al terminar sabrás:

1. Listar pisos filtrando por provincia, localidad y calle.
2. Añadir anuncios propios al catálogo local.
3. Generar enlaces de búsqueda para los portales del listado de webs.
4. Exportar resultados y ejecutar las pruebas automáticas.
5. Generar los paquetes zip y deb y entender el mirror GitHub ⇄ GitLab.

## 0. Requisitos

- Linux, macOS o Windows con **Python 3.8+**.
- Para el `.deb`: Debian/Ubuntu con `dpkg` (o `apt`).
- Opcional: `git`, `gh` y `glab` para el mirror.

Comprueba la versión:

```bash
python3 --version
```

## 1. Obtener el programa

```bash
git clone https://github.com/BENDER35/sc_list_pisos_fincas.git
cd sc_list_pisos_fincas
```

O instala el `.deb` de la release:

```bash
sudo apt install ./sc-list-pisos-fincas_0.1.0_all.deb
pisos-fincas --version
```

Cuando uses el código fuente, el comando es `python3 -m pisos_fincas`; cuando instales el `.deb`, es `pisos-fincas`. En los ejemplos se usa la forma corta. Define un alias si lo prefieres:

```bash
alias pisos-fincas='python3 -m pisos_fincas'
```

## 2. Conocer los datos

El archivo `data/pisos.json` contiene anuncios. Cada uno describe una ubicación y unas características:

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
  "notas": "Dato de ejemplo ficticio"
}
```

Los datos incluidos son **ficticios** y sirven para aprender y verificar el programa.

Ejercicio 1 — cuántos anuncios hay:

```bash
pisos-fincas stats
```

Debe mostrar `Anuncios: 18`.

## 3. Tu primera búsqueda

Busca todos los pisos de una localidad:

```bash
pisos-fincas list --localidad "Alcalá de Henares"
```

Ahora añade la calle:

```bash
pisos-fincas list --localidad "Alcalá de Henares" --calle Mayor
```

Verás cuatro anuncios en la calle Mayor (`p001`, `p002`, `p003`, `p018`).

Observaciones importantes:

- No importan los acentos: `--localidad "Alcala de Henares"` funciona igual.
- No importa la forma de la calle: `Mayor`, `Calle Mayor` o `Calle Mayor, 12` encuentran lo mismo.
- La búsqueda es parcial: `Mayor` también coincide con `Calle Mayorazgo`.

Ejercicio 2 — busca por provincia:

```bash
pisos-fincas list --provincia Barcelona
```

## 4. Añadir una localidad, provincia o calle

El programa consulta el catálogo local. Para ampliarlo, da de alta un anuncio:

```bash
pisos-fincas add \
  --provincia Madrid \
  --localidad Getafe \
  --calle "Calle Nueva, 1" \
  --precio 123000 --habitaciones 2 --m2 70 \
  --portal manual
```

Ahora consulta lo nuevo:

```bash
pisos-fincas list --localidad Getafe --calle Nueva
```

Si quieres partir de cero, copia el JSON y usa `--datos`:

```bash
cp data/pisos.json /tmp/mis-pisos.json
 pisos-fincas --datos /tmp/mis-pisos.json add --provincia Valencia \
   --localidad Gandía --calle "Calle San Francisco, 3" --precio 90000
pisos-fincas --datos /tmp/mis-pisos.json list --localidad Gandía
```

## 5. Filtrar y exportar

```bash
# Solo alquileres de Barcelona con menos de 1300 € y al menos 60 m²
pisos-fincas list --provincia Barcelona --operacion alquiler --precio-max 1300 --m2-min 60

# Ordenar por superficie
pisos-fincas list --provincia Barcelona --orden m2

# JSON (ideal para otros programas)
pisos-fincas list --calle Colón --formato json

# CSV (ideal para hojas de cálculo)
pisos-fincas list --calle Colón --formato csv > colon.csv
```

Ejercicio 3 — cuenta los anuncios de la calle Mallorca y expórtalos a CSV.

## 6. El listado de webs

`data/webs.json` es el catálogo de portales. Puedes editarlo para añadir tus webs o cambiar las plantillas de búsqueda.

```bash
pisos-fincas webs
pisos-fincas webs --provincia Madrid --localidad "Alcalá de Henares" --calle Mayor
pisos-fincas webs --formato json > urls.json
```

Cada entrada usa marcadores como `{provincia_slug}` o `{calle}`; el programa los sustituye por los valores que pases. Por ejemplo:

```text
https://ejemplo.test/pisos?localidad=alcala-de-henares&calle=calle-mayor
```

Las URLs son orientativas: las webs cambian su formato. Ajusta las plantillas a tus necesidades.

## 7. Consulta opcional a Internet

```bash
pisos-fincas fetch --web demo-local --localidad Valencia --allow-network
```

Sin `--allow-network` el programa se niega a acceder a la red. Con él:

1. Lee `robots.txt` del portal.
2. Si la consulta no está permitida, no descarga nada.
3. Si está permitida, extrae enlaces de anuncios del HTML.

Muchos portales renderizan con JavaScript y no devuelven anuncios en el HTML inicial: en ese caso verás un aviso, no un error. Revisa siempre las condiciones de uso del portal.

## 8. Verificar que todo funciona

```bash
python3 -m unittest discover -s tests -v
bash scripts/verify.sh
```

Las 20 pruebas comprueban normalización, búsquedas, altas, generación de URLs, CLI y formatos de salida.

## 9. Crear zip y deb

```bash
bash scripts/build_release.sh
ls -lh dist/
```

- El **zip** contiene el proyecto completo: código, datos, documentación y pruebas.
- El **deb** instala el ejecutable `pisos-fincas` y los datos en `/usr/share/sc-list-pisos-fincas/`.

Para probar el deb sin instalarlo:

```bash
dpkg-deb -x dist/sc-list-pisos-fincas_0.1.0_all.deb /tmp/deb-test
SC_PISOS_HOME=/tmp/deb-test/usr/share/sc-list-pisos-fincas \
  /tmp/deb-test/usr/bin/pisos-fincas stats
```

## 10. Mirror automático GitHub ⇄ GitLab

1. Crea los repositorios vacíos en GitHub y GitLab con el mismo nombre.
2. En GitHub → *Settings → Secrets and variables → Actions*, añade `GITLAB_REPO_URL` con:
   `https://oauth2:TU_TOKEN@gitlab.com/BENDER_5000/sc_list_pisos_fincas.git`
3. En GitLab → *Settings → CI/CD → Variables*, añade `GH_TOKEN` con un token de GitHub con permiso `repo`.
4. Haz push a `main`. GitHub Actions replicará en GitLab; el pipeline de GitLab replicará de vuelta.

Para evitar bucles, los scripts comparan los hashes de los commits y respetan `[skip mirror]` en el mensaje del commit.

Ejercicio 4 — haz un cambio pequeño en el README, haz push y comprueba en *Actions* y en *CI/CD → Pipelines* que ambos lados se sincronizan.

## 11. Problemas frecuentes

| Síntoma | Solución |
| --- | --- |
| `No se han encontrado anuncios` | Revisa que la localidad esté bien escrita; prueba solo con `--calle`. |
| `Error: no such file` en los datos | Indica la ruta con `--datos` o reinstala el deb. |
| `Web desconocida` en `fetch` | Lista los ids válidos con `pisos-fincas webs`. |
| `robots.txt no permite...` | Es el comportamiento esperado: usa solo el catálogo local. |
| El mirror no dispara | Comprueba secretos, permisos de los tokens y que Actions/CI estén habilitados. |

## Ejercicios propuestos

1. Añade tres pisos nuevos en tu localidad y listarlos ordenados por precio.
2. Crea un portal nuevo en `data/webs.json` con tus plantillas y comprueba `pisos-fincas webs`.
3. Exporta a CSV los alquileres de toda una provincia y ábrelos en una hoja de cálculo.
4. Genera una release nueva cambiando `VERSION` y ejecutando el script de build.
