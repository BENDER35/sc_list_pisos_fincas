#!/usr/bin/env bash
# Verificación completa: pruebas, paquetes y ejecución real desde el .deb extraído.
set -euo pipefail

cd "$(dirname "$0")/.."
VERSION="$(head -n 1 VERSION | tr -d '\r\n')"
ZIP="dist/sc_list_pisos_fincas-${VERSION}.zip"
DEB="dist/sc-list-pisos-fincas_${VERSION}_all.deb"
TRABAJO="$(mktemp -d)"
trap 'rm -rf "$TRABAJO"' EXIT

echo "[1/6] Pruebas unitarias"
/usr/bin/python3 -m unittest discover -s tests -v

echo "[2/6] Comprobación de artefactos"
test -f "$ZIP" || { echo "Falta $ZIP"; exit 1; }
test -f "$DEB" || { echo "Falta $DEB"; exit 1; }

echo "[3/6] Integridad del ZIP"
unzip -tq "$ZIP"

echo "[4/6] Metadatos del .deb"
dpkg-deb --info "$DEB" | grep -E 'Package:|Version:|Architecture:'

echo "[5/6] Ejecución del ejecutable instalado por el .deb"
dpkg-deb -x "$DEB" "$TRABAJO/deb"
SC_PISOS_HOME="$TRABAJO/deb/usr/share/sc-list-pisos-fincas" \
  "$TRABAJO/deb/usr/bin/pisos-fincas" --version
SC_PISOS_HOME="$TRABAJO/deb/usr/share/sc-list-pisos-fincas" \
  "$TRABAJO/deb/usr/bin/pisos-fincas" list \
    --localidad "Alcalá de Henares" --calle Mayor --formato json \
  > "$TRABAJO/resultado.json"
/usr/bin/python3 - "$TRABAJO/resultado.json" <<'PY'
import json, sys
datos = json.load(open(sys.argv[1], encoding="utf-8"))
ids = sorted(item["id"] for item in datos)
assert ids == ["p001", "p002", "p003", "p018"], ids
print(f"  {len(ids)} anuncios correctos en Calle Mayor: {', '.join(ids)}")
PY

echo "[6/6] Generación de URLs desde el ZIP"
unzip -q "$ZIP" -d "$TRABAJO/zip"
( cd "$TRABAJO/zip/sc_list_pisos_fincas-$VERSION" && \
  /usr/bin/python3 -m pisos_fincas webs --localidad Valencia --calle Colon --formato json \
  > "$TRABAJO/urls.json" )
/usr/bin/python3 - "$TRABAJO/urls.json" <<'PY'
import json, sys
urls = json.load(open(sys.argv[1], encoding="utf-8"))
assert len(urls) > 0
assert any("valencia" in u["url"] for u in urls)
print(f"  {len(urls)} portales con URL generada")
PY

echo "VERIFICACIÓN CORRECTA"
