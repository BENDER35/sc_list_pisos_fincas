"""Consulta opcional a portales externos (desactivada por defecto).

Respeta robots.txt, usa un User-Agent identificable y no elude medidas de acceso.
Antes de usar un portal, revisa sus condiciones de uso.
"""

from __future__ import annotations

import html as html_lib
import re
import urllib.robotparser
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin
from urllib.request import Request, urlopen

from .core import construir_url, leer_json, ruta_por_defecto

USER_AGENT = "sc-list-pisos-fincas/0.1 (+https://github.com/BENDER35/sc_list_pisos_fincas)"
MAX_BYTES = 2_000_000
PATRON_ENLACE = re.compile(r"<a\b[^>]*href=[\"']([^\"']+)[\"'][^>]*>(.*?)</a>", re.I | re.S)
PATRON_TEXTO = re.compile(r"<[^>]+>")
PALABRAS_ANUNCIO = ("inmueble", "piso", "vivienda", "finca", "anuncio", "detalle", "propiedad")


def cargar_webs(ruta: Optional[Path] = None) -> List[Dict[str, Any]]:
    datos = leer_json(ruta or ruta_por_defecto("data/webs.json"))
    if isinstance(datos, dict):
        datos = datos.get("webs", [])
    return [dict(item) for item in datos]


def filtrar_webs(
    webs: List[Dict[str, Any]],
    provincia: Optional[str] = None,
    localidad: Optional[str] = None,
    calle: Optional[str] = None,
) -> List[Dict[str, Any]]:
    return list(webs)


def robots_permite(url: str, robots_url: Optional[str] = None, timeout: float = 8.0) -> bool:
    parser = urllib.robotparser.RobotFileParser()
    parser.set_url(robots_url or urljoin(url, "/robots.txt"))
    try:
        parser.read()
    except Exception:
        return False
    return bool(parser.can_fetch(USER_AGENT, url))


def descargar(url: str, timeout: float = 8.0) -> str:
    peticion = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/json"})
    with urlopen(peticion, timeout=timeout) as respuesta:
        datos = respuesta.read(MAX_BYTES)
    return datos.decode("utf-8", errors="replace")


def extraer_enlaces(contenido: str, base_url: str, limite: int = 20) -> List[Dict[str, str]]:
    resultados: List[Dict[str, str]] = []
    vistos = set()
    for href, texto in PATRON_ENLACE.findall(contenido):
        destino = urljoin(base_url, html_lib.unescape(href))
        if destino in vistos or not any(p in destino.lower() for p in PALABRAS_ANUNCIO):
            continue
        titulo = re.sub(r"\s+", " ", html_lib.unescape(PATRON_TEXTO.sub(" ", texto))).strip()
        if not titulo:
            continue
        vistos.add(destino)
        resultados.append({"titulo": titulo[:180], "url": destino})
        if len(resultados) >= limite:
            break
    return resultados


def consultar(
    web: Dict[str, Any],
    provincia: Optional[str] = None,
    localidad: Optional[str] = None,
    calle: Optional[str] = None,
    timeout: float = 8.0,
    limite: int = 20,
) -> Dict[str, Any]:
    url = construir_url(web, provincia, localidad, calle)
    resultado: Dict[str, Any] = {
        "web": web.get("id"),
        "url": url,
        "permitido_por_robots": None,
        "resultados": [],
        "error": None,
    }
    if not url.startswith(("http://", "https://")):
        resultado["error"] = "La web no tiene una URL de búsqueda configurada"
        return resultado
    try:
        resultado["permitido_por_robots"] = robots_permite(
            url, web.get("robots"), timeout=timeout
        )
        if not resultado["permitido_por_robots"]:
            resultado["error"] = "robots.txt no permite esta consulta; no se ha descargado nada"
            return resultado
        contenido = descargar(url, timeout=timeout)
        resultado["resultados"] = extraer_enlaces(contenido, url, limite=limite)
    except Exception as exc:  # red,TimeoutError,HTTPError, etc.
        resultado["error"] = f"{type(exc).__name__}: {exc}"
    return resultado
