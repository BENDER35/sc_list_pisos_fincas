"""Interfaz de línea de comandos de sc-list-pisos-fincas."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from . import core, web
from .version import __version__

DESCRIPCION = (
    "Lista pisos y fincas guardados localmente filtrando por provincia, localidad y calle, "
    "y muestra enlaces de búsqueda de los portales configurados."
)


def construir_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pisos-fincas",
        description=DESCRIPCION,
        epilog=(
            "Ejemplo: pisos-fincas list --provincia Madrid --localidad 'Alcalá de Henares' "
            "--calle Mayor"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--datos", type=Path, default=None, help="Ruta al JSON de anuncios")
    parser.add_argument("--webs", type=Path, default=None, help="Ruta al JSON de portales")
    parser.add_argument("--version", action="version", version=f"pisos-fincas {__version__}")

    sub = parser.add_subparsers(dest="comando", metavar="COMANDO")
    sub.required = True

    listado = sub.add_parser("list", aliases=["search", "buscar"], help="Listar anuncios filtrados")
    _anadir_filtros(listado)
    listado.add_argument("--portal", help="Filtrar por portal (búsqueda parcial)")
    listado.add_argument("--operacion", choices=["venta", "alquiler"], help="Tipo de operación")
    listado.add_argument("--precio-max", type=float, help="Precio máximo")
    listado.add_argument("--m2-min", type=float, help="Superficie mínima en m²")
    listado.add_argument("--orden", choices=["precio", "m2", "localidad"], default="precio")
    listado.add_argument("--formato", choices=["tabla", "json", "csv"], default="tabla")
    listado.set_defaults(funcion=comando_listar)

    alta = sub.add_parser("add", aliases=["anadir"], help="Añadir un anuncio al JSON local")
    alta.add_argument("--provincia", required=True)
    alta.add_argument("--localidad", required=True)
    alta.add_argument("--calle", required=True)
    alta.add_argument("--portal", default="manual")
    alta.add_argument("--operacion", default="venta", choices=["venta", "alquiler"])
    alta.add_argument("--precio", type=float)
    alta.add_argument("--habitaciones", type=int)
    alta.add_argument("--m2", type=float)
    alta.add_argument("--url", default="")
    alta.add_argument("--fecha", default="")
    alta.add_argument("--notas", default="")
    alta.add_argument("--id", dest="identificador")
    alta.add_argument("--formato", choices=["tabla", "json"], default="tabla")
    alta.set_defaults(funcion=comando_anadir)

    portales = sub.add_parser("webs", aliases=["urls"], help="Mostrar webs y sus URLs de búsqueda")
    _anadir_filtros(portales)
    portales.add_argument("--formato", choices=["tabla", "json"], default="tabla")
    portales.set_defaults(funcion=comando_webs)

    stats = sub.add_parser("stats", aliases=["estadisticas"], help="Resumen del catálogo local")
    stats.add_argument("--formato", choices=["tabla", "json"], default="tabla")
    stats.set_defaults(funcion=comando_estadisticas)

    consulta = sub.add_parser("fetch", help="Consultar un portal (requiere --allow-network)")
    consulta.add_argument("--web", required=True, help="Identificador de data/webs.json")
    _anadir_filtros(consulta)
    consulta.add_argument("--allow-network", action="store_true", help="Autorizar acceso a Internet")
    consulta.add_argument("--timeout", type=float, default=8.0)
    consulta.add_argument("--limite", type=int, default=20)
    consulta.add_argument("--formato", choices=["tabla", "json"], default="tabla")
    consulta.set_defaults(funcion=comando_fetch)

    return parser


def _anadir_filtros(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--provincia", help="Provincia (búsqueda parcial, sin acentos)")
    parser.add_argument("--localidad", help="Localidad (búsqueda parcial, sin acentos)")
    parser.add_argument("--calle", help="Calle (búsqueda parcial; admite 'Calle Mayor, 12')")


def _rutas(args: argparse.Namespace) -> tuple[Path, Path]:
    datos = args.datos or core.ruta_por_defecto("data/pisos.json")
    portales = args.webs or core.ruta_por_defecto("data/webs.json")
    return datos, portales


def comando_listar(args: argparse.Namespace, datos: Path, portales: Path) -> int:
    resultados = core.buscar(
        core.cargar_listados(datos),
        provincia=args.provincia,
        localidad=args.localidad,
        calle=args.calle,
        portal=args.portal,
        operacion=args.operacion,
        precio_max=args.precio_max,
        m2_min=args.m2_min,
        orden=args.orden,
    )
    if args.formato == "json":
        print(json.dumps(resultados, ensure_ascii=False, indent=2))
    elif args.formato == "csv":
        print(core.csv_texto(resultados), end="")
    else:
        print(core.tabla(resultados))
    return 0


def comando_anadir(args: argparse.Namespace, datos: Path, portales: Path) -> int:
    anuncio = core.anadir(
        datos,
        {},
        args.provincia,
        args.localidad,
        args.calle,
        portal=args.portal,
        operacion=args.operacion,
        precio=args.precio,
        habitaciones=args.habitaciones,
        m2=args.m2,
        url=args.url,
        fecha=args.fecha,
        notas=args.notas,
        id=args.identificador,
    )
    if args.formato == "json":
        print(json.dumps(anuncio, ensure_ascii=False, indent=2))
    else:
        print(f"Añadido {anuncio['id']}: {anuncio['localidad']} — {anuncio['calle']} ({datos})")
    return 0


def comando_webs(args: argparse.Namespace, datos: Path, portales: Path) -> int:
    lista = web.filtrar_webs(
        web.cargar_webs(portales), args.provincia, args.localidad, args.calle
    )
    filas = [
        {
            "id": item.get("id", ""),
            "nombre": item.get("nombre", ""),
            "tipo": item.get("tipo", ""),
            "cobertura": item.get("cobertura", ""),
            "url": core.construir_url(item, args.provincia, args.localidad, args.calle),
            "nota": item.get("nota", ""),
        }
        for item in lista
    ]
    if args.formato == "json":
        print(json.dumps(filas, ensure_ascii=False, indent=2))
    else:
        for fila in filas:
            print(f"{fila['nombre']} [{fila['id']}]\n  {fila['url']}")
    return 0


def comando_estadisticas(args: argparse.Namespace, datos: Path, portales: Path) -> int:
    resumen = core.estadisticas(core.cargar_listados(datos))
    if args.formato == "json":
        print(json.dumps(resumen, ensure_ascii=False, indent=2))
    else:
        print(f"Anuncios: {resumen['total']}")
        for titulo, clave in (
            ("Provincias", "por_provincia"),
            ("Localidades", "por_localidad"),
            ("Portales", "por_portal"),
            ("Operaciones", "por_operacion"),
        ):
            print(f"\n{titulo}:")
            for nombre, cantidad in resumen[clave].items():
                print(f"  {nombre or '(sin dato)'}: {cantidad}")
    return 0


def comando_fetch(args: argparse.Namespace, datos: Path, portales: Path) -> int:
    if not args.allow_network:
        print(
            "Esta orden consulta Internet. Añade --allow-network tras revisar robots.txt "
            "y las condiciones de uso del portal.",
            file=sys.stderr,
        )
        return 2
    webs = {item.get("id"): item for item in web.cargar_webs(portales)}
    if args.web not in webs:
        print(f"Web desconocida: {args.web}. Usa 'pisos-fincas webs' para ver los ids.", file=sys.stderr)
        return 2
    resultado = web.consultar(
        webs[args.web],
        provincia=args.provincia,
        localidad=args.localidad,
        calle=args.calle,
        timeout=args.timeout,
        limite=args.limite,
    )
    if args.formato == "json":
        print(json.dumps(resultado, ensure_ascii=False, indent=2))
    else:
        print(f"URL: {resultado['url']}")
        if resultado["error"]:
            print(f"Aviso: {resultado['error']}")
        if resultado["resultados"]:
            for enlace in resultado["resultados"]:
                print(f"- {enlace['titulo']}\n  {enlace['url']}")
        else:
            print("No se han extraído anuncios (los portales pueden usar JavaScript).")
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = construir_parser()
    args = parser.parse_args(argv)
    datos, portales = _rutas(args)
    try:
        return int(args.funcion(args, datos, portales))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
