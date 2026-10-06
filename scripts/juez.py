#!/usr/bin/env python3
"""Paso 9b: juez de otra familia (Gemini) sobre TODAS las notas del capítulo + compuerta estadística.

Misma lógica que periodico_kindle/calidad (lecciones de Staniloae), en versión compacta:
- Calibración por corrida: se siembran errores reales (oración omitida, número cambiado, negación)
  en traducciones del capítulo; el juez debe marcarlos. Sensibilidad = detectados / sembrados.
- Cada nota marcada NO pasa por el corrector (DeepSeek, con el motivo del juez) y se vuelve a juzgar.
- Compuerta: extremo superior de Wilson (95 %) de los errores que quedan, ajustado por la
  sensibilidad, debe ser < 3 %. Lo que queda va a informes/cola_<LIBRO>_<CC>.json (lo resuelve Claude).
- Caché de veredictos por (id, huella del español): una nota idéntica no se vuelve a juzgar.

Uso: python3 scripts/juez.py JHN [CAP|todos]
"""
import collections
import json
import math
import os
import random
import re
import sys
from concurrent.futures import ThreadPoolExecutor

import comun as C
import traducir as T

UMBRAL = 0.03
LOTE = 12


def wilson_sup(k, n, z=1.96):
    if n == 0:
        return 1.0
    p = k / n
    return (p + z * z / (2 * n) + z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / (1 + z * z / n)


def prompt(pares):
    entrada = [{"id": i, "ingles": en, "espanol": es} for i, en, es in pares]
    return ("Eres revisor de traducciones de comentarios bíblicos y patrísticos (inglés -> español). Para cada par, "
            "responde veredicto SI si el español es fiel y completo (sin omisiones, adiciones ni cambios de sentido, "
            "números o referencias), o NO con un motivo breve y concreto. No juzgues el estilo. Ten en cuenta que "
            "la edición usa el vocabulario de la Reina-Valera 1909 («el Verbo», «Consolador»). "
            "Devuelve SOLO {\"resultados\": [{\"id\": ..., \"veredicto\": \"SI\"|\"NO\", \"motivo\": ...}]}.\n"
            f"<<<JSON{json.dumps(entrada, ensure_ascii=False)}JSON>>>")


def juzgar(pares, cadena=None):
    """Lotes en paralelo (JUEZ_HILOS, 4 por defecto): el razonador tarda minutos por pedido."""
    def lote(k):
        try:
            return C.llamar(prompt(pares[k:k + LOTE]), cadena or C.CONTROL, temperatura=0)
        except RuntimeError as e:                      # el lote queda sin veredicto (pendiente); el resto sigue
            print(f"  lote sin veredicto ({len(pares[k:k + LOTE])} pares): {str(e)[:160]}", flush=True)
            return {}, None
    out = {}
    with ThreadPoolExecutor(int(os.getenv("JUEZ_HILOS", "4"))) as ex:
        for r, modelo in ex.map(lote, range(0, len(pares), LOTE)):
            for x in r.get("resultados", []):
                out[x["id"]] = (str(x.get("veredicto", "")).upper().startswith("S"), x.get("motivo", ""), modelo)
    return out


def sembrar(es, rnd):
    oraciones = re.split(r"(?<=[.;!?])\s+", es)
    if len(oraciones) > 2 and rnd.random() < 0.4:
        return " ".join(oraciones[:-1]), "omisión"
    nums = re.findall(r"\b\d+\b", es)
    if nums and rnd.random() < 0.6:
        n = rnd.choice(nums)
        return re.sub(rf"\b{n}\b", str(int(n) + 3), es, count=1), "número"
    m = re.search(r"\b(es|era|fue|está|tiene)\b", es)
    if m:
        return es[:m.start()] + "no " + es[m.start():], "negación"
    return None, None


def main():
    libro = sys.argv[1] if len(sys.argv) > 1 else "JHN"
    pedido = sys.argv[2] if len(sys.argv) > 2 else "1"
    us = C.unidades(libro)
    caps = sorted({C.cap(n["ref"]) for n in us}) if pedido == "todos" else [int(pedido)]
    rnd = random.Random(17)
    for c in caps:
        try:
            capitulo(libro, c, us, rnd)
        except RuntimeError as e:      # sin modelos: lo juzgado queda en la caché y la próxima corrida sigue
            print(f"cap.{c}: JUEZ INCOMPLETO ({C._sin_claves(str(e))[:300]})", flush=True)
    if pedido == "todos":
        print(compuerta_libro(libro, caps), flush=True)


def compuerta_libro(libro, caps):
    """Compuerta del libro entero: con menos de ~130 notas el extremo de Wilson no baja del 3 % ni con cero
    errores, así que la decisión estadística se toma sumando capítulos. Lo que Claude resolvió con evidencia
    (revision/adjudicaciones y aceptados) no cuenta como error pendiente."""
    resueltos = set(C.cargar(f"revision/adjudicaciones_{libro}.json", {})) | set(C.cargar(f"revision/aceptados_{libro}.json", {}))
    n = quedan = det = tot = sin_juzgar = 0
    for c in caps:
        cache = C.cargar(f"traducido/{libro}/juez_{c:02d}.json", {})
        cal = cache.get("_calibracion", {})
        det, tot = det + cal.get("detect", 0), tot + cal.get("total", 0)
        n_cap = sum(1 for u in C.unidades(libro) if C.cap(u["ref"]) == c)
        juzgadas = sum(1 for k in cache if not k.startswith("_"))
        n += n_cap
        sin_juzgar += n_cap - juzgadas
        quedan += sum(1 for x in C.cargar(f"informes/cola_{libro}_{c:02d}.json", []) if x["id"] not in resueltos)
    sens = det / tot if tot else 0
    sup = wilson_sup(quedan, n) / max(sens, 0.01)
    estado = "APROBADO" if sup < UMBRAL and sens >= 0.8 and not sin_juzgar else "REVISAR"
    if sin_juzgar:
        estado += f" (sin juzgar {sin_juzgar})"
    return (f"libro {libro}: {n} notas; sensibilidad {det}/{tot} = {sens:.0%}; pendientes {quedan}; "
            f"extremo superior ajustado {sup:.2%} -> {estado}")


def capitulo(libro, c, us, rnd):
    ruta, rcache = f"traducido/{libro}/{c:02d}.json", f"traducido/{libro}/juez_{c:02d}.json"
    tr = C.cargar(ruta, {})
    cache = C.cargar(rcache, {})
    ns = [n for n in us if C.cap(n["ref"]) == c and tr.get(n["id"], {}).get("text_es")]
    par = lambda n: (n["id"], T.texto_a_traducir(n), tr[n["id"]]["text_es"])
    vigente = lambda i: (cache.get(i, {}).get("huella") == C.huella(tr[i]["text_es"])
                         and cache[i].get("modelo") in C.CONTROL)      # veredictos de modelos retirados se rehacen
    # censo
    pend = [par(n) for n in ns if not vigente(n["id"])]
    for k in range(0, len(pend), LOTE * 8):          # caché guardada por tramos: un corte no pierde lo juzgado
        for i, (ok, motivo, modelo) in juzgar(pend[k:k + LOTE * 8]).items():
            cache[i] = {"ok": ok, "motivo": motivo, "modelo": modelo, "huella": C.huella(tr[i]["text_es"])}
        C.guardar(rcache, cache)
    # corrección de lo marcado (una vez por motivo)
    malos = [n for n in ns if not cache.get(n["id"], {}).get("ok", True)
             and tr[n["id"]].get("corregido_por_juez") != cache[n["id"]]["motivo"]]
    for n in malos:
        p = T.prompt([n]).replace("Devuelve SOLO", f"Una revisión señaló este problema en una traducción anterior: "
                                                   f"«{cache[n['id']]['motivo']}». Evítalo. Devuelve SOLO")
        r, modelo = C.llamar(p, C.TRADUCTOR)
        x = next((y for y in r.get("notas", []) if y.get("id") == n["id"]), None)
        if x and x.get("texto"):
            tr[n["id"]].update(text_es=T.limpiar(x["texto"]), lemas_es=x.get("lemas") or tr[n["id"]].get("lemas_es", []),
                               modelo=modelo, corregido_por_juez=cache[n["id"]]["motivo"])
    if malos:
        for i, (ok, motivo, modelo) in juzgar([par(n) for n in malos]).items():
            cache[i] = {"ok": ok, "motivo": motivo, "modelo": modelo, "huella": C.huella(tr[i]["text_es"])}
    # calibración con el MISMO modelo que hizo el censo (el que dio la mayoría de los veredictos)
    censo = collections.Counter(cache[n["id"]]["modelo"] for n in ns if n["id"] in cache).most_common(1)
    modelo_censo = censo[0][0] if censo else C.CONTROL[0]
    cal = cache.get("_calibracion", {})
    if cal.get("modelo") != modelo_censo:
        muestra = rnd.sample(ns, min(20, len(ns)))
        sembrados = [(f"mut:{n['id']}", T.texto_a_traducir(n), m) for n in muestra
                     for m, _ in [sembrar(tr[n["id"]]["text_es"], rnd)] if m]
        v = juzgar(sembrados, [modelo_censo])
        cal = {"detect": sum(1 for i, *_ in sembrados if i in v and not v[i][0]),
               "total": sum(1 for i, *_ in sembrados if i in v), "modelo": modelo_censo}
        if cal["total"]:                               # sin veredictos no hay calibración que guardar
            cache["_calibracion"] = cal
    detect, total = cal["detect"], cal["total"]
    sens = detect / total if total else 0
    quedan = [n["id"] for n in ns if not cache.get(n["id"], {}).get("ok", True)]
    sup = wilson_sup(len(quedan), len(ns)) / max(sens, 0.01)
    C.guardar(ruta, tr)
    C.guardar(rcache, cache)
    C.guardar(f"informes/cola_{libro}_{c:02d}.json",
              [{"id": i, "motivo": cache[i]["motivo"], "en": next(par(n)[1] for n in ns if n["id"] == i),
                "es": tr[i]["text_es"]} for i in quedan])
    sin_juzgar = sum(1 for n in ns if not vigente(n["id"]))
    estado = "APROBADO" if sup < UMBRAL and sens >= 0.8 and not sin_juzgar else "REVISAR"
    if sin_juzgar:
        estado += f" (sin juzgar {sin_juzgar})"
    print(f"cap.{c}: {len(ns)} notas; juez {modelo_censo}; sensibilidad {detect}/{total} = {sens:.0%}; marcadas {len(malos)}, "
          f"quedan {len(quedan)}; extremo superior ajustado {sup:.1%} -> {estado}", flush=True)

if __name__ == "__main__":
    main()
