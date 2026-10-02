#!/usr/bin/env python3
"""Paso 9a: batería determinista por capítulo (un fallo bloquea; ver HANDOVER.md).

 1 cada nota seleccionada traducida, ids únicos
 2-3 mismos números en inglés y español (referencias bíblicas, fechas, cifras); cursivas preservadas
 4 glosario: ningún término prohibido; «Verbo» donde el inglés dice «the Word»
 5 sin inglés residual, entidades HTML, marcas de prueba ni comentarios del modelo
 6 razón de longitud español/inglés (caracteres) en [0,9; 1,5]
 7 licencia y procedencia; citas patrísticas con obra y pasaje
 8 cada lema re-anclado existe literalmente en su versículo RV1909
 + citas bíblicas: el capítulo existe y todas quedan en forma única (biblia.py)

Uso: python3 scripts/verificar.py JHN [CAP|todos]  -> informes/verificacion_<LIBRO>.md; sale con 1 si algo falla
"""
import collections
import re
import sys

import biblia as B
import comun as C
import traducir as T

INGLES = set("the and of which that with from this these those would should their there is are was were "
             "has have been not by be it his her they them".split())
COMENTARIO = re.compile(r"(?i)\b(?:nota del traductor|traducción:|aquí est[aá] la traducción|here is|translator'?s note)\b|\[ES\]")


def numeros(t):
    t = re.sub(r"\b(III|II|I)(?= [A-ZÁÉ][a-záéíóú])", lambda m: str(len(m.group(1))), t)   # «I Corintios» = «1 Corinthians»
    return collections.Counter(re.findall(r"\d+", t))


def revisar(n, t, rv):
    t = dict(t or {})
    t.update(C.adjudicacion(n["id"]))
    fallos = []
    src, es = T.texto_a_traducir(n), (t or {}).get("text_es") or ""
    if not es:
        return ["1 sin traducir"]
    if numeros(src) != numeros(es):
        dif = (numeros(src) - numeros(es)) + (numeros(es) - numeros(src))
        fallos.append(f"2 números distintos: {dict(dif)}")
    if abs(src.count("⸢") - es.count("⸢")) > 1:
        fallos.append(f"3 cursivas {src.count('⸢')} -> {es.count('⸢')}")
    for term in C.glosario_para(src):
        if term.get("prohibido") and re.search(term["prohibido"], es):
            fallos.append(f"4 término prohibido para «{term['es']}»")
    if re.search(r"\bthe Word\b", src) and "Verbo" not in es:
        fallos.append("4 falta «Verbo»")
    pal = re.findall(r"[a-záéíóúñ]+", es.lower())
    if pal and sum(w in INGLES for w in pal) / len(pal) > 0.03:
        fallos.append("5 inglés residual")
    if re.search(r"&\w+;|<[a-z/]", es) or COMENTARIO.search(es):
        fallos.append("5 HTML, marca de prueba o comentario del modelo")
    r = len(es) / max(1, len(src))
    if len(src) > 300 and not 0.9 <= r <= 1.5:
        fallos.append(f"6 razón de longitud {r:.2f}")
    if not n.get("license") or not n.get("provenance"):
        fallos.append("7 sin licencia o procedencia")
    if n["layer"] == "padres" and not (n["source"].get("work") and (n["source"].get("passage") or n["source"].get("work"))):
        fallos.append("7 cita patrística sin obra/pasaje")
    for a in (t or {}).get("lemas_rv1909", []):
        if a["lema"] and a["lema"] not in rv.get(a["ref"], {}).get("texto", ""):
            fallos.append(f"8 lema «{a['lema']}» no está en {a['ref']}")
    malas = []
    norm = B.normalizar(es, malas, None)
    for x in re.findall(r"(?<!⸣ )\b((?:[1-3I]{1,3} )?[A-Z][a-zé]+\.? \d+:\d+)", norm):
        fallos.append(f"+ cita sin forma única (libro inglés o abreviatura desconocida): {x}")
    fallos += [f"+ cita bíblica inexistente: {x}" for _, x in malas]
    return fallos


def main():
    libro = sys.argv[1] if len(sys.argv) > 1 else "JHN"
    pedido = sys.argv[2] if len(sys.argv) > 2 else "1"
    rv = C.cargar(f"normalizado/rv1909/{libro}.json")
    us = C.unidades(libro)
    caps = sorted({C.cap(n["ref"]) for n in us}) if pedido == "todos" else [int(pedido)]
    lin, total = [f"# Verificación {libro}", ""], 0
    detalle = []
    for c in caps:
        tr = C.cargar(f"traducido/{libro}/{c:02d}.json", {})
        ns = [n for n in us if C.cap(n["ref"]) == c]
        ids = [n["id"] for n in ns]
        res = {n["id"]: revisar(n, tr.get(n["id"]), rv) for n in ns}
        malos = {i: f for i, f in res.items() if f}
        tipos = collections.Counter(x.split(" ")[0] for f in malos.values() for x in f)
        ok = not malos and len(ids) == len(set(ids))
        total += len(malos)
        lin.append(f"- cap.{c}: {'OK' if ok else 'FALLA'} — {len(ns)} notas; con fallos {len(malos)} "
                   + (f"(por punto: {dict(sorted(tipos.items()))})" if tipos else ""))
        detalle += [f"  - {i}: {'; '.join(f)}" for i, f in list(malos.items())[:15]]
    lin += ["", "## Primeros fallos", ""] + detalle if detalle else []
    (C.RAIZ / "informes" / f"verificacion_{libro}.md").write_text("\n".join(lin) + "\n")
    print("\n".join(lin[:len(caps) + 2]))
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
