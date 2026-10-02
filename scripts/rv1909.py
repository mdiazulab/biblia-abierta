#!/usr/bin/env python3
"""Paso 3 (texto): RV1909 desde el USFX fijado -> normalizado/rv1909/<LIBRO>.json con ids OSIS.

Decisión del usuario (02-10-2026): se modernizan SOLO los acentos que la norma ya no usa en
monosílabos («fué»->«fue», «á»->«a», «ó»->«o»), sin cambiar ninguna palabra. Se guarda el
texto de 1909 intacto en "texto_1909" y la lista de cambios en informes/rv1909_<LIBRO>.md.
Las palabras añadidas por los traductores (<add>, en cursiva en el impreso) van entre ⸢ ⸣.

Uso: python3 scripts/rv1909.py [JHN]
"""
import collections
import json
import pathlib
import re
import sys

RAIZ = pathlib.Path(__file__).resolve().parent.parent
FUENTE = RAIZ / "fuentes" / "rv1909" / "spa-rv1909.usfx.xml"

# monosílabos con tilde obsoleta (Ortografía RAE 1959/2010); NO se tocan dé, sé, él, mí, tú, sí, más, qué...
ACENTOS = {"fué": "fue", "Fué": "Fue", "fuí": "fui", "Fuí": "Fui", "dió": "dio", "Dió": "Dio", "vió": "vio",
           "Vió": "Vio", "ví": "vi", "Ví": "Vi", "fuí": "fui", "dí": "di", "Dí": "Di", "fé": "fe", "tí": "ti",
           "á": "a", "Á": "A", "ó": "o", "é": "e", "piés": "pies", "ríe": "ríe"}
PALABRA = re.compile(r"\b\w+\b", re.UNICODE)


def modernizar(t, cuenta):
    def rep(m):
        w = m.group(0)
        n = ACENTOS.get(w, w)
        if n != w:
            cuenta[f"{w}->{n}"] += 1
        return n
    return PALABRA.sub(rep, t)


def libro_xml(libro):
    x = FUENTE.read_text(encoding="utf-8")
    i = x.index(f'<book id="{libro}"')
    j = x.find("<book id=", i + 10)
    return x[i:j if j > 0 else len(x)]


def versiculos(libro):
    x = libro_xml(libro)
    x = re.sub(r"<add>(.*?)</add>", r"⸢\1⸣", x, flags=re.S)
    x = re.sub(r"<(?:f|x)\b.*?</(?:f|x)>", "", x, flags=re.S)          # notas/referencias del USFX, si las hay
    cap, out = None, {}
    for m in re.finditer(r'<c id="(\d+)"\s*/>|<v id="(\d+)"\s*/>(.*?)(?=<ve\s*/>|<v id=|<c id=|$)', x, flags=re.S):
        if m.group(1):
            cap = int(m.group(1))
            continue
        t = re.sub(r"<[^>]+>", " ", m.group(3))
        t = re.sub(r"\s+", " ", t).strip()
        t = re.sub(r"\s+([,.;:?!)])", r"\1", t)
        t = re.sub(r"([(¿¡])\s+", r"\1", t)
        # versalitas del impreso en la primera palabra del libro («EN el principio») -> tipo oración
        t = re.sub(r"^([A-ZÁÉÍÓÚÑ])([A-ZÁÉÍÓÚÑ]+)\b", lambda m: m.group(1) + m.group(2).lower(), t)
        out[f"{libro}.{cap}.{int(m.group(2))}"] = t
    return out


def main():
    libro = sys.argv[1] if len(sys.argv) > 1 else "JHN"
    cuenta = collections.Counter()
    vs = versiculos(libro)
    datos = {ref: {"texto": modernizar(t, cuenta), "texto_1909": t} for ref, t in vs.items()}
    destino = RAIZ / "normalizado" / "rv1909"
    destino.mkdir(parents=True, exist_ok=True)
    (destino / f"{libro}.json").write_text(json.dumps(datos, ensure_ascii=False, indent=0))
    caps = collections.Counter(r.split(".")[1] for r in datos)
    lin = [f"# RV1909 {libro}", "", f"{len(datos)} versículos en {len(caps)} capítulos.", "",
           "Acentos modernizados (solo tildes obsoletas en monosílabos; ninguna palabra cambia):", ""]
    lin += [f"- {k}: {n}" for k, n in cuenta.most_common()]
    (RAIZ / "informes" / f"rv1909_{libro}.md").write_text("\n".join(lin) + "\n")
    print("\n".join(lin[:3]), "| cambios de acento:", sum(cuenta.values()))


if __name__ == "__main__":
    main()
