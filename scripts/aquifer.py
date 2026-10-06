#!/usr/bin/env python3
"""Paso 3-5 (contexto): notas de Aquifer -> normalizado/<LIBRO>/aquifer.json, una unidad por nota.

Cada nota guarda el inglés (revisión "Professional") y el español existente de Aquifer
(sin revisión) emparejados por reference_id; el lema es la frase en cursiva con la que abre
la nota («<em>In the beginning</em>: …»). Las referencias bíblicas internas (<data
class="bible-ref">) se conservan como lista OSIS para el control de referencias.

Uso: python3 scripts/aquifer.py [JHN]
"""
import html
import json
import pathlib
import re
import sys

RAIZ = pathlib.Path(__file__).resolve().parent.parent
from libros import LIBROS
NUM = {k: v["aquifer"] for k, v in LIBROS.items()}
LIBRO_POR_NUM = {"01": "GEN", "02": "EXO", "03": "LEV", "04": "NUM", "05": "DEU", "06": "JOS", "07": "JDG", "08": "RUT",
                 "09": "1SA", "10": "2SA", "11": "1KI", "12": "2KI", "13": "1CH", "14": "2CH", "15": "EZR", "16": "NEH",
                 "17": "EST", "18": "JOB", "19": "PSA", "20": "PRO", "21": "ECC", "22": "SNG", "23": "ISA", "24": "JER",
                 "25": "LAM", "26": "EZK", "27": "DAN", "28": "HOS", "29": "JOL", "30": "AMO", "31": "OBA", "32": "JON",
                 "33": "MIC", "34": "NAM", "35": "HAB", "36": "ZEP", "37": "HAG", "38": "ZEC", "39": "MAL", "40": "MAT",
                 "41": "MRK", "42": "LUK", "43": "JHN", "44": "ACT", "45": "ROM", "46": "1CO", "47": "2CO", "48": "GAL",
                 "49": "EPH", "50": "PHP", "51": "COL", "52": "1TH", "53": "2TH", "54": "1TI", "55": "2TI", "56": "TIT",
                 "57": "PHM", "58": "HEB", "59": "JAS", "60": "1PE", "61": "2PE", "62": "1JN", "63": "2JN", "64": "3JN",
                 "65": "JUD", "66": "REV"}


def osis(r):
    """«43001004» -> «JHN.1.4»"""
    return f"{LIBRO_POR_NUM[r[:2]]}.{int(r[2:5])}.{int(r[5:8])}"


def rango(ref):
    a, _, b = ref.partition("-")
    return osis(a), osis(b or a)


def texto(h):
    h = re.sub(r"</p>\s*<p>", "\n\n", h)
    h = re.sub(r"<em>(.*?)</em>", r"⸢\1⸣", h, flags=re.S)
    return html.unescape(re.sub(r"<[^>]+>", "", h)).strip()


def refs(h):
    return [osis(a) + ("-" + osis(b) if b != a else "") for a, b in
            re.findall(r'data-start-ref="(\d{8})" data-end-ref="(\d{8})"', h)]


def lema(h):
    """Lemas de la nota: frase en cursiva seguida de «:» al comienzo de un párrafo o de un ítem de lista
    (una nota puede comentar varias frases del pasaje: <ul><li><p><em>In Him was life</em>: …)."""
    return [html.unescape(re.sub(r"<[^>]+>", "", m)).strip()
            for m in re.findall(r"(?:^|<p>|<li>)\s*(?:<p>)?\s*<em>([^<]{2,200})</em>\s*:", h)]


def main():
    libro = sys.argv[1] if len(sys.argv) > 1 else "JHN"
    base = RAIZ / "fuentes" / "aquifer"
    sha = json.loads((RAIZ / "manifest.json").read_text())["fuentes"]["aquifer"]["sha"]
    en = json.load(open(base / "eng" / "json" / f"{NUM[libro]}.content.json"))
    es = {x["reference_id"]: x for x in json.load(open(base / "spa" / "json" / f"{NUM[libro]}.content.json"))}
    notas = []
    for x in en:
        ini, fin = rango(x["index_reference"])
        y = es.get(x["reference_id"])
        notas.append({
            "id": f"aquifer:{x['content_id']}", "ref": ini, "ref_fin": fin, "layer": "contexto",
            "tradition": "evangélica moderna", "lemma_src": lema(x["content"]), "lemma_rv1909": [],
            "text_src": texto(x["content"]), "refs_src": refs(x["content"]),
            "text_es_aquifer": texto(y["content"]) if y else None, "text_es": None,
            "source": {"work": "Tyndale Open Study Notes (Aquifer)", "author": None, "passage": x["title"],
                       "url": f"https://github.com/BibleAquifer/AquiferOpenStudyNotes/blob/{sha}/eng/json/{NUM[libro]}.content.json"},
            "license": "CC-BY-SA-4.0",
            "provenance": {"repo": "BibleAquifer/AquiferOpenStudyNotes", "sha": sha, "content_id": x["content_id"],
                           "review_level": x["review_level"], "version": x["version"]},
            "translation": None, "review": {"human": False, "status": "pendiente"},
        })
    destino = RAIZ / "normalizado" / libro
    destino.mkdir(parents=True, exist_ok=True)
    (destino / "aquifer.json").write_text(json.dumps(notas, ensure_ascii=False, indent=1))
    ids = [n["id"] for n in notas]
    assert len(ids) == len(set(ids)), "ids repetidos"
    print(f"aquifer {libro}: {len(notas)} notas; con lema {sum(1 for n in notas if n['lemma_src'])}; "
          f"con español existente {sum(1 for n in notas if n['text_es_aquifer'])}; "
          f"palabras EN {sum(len(n['text_src'].split()) for n in notas)}")


if __name__ == "__main__":
    main()
