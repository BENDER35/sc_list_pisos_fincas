#!/usr/bin/env bash
# Genera el ZIP de fuentes y el .deb en dist/.
set -euo pipefail

cd "$(dirname "$0")/.."
VERSION="$(head -n 1 VERSION | tr -d '\r\n')"
NOMBRE="sc_list_pisos_fincas"
PAQUETE="sc-list-pisos-fincas"
DEST="dist"
TRABAJO="$(mktemp -d)"
trap 'rm -rf "$TRABAJO"' EXIT

echo "Construyendo versión $VERSION..."
rm -rf "$DEST" "$TRABAJO"
mkdir -p "$DEST"

# --- ZIP de fuentes -------------------------------------------------------
ZIP_ROOT="$TRABAJO/zip/$NOMBRE-$VERSION"
mkdir -p "$ZIP_ROOT"
for ruta in pisos_fincas data docs tests scripts packaging README.md README.en.md \
            CHANGELOG.md LICENSE VERSION; do
  cp -R "$ruta" "$ZIP_ROOT/"
done
find "$ZIP_ROOT" -type d -name '__pycache__' -prune -exec rm -rf {} +
find "$ZIP_ROOT" -type f \( -name '*.pyc' -o -name '.DS_Store' \) -delete
(
  cd "$TRABAJO/zip"
  zip -q -r "$OLDPWD/$DEST/${NOMBRE}-${VERSION}.zip" "$NOMBRE-$VERSION"
)

# --- Paquete .deb ---------------------------------------------------------
DEB_ROOT="$TRABAJO/deb/$PAQUETE"
mkdir -p "$DEB_ROOT/DEBIAN" "$DEB_ROOT/usr/bin" "$DEB_ROOT/usr/share/$PAQUETE"
sed "s/@VERSION@/$VERSION/g" packaging/deb/control > "$DEB_ROOT/DEBIAN/control"
install -m 0755 packaging/deb/pisos-fincas "$DEB_ROOT/usr/bin/pisos-fincas"
cp -R pisos_fincas data docs README.md README.en.md CHANGELOG.md LICENSE VERSION \
  "$DEB_ROOT/usr/share/$PAQUETE/"
find "$DEB_ROOT" -type d -name '__pycache__' -prune -exec rm -rf {} +
find "$DEB_ROOT" -type f \( -name '*.pyc' -o -name '.DS_Store' \) -delete
dpkg-deb --root-owner-group --build "$DEB_ROOT" "$DEST/${PAQUETE}_${VERSION}_all.deb"

echo "Listo:"
ls -lh "$DEST"
