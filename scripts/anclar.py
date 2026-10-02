#!/usr/bin/env python3
"""Paso 8: re-anclaje de los lemas a la RV1909.

Tyndale cita la NLT, no la RV1909: el lema traducido casi nunca aparece tal cual en el versículo.
Regla determinista primero (lección de Ware: reglas baratas, el modelo solo para el residuo):
se busca en los versículos del rango el tramo de palabras que más se parece al lema traducido
(coincidencia de raíces). El tramo se copia del propio versículo, así que existe literalmente;
si el parecido no alcanza, la nota se ancla al versículo completo («v. N:»).

Uso: python3 scripts/anclar.py JHN [CAP|todos]  -> agrega "lemas_rv1909" en traducido/<LIBRO>/<CC>.json
"""
import re
import sys
import unicodedata

import comun as C

UMBRAL = 0.5
VACIAS = set("el la los las un una unos unas de del al a y e o u que en por para con su sus se lo le les como "
             "mas pero no ni es era fue ha han the of and to in that".split())


def raiz(w):
    w = "".join(c for c in unicodedata.normalize("NFD", w.lower()) if unicodedata.category(c) != "Mn")
    return w[:5]


def palabras(t):
    return re.findall(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+", re.sub(r"[⸢⸣]", "", t))


def mejor_tramo(lema, versos):
    """(tramo literal del versículo, ref, puntaje) o (None, None, 0)."""
    objetivo = [raiz(w) for w in palabras(lema) if w.lower() not in VACIAS]
    if not objetivo:
        return None, None, 0.0
    mejor = (None, None, 0.0)
    for ref, texto in versos:
        toks = list(re.finditer(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ⸢⸣]+", texto))
        n = len(palabras(lema))
        for largo in range(max(1, n - 2), n + 3):
            for i in range(0, max(1, len(toks) - largo + 1)):
                ventana = toks[i:i + largo]
                if not ventana:
                    continue
                rs = [raiz(re.sub(r"[⸢⸣]", "", m.group(0))) for m in ventana]
                hits = [k for k, r in enumerate(rs) if r in objetivo]
                if not hits:
                    continue
                aciertos = len({rs[k] for k in hits})
                acierto = aciertos / len(objetivo)
                if aciertos < min(2, len(objetivo)):
                    continue
                ini, fin = i + hits[0], i + hits[-1]          # el tramo empieza y termina en palabras del lema
                del_lema = {w.lower() for w in palabras(lema)}
                for _ in range(2):                            # …más las palabras vacías del lema que lo rodean («En el principio»)
                    if ini > 0 and toks[ini - 1].group(0).lower().strip("⸢⸣") in del_lema:
                        ini -= 1
                ventana = toks[ini:fin + 1]
                puntaje = acierto - 0.01 * abs(len(ventana) - n)
                if puntaje > mejor[2]:
                    tramo = texto[ventana[0].start():ventana[-1].end()]
                    mejor = (tramo.strip(" ,;:.()"), ref, puntaje)
    return mejor


def versos_de(n, rv):
    a, b = n["ref"], n.get("ref_fin", n["ref"])
    return [(r, v["texto"]) for r, v in rv.items()
            if (C.cap(a), C.ver(a)) <= (C.cap(r), C.ver(r)) <= (C.cap(b), C.ver(b))]


def main():
    libro = sys.argv[1] if len(sys.argv) > 1 else "JHN"
    pedido = sys.argv[2] if len(sys.argv) > 2 else "1"
    rv = C.cargar(f"normalizado/rv1909/{libro}.json")
    us = {n["id"]: n for n in C.unidades(libro)}
    caps = sorted({C.cap(n["ref"]) for n in us.values()}) if pedido == "todos" else [int(pedido)]
    for c in caps:
        ruta = f"traducido/{libro}/{c:02d}.json"
        tr = C.cargar(ruta, {})
        ok = residuo = 0
        for i, t in tr.items():
            n = us.get(i)
            if not n or not n.get("lemma_src"):
                continue
            anclas = []
            for lema in t.get("lemas_es") or []:
                tramo, ref, p = mejor_tramo(lema, versos_de(n, rv))
                if p >= UMBRAL:
                    anclas.append({"lema": tramo, "ref": ref})
                    ok += 1
                else:
                    anclas.append({"lema": None, "ref": n["ref"]})
                    residuo += 1
            t["lemas_rv1909"] = anclas
        C.guardar(ruta, tr)
        print(f"cap.{c}: lemas anclados {ok}; al versículo completo {residuo}")


if __name__ == "__main__":
    main()
