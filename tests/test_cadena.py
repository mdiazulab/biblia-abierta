"""Pruebas sin red (modelo falso): cada caso es una regla que ya importó."""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import anclar as A          # noqa: E402
import biblia as B          # noqa: E402
import comun as C           # noqa: E402
import juez as J            # noqa: E402
import verificar as V       # noqa: E402


class Anclaje(unittest.TestCase):
    rv = C.cargar("normalizado/rv1909/JHN.json")

    def tramo(self, lema, ref):
        return A.mejor_tramo(lema, [(ref, self.rv[ref]["texto"])])[0]

    def test_lema_literal(self):
        self.assertEqual(self.tramo("En el principio", "JHN.1.1"), "En el principio")
        self.assertEqual(self.tramo("el Cordero de Dios", "JHN.1.29"), "el Cordero de Dios")

    def test_lema_nlt_distinto_va_al_versiculo(self):
        """«las tinieblas no la han vencido» (NLT) no calza con «no la comprendieron» (RV1909)."""
        self.assertIsNone(self.tramo("las tinieblas no la han vencido", "JHN.1.5"))


class Bateria(unittest.TestCase):
    def test_ordinal_romano_cuenta_como_numero(self):
        self.assertEqual(V.numeros("1 Corinthians 13:4"), V.numeros("I Corintios 13:4"))

    def test_cita_biblica_forma_unica(self):
        self.assertEqual(B.normalizar("(Juan 1:3)"), "(⸢Juan⸣ 1:3)")

    def test_rv1909_texto(self):
        rv = C.cargar("normalizado/rv1909/JHN.json")
        self.assertEqual(len(rv), 879)
        self.assertTrue(rv["JHN.1.1"]["texto"].startswith("En el principio era el Verbo"))
        self.assertIn("fue hecho carne", rv["JHN.1.14"]["texto"])
        self.assertIn("fué hecho carne", rv["JHN.1.14"]["texto_1909"])


class Compuerta(unittest.TestCase):
    # clases halladas en la corrida del capítulo 1 (02-10-2026)
    def test_libros_ingleses_a_forma_unica(self):
        self.assertEqual(B.normalizar("(John 5:26) (Exod. 7:1) (1 Ped. 2:9)"),
                         "(⸢Juan⸣ 5:26) (⸢Éxodo⸣ 7:1) (⸢I Pedro⸣ 2:9)")

    def test_llamada_de_nota_pegada(self):
        import traducir as T
        self.assertEqual(T.limpiar("en el Señor1. (Ef. 5:8) y vida1, c. 15"), "en el Señor. (Ef. 5:8) y vida, c. 15")

    def test_tildes_obsoletas(self):
        import rv1909 as R
        par = {"éste": "este", "Aquél": "Aquel", "Respondióles": "Respondioles", "fuése": "fuese", "dínos": "dinos",
               "dióselo": "dióselo", "Judíos": "Judíos", "ríos": "ríos", "José": "José", "Melchîsedec": "Melchisedec", "Sichâr": "Sichar"}
        self.assertEqual({w: R._sin_tilde(w) for w in par}, par)

    # clases de la corrida completa de Juan (02-10-2026)
    def test_yo_soy_no_es_numero(self):
        self.assertEqual(V.numeros("Before Abraham was, I Am."), V.numeros("Antes que Abraham fuese, Yo soy."))
        self.assertEqual(V.numeros("I Corinthians 13:4"), V.numeros("1 Corintios 13:4"))

    def test_palabra_mayuscula(self):
        self.assertTrue(V.PALABRA_MAY.search("Sí, pero Él es la Palabra del Padre."))
        self.assertFalse(V.PALABRA_MAY.search("Palabra fiel es esta. «Palabra de Dios»"))
        self.assertTrue(V.CRISTO_EN.search("Yea, but He is the Word of the Father."))
        self.assertFalse(V.CRISTO_EN.search("having now sown the Word of salvation"))

    def test_oraciones_sin_abreviaturas(self):
        self.assertEqual(V.oraciones("I will see you, i. e. I will take you (in Joan. tom. vi. c. 15). Or thus."), 2)

    def test_sensibles_por_libro(self):
        self.assertTrue(C.es_sensible({"ref": "HEB.2.10"}))
        self.assertFalse(C.es_sensible({"ref": "JHN.2.10"}))          # mismo cap:vers, otro libro
        self.assertTrue(C.es_sensible({"ref": "JHN.6.50", "ref_fin": "JHN.6.52"}))

    def test_vocabulario_rv1909(self):
        import traducir as T
        self.assertEqual(T.limpiar("El sumo sacerdote y los sumos sacerdotes, según Melquisedec."),
                         "El pontífice y los pontífices, según Melchisedec.")

    def test_errata_y_tildes_rv1909(self):
        import rv1909 as R
        self.assertEqual(R.errata("HEB.12.2", "Puestos los ojos en al autor"), "Puestos los ojos en el autor")
        self.assertEqual(R.ACENTOS["oir"], "oír")

    def test_json_mal_formado_no_descarta_el_modelo(self):
        import os, requests
        respuestas = iter(['{"notas": [{"id": "a",, }]}', '{"notas": []}'])
        orig, falso, dormir = C._deepseek, os.environ.pop("MODELO_FALSO", None), C.time.sleep
        os.environ["DEEPSEEK_API_KEY"] = "x"
        C._deepseek = lambda *a: next(respuestas)
        C.time.sleep = lambda s: None
        try:
            self.assertEqual(C.llamar("p", ["deepseek:prueba"])[0], {"notas": []})
            self.assertNotIn("deepseek:prueba", C._CAIDOS)
            def sin_permiso(*a):
                r = requests.Response(); r.status_code = 404
                raise requests.HTTPError("404 Not Found", response=r)
            C._deepseek = sin_permiso
            with self.assertRaises(RuntimeError):
                C.llamar("p", ["deepseek:prueba"])
            self.assertIn("deepseek:prueba", C._CAIDOS)
        finally:
            C._deepseek = orig; C.time.sleep = dormir; C._CAIDOS.clear(); os.environ.pop("DEEPSEEK_API_KEY", None)
            if falso is not None:
                os.environ["MODELO_FALSO"] = falso

    def test_wilson(self):
        self.assertLess(J.wilson_sup(0, 200), 0.02)
        self.assertGreater(J.wilson_sup(5, 100), 0.03)

    def test_error_sembrado_cambia_el_texto(self):
        import random
        m, tipo = J.sembrar("Jesús es el Verbo. Vino en el año 30. Fue enviado.", random.Random(1))
        self.assertIsNotNone(m)
        self.assertNotEqual(m, "Jesús es el Verbo. Vino en el año 30. Fue enviado.")


if __name__ == "__main__":
    unittest.main()
