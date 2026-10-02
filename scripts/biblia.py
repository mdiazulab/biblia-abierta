"""Citas bíblicas: una sola forma en todo el libro y control de que existan.

Regla del usuario (30-09-2026): en todo libro de teología o Biblia, revisión final de
todas las citas bíblicas para que sean consistentes. Errores reales que lo motivaron
(Ware): «17 Cor. 6:9» (el «II» en cursiva leído «17»), «1 Corintios» por «I Corintios»,
«I Tesalonicenses 6:19-20» (tiene 5 capítulos), «Salmos 31:6» por 82:6.

Forma única: ⸢[ordinal romano] [San] Libro⸣ cap:vers[-vers] — libro con su nombre
completo y en cursiva (como el impreso), números en arábigos y sin espacios.
Las formas en prosa («la Segunda Carta a los Corintios 6:14-15») conservan la prosa y
solo se normalizan los números.
"""
import re

# nombre -> (capítulos, abreviaturas). Numeración de capítulos de las Biblias en castellano.
LIBROS = {
    "Génesis": (50, "Gn Gén Gen"), "Éxodo": (40, "Ex Éx"), "Levítico": (27, "Lv Lev"), "Números": (36, "Nm Núm"),
    "Deuteronomio": (34, "Dt Deut"), "Josué": (24, "Jos"), "Jueces": (21, "Jue"), "Rut": (4, ""),
    "Samuel": (31, "Sam S"), "Reyes": (25, "Re Rey"), "Crónicas": (36, "Cr Crón"), "Esdras": (10, "Esd"),
    "Nehemías": (13, "Neh"), "Tobías": (14, "Tob Tobit"), "Judit": (16, "Jdt Judith"), "Ester": (10, "Est"),
    "Macabeos": (16, "Mac"), "Job": (42, "Jb"), "Salmos": (150, "Sal Salmo"), "Proverbios": (31, "Prov Pr"),
    "Eclesiastés": (12, "Ecl Qo"), "Cantar de los Cantares": (8, "Cant Ct"), "Sabiduría": (19, "Sab Sb"),
    "Eclesiástico": (51, "Eclo Sir Sirach Sirácida"), "Isaías": (66, "Is Isa"), "Jeremías": (52, "Jer Jr"),
    "Lamentaciones": (5, "Lam"), "Baruc": (6, "Bar Baruch"), "Ezequiel": (48, "Ez Ezeq"), "Daniel": (14, "Dn Dan"),
    "Oseas": (14, "Os"), "Joel": (4, "Jl"), "Amós": (9, "Am"), "Abdías": (1, "Abd"), "Jonás": (4, "Jon"),
    "Miqueas": (7, "Miq"), "Nahúm": (3, "Nah"), "Habacuc": (3, "Hab"), "Sofonías": (3, "Sof"), "Ageo": (2, "Ag"),
    "Zacarías": (14, "Zac"), "Malaquías": (4, "Mal"),
    "Mateo": (28, "Mt Mat"), "Marcos": (16, "Mc Mr Marc"), "Lucas": (24, "Lc Luc"), "Juan": (21, "Jn"),
    "Hechos": (28, "Hch Hech"), "Romanos": (16, "Ro Rom Rm"), "Corintios": (16, "Cor Co"),
    "Gálatas": (6, "Gál Gal Gá Ga"), "Efesios": (6, "Ef Efe"), "Filipenses": (4, "Flp Fil"),
    "Colosenses": (4, "Col"), "Tesalonicenses": (5, "Tes Ts Tes"), "Timoteo": (6, "Tim Ti"), "Tito": (3, "Tit Tt"),
    "Filemón": (1, "Flm"), "Hebreos": (13, "Heb Hb"), "Santiago": (5, "Sant St Stg"), "Pedro": (5, "Pe Pd P"),
    "Judas": (1, "Jud"), "Apocalipsis": (22, "Ap Apoc"),
}
# capítulos por libro cuando hay I/II/III (el máximo de LIBROS vale para el más largo)
POR_ORDINAL = {("Samuel", "I"): 31, ("Samuel", "II"): 24, ("Reyes", "I"): 22, ("Reyes", "II"): 25,
               ("Crónicas", "I"): 29, ("Crónicas", "II"): 36, ("Corintios", "I"): 16, ("Corintios", "II"): 13,
               ("Tesalonicenses", "I"): 5, ("Tesalonicenses", "II"): 3, ("Timoteo", "I"): 6, ("Timoteo", "II"): 4,
               ("Pedro", "I"): 5, ("Pedro", "II"): 3, ("Juan", "I"): 5, ("Juan", "II"): 1, ("Juan", "III"): 1,
               ("Macabeos", "I"): 16, ("Macabeos", "II"): 15}
CON_ORDINAL = {"Samuel", "Reyes", "Crónicas", "Corintios", "Tesalonicenses", "Timoteo", "Pedro", "Macabeos"}
ALIAS = {}
for nombre, (_, abrev) in LIBROS.items():
    ALIAS[nombre] = nombre
    for a in abrev.split():
        ALIAS[a] = nombre
ALIAS["Cantar"] = "Cantar de los Cantares"
# abreviaturas inglesas que quedaron en la traducción de Staniloae («Lk 10.13», «Jas 3.17»)
ALIAS.update({"Gen": "Génesis", "Exod": "Éxodo", "Lev": "Levítico", "Num": "Números", "Josh": "Josué", "Judg": "Jueces",
              "Kgs": "Reyes", "Chr": "Crónicas", "Esth": "Ester", "Ps": "Salmos", "Pss": "Salmos", "Eccl": "Eclesiastés",
              "Song": "Cantar de los Cantares", "Wis": "Sabiduría", "Isa": "Isaías", "Ezek": "Ezequiel", "Hos": "Oseas",
              "Obad": "Abdías", "Mic": "Miqueas", "Zeph": "Sofonías", "Hag": "Ageo", "Zech": "Zacarías", "Matt": "Mateo",
              "Mk": "Marcos", "Lk": "Lucas", "Acts": "Hechos", "Phil": "Filipenses", "Thess": "Tesalonicenses",
              "Philem": "Filemón", "Jas": "Santiago", "Pet": "Pedro", "Rev": "Apocalipsis", "Macc": "Macabeos"})

M = r"[⸢⸣]?"
NOMBRES = "|".join(sorted((re.escape(a) for a in ALIAS), key=len, reverse=True))
# «I Corintios 3:9», «(17 Cor. 6:9)», «San Mateo 25: 41», «Efesios v, 25», «Ro. 10, 14-15», «Timoteo VI:20»
V = r"\d{1,3}(?:\s?[-–]\s?\d{1,3})?"
LV = r",\s?\d{1,3}(?:\s?[-–]\s?\d{1,3})?(?![\d\.:]|\s[A-ZÁÉÍÓÚ])"   # «13.54,58» (no «2:13, 1 Corintios», no «10:4, 13:10»)
CITA = re.compile(
    rf"(?P<pre>(?<![\w\.])(?:III|II|I|[123]|17|ll|Il|lI|l)\s+{M})?(?P<san>San\s+{M})?(?<![\wáéíóúñ])(?P<libro>{NOMBRES})(?![\wáéíóúñ])"
    rf"(?P<punto>\.?){M},?{M}\s*{M}(?P<cap>\d{{1,3}}|[ivxlcIVXLC]{{1,7}})(?![\wáéíóúñ]){M}\s?"
    # «Jn 1,18» (coma = capítulo,versículo) o «Rom 11.33» / «Rom 11:33», que admiten lista «13.54,58»
    rf"(?:(?P<sep>,)\s?{M}(?P<ver1>{V})|(?P<sep2>[:\.])\s?{M}(?P<ver>{V}(?:{LV})*))(?![\d\.]\d)"
    # cadena «1 Cor 1.24; 2.7», «Rom 10:4, 13:10», «Jn 16.7, 14.16» (capítulos del mismo libro)
    rf"(?P<cadena>(?:[;,]\s?\d{{1,3}}[:\.]\d{{1,3}}(?:\s?[-–]\s?\d{{1,3}})?(?:{LV})*(?![\d\.]\d))*)")
# referencias que no son de la Biblia aunque se parezcan («A los Efesios 20.2» de San Ignacio, homilías)
NO_BIBLICA = re.compile(r"(?:A los|Homilías sobre|Contra las Herejías|Didache|Stromateis|Carta|Tratados?)\W*(?:\[[^\]]*\]\s*)?(?:San\s+)?$")
# cartas de Padres apostólicos con el mismo nombre que las paulinas («Clemente a los Corintios 42.1»)
PATRISTICA = re.compile(r"(?:Ignacio|Clemente|Policarpo|Bernabé|Barnabas)[^.;()]{0,60}$")
ORDINAL = {"1": "I", "I": "I", "l": "I", "2": "II", "II": "II", "ll": "II", "Il": "II", "lI": "II", "17": "II",
           "3": "III", "III": "III"}


def _romano(s):
    v = {"i": 1, "v": 5, "x": 10, "l": 50, "c": 100}
    s = s.lower()
    total = 0
    for i, ch in enumerate(s):
        total += -v[ch] if i + 1 < len(s) and v[ch] < v[s[i + 1]] else v[ch]
    return total


def _versiculos(v):
    v = re.sub(r"\s", "", v).replace("–", "-")
    if "-" in v:
        a, b = v.split("-")
        if len(b) < len(a):
            b = a[:len(a) - len(b)] + b                     # «22-3» -> «22-23», «30-1» -> «30-31»
        return f"{a}-{b}"
    return v


def _balancear(t):
    """Cursivas ⸢⸣ bien anidadas después de rehacer las citas."""
    out, abierta = [], False
    for ch in t:
        if ch == "⸢":
            if abierta:
                continue
            abierta = True
        elif ch == "⸣":
            if not abierta:
                continue
            abierta = False
        out.append(ch)
    return "".join(out) + ("⸣" if abierta else "")


def normalizar(texto, problemas=None, pag=None):
    """Devuelve el texto con las citas en la forma única; anota en `problemas` las que no existen."""
    def rep(m):
        antes = re.sub(r"[⸢⸣]", "", texto[max(0, m.start() - 40):m.start()])
        if NO_BIBLICA.search(antes) or PATRISTICA.search(antes):
            return m.group(0)
        if m.group("libro") in ("Núm", "Num") and m.group("sep"):
            return m.group(0)                                # «Núm. 4, 203»: número de revista, no el libro
        libro = ALIAS[m.group("libro")]
        cap = m.group("cap")
        if not cap.isdigit():
            if not re.fullmatch(r"[ivxlc]+", cap, re.I):
                return m.group(0)
            cap = str(_romano(cap))
        pre = m.group("pre")
        ordinal = ORDINAL.get(pre.strip().strip("⸢⸣").strip()) if pre else None
        if pre and not ordinal:
            return m.group(0)
        if ordinal and libro not in CON_ORDINAL | {"Juan"}:
            return m.group(0)                                # «1 Juan» sí; «3 Mateo» no es una cita
        maximo = POR_ORDINAL.get((libro, ordinal), LIBROS[libro][0])
        if problemas is not None and not (1 <= int(cap) <= maximo):
            problemas.append((pag, f"{ordinal + ' ' if ordinal else ''}{libro} {cap}: el libro tiene {maximo} capítulos"))
        if libro == "Pedro" and m.group("libro") == "P" and not ordinal:
            return m.group(0)                                # «P.» solo es Pedro con ordinal («1 P 2:9»)
        ver = ", ".join(_versiculos(x) for x in re.split(r",\s?", m.group("ver") or m.group("ver1")))
        cadena = "".join(f"; {c}:{_versiculos(v)}" for c, v in re.findall(r"(\d{1,3})[:\.](\d{1,3}(?:\s?[-–]\s?\d{1,3})?(?:,\s?\d{1,3}(?:-\d{1,3})?)*)", m.group("cadena") or ""))
        # prosa («Segunda Carta a los Corintios 6:14-15»): solo los números
        prosa = re.search(r"(?:Carta|Epístola)\s+(?:de\s+San\s+|a\s+los\s+)$", antes)
        if prosa:
            return m.group(0)[:m.start("libro") - m.start()] + m.group("libro") + "⸣" * ("⸣" in m.group(0)) + f" {cap}:{ver}{cadena}"
        if libro == "Reyes" and ordinal in ("III", "IV"):
            ordinal = {"III": "I", "IV": "II"}[ordinal]      # numeración griega (LXX): 3 Reyes = I Reyes
        nombre = (ordinal + " " if ordinal else "") + ("San " if m.group("san") else "") + libro
        return f"⸢{nombre}⸣ {cap}:{ver}{cadena}"
    t = CITA.sub(rep, texto)
    # «(⸢I Corintios⸣…» y no «⸢(I Corintios⸣…»: el paréntesis queda fuera de la cursiva; «⸣⸢» sobrante fuera
    t = re.sub(r"⸢([\(\[])⸢?", r"\1⸢", t)
    t = re.sub(r"⸢⸢", "⸢", t)
    return re.sub(r"⸢⸣", "", _balancear(t))


def citas(texto):
    """Citas bíblicas del texto (para el control de calidad)."""
    return [m.group(0) for m in CITA.finditer(texto)]
