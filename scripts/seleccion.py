#!/usr/bin/env python3
"""Paso 5: qué notas entran en la edición (densidad patrística alta, pero legible).

- Contexto: todas las notas de Aquifer.
- Padres: la Catena Aurea completa (selección de Tomás de Aquino, Oriente y Occidente).
- Complemento por versículo, cada uno de hasta MAX_PALABRAS: un texto de Oriente (Crisóstomo,
  Homilías sobre Juan; si no, Cirilo, Comentario) donde la Catena no trae voz oriental, y uno de
  Occidente (Agustín, Tratados sobre Juan) donde la Catena no llega; ambos en versículos sensibles.

Uso: python3 scripts/seleccion.py [JHN]  -> normalizado/<LIBRO>/seleccion.json + informes/seleccion_<LIBRO>.md
"""
import collections
import sys

import comun as C

MAX_PALABRAS = 350
from libros import LIBROS


def main():
    libro = sys.argv[1] if len(sys.argv) > 1 else "JHN"
    aq = C.cargar(f"normalizado/{libro}/aquifer.json")
    pa = C.cargar(f"normalizado/{libro}/padres.json")
    versos = C.cargar(f"normalizado/rv1909/{libro}.json")
    sel = [n["id"] for n in aq]
    L = LIBROS[libro]
    ORIENTE, OCCIDENTE = L["oriente"], L["occidente"]
    es_base = lambda n: n["source"]["work"].startswith("Catena") or any(
        n["source"]["author"] == a and n["source"]["work"].startswith(w) for a, w in L["base"])
    catena = [n for n in pa if es_base(n)]
    sel += [n["id"] for n in catena]
    con_catena = {n["ref"] for n in catena}
    palabras = lambda n: len(n["text_src"].split())
    por_ref = collections.defaultdict(list)
    for n in pa:
        if not es_base(n) and palabras(n) <= MAX_PALABRAS:
            por_ref[n["ref"]].append(n)
    extra = 0
    oriente_catena = {n["ref"] for n in catena if n["tradition"] == "oriente"}
    for ref in versos:
        sensible = C.es_sensible({"ref": ref})
        grupos = []
        if ref not in oriente_catena or sensible:      # equilibrio: toda nota patrística con una voz de Oriente
            grupos.append(ORIENTE)
        if ref not in con_catena or sensible:
            grupos.append(OCCIDENTE)
        for grupo in grupos:
            cand = [n for a, w in grupo for n in por_ref.get(ref, []) if n["source"]["author"] == a and n["source"]["work"].startswith(w)]
            if cand:
                sel.append(min(cand, key=palabras)["id"])
                extra += 1
        if L.get("libre"):                              # voces adicionales sin obra fija (Hebreos)
            tope = L["libre"][1 if sensible else 0]
            cand = sorted(por_ref.get(ref, []), key=lambda n: (n["tradition"] == "oriente", palabras(n)))
            autores = set()
            for n in cand:
                if len(autores) < tope and n["source"]["author"] not in autores:
                    sel.append(n["id"]); autores.add(n["source"]["author"]); extra += 1
    if L.get("reforma"):                                # capa «Reforma»: el comentario completo
        sel += [n["id"] for n in C.cargar(f"normalizado/{libro}/reforma.json", [])]
    if L.get("griego"):                                 # capa «Griego»: todas las notas que pasaron el filtro de griego.py
        sel += [n["id"] for n in C.cargar(f"normalizado/{libro}/griego.json", [])]
    sel = list(dict.fromkeys(sel))
    C.guardar(f"normalizado/{libro}/seleccion.json", sel)
    us = C.unidades(libro)
    cubiertos = set()
    for n in us:
        a, b = n["ref"], n.get("ref_fin", n["ref"])
        cubiertos |= {r for r in versos if (C.cap(a), C.ver(a)) <= (C.cap(r), C.ver(r)) <= (C.cap(b), C.ver(b))}
    w = collections.Counter()
    for n in us:
        w[n["layer"] + ("/" + n["tradition"] if n["layer"] == "padres" else "")] += palabras(n)   # contexto, padres/…, reforma, griego
    lin = [f"# Selección {libro}", "",
           f"- unidades: {len(us)} (Aquifer {len(aq)}, Catena {len(catena)}, complemento {extra})",
           f"- palabras (inglés): {sum(w.values()):,} — " + ", ".join(f"{k} {v:,}" for k, v in w.most_common()),
           f"- versículos con al menos una nota: {len(cubiertos)}/{len(versos)} ({len(cubiertos) / len(versos):.1%})"]
    (C.RAIZ / "informes" / f"seleccion_{libro}.md").write_text("\n".join(lin) + "\n")
    print("\n".join(lin[2:]))


if __name__ == "__main__":
    main()
