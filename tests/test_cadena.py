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
               "dióselo": "dióselo", "Judíos": "Judíos", "ríos": "ríos", "José": "José"}
        self.assertEqual({w: R._sin_tilde(w) for w in par}, par)

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
