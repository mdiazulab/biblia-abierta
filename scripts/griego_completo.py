#!/usr/bin/env python3
"""Volumen complementario «El texto griego explicado»: TODAS las notas de unfoldingWord® Translation Notes de un
libro, con las indicaciones para traductores incluidas (a quien no lee griego le muestran el razonamiento: qué
figura hay, qué queda implícito, cómo se puede decir de otro modo), más las introducciones al libro y a cada
capítulo y un glosario con la «Descripción» de cada categoría de unfoldingWord® Translation Academy.

La Biblia de estudio usa solo la selección de griego.py (capa G); este volumen es una obra aparte.

Unidades (normalizado/<LIBRO>/griego_completo.json):
- layer "griego_c": una por nota de versículo (frase griega aparte, glosa de la ULT como lema, categoría);
- layer "griego_intro": una por sección de la introducción al libro (capitulo 0) o a un capítulo;
- layer "glosario_g": una por categoría citada (solo la sección «Description» del artículo).

Uso: python3 scripts/griego_completo.py HEB
"""
import html
import json
import re
import sys

import comun as C
from aquifer import osis
from griego import nota
from libros import LIBROS

# nombres españoles de las categorías de unfoldingWord® Translation Academy (para el rótulo de cada nota)
CATEGORIAS = {
    "Abstract Nouns": "Sustantivos abstractos", "Active or Passive": "Voz activa o pasiva",
    "Assumed Knowledge and Implicit Information": "Conocimiento supuesto e información implícita",
    "Background Information": "Información de trasfondo", "Biblical Imagery — Extended Metaphors": "Imágenes bíblicas: metáforas extendidas",
    "Blessings": "Bendiciones", "Collective Nouns": "Sustantivos colectivos",
    "Connect — Background Information": "Conexión: información de trasfondo",
    "Connect — Contrary to Fact Conditions": "Conexión: condiciones contrarias a los hechos",
    "Connect — Contrast Relationship": "Conexión: relación de contraste", "Connect — Factual Conditions": "Conexión: condiciones reales",
    "Connect — Hypothetical Conditions": "Conexión: condiciones hipotéticas",
    "Connect — Reason-and-Result Relationship": "Conexión: causa y efecto",
    "Connect — Sequential Time Relationship": "Conexión: sucesión temporal",
    "Connect — Simultaneous Time Relationship": "Conexión: simultaneidad", "Connecting Words and Phrases": "Palabras y frases de enlace",
    "Copy or Borrow Words": "Copiar o tomar prestadas palabras",
    "Distinguishing Versus Informing or Reminding": "Distinguir frente a informar o recordar",
    "Double Negatives": "Doble negación", "Doublet": "Doblete", "Ellipsis": "Elipsis", "Euphemism": "Eufemismo",
    "Exclamations": "Exclamaciones", "Exclusive and Inclusive ‘We’": "«Nosotros» exclusivo e inclusivo",
    "First, Second or Third Person": "Primera, segunda o tercera persona", "Forms of ‘You’ — Singular": "Formas de «tú»: singular",
    "Generic Noun Phrases": "Frases nominales genéricas", "Go and Come": "Ir y venir", "Hendiadys": "Endíadis",
    "How to Translate Names": "Cómo traducir los nombres", "Hyperbole": "Hipérbole", "Idiom": "Modismo",
    "Imperatives — Other Uses": "Imperativos: otros usos", "Information Structure": "Estructura de la información",
    "Kinship": "Parentesco", "Litotes": "Litote", "Merism": "Merismo", "Metaphor": "Metáfora", "Metonymy": "Metonimia",
    "Nominal Adjectives": "Adjetivos sustantivados", "Numbers": "Números", "Oath Formulas": "Fórmulas de juramento",
    "Ordinal Numbers": "Números ordinales", "Parallelism": "Paralelismo", "Personification": "Personificación",
    "Possession": "Posesión", "Predictive Past": "Pasado profético", "Pronouns — When to Use Them": "Pronombres: cuándo usarlos",
    "Quotations and Quote Margins": "Citas y fórmulas de cita", "Quote Markings": "Marcas de cita",
    "Quotes within Quotes": "Citas dentro de citas", "Reflexive Pronouns": "Pronombres reflexivos",
    "Rhetorical Question": "Pregunta retórica", "Simile": "Símil", "Symbolic Action": "Acción simbólica",
    "Synecdoche": "Sinécdoque", "Textual Variants": "Variantes textuales", "Third-Person Imperatives": "Imperativos de tercera persona",
    "Translate Unknowns": "Traducir lo desconocido", "Translating Son and Father": "Traducir «Hijo» y «Padre»",
    "Verse Bridges": "Puentes de versículos", "When Masculine Words Include Women": "Cuando las palabras masculinas incluyen a mujeres",
    "When to Keep Information Implicit": "Cuándo dejar implícita la información",
}


def texto_html(h):
    """HTML de unfoldingWord -> párrafos separados por línea en blanco; negrita -> ⸢…⸣; ítems de lista con «• »."""
    marcas, prof, partes = "•◦▪", 0, []
    for t in re.split(r"(</?(?:ul|ol)>|<li>)", h):          # viñeta según la profundidad (esquema del libro)
        if t in ("<ul>", "<ol>"):
            prof += 1
        elif t in ("</ul>", "</ol>"):
            prof = max(0, prof - 1)
        elif t == "<li>":
            t = "\n\n" + marcas[min(max(prof, 1), 3) - 1] + " "
        partes.append(t)
    h = "".join(partes)
    h = re.sub(r"</?(?:p|ul|ol|li|h\d)>", "\n\n", h)
    h = re.sub(r"<strong>(.*?)</strong>", lambda m: "⸢" + m.group(1) + "⸣", h, flags=re.S)
    t = html.unescape(re.sub(r"<[^>]+>", "", h)).replace("{", "").replace("}", "")
    ps = [re.sub(r"[ \t\r\n]+", " ", p).strip().replace("⸣ ⸢", " ") for p in t.split("\n\n")]
    return [p for p in ps if p and p not in marcas]


def secciones(h):
    """[(títulos, párrafos)] partiendo en cada h2/h3; los títulos seguidos sin cuerpo se juntan con el siguiente."""
    h = re.sub(r"<h1>.*?</h1>", "", h, flags=re.S)
    trozos = re.split(r"(<h[23]>.*?</h[23]>)", h, flags=re.S)
    out, titulos = [], []
    for t in trozos:
        m = re.fullmatch(r"<h([23])>(.*?)</h[23]>", t.strip(), re.S)
        if m:
            titulos.append((int(m.group(1)), " ".join(texto_html(m.group(2)))))
            continue
        cuerpo = texto_html(t)
        if cuerpo:
            out.append((titulos, cuerpo))
            titulos = []
    return out


def cuerpo_nota(x):
    """Todo el cuerpo de la nota (sin el «See: …» final), con las traducciones alternativas entre «»."""
    ps = re.findall(r"<p>(.*?)</p>", x["content"], re.S)
    ps = ps[2:] if ps and ps[0].startswith("<strong><span") else ps
    t = " ".join(" ".join(texto_html(p)) for p in ps if not p.startswith("See:"))
    t = re.sub(r"\[([^\]]*)\]", r"«\1»", t)
    return re.sub(r"\s+", " ", t).strip()


def main():
    libro = sys.argv[1] if len(sys.argv) > 1 else "HEB"
    num = LIBROS[libro]["aquifer"]
    m = json.loads((C.RAIZ / "manifest.json").read_text())["fuentes"]
    sha, sha_m = m["uwtn"]["sha"], m["uwtm"]["sha"]
    rv = C.cargar(f"normalizado/rv1909/{libro}.json")
    datos = json.load(open(C.RAIZ / "fuentes" / "uwtn" / "eng" / "json" / f"{num}.content.json"))
    manual = {x["title"].strip(): x for x in json.load(open(C.RAIZ / "fuentes" / "uwtm" / "eng" / "json" / "001.content.json"))}
    url = f"https://github.com/BibleAquifer/UWTranslationNotes/blob/{sha}/eng/json/{num}.content.json"
    base = lambda: {"lemma_rv1909": [], "text_es": None, "license": "CC-BY-SA-4.0", "translation": None,
                    "review": {"human": False, "status": "pendiente"}}
    out, usadas = [], set()
    for x in datos:
        r = x["index_reference"]
        prov = {"repo": "BibleAquifer/UWTranslationNotes", "sha": sha, "content_id": x["content_id"], "version": x["version"]}
        fuente = {"work": "unfoldingWord® Translation Notes", "author": None, "passage": x["title"], "url": url}
        if r.endswith("000"):                           # introducción al libro (capítulo 0) o a un capítulo
            cap = int(r[2:5])
            for k, (titulos, cuerpo) in enumerate(secciones(x["content"])):
                out.append({**base(), "id": f"uwtn-c:{x['content_id']}#{k}", "ref": f"{libro}.{max(cap, 1)}.1",
                            "ref_fin": f"{libro}.{max(cap, 1)}.1", "capitulo": cap, "orden": k, "layer": "griego_intro",
                            "tradition": "griego", "niveles": [n for n, _ in titulos], "lemma_src": [],
                            "text_src": "\n\n".join([t for _, t in titulos] + cuerpo), "source": fuente, "provenance": prov})
            continue
        partes = nota(x)
        if not partes:
            print("nota sin estructura", x["title"]); continue
        griego, glosa, _, categoria = partes
        ref = osis(r)
        if ref not in rv:
            print("ref inexistente", ref); continue
        texto = cuerpo_nota(x)
        if not texto:
            continue
        if categoria:
            usadas.add(categoria)
        out.append({**base(), "id": f"uwtn-c:{x['content_id']}", "ref": ref, "ref_fin": ref,
                    "orden": int((re.search(r"#(\d+)", x["title"]) or [0, 0])[1]), "layer": "griego_c", "tradition": "griego",
                    "griego": griego, "lemma_src": [glosa] if glosa else [], "categoria": categoria, "text_src": texto,
                    "source": fuente, "provenance": prov})
    for k, cat in enumerate(sorted(usadas, key=lambda c: CATEGORIAS[c])):
        a = manual[cat]
        d = re.search(r"<h\d>\s*Description\s*</h\d>(.*?)(?=<h\d>)", a["content"], re.S)
        cuerpo = texto_html(d.group(1) if d else a["content"])
        out.append({**base(), "id": f"uwtm:{a['content_id']}", "ref": f"{libro}.1.1", "ref_fin": f"{libro}.1.1", "orden": k,
                    "layer": "glosario_g", "tradition": "griego", "categoria": cat, "lemma_src": [],
                    "text_src": "\n\n".join(cuerpo),
                    "source": {"work": "unfoldingWord® Translation Academy", "author": None, "passage": cat,
                               "url": f"https://github.com/BibleAquifer/UWTranslationManual/blob/{sha_m}/eng/json/001.content.json"},
                    "provenance": {"repo": "BibleAquifer/UWTranslationManual", "sha": sha_m, "content_id": a["content_id"],
                                   "version": a["version"]}})
    faltan = [c for c in usadas if c not in CATEGORIAS]
    assert not faltan, f"categorías sin nombre español: {faltan}"
    ids = [n["id"] for n in out]
    assert len(ids) == len(set(ids)), "ids repetidos"
    C.guardar(f"normalizado/{libro}/griego_completo.json", out)
    w = lambda capa: sum(len(n["text_src"].split()) for n in out if n["layer"] == capa)
    print(f"griego completo {libro}: notas {sum(n['layer'] == 'griego_c' for n in out)} ({w('griego_c'):,} palabras), "
          f"introducciones {sum(n['layer'] == 'griego_intro' for n in out)} secciones ({w('griego_intro'):,}), "
          f"glosario {len(usadas)} categorías ({w('glosario_g'):,})")


if __name__ == "__main__":
    main()
