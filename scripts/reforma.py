#!/usr/bin/env python3
"""Capa «Reforma»: Juan Calvino, Comentario a la Epístola a los Hebreos (1549), trad. inglesa de John Owen,
Calvin Translation Society, Edimburgo 1853 (dominio público), en el ThML de CCEL (fuentes/calvino/calcom44.xml,
SHA-256 en manifest.json; lo trae el workflow «Biblia abierta (fuentes web)» porque CCEL no está en GitHub).

Una unidad por versículo comentado (<div class="Commentary" id="Bible:Heb.C.V">), más «El argumento» de la epístola
anclado a 1:1. Se omiten la tabla del texto inglés/latino de cada perícopa y las notas al pie de Owen (son del
traductor). Lemas = frases en cursiva al comienzo de cada párrafo.

Uso: python3 scripts/reforma.py HEB  -> normalizado/HEB/reforma.json
"""
import hashlib
import html
import re
import sys

import comun as C

FUENTE = C.RAIZ / "fuentes" / "calvino" / "calcom44.xml"
EDICION = "Juan Calvino, Comentario a la Epístola a los Hebreos (1549), trad. J. Owen, Calvin Translation Society, Edimburgo 1853"
URL = "https://ccel.org/ccel/calvin/calcom44.xml"


def tabla_a_texto(m):
    filas = []
    for fila in re.findall(r"<tr\b.*?</tr>", m.group(0), re.S):
        celdas = [limpio(c) for c in re.findall(r"<td\b[^>]*>(.*?)</td>", fila, re.S)]
        celdas = [c for c in celdas if c]
        if celdas:
            filas.append(" — ".join(celdas))
    return "<p>" + "\n".join(filas) + "</p>"


def limpio(fragmento):
    t = re.sub(r"<note\b.*?</note>", "", fragmento, flags=re.S)          # notas de Owen
    t = re.sub(r"<pb\b[^>]*/>|<scripCom\b[^>]*/>", "", t)
    t = re.sub(r"<i>(.*?)</i>", lambda m: "⸢" + m.group(1) + "⸣" if m.group(1).strip() else m.group(1), t, flags=re.S)
    t = re.sub(r"<[^>]+>", "", t)
    t = html.unescape(t)
    t = re.sub(r"[ \t\r\n]+", " ", t).strip()
    return t.replace("⸣ ⸢", " ").replace("⸣⸢", "")


def parrafos(bloque):
    bloque = re.sub(r"<note\b.*?</note>", "", bloque, flags=re.S)        # antes de partir: las notas traen <p> anidados
    bloque = re.sub(r"<table\b.*?</table>", tabla_a_texto, bloque, flags=re.S)
    ps = [limpio(p) for p in re.findall(r"<p\b[^>]*>(.*?)</p>", bloque, re.S)]
    return [p for p in ps if p and not re.fullmatch(r"[\W\d]*", p) and not (p.isupper() and len(p) < 80)]


def main():
    libro = sys.argv[1] if len(sys.argv) > 1 else "HEB"
    if libro != "HEB":
        print("solo Hebreos por ahora"); return
    x = FUENTE.read_text(encoding="utf-8")
    sha = hashlib.sha256(FUENTE.read_bytes()).hexdigest()
    rv = C.cargar(f"normalizado/rv1909/{libro}.json")
    notas = []
    # «El argumento»
    m = re.search(r'<div1[^>]*title="The Argument"[^>]*>(.*?)</div1>', x, re.S)
    if m:
        notas.append(("HEB.1.1", "Argumento de la epístola", parrafos(m.group(1))))
    for m in re.finditer(r'<div class="Commentary" id="Bible:Heb\.(\d+)\.(\d+)">(.*?)(?=<div class="Commentary"|</div2>|<div2\b|<div1\b)', x, re.S):
        c, v = int(m.group(1)), int(m.group(2))
        ps = parrafos(m.group(3))
        if ps:
            notas.append((f"HEB.{c}.{v}", f"Heb {c}:{v}", ps))
    out, palabras = [], 0
    for k, (ref, pasaje, ps) in enumerate(notas):
        if ref not in rv:
            print("ref inexistente", ref); continue
        texto = "\n\n".join(ps)
        lemas = [re.sub(r",? etc\.?$", "", m.group(1)).rstrip(" ,;:.") for p in ps for m in [re.match(r"(?:\d+\.\s*)?⸢([^⸣]+)⸣", p)] if m]
        palabras += len(texto.split())
        out.append({"id": f"calvino:{ref}#{'arg' if pasaje.startswith('Argumento') else k}", "ref": ref, "ref_fin": ref,
                    "layer": "reforma", "tradition": "reforma", "lemma_src": lemas, "lemma_rv1909": [],
                    "text_src": texto, "text_es": None,
                    "source": {"author": "John Calvin", "work": "Commentary on Hebrews", "passage": pasaje, "edition": EDICION},
                    "license": "dominio_publico",
                    "provenance": {"url": URL, "sha256": sha}, "translation": None,
                    "review": {"human": False, "status": "pendiente"}})
    C.guardar(f"normalizado/{libro}/reforma.json", out)
    cubiertos = {n["ref"] for n in out}
    print(f"Calvino {libro}: {len(out)} notas, {palabras:,} palabras, {len(cubiertos)}/{len(rv)} versículos; sha256 {sha[:12]}")


if __name__ == "__main__":
    main()
