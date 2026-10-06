#!/usr/bin/env python3
"""Capa «Griego» (G): notas sobre el texto griego de unfoldingWord® Translation Notes (CC BY-SA 4.0, edición
Aquifer, release v91 de unfoldingWord), fuentes/uwtn/eng/json/<NN>.content.json en el SHA de manifest.json.

Las notas están escritas para traductores («If it would be helpful in your language, you could…»). Se conserva
solo lo que le sirve al lector de una Biblia de estudio:
- las notas que exponen lecturas posibles «(1) … (2) …» (el aporte central: alternativas exegéticas del griego),
  de cualquier categoría;
- las de trasfondo, variantes textuales, términos desconocidos, acciones simbólicas e imágenes bíblicas, y las que
  no tienen categoría (suelen ser de gramática y tiempo verbal: 10:14 «perfeccionó… a los que están siendo
  santificados»).
Se quitan las oraciones dirigidas al traductor, las categorías de técnica de traducción (voz pasiva, sustantivos
abstractos, pronombres, conectores…) y las «Alternate translation» fuera de las listas de opciones; dentro de una
lista, la paráfrasis queda entre paréntesis porque aclara qué significa cada opción.

La frase griega no se traduce: va en "griego"; la glosa inglesa es el lema (se ancla a la RV1909 como los demás).

Uso: python3 scripts/griego.py HEB  -> normalizado/HEB/griego.json
"""
import html
import json
import re
import sys

import comun as C
from aquifer import osis
from libros import LIBROS

CONSERVAR = {"Assumed Knowledge and Implicit Information", "Background Information", "Connect — Background Information",
             "Textual Variants", "Translate Unknowns", "Symbolic Action", "Biblical Imagery — Extended Metaphors",
             "Translating Son and Father", "Kinship"}
AL_TRADUCTOR = re.compile(r"\byour?\b|\byou (?:could|should|may|can|must|might|will|would)\b|\bIf it would be helpful\b"
                          r"|\bULT\b|\bUST\b|\btranslate\b|\btranslating\b|\bnatural (?:form|way)\b|\bit is best to\b|\bif possible\b"
                          r"|^Use (?:a|an|the)\b|\buse a (?:general|word|phrase)\b|\bfootnote", re.I)
ALTERNATIVA = re.compile(r"\s*Alternat\w* translations?:?\s*((?:(?:\(\d\)\s*)?(?:\[[^\]]*\]|“[^”]*”)(?:\s*or\s*)?)+)")
MINIMO = 10          # palabras de explicación que tienen que quedar


def plano(h):
    h = re.sub(r"<strong>(.*?)</strong>", lambda m: "⸢" + m.group(1) + "⸣", h, flags=re.S)
    t = html.unescape(re.sub(r"<[^>]+>", "", h))
    t = t.replace("{", "").replace("}", "")
    return re.sub(r"\s+", " ", t).strip().replace("⸣ ⸢", " ")


def oraciones(t):
    return re.split(r"(?<=[.!?])\s+(?=[A-Z“(⸢])", t)


def limpiar(cuerpo):
    """Explicación para el lector, o None si no queda nada útil (o si quitar lo dirigido al traductor rompería
    una lista de opciones)."""
    opciones = bool(re.search(r"\(1\).*\(2\)", cuerpo))
    alternativas = []

    def apartar(m):                                 # las paráfrasis se apartan antes de filtrar oraciones: su
        alternativas.append(m.group(1))             # «you» es del texto bíblico, no una indicación al traductor
        return f" ⟦{len(alternativas) - 1}⟧"
    t = ALTERNATIVA.sub(apartar, cuerpo)
    partes, rotas = [], False
    for o in oraciones(t):
        if AL_TRADUCTOR.search(o):
            rotas = rotas or bool(re.search(r"\(\d\)", o))
        else:
            partes.append(o)
    if rotas:
        return None
    t = " ".join(partes).strip()

    def poner(m):
        if not opciones:
            return ""
        return " (" + " o ".join("«" + a.strip() + "»" for a in re.findall(r"\[([^\]]*)\]|“([^”]*)”", alternativas[int(m.group(1))])
                                 for a in [a[0] or a[1]]) + ")"
    t = re.sub(r"\s*⟦(\d+)⟧", poner, t)
    t = re.sub(r"\s+([;.,])", r"\1", t).replace(".)", ").").strip()
    t = re.sub(r"\s*\(See:\s*([^)]*)\)", r" (véase \1)", t)
    return t if len(t.split()) >= MINIMO else None


def nota(x):
    """(griego, glosa, explicación, categoría) de una nota de versículo. Las notas sobre el versículo entero
    (la historia de Enoc en 11:5) no traen frase griega ni glosa: (None, None, …)."""
    ps = re.findall(r"<p>(.*?)</p>", x["content"], re.S)
    m = re.search(r'UWTranslationManual">([^<]+)<', x["content"])
    categoria = m.group(1).strip() if m else None
    if len(ps) >= 3 and ps[0].startswith("<strong><span"):
        griego = plano(ps[0]).strip("⸢⸣ ").replace(" & ", " … ").replace("&", "…")
        glosa = plano(ps[1]).strip("⸢⸣ ").strip('"“”')
        ps = ps[2:]
    elif ps and not ps[0].startswith("<strong>"):
        griego = glosa = None
    else:
        return None
    cuerpo = " ".join(plano(p) for p in ps if not p.startswith("See:"))
    return griego, glosa, cuerpo, categoria


def main():
    libro = sys.argv[1] if len(sys.argv) > 1 else "HEB"
    num = LIBROS[libro]["aquifer"]
    sha = json.loads((C.RAIZ / "manifest.json").read_text())["fuentes"]["uwtn"]["sha"]
    rv = C.cargar(f"normalizado/rv1909/{libro}.json")
    datos = json.load(open(C.RAIZ / "fuentes" / "uwtn" / "eng" / "json" / f"{num}.content.json"))
    out, vistos, palabras = [], 0, 0
    for x in datos:
        r = x["index_reference"]
        if r.endswith("000"):                           # introducciones del libro y de capítulo: no (son para traductores)
            continue
        vistos += 1
        partes = nota(x)
        if not partes:
            continue
        griego, glosa, cuerpo, categoria = partes
        opciones = bool(re.search(r"\(1\).*\(2\)", cuerpo))
        if not (opciones or categoria is None or categoria in CONSERVAR):
            continue
        texto = limpiar(cuerpo)
        if not texto:
            continue
        ref = osis(r)
        if ref not in rv:
            print("ref inexistente", ref); continue
        orden = int((re.search(r"#(\d+)", x["title"]) or [0, 0])[1])
        palabras += len(texto.split())
        out.append({"id": f"uwtn:{x['content_id']}", "ref": ref, "ref_fin": ref, "orden": orden,
                    "layer": "griego", "tradition": "griego", "griego": griego, "lemma_src": [glosa] if glosa else [], "lemma_rv1909": [],
                    "text_src": texto, "text_es": None, "categoria": categoria,
                    "source": {"work": "unfoldingWord® Translation Notes", "author": None, "passage": x["title"],
                               "url": f"https://github.com/BibleAquifer/UWTranslationNotes/blob/{sha}/eng/json/{num}.content.json"},
                    "license": "CC-BY-SA-4.0",
                    "provenance": {"repo": "BibleAquifer/UWTranslationNotes", "sha": sha, "content_id": x["content_id"],
                                   "version": x["version"]},
                    "translation": None, "review": {"human": False, "status": "pendiente"}})
    out.sort(key=lambda n: (C.cap(n["ref"]), C.ver(n["ref"]), n["orden"]))
    ids = [n["id"] for n in out]
    assert len(ids) == len(set(ids)), "ids repetidos"
    C.guardar(f"normalizado/{libro}/griego.json", out)
    print(f"griego {libro}: {len(out)}/{vistos} notas, {palabras:,} palabras, "
          f"{len({n['ref'] for n in out})}/{len(rv)} versículos; sha {sha[:10]}")


if __name__ == "__main__":
    main()
