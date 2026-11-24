"""Pruebas automáticas: se ejecutan con 'python3 -m unittest discover -s tests -v'."""

from __future__ import annotations

import csv
import io
import json
import shutil
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

from pisos_fincas import cli, core, web

RAIZ = Path(__file__).resolve().parent.parent
DATOS = RAIZ / "data" / "pisos.json"
WEBS = RAIZ / "data" / "webs.json"


class TestNormalizacion(unittest.TestCase):
    def test_normalizar_quita_acentos(self):
        self.assertEqual(core.normalizar("Alcalá de Henares"), "alcala de henares")

    def test_limpiar_calle_ignora_tipo_y_numero(self):
        self.assertEqual(core.limpiar_calle("Calle Mayor, 12"), "mayor")
        self.assertEqual(core.limpiar_calle("c/ Mallorca, 5"), "mallorca")

    def test_slug(self):
        self.assertEqual(core.slug("Alcalá de Henares"), "alcala-de-henares")


class TestBusqueda(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.listados = core.cargar_listados(DATOS)

    def test_buscar_por_provincia(self):
        resultados = core.buscar(self.listados, provincia="Madrid")
        self.assertEqual(len(resultados), 8)

    def test_buscar_por_localidad_y_calle(self):
        resultados = core.buscar(
            self.listados, localidad="Alcalá de Henares", calle="Calle Mayor"
        )
        self.assertEqual(sorted(i["id"] for i in resultados), ["p001", "p002", "p003", "p018"])

    def test_buscar_sin_acentos_y_parcial(self):
        resultados = core.buscar(self.listados, provincia="malaga", calle="larios")
        self.assertEqual([i["id"] for i in resultados], ["p014"])

    def test_buscar_con_operacion_y_precio(self):
        resultados = core.buscar(
            self.listados, provincia="Madrid", operacion="alquiler", precio_max=1000
        )
        self.assertEqual([i["id"] for i in resultados], ["p003"])

    def test_orden_por_m2(self):
        resultados = core.buscar(self.listados, localidad="Barcelona", orden="m2")
        self.assertEqual(resultados[0]["id"], "p009")

    def test_sin_resultados(self):
        self.assertEqual(core.buscar(self.listados, calle="NoExiste"), [])


class TestAltas(unittest.TestCase):
    def setUp(self):
        self.temporal = tempfile.TemporaryDirectory()
        self.ruta = Path(self.temporal.name) / "pisos.json"
        shutil.copy(DATOS, self.ruta)

    def tearDown(self):
        self.temporal.cleanup()

    def test_anadir_y_consultar(self):
        core.anadir(
            self.ruta,
            {},
            "Madrid",
            "Getafe",
            "Calle Nueva, 1",
            precio=123000,
            portal="manual",
        )
        resultados = core.buscar(core.cargar_listados(self.ruta), calle="Nueva")
        self.assertEqual(len(resultados), 1)
        self.assertEqual(resultados[0]["id"], "p019")

    def test_anadir_rechaza_id_duplicado(self):
        core.anadir(self.ruta, {}, "Madrid", "Getafe", "Calle Nueva, 1", id="p100")
        with self.assertRaises(ValueError):
            core.anadir(self.ruta, {}, "Madrid", "Getafe", "Calle Otra, 2", id="p100")

    def test_anadir_requiere_campos(self):
        with self.assertRaises(ValueError):
            core.anadir(self.ruta, {}, "", "Getafe", "Calle Nueva, 1")


class TestWebs(unittest.TestCase):
    def test_cargar_catalogo(self):
        self.assertGreaterEqual(len(web.cargar_webs(WEBS)), 5)

    def test_url_con_localidad_y_calle(self):
        portal = next(w for w in web.cargar_webs(WEBS) if w["id"] == "demo-local")
        url = core.construir_url(portal, "Madrid", "Alcalá de Henares", "Calle Mayor")
        self.assertIn("alcala-de-henares", url)
        self.assertIn("calle-mayor", url)

    def test_url_sin_barras_duplicadas(self):
        portal = next(w for w in web.cargar_webs(WEBS) if w["id"] == "idealista")
        url = core.construir_url(portal, localidad="Valencia", calle="Colon")
        self.assertNotIn("//", url.replace("https://", "").replace("http://", ""))

    def test_url_encodeda_cuando_no_hay_slug(self):
        portal = next(w for w in web.cargar_webs(WEBS) if w["id"] == "milanuncios")
        url = core.construir_url(portal, localidad="Alcalá de Henares", calle="Mayor")
        self.assertIn("alcala%20de%20henares", url)
        self.assertIn("mayor", url)


class TestCli(unittest.TestCase):
    def test_listar_json(self):
        salida = io.StringIO()
        with redirect_stdout(salida):
            codigo = cli.main(
                [
                    "--datos", str(DATOS), "--webs", str(WEBS),
                    "list", "--localidad", "Alcalá de Henares", "--calle", "Mayor",
                    "--formato", "json",
                ]
            )
        self.assertEqual(codigo, 0)
        self.assertEqual(sorted(i["id"] for i in json.loads(salida.getvalue())), ["p001", "p002", "p003", "p018"])

    def test_listar_csv(self):
        salida = io.StringIO()
        with redirect_stdout(salida):
            cli.main(["--datos", str(DATOS), "--webs", str(WEBS), "list", "--calle", "larios", "--formato", "csv"])
        filas = list(csv.DictReader(io.StringIO(salida.getvalue())))
        self.assertEqual([f["id"] for f in filas], ["p014"])

    def test_webs_tabla(self):
        salida = io.StringIO()
        with redirect_stdout(salida):
            cli.main(["--webs", str(WEBS), "webs", "--localidad", "Valencia", "--calle", "Colón"])
        texto = salida.getvalue()
        self.assertIn("Idealista", texto)
        self.assertIn("valencia", texto)

    def test_fetch_requiere_autorizacion(self):
        error = io.StringIO()
        with redirect_stdout(io.StringIO()), mock.patch("sys.stderr", error):
            codigo = cli.main(["--webs", str(WEBS), "fetch", "--web", "demo-local"])
        self.assertEqual(codigo, 2)
        self.assertIn("--allow-network", error.getvalue())

    def test_stats_json(self):
        salida = io.StringIO()
        with redirect_stdout(salida):
            cli.main(["--datos", str(DATOS), "--webs", str(WEBS), "stats", "--formato", "json"])
        self.assertEqual(json.loads(salida.getvalue())["total"], 18)


if __name__ == "__main__":
    unittest.main()
