#!/usr/bin/env python3
"""Paso 6: traducción de las notas seleccionadas de un capítulo (o de todo el libro).

- Una traducción por nota (DeepSeek, glosario del proyecto en el prompt, temperatura baja).
- Segunda traducción independiente (Gemini) solo para las notas de versículos sensibles: queda en
  "text_es_2" para la adjudicación.
- Idempotente: una nota cuyo inglés no cambió (misma huella) no se vuelve a traducir.
- Salida: traducido/<LIBRO>/<CC>.json  {id: {text_es, lemas_es, modelo, huella, [text_es_2, modelo_2]}}

Uso: python3 scripts/traducir.py JHN [CAP|todos]
"""
import concurrent.futures as cf
import json
import re
import sys

import comun as C

MAX_LOTE = 1800          # palabras de inglés por pedido


def texto_a_traducir(n):
    t = n["text_src"]
    p = n["source"].get("passage")
    if n["layer"] == "padres" and p and t.lstrip().startswith(f"({p})"):
        t = t.lstrip()[len(p) + 2:].lstrip()          # el locus va en la atribución, no en el cuerpo
    # llamadas de nota de la edición inglesa pegadas a la palabra («In Him was life1.», «the preposition by1»)
    return re.sub(NOTA_PEGADA, "", t)


# llamada de nota pegada a una palabra; también se limpia en la salida por si el modelo la copia
NOTA_PEGADA = r"(?<=[a-záéíóúñ])\d{1,2}(?=[\s.,;:?!)»]|$)"


def limpiar(es):
    return re.sub(NOTA_PEGADA, "", es.strip())


def prompt(lote):
    entrada = [{"id": n["id"], "texto": texto_a_traducir(n), "lemas": n.get("lemma_src") or []} for n in lote]
    glos = {}
    for n in lote:
        for t in C.glosario_para(texto_a_traducir(n)):
            glos[t["en"]] = t["es"]
    reglas = "\n".join(f"- {r}" for r in C.TERMINOS["reglas"])
    limpio = lambda k: re.sub(r"\\b|[()?:|\\]", "", k)
    gl = "\n".join("- " + limpio(k) + " -> " + v for k, v in glos.items()) or "- (ninguno)"
    return (f"Eres traductor de comentarios bíblicos y patrísticos del inglés al español para una Biblia de estudio "
            f"basada en la Reina-Valera 1909.\nReglas:\n{reglas}\nGlosario obligatorio para estas notas:\n{gl}\n\n"
            f"Devuelve SOLO un objeto JSON {{\"notas\": [{{\"id\": ..., \"texto\": ..., \"lemas\": [...]}}]}} con "
            f"exactamente los mismos ids y en el mismo orden; 'lemas' traduce cada lema de entrada (misma cantidad).\n"
            f"<<<JSON{json.dumps(entrada, ensure_ascii=False)}JSON>>>")


def lotes(ns):
    actual, w = [], 0
    for n in ns:
        k = len(texto_a_traducir(n).split())
        if actual and w + k > MAX_LOTE:
            yield actual
            actual, w = [], 0
        actual.append(n)
        w += k
    if actual:
        yield actual


def traducir_lote(lote, cadena):
    r, modelo = C.llamar(prompt(lote), cadena)
    salida = {x["id"]: x for x in r.get("notas", []) if isinstance(x, dict) and "id" in x}
    faltan = [n for n in lote if n["id"] not in salida or not (salida[n["id"]].get("texto") or "").strip()]
    if faltan and len(lote) > 1:                       # se reintenta de a una (nunca se fusionan ni dividen)
        for n in faltan:
            salida.update(traducir_lote([n], cadena)[0])
    return {i: v for i, v in salida.items() if i in {n["id"] for n in lote}}, modelo


def main():
    libro = sys.argv[1] if len(sys.argv) > 1 else "JHN"
    pedido = sys.argv[2] if len(sys.argv) > 2 else "1"
    us = C.unidades(libro)
    caps = sorted({C.cap(n["ref"]) for n in us}) if pedido == "todos" else [int(pedido)]
    for c in caps:
        ruta = f"traducido/{libro}/{c:02d}.json"
        hecho = C.cargar(ruta, {})
        ns = sorted([n for n in us if C.cap(n["ref"]) == c], key=lambda n: (C.ver(n["ref"]), n["layer"] != "contexto", n["id"]))
        pend = [n for n in ns if hecho.get(n["id"], {}).get("huella") != C.huella(n["text_src"])]
        pend2 = [n for n in ns if C.es_sensible(n) and "text_es_2" not in hecho.get(n["id"], {})]
        with cf.ThreadPoolExecutor(6) as ex:
            for salida, modelo in ex.map(lambda l: traducir_lote(l, C.TRADUCTOR), list(lotes(pend))):
                for i, x in salida.items():
                    n = next(u for u in pend if u["id"] == i)
                    hecho[i] = {"text_es": limpiar(x["texto"]), "lemas_es": x.get("lemas") or [], "modelo": modelo,
                                "huella": C.huella(n["text_src"])}
            for salida, modelo in ex.map(lambda l: traducir_lote(l, C.CONTROL), list(lotes(pend2))):
                for i, x in salida.items():
                    hecho.setdefault(i, {}).update(text_es_2=limpiar(x["texto"]), modelo_2=modelo)
        C.guardar(ruta, hecho)
        sin = [n["id"] for n in ns if n["id"] not in hecho or not hecho[n["id"]].get("text_es")]
        print(f"cap.{c}: {len(ns)} notas; traducidas ahora {len(pend)}; segunda traducción {len(pend2)}; sin traducir {len(sin)}")


if __name__ == "__main__":
    main()
