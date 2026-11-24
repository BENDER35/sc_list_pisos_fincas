"""Núcleo del buscador: normalización, búsqueda, altas y catálogo de webs."""

from __future__ import annotations

import csv
import io
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional
from urllib.parse import quote

from .version import __version__

CAMPOS = (
    "id",
    "provincia",
    "localidad",
    "calle",
    "portal",
    "operacion",
    "precio",
    "habitaciones",
    "m2",
    "url",
    "fecha",
    "notas",
)

TIPOS_PREFIXO = re.compile(
    r"^(?:calle|avda?\.?|avenida|plaza|pza\.?|carrer|passeig)\b|^c\s*[/.]\s*", re.I
)


def normalizar(texto: Optional[str]) -> str:
    """Quita acentos, pasa a minúsculas y colapsa espacios."""
    if texto is None:
        return ""
    descompuesto = unicodedata.normalize("NFKD", str(texto))
    sin_acentos = "".join(c for c in descompuesto if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", sin_acentos).strip().lower()


def slug(texto: Optional[str]) -> str:
    """Convierte texto en un slug apto para URL."""
    return re.sub(r"[^a-z0-9]+", "-", normalizar(texto)).strip("-")


def limpiar_calle(texto: Optional[str]) -> str:
    """Elimina el tipo de vía para buscar 'Mayor' en 'Calle Mayor, 12'."""
    valor = normalizar(texto)
    valor = re.sub(r"^\s*\d+\s*,\s*", "", valor)
    valor = TIPOS_PREFIXO.sub("", valor)
    valor = re.sub(r"[,\s]+\d+.*$", "", valor)
    return valor.strip(" ,.")


def ruta_por_defecto(nombre: str) -> Path:
    """Resuelve una ruta de datos, tanto en el checkout como en el .deb."""
    entorno = __import__("os").environ.get("SC_PISOS_HOME")
    if entorno:
        return Path(entorno) / nombre
    candidata = Path(__file__).resolve().parent.parent / nombre
    if candidata.exists():
        return candidata
    return Path.cwd() / nombre


def leer_json(ruta: Path) -> Any:
    with Path(ruta).open("r", encoding="utf-8") as manejador:
        return json.load(manejador)


def escribir_json(ruta: Path, datos: Any) -> None:
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with ruta.open("w", encoding="utf-8") as manejador:
        json.dump(datos, manejador, ensure_ascii=False, indent=2)
        manejador.write("\n")


def cargar_listados(ruta: Path) -> List[Dict[str, Any]]:
    datos = leer_json(ruta)
    if isinstance(datos, dict):
        datos = datos.get("pisos", datos.get("listados", []))
    if not isinstance(datos, list):
        raise ValueError(f"Formato no reconocido en {ruta}: se esperaba una lista de anuncios")
    return [dict(item) for item in datos]


def guardar_listados(ruta: Path, listados: Iterable[Dict[str, Any]]) -> None:
    escribir_json(ruta, list(listados))


def buscar(
    listados: Iterable[Dict[str, Any]],
    provincia: Optional[str] = None,
    localidad: Optional[str] = None,
    calle: Optional[str] = None,
    portal: Optional[str] = None,
    operacion: Optional[str] = None,
    precio_max: Optional[float] = None,
    m2_min: Optional[float] = None,
    orden: str = "precio",
) -> List[Dict[str, Any]]:
    """Filtra anuncios. Provincia/localidad/calle son búsquedas parciales e insensibles a acentos."""
    filtros = [
        (normalizar(provincia), "provincia"),
        (normalizar(localidad), "localidad"),
        (limpiar_calle(calle), "calle"),
    ]
    filtros = [(valor, campo) for valor, campo in filtros if valor]

    resultados: List[Dict[str, Any]] = []
    for anuncio in listados:
        if any(valor not in normalizar(anuncio.get(campo)) for valor, campo in filtros):
            continue
        if portal and normalizar(portal) not in normalizar(anuncio.get("portal")):
            continue
        if operacion and normalizar(operacion) != normalizar(anuncio.get("operacion")):
            continue
        try:
            precio = float(anuncio.get("precio") or 0)
        except (TypeError, ValueError):
            precio = 0.0
        try:
            metros = float(anuncio.get("m2") or 0)
        except (TypeError, ValueError):
            metros = 0.0
        if precio_max is not None and (not precio or precio > precio_max):
            continue
        if m2_min is not None and metros < m2_min:
            continue
        resultados.append(anuncio)

    claves = {
        "precio": lambda a: (float(a.get("precio") or 0), normalizar(a.get("localidad"))),
        "m2": lambda a: (float(a.get("m2") or 0), normalizar(a.get("localidad"))),
        "localidad": lambda a: (normalizar(a.get("localidad")), normalizar(a.get("calle"))),
    }
    if orden not in claves:
        raise ValueError(f"Orden desconocido: {orden}. Usa: {', '.join(claves)}")
    return sorted(resultados, key=claves[orden])


def anadir(
    ruta: Path,
    datos: Dict[str, Any],
    provincia: str,
    localidad: str,
    calle: str,
    **extra: Any,
) -> Dict[str, Any]:
    """Añade un anuncio al fichero JSON y lo devuelve."""
    for nombre, valor in (("provincia", provincia), ("localidad", localidad), ("calle", calle)):
        if not str(valor or "").strip():
            raise ValueError(f"Falta el campo obligatorio: {nombre}")

    listados = cargar_listados(ruta)
    anuncio = {
        "id": str(extra.pop("id", "") or f"p{len(listados) + 1:03d}"),
        "provincia": provincia.strip(),
        "localidad": localidad.strip(),
        "calle": calle.strip(),
        "portal": extra.pop("portal", "manual") or "manual",
        "operacion": extra.pop("operacion", "venta") or "venta",
        "precio": extra.pop("precio", None),
        "habitaciones": extra.pop("habitaciones", None),
        "m2": extra.pop("m2", None),
        "url": extra.pop("url", "") or "",
        "fecha": extra.pop("fecha", "") or "",
        "notas": extra.pop("notas", "") or "",
    }
    anuncio.update({k: v for k, v in extra.items() if k in CAMPOS})

    if any(str(item.get("id")) == anuncio["id"] for item in listados):
        raise ValueError(f"Ya existe un anuncio con id {anuncio['id']}")

    listados.append(anuncio)
    guardar_listados(ruta, listados)
    return anuncio


def estadisticas(listados: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    items = list(listados)
    return {
        "total": len(items),
        "por_provincia": dict(Counter(i.get("provincia", "") for i in items).most_common()),
        "por_localidad": dict(Counter(i.get("localidad", "") for i in items).most_common()),
        "por_portal": dict(Counter(i.get("portal", "") for i in items).most_common()),
        "por_operacion": dict(Counter(i.get("operacion", "") for i in items).most_common()),
    }


def construir_url(
    web: Dict[str, Any],
    provincia: Optional[str] = None,
    localidad: Optional[str] = None,
    calle: Optional[str] = None,
) -> str:
    """Genera la URL de búsqueda de un portal según los filtros disponibles."""
    plantillas = web.get("plantillas", {})
    if calle:
        clave = "calle"
    elif localidad:
        clave = "localidad"
    elif provincia:
        clave = "provincia"
    else:
        clave = "inicio"
    plantilla = plantillas.get(clave)
    if not plantilla:
        for alternativa in ("calle", "localidad", "provincia", "inicio"):
            if plantillas.get(alternativa):
                plantilla = plantillas[alternativa]
                clave = alternativa
                break
    if not plantilla:
        return str(web.get("url", ""))

    valores = {
        "provincia": quote(normalizar(provincia), safe=""),
        "localidad": quote(normalizar(localidad), safe=""),
        "calle": quote(normalizar(calle), safe=""),
        "provincia_slug": slug(provincia),
        "localidad_slug": slug(localidad),
        "calle_slug": slug(calle),
        "url": str(web.get("url", "")),
        "version": __version__,
    }
    try:
        return plantilla.format(**valores)
    except (KeyError, IndexError):
        return str(web.get("url", ""))


def tabla(listados: Iterable[Dict[str, Any]]) -> str:
    columnas = ("id", "provincia", "localidad", "calle", "portal", "operacion", "precio", "m2")
    filas = [[str(item.get(c, "") or "") for c in columnas] for item in listados]
    anchos = [max(len(c), *(len(f[i]) for f in filas)) if filas else len(c) for i, c in enumerate(columnas)]
    separador = "-+-".join("-" * a for a in anchos)
    cabecera = " | ".join(c.ljust(anchos[i]) for i, c in enumerate(columnas))
    cuerpo = [" | ".join(f[i].ljust(anchos[i]) for i in range(len(columnas))) for f in filas]
    if filas:
        return "\n".join([cabecera, separador, *cuerpo])
    return "No se han encontrado anuncios con esos filtros."


def csv_texto(listados: Iterable[Dict[str, Any]]) -> str:
    salida = io.StringIO()
    escritor = csv.DictWriter(salida, fieldnames=CAMPOS, extrasaction="ignore")
    escritor.writeheader()
    for item in listados:
        escritor.writerow({c: item.get(c, "") for c in CAMPOS})
    return salida.getvalue()
