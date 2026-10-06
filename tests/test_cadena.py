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

    def test_clases_hebreos_06_10(self):
        import rv1909 as R
        self.assertEqual(B.normalizar("(Judas 19) (Hageo 2:6)"), "(⸢Judas⸣ 1:19) (⸢Ageo⸣ 2:6)")
        self.assertEqual(V.numeros("(Luke xxii. 19.)"), V.numeros("(Lucas 22:19)"))
        self.assertEqual(R._sin_tilde("constituído"), "constituido")

    def test_alias_apuntan_a_libros(self):
        self.assertEqual({k: v for k, v in B.ALIAS.items() if v not in B.LIBROS}, {})

    def test_comillas_espanolas(self):
        import traducir as T
        self.assertEqual(T.comillas('"Por tanto" (dice) "también nosotros". ...\"Aprendió", dice.'),
                         '«Por tanto» (dice) «también nosotros». ...«Aprendió», dice.')
        self.assertEqual(T.comillas('«Él dijo: "sí"» y "no"'), '«Él dijo: “sí”» y «no»')

    def test_titulos_de_obras(self):
        import epub as E
        self.assertEqual(E.obra_es("Homily on Hebrews 13"), "Homilías sobre la Epístola a los Hebreos 13")
        self.assertEqual(E.obra_es("The Divine Institutes Book 4, Chapter XI"), "Instituciones divinas libro 4, cap. XI")

    def test_wilson(self):
        self.assertLess(J.wilson_sup(0, 200), 0.02)
        self.assertGreater(J.wilson_sup(5, 100), 0.03)

    def test_error_sembrado_cambia_el_texto(self):
        import random
        m, tipo = J.sembrar("Jesús es el Verbo. Vino en el año 30. Fue enviado.", random.Random(1))
        self.assertIsNotNone(m)
        self.assertNotEqual(m, "Jesús es el Verbo. Vino en el año 30. Fue enviado.")

    def test_word_of_god_escritura_no_es_el_hijo(self):
        # Calvino (Owen) 10:37: «his watchtower was the Word of God» es la Escritura; «was the Word» sigue siendo el Hijo
        self.assertIsNone(V.CRISTO_EN.search("and his watchtower was the Word of God, by which he was raised"))
        self.assertIsNotNone(V.CRISTO_EN.search("In the beginning was the Word, and the Word was with God"))

    def test_solo_deepseek_sin_rejuzgar_lo_aprobado(self):
        self.assertTrue(all(m.startswith("deepseek:") for m in C.TRADUCTOR + C.CONTROL))
        self.assertIn("gemini-3.6-flash", C.JUECES_VALIDOS)          # Juan 1-8: veredictos calibrados, no se rehacen
        self.assertNotIn("gemini-3.1-flash-lite", C.JUECES_VALIDOS)  # retirado por baja sensibilidad


class Griego(unittest.TestCase):
    """Notas de unfoldingWord: fuera lo dirigido al traductor, sin romper las listas de lecturas posibles."""

    def test_quita_indicaciones_al_traductor(self):
        import griego as G
        t = G.limpiar("The word ⸢approach⸣ refers implicitly to getting close to something. This means that they enter "
                      "into God’s presence. If it would be helpful in your language, you could use a word that refers to "
                      "being in someone’s presence. Alternate translation: [the ones going before God]")
        self.assertNotIn("your", t)
        self.assertNotIn("going before", t)            # paráfrasis fuera de una lista de opciones: se quita
        self.assertIn("God’s presence", t)

    def test_conserva_opciones_con_parafrasis(self):
        import griego as G
        t = G.limpiar("The phrase ⸢yourselves also⸣ could refer to: (1) the audience. Alternate translation: "
                      "[also you yourselves]; (2) the ones being mistreated. Alternate translation: [they also being]")
        self.assertIn("(2) the ones being mistreated", t)   # el «you» de la paráfrasis no borra la opción
        self.assertIn("«also you yourselves»", t)

    def test_lista_rota_descarta_la_nota(self):
        import griego as G
        self.assertIsNone(G.limpiar("It could mean: (1) something that you could say. (2) another thing entirely here."))

    def test_nota_sin_frase_griega(self):
        import griego as G                             # 11:5 (Enoc): nota sobre el versículo entero
        x = {"content": "<p>The author refers to a story about a man named <strong>Enoch</strong>.</p>"
                        '<p>See: <data class="resource-ref" data-resource-code="UWTranslationManual">Background Information</data></p>'}
        self.assertEqual(G.nota(x)[:2], (None, None))

    def test_introduccion_por_secciones(self):
        import griego_completo as GC
        s = GC.secciones("<h1>Intro</h1><h2>Part 1</h2><h3>Outline</h3><p>Text.</p><ul><li>A<ul><li>B</li></ul></li></ul>"
                         "<h3>Who wrote it?</h3><p>Nobody knows.</p>")
        self.assertEqual([[n for n, _ in t] for t, _ in s], [[2, 3], [3]])     # títulos sin cuerpo van con el siguiente
        self.assertEqual(s[0][1], ["Text.", "• A", "◦ B"])

    def test_categorias_con_nombre_espanol(self):
        import griego_completo as GC
        import json
        ruta = C.RAIZ / "normalizado" / "HEB" / "griego_completo.json"
        if ruta.exists():
            cats = {n["categoria"] for n in json.loads(ruta.read_text()) if n.get("categoria")}
            self.assertFalse(cats - set(GC.CATEGORIAS))


if __name__ == "__main__":
    unittest.main()
