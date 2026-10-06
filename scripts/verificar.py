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
             "have been not by be it his her they them".split())
LIBROS_ORDINAL = ("Corintios|Corinthians|Cor|Reyes|Kings|Samuel|Sam|Crónicas|Chronicles|Chron|Timoteo|Timothy|Tim|"
                  "Tesalonicenses|Thessalonians|Thess|Tes|Pedro|Peter|Pet|Ped|Juan|John|Macabeos|Maccabees|Macc|Esdras")
# «the Word» que nombra al Hijo (no la palabra predicada: «the Word of salvation», «sanctified it by the Word»)
CRISTO_EN = re.compile(r"\b(?:God the Word|(?:is|was) the Word\b(?! of (?:God|the Lord)\b)|uttered the Word|Word of the Father|the Word (?:was|became|"
                       r"made|Himself|incarnate|of God,? (?:who|which|that) (?:was|is|became)))")
# «Palabra» con mayúscula en medio de oración: o es el Hijo («el Verbo», RV1909) o va en minúscula
PALABRA_MAY = re.compile(r"(?<![.!?¿¡«»“”\"(\n]) (?:\w+ )?Palabra\b")
# remisiones que no son libros: «Véase 8:48» (mismo libro), «Infra 17:24», «Ep. 112:100» (cartas de Agustín)
NO_LIBRO = {"En", "Y", "Cf", "Véase", "Vea", "Ver", "Cf", "Comp", "Infra", "Supra", "Ep", "Epist", "Serm", "Hom", "Tract", "Tr", "Cap", "Cp", "Ibid", "Lib", "Mor", "Aug"}
INGLES_CURSIVA = INGLES | {"his", "he", "him", "you", "your", "will", "for", "all", "one", "who", "with", "our", "we", "to", "out"}
ARCAICO = re.compile(r"\b(?:saith|hath|thou|thee|thy|doth|dost|art|ye)\b")
COMENTARIO = re.compile(r"(?i:\b(?:nota del traductor|traducción:|aquí est[aá] la traducción|here is|translator'?s note)\b)|\[ES\] ")


def numeros(t):
    t = B.normalizar(t)          # «Luke xxii. 19» y «Lucas 22:19» cuentan igual (romanos de la edición inglesa)
    # «I Corintios» = «1 Corinthians»; solo ante libros con ordinal («I Am» de Jn 8,58 no es un número)
    t = re.sub(r"\b(III|II|I)(?= (?:" + LIBROS_ORDINAL + r")\b)", lambda m: str(len(m.group(1))), t)
    return collections.Counter(re.findall(r"\d+", t))


def oraciones(x):
    """Fin de oración = signo + cierre opcional + mayúscula siguiente; las abreviaturas de las referencias
    («tom. vi. c. 15», «i. e.», «Gen. 1:26») no cuentan."""
    x = re.sub(r"\([^()]{0,60}\)", "", x)                          # referencias entre paréntesis
    x = re.sub(r"\bi\. ?e\.", "", x)                                 # «i. e. I will…»
    return len(re.findall(r"[.!?][\"”’»)]*\s+(?=[«\"“¿¡(]?[A-ZÁÉÍÓÚÑ])", x)) + 1


def revisar(n, t, rv):
    t = dict(t or {})
    t.update(C.adjudicacion(n["id"], n["ref"].split(".")[0], t.get("text_es")))
    fallos = []
    src, es = T.texto_a_traducir(n), (t or {}).get("text_es") or ""
    if not es:
        return ["1 sin traducir"]
    if t.get("adjudicacion_pendiente"):
        fallos.append(f"+ adjudicación de Claude que ya no se aplica (la nota cambió): {t['adjudicacion_pendiente']}")
    for frag in re.findall(r"⸢([^⸣]+)⸣", es):            # lema o frase en cursiva que quedó en inglés
        pal = re.findall(r"[a-z]+", frag.lower())
        if len(pal) >= 2 and frag in src and any(w in INGLES_CURSIVA for w in pal):
            fallos.append(f"5 cursiva sin traducir: «{frag}»")
    if numeros(src) != numeros(es):
        dif = (numeros(src) - numeros(es)) + (numeros(es) - numeros(src))
        fallos.append(f"2 números distintos: {dict(dif)}")
    if n["layer"] in ("griego_intro", "glosario_g") and src.count("\n\n") != es.count("\n\n"):   # títulos y viñetas
        fallos.append(f"3 párrafos {src.count(chr(10) * 2) + 1} -> {es.count(chr(10) * 2) + 1}")
    if abs(src.count("⸢") - es.count("⸢")) > 1:
        fallos.append(f"3 cursivas {src.count('⸢')} -> {es.count('⸢')}")
    for term in C.glosario_para(src):
        if term.get("prohibido") and re.search(term["prohibido"], es):
            fallos.append(f"4 término prohibido para «{term['es']}»")
    if PALABRA_MAY.search(es):
        fallos.append("4 «Palabra» con mayúscula (el Hijo es «el Verbo»; si no, minúscula)")
    if CRISTO_EN.search(src) and "Verbo" not in es:
        fallos.append("4 falta «Verbo»")
    pal = re.findall(r"[a-záéíóúñ]+", es.lower())
    if pal and sum(w in INGLES for w in pal) / len(pal) > 0.03:
        fallos.append("5 inglés residual")
    if re.search(r"&\w+;|<[a-z/]|rc://", es) or COMENTARIO.search(es):
        fallos.append("5 HTML, marca de prueba o comentario del modelo")
    # las traducciones inglesas del s. XIX (NPNF, Newman, Pusey: «saith», «thou hast») son más largas: mediana 0,97 y p5 0,88 en Juan,
    # 26 pares entre 0,79 y 0,89 leídos completos el 02-10-2026 -> mínimo 0,78; la omisión la mide el conteo de oraciones
    r = len(es) / max(1, len(src))
    # notas de unfoldingWord: el español queda más compacto («If it would be helpful in your language, you could» ->
    # «Si en su idioma sería útil, podría»); 40 pares entre 0,81 y 0,90 leídos el 06-10-2026, completos -> 0,8
    minimo = (0.78 if n["layer"] in ("padres", "reforma") or ARCAICO.search(src)
              else 0.8 if n["layer"] in ("griego", "griego_c", "griego_intro", "glosario_g") else 0.9)
    if len(src) > 300 and not minimo <= r <= 1.5:
        fallos.append(f"6 razón de longitud {r:.2f}")
    o_en, o_es = (oraciones(x) for x in (src, es))
    if o_en >= 4 and o_es < 0.75 * o_en:
        fallos.append(f"6 posible omisión: {o_en} oraciones -> {o_es}")
    if not n.get("license") or not n.get("provenance"):
        fallos.append("7 sin licencia o procedencia")
    if n["layer"] in ("padres", "reforma") and not (n["source"].get("work") and (n["source"].get("passage") or n["source"].get("work"))):
        fallos.append("7 cita patrística sin obra/pasaje")
    for a in (t or {}).get("lemas_rv1909", []):
        if a["lema"] and a["lema"] not in rv.get(a["ref"], {}).get("texto", ""):
            fallos.append(f"8 lema «{a['lema']}» no está en {a['ref']}")
    malas = []
    norm = B.normalizar(es, malas, None)
    for x in re.findall(r"(?<!⸣ )\b((?:[1-3I]{1,3} )?[A-Z][a-zé]+\.? \d+:\d+)", norm):
        if x.split()[-2].rstrip(".") in NO_LIBRO:
            continue
        fallos.append(f"+ cita sin forma única (libro inglés o abreviatura desconocida): {x}")
    for x in re.findall(r"(?:\(|; )(?!⸢)([A-ZÁÉÍÓÚ][a-záéíóú]+)\.? \d{1,3}\.?(?:\)|;)", norm):          # capítulo entero
        if x in NO_LIBRO:
            continue
        fallos.append(f"+ cita sin forma única (libro inglés o abreviatura desconocida): {x}")
    fallos += [f"+ cita bíblica inexistente: {x}" for _, x in malas]
    acept = C.cargar(f"revision/aceptados_{n['ref'].split('.')[0]}.json", {}).get(n["id"], {})   # hallazgos leídos y aceptados, con evidencia
    return [f for f in fallos if not any(f.startswith(a) for a in acept.get("puntos", []))]


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
