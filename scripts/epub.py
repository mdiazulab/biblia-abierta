#!/usr/bin/env python3
"""Paso 10: EPUB 3 — RV1909 con notas emergentes por capa y versículo.

Cada versículo lleva, al final, una llamada por capa que tenga notas («C» Contexto, «P» Padres);
la nota emergente agrupa todas las notas de esa capa para ese versículo, con el lema RV1909 en
negrita (o «v. N:»), y cada cita patrística con autor, tradición (Oriente/Occidente), obra, pasaje
y edición. Las citas bíblicas de las notas pasan por biblia.normalizar (forma única).
Páginas de fuentes, atribuciones y licencias. Índice sin numeración automática (lección de Ware).

Uso: python3 scripts/epub.py JHN [CAP|todos]  -> epub/Juan_RV1909_estudio.epub
"""
import datetime
import html
import re
import sys
import uuid
import zipfile

import biblia as B
import comun as C

from libros import LIBROS
LIBRO_ES = {k: v["es"] for k, v in LIBROS.items()}
AUTORES = {"Augustine of Hippo": "San Agustín", "John Chrysostom": "San Juan Crisóstomo",
           "Cyril of Alexandria": "San Cirilo de Alejandría", "Theophylact of Ohrid": "Teofilacto de Ohrid",
           "Origen of Alexandria": "Orígenes", "Alcuin of York": "Alcuino de York", "Bede": "San Beda",
           "Hilary of Poitiers": "San Hilario de Poitiers", "Gregory the Dialogist": "San Gregorio Magno",
           "Tertullian": "Tertuliano", "Irenaeus": "San Ireneo", "Cyprian": "San Cipriano",
           "Clement of Alexandria": "Clemente de Alejandría", "Hippolytus of Rome": "San Hipólito",
           "Ignatius of Antioch": "San Ignacio de Antioquía", "Athanasius of Alexandria": "San Atanasio",
           "Cyril of Jerusalem": "San Cirilo de Jerusalén", "Ambrose of Milan": "San Ambrosio",
           "Philoxenus of Mabbug": "Filoxeno de Mabbug", "Apostolic Constitutions": "Constituciones Apostólicas",
           "Leo the Great": "San León Magno", "Basil of Caesarea": "San Basilio", "Gregory of Nyssa": "San Gregorio de Nisa",
           "Chrysologus": "San Pedro Crisólogo"}
OBRAS = [(r"^Tractates on John\s*(\d+)?", r"Tratados sobre el Evangelio de Juan \1"),
         (r"^Homily on the Gospel of John\s*(\d+)?", r"Homilías sobre el Evangelio de Juan \1"),
         (r"^Commentary on the Gospel of John[,\s-]*Book\s*(\w+)", r"Comentario al Evangelio de Juan, libro \1"),
         (r"^Commentary on the Gospel of John", "Comentario al Evangelio de Juan"),
         (r"^On the Trinity", "Sobre la Trinidad"), (r"^Against Heresies", "Contra las herejías"),
         (r"^Catena Aurea.*", "Catena Aurea")]
FICHAS = C.cargar("glosario/autores.json", {}).get("autores", {})
AUTORES.update({k: v["es"] for k, v in FICHAS.items()})


def ancla_autor(a):
    return "a-" + re.sub(r"[^a-z0-9]+", "-", a.lower()).strip("-")


def md_xhtml(md):
    """Markdown mínimo de editorial/*.md: #, ##, ###, párrafos, listas «- », *cursiva*, **negrita**."""
    def fmt(s):
        s = x(s)
        s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
        return re.sub(r"\*(.+?)\*", r"<em>\1</em>", s)
    out = []
    for bloque in md.strip().split("\n\n"):
        parrafo, items = [], []
        for linea in bloque.split("\n"):
            if linea.startswith("- "):
                items.append(linea[2:])
            elif items and linea.startswith("  "):          # continuación de un ítem
                items[-1] += " " + linea.strip()
            else:
                parrafo.append(linea)
        texto = " ".join(parrafo).strip()
        m = re.match(r"(#{1,3}) (.*)", texto)
        if m:
            out.append(f"<h{len(m.group(1))}>{fmt(m.group(2))}</h{len(m.group(1))}>")
        elif texto:
            out.append(f"<p>{fmt(texto)}</p>")
        if items:
            out.append("<ul>" + "".join(f"<li>{fmt(i)}</li>" for i in items) + "</ul>")
    return "\n".join(out)


def padres_xhtml(usados):
    claves = sorted({n["source"]["author"] for n in usados if n["layer"] in ("padres", "reforma")} |
                    ({"Catena Aurea"} if any(n["source"]["work"].startswith("Catena") for n in usados) else set()),
                    key=lambda a: re.sub(r"^(San|Santa|El) ", "", AUTORES.get(a, a)))
    cuerpo = ["<h1>Los autores en su contexto</h1>",
              "<p>Cada Padre escribió en una época, un lugar y una situación concretas: controversias, predicación, "
              "persecución, la escuela en que se formó y el texto bíblico que leía. Estas fichas, redactadas para esta "
              "edición, ayudan a leer sus notas en ese contexto y a distinguir su aplicación de la intención del autor "
              "bíblico.</p>"]
    for a in claves:
        f = FICHAS.get(a)
        if not f:
            continue
        trad = "Oriente" if f["tradicion"] == "oriente" else "Occidente"
        cuerpo.append(f'<h2 id="{ancla_autor(a)}">{x(f["es"])}</h2><p class="fuente">{x(f["fechas"])} · {x(f["lugar"])} · {trad}</p>'
                      f'<p>{x(f["contexto"])}</p>')
    return "\n".join(cuerpo)


CSS = """body { font-family: serif; line-height: 1.5; margin: 0 4%; }
h1 { font-size: 1.6em; text-align: center; font-weight: bold; margin: 1.5em 0 1em; }
h2 { font-size: 1.15em; font-weight: bold; margin: 1.4em 0 0.6em; }
p { margin: 0 0 0.35em; text-indent: 0; text-align: justify; }
.v sup.n { font-size: 0.65em; color: #8a1c1c; font-weight: bold; margin-right: 0.15em; }
a.ll { text-decoration: none; font-size: 0.7em; vertical-align: super; line-height: 0; font-family: sans-serif; }
a.ll.c { color: #1f5a8a; } a.ll.g { color: #6a2c7a; } a.ll.p { color: #7a4b00; } a.ll.r { color: #2e6b2e; }
.grc { font-weight: bold; }
section.notas { margin-top: 2.5em; font-size: 0.9em; border-top: 1px solid #999; }
aside { margin: 1em 0; }
aside h3 { font-size: 0.95em; font-weight: bold; margin: 0.8em 0 0.3em; }
aside p { text-indent: 0; }
.lema { font-weight: bold; }
.autor { font-weight: bold; font-variant: small-caps; }
.trad { font-size: 0.8em; color: #555; }
.fuente { font-size: 0.82em; color: #444; font-style: italic; }
nav#toc ol { list-style-type: none; padding-left: 1.2em; } nav#toc > ol { padding-left: 0; }
nav#toc li { text-align: left; margin: 0.25em 0; } nav#toc a { text-decoration: none; }
.portada { text-align: center; margin-top: 30%; }
a.autor { color: inherit; text-decoration: none; }
ul { margin: 0.3em 0 0.6em 1.2em; padding: 0; } li { margin: 0.15em 0; text-align: left; }
h3 { font-size: 1em; font-weight: bold; margin: 1em 0 0.4em; }
"""


def x(t):
    return html.escape(t, quote=False)


def inline(t):
    """Escapa, normaliza citas bíblicas y convierte ⸢…⸣ en cursiva."""
    t = B.normalizar(t)
    t = x(t).replace("⸢", "<em>").replace("⸣", "</em>")
    t = t.replace("\n\n", "</p><p>")
    return t + "</em>" * (t.count("<em>") - t.count("</em>"))


# títulos españoles por prefijo del título inglés de HCF; el resto («Book 4, Chapter XI») se traduce aparte
TITULOS = {
    "Homily on Hebrews": "Homilías sobre la Epístola a los Hebreos", "Commentary on Hebrews": "Comentario a la Epístola a los Hebreos", "Homily on the Gospel of John": "Homilías sobre el Evangelio de Juan",
    "Tractates on John": "Tratados sobre el Evangelio de Juan", "Commentary on the Gospel of John": "Comentario al Evangelio de Juan",
    "The Christian Topography": "Topografía cristiana", "The Stromata": "Stromata", "An Answer to the Jews": "Respuesta a los judíos",
    "City of God": "La ciudad de Dios", "Confessions": "Confesiones", "Shepherd of Hermas, Vision": "El Pastor, Visión",
    "Shepherd of Hermas, Similitude": "El Pastor, Comparación", "Shepherd of Hermas, Commandment": "El Pastor, Mandamiento",
    "Catechetical Lecture": "Catequesis", "13 Ascetic Discourses": "Discursos ascéticos", "On Modesty": "Sobre la modestia",
    "Against Marcion": "Contra Marción", "Letter to the Corinthians (Clement": "Carta a los Corintios",
    "Clement's First Letter to the Corinthians": "Primera carta a los Corintios", "On Prayer": "Sobre la oración",
    "On Exhortation to Chastity": "Exhortación a la castidad", "Epistles on the Arian Heresy - Epistle Catholic": "Carta católica sobre la herejía arriana",
    "Epistles on the Arian Heresy - To Alexander": "Carta a Alejandro de Constantinopla sobre la herejía arriana",
    "Constitutions of the Holy Apostles": "Constituciones de los santos apóstoles", "Discourses Against the Arians": "Discursos contra los arrianos",
    "Methodius Discourse V. Thallousa": "Banquete, discurso V (Talusa)", "Methodius Discourse III. Thaleia": "Banquete, discurso III (Talía)",
    "Methodius Discourse VII. Procilla": "Banquete, discurso VII (Procila)", "Methodius Oration Concerning Simeon and Anna": "Discurso sobre Simeón y Ana",
    "Methodius From the Discourse on the Resurrection": "Del discurso sobre la resurrección",
    "Second Epistle To The Corinthians (Pseudo-Clement": "Segunda carta de Clemente", "On the Veiling of Virgins": "Sobre el velo de las vírgenes",
    "On Monogamy": "Sobre la monogamia", "Of Patience": "Sobre la paciencia", "On Repentance": "Sobre el arrepentimiento",
    "Exposition of the Christian Faith": "Exposición de la fe cristiana", "Exhortation to the Heathen": "Exhortación a los paganos",
    "Treatise XI Exhortation to Martyrdom Addressed to Fortunatus": "Tratado XI: exhortación al martirio, a Fortunato",
    "Treatise XII Three Books of Testimonies Against the Jews": "Tratado XII: tres libros de testimonios contra los judíos",
    "Pseudo-Cyprian On the Glory of Martyrdom": "Pseudo-Cipriano, Sobre la gloria del martirio", "Epistle": "Carta",
    "Epistle III.-To Fabius Bishop of Antioch": "Carta III, a Fabio de Antioquía", "Hippolytus Refutation of All Heresies": "Refutación de todas las herejías",
    "Dubious Hippolytus Fragments": "Fragmentos dudosos", "Fragments - Dogmatic and Historical": "Fragmentos dogmáticos e históricos",
    "Epistle of Ignatius to the Smyrnaeans": "Carta a los esmirniotas", "Epistle of Ignatius to the Trallians": "Carta a los tralianos",
    "Epistle of Ignatius to the Magnesians": "Carta a los magnesios",
    "Epistle of Pseudo-Ignatius to Hero, a Deacon of Antioch": "Pseudo-Ignacio, Carta a Herón, diácono de Antioquía",
    "Fragments from the Lost Writings of Irenaeus": "Fragmentos de obras perdidas", "Irenaeus Against Heresies": "Contra los herejes",
    "Dialogue with Trypho": "Diálogo con Trifón", "The First Apology": "Primera apología", "The Divine Institutes": "Instituciones divinas",
    "Two Epistles on Virginity": "Dos cartas sobre la virginidad", "The Apology": "Apología", "On Baptism": "Sobre el bautismo",
    "On the Apparel of Women": "Sobre el adorno de las mujeres", "The Prescription Against Heretics": "Prescripción contra los herejes",
    "Pseudo-Tertullian Against All Heresies": "Pseudo-Tertuliano, Contra todas las herejías",
    "Pseudo-Tertullian AGAINST ALL HERESIES": "Pseudo-Tertuliano, Contra todas las herejías", "To His Wife": "A su esposa",
    "From His Seven Books of Hypotyposes or Outlines": "Hipotiposis (fragmentos)", "The Didache": "Didaché", "Letter": "Carta",
    "Concerning Repentance": "Sobre la penitencia", "On the Spirit": "Sobre el Espíritu Santo", "On the Trinity": "La Trinidad",
    "Against Praxeas": "Contra Práxeas", "Sermons on the Song of Songs": "Sermones sobre el Cantar de los Cantares",
}
RESTO = [(r"\bBooks?\b", "libro"), (r"\bChapters?\b", "cap."), (r"\bDiscourse\b", "discurso"), (r"\bEpistle\b", "carta"),
         (r"\bSection\b", "sección"), (r"\bHomily\b", "homilía"), (r"\s*--\s*On Faith: First Discourse on Simplicity", ": sobre la fe; sobre la sencillez"),
         (r"\s*--\s*On Faith", ": sobre la fe"), (r"\s*--\s*On Gluttony", ": sobre la gula"), (r"^\)\s*", "")]


def obra_es(w):
    for pat, rep in OBRAS:
        if re.match(pat, w):
            return re.sub(pat, rep, w).strip()
    base = max((k for k in TITULOS if w.startswith(k)), key=len, default=None)
    if not base:
        return w
    resto = w[len(base):]
    for pat, rep in RESTO:
        resto = re.sub(pat, rep, resto)
    return (TITULOS[base] + resto).strip().rstrip(",")


def atribucion(n):
    s = n["source"]
    autor = AUTORES.get(s["author"], s["author"])
    trad = {"oriente": "Oriente", "reforma": "Reforma"}.get(n["tradition"], "Occidente")
    if s["author"] in FICHAS:
        trad += ", " + FICHAS[s["author"]]["fechas"]
    if s["work"].startswith("Catena"):
        donde = (f"<em>{x(s['passage'])}</em>, " if s.get("passage") and s["passage"] != s["work"] else "") + "en la <em>Catena Aurea</em> de santo Tomás de Aquino"
    else:
        donde = f"<em>{x(obra_es(s['work']))}</em>"
    ed = s.get("edition") or ""
    if s["work"].startswith("Catena"):            # la edición repite autor y obra: queda solo «trad. …»
        ed = re.sub(r"^.*?Catena Aurea,?\s*", "", ed)
        donde, ed = (f"{donde}, {x(ed)}", "") if ed else (donde, "")
    nombre = (f'<a class="autor" href="padres.xhtml#{ancla_autor(s["author"])}">{x(autor)}</a>' if s["author"] in FICHAS
              else f'<span class="autor">{x(autor)}</span>')
    return (f'{nombre} <span class="trad">({trad})</span>',
            f'<p class="fuente">{donde}.' + (f" {x(ed)}" if ed else "") + "</p>")


DEPURADO = {}


def _norm(s):
    return re.sub(r"\W+", " ", s.lower()).strip()


def _oraciones(s):
    return [o for o in re.split(r"(?<=[.!?»”\"])\s+(?=[«“\"¿¡(A-ZÁÉÍÓÚÑ])", s.strip()) if o]


def sin_repeticiones(libro, us, tr):
    """HCF reparte un mismo pasaje entre versículos vecinos: el párrafo que repite uno ya mostrado por el mismo
    autor (hasta 6 notas antes) se quita de la nota posterior. Idéntico: se quita entero (los conteos de párrafos
    inglés/español coinciden en todos los casos). Contenido con agregado: se quitan sus primeras/últimas oraciones
    si el conteo de oraciones coincide; si no, queda y se informa. Devuelve {id: texto_es depurado} e informe."""
    por, salida, informe = {}, {}, []
    for n in sorted((n for n in us if n["layer"] == "padres"), key=lambda n: (C.cap(n["ref"]), C.ver(n["ref"]), n["id"])):
        por.setdefault(n["source"]["author"], []).append(n)
    for ns in por.values():
        for i, y in enumerate(ns):
            es = (tr.get(y["id"]) or {}).get("text_es")
            if not es:
                continue
            en_p, es_p = y["text_src"].split("\n\n"), es.split("\n\n")
            if len(en_p) != len(es_p):
                continue
            previos = [_norm(p) for x in ns[max(0, i - 6):i] for p in x["text_src"].split("\n\n") if len(_norm(p)) > 60]
            nuevos = []
            for pe, ps in zip(en_p, es_p):
                q = _norm(pe)
                if q in previos:
                    informe.append(f"{y['id']}: párrafo repetido quitado")
                    continue
                # contenido: solo párrafos largos; uno breve suele ser la cita del versículo o una frase de enlace
                base = next((p for p in previos if len(p) > 250 and p in q), None)
                if base:
                    oe, os_ = _oraciones(pe), _oraciones(ps)
                    k = sum(1 for o in oe if _norm(o) and _norm(o) in base)
                    if len(oe) == len(os_) and 0 < k < len(oe):
                        pref = all(_norm(o) in base for o in oe[:k])
                        ps = " ".join(os_[k:] if pref else os_[:len(os_) - k])
                        informe.append(f"{y['id']}: {k} oración(es) repetida(s) quitada(s)")
                    else:
                        informe.append(f"{y['id']}: párrafo con repetición parcial SIN quitar (oraciones {len(oe)}/{len(os_)})")
                nuevos.append(ps)
            if len(nuevos) != len(es_p) or "\n\n".join(nuevos) != es:
                salida[y["id"]] = "\n\n".join(nuevos)
    return salida, informe


def griego_cab(n, t):
    """«τετελείωκεν… (hizo perfectos): » — la frase griega y, entre paréntesis, el tramo de la RV1909 al que se
    ancló la glosa (o la glosa traducida si no se ancló)."""
    lemas = [a["lema"] for a in t.get("lemas_rv1909", []) if a.get("lema")] or [l for l in t.get("lemas_es") or [] if l]
    lema = f' <span class="lema">({x("; ".join(lemas))})</span>' if lemas else ""
    return f'<span class="grc" lang="grc" xml:lang="grc">{x(n["griego"])}</span>{lema}: '


def capitulo_xhtml(libro, c, rv, ns, tr):
    por = {}
    for n in ns:
        t = dict(tr.get(n["id"], {}))
        t.update(C.adjudicacion(n["id"], libro, t.get("text_es")))
        if n["id"] in DEPURADO:
            t["text_es"] = DEPURADO[n["id"]]
        if not t.get("text_es"):
            continue
        ancla = n["ref"]
        anclas = t.get("lemas_rv1909") or []
        if anclas and anclas[0].get("ref"):
            ancla = anclas[0]["ref"]
        capa = {"contexto": "c", "reforma": "r", "griego": "g"}.get(n["layer"], "p")
        por.setdefault((ancla, capa), []).append((n, t))
    cuerpo, notas = [], []
    for ref in [r for r in rv if C.cap(r) == c]:
        v = C.ver(ref)
        llamadas = ""
        for capa, letra in (("c", "C"), ("g", "G"), ("p", "P"), ("r", "R")):
            if (ref, capa) in por:
                nid = f"n{c}-{v}-{capa}"
                llamadas += f' <a class="ll {capa}" epub:type="noteref" href="#{nid}" id="r{nid}">{letra}</a>'
                bloques = []
                for n, t in por[(ref, capa)]:
                    if capa == "c":
                        lemas = [a["lema"] for a in t.get("lemas_rv1909", []) if a.get("lema")]
                        cab = (f'<span class="lema">{x("; ".join(lemas))}:</span> ' if lemas
                               else f'<span class="lema">v. {C.ver(n["ref"])}' +
                               (f'-{C.ver(n["ref_fin"])}' if n.get("ref_fin", n["ref"]) != n["ref"] else "") + ":</span> ")
                        bloques.append(f"<p>{cab}{inline(t['text_es'])}</p>")
                    elif capa == "g":
                        bloques.append(f"<p>{griego_cab(n, t)}{inline(t['text_es'])}</p>")
                    else:
                        quien, fuente = atribucion(n)
                        bloques.append(f"<p>{quien}: {inline(t['text_es'])}</p>{fuente}")
                titulo = {"c": "Contexto", "g": "El texto griego", "p": "Padres de la Iglesia", "r": "Reforma"}[capa] + f" — {LIBRO_ES[libro]} {c}:{v}"
                notas.append(f'<aside epub:type="footnote" id="{nid}"><h3><a href="#r{nid}">{x(titulo)}</a></h3>'
                             + "".join(bloques) + "</aside>")
        texto = x(rv[ref]["texto"]).replace("⸢", "<em>").replace("⸣", "</em>")
        cuerpo.append(f'<p class="v" id="v{c}-{v}"><sup class="n">{v}</sup>{texto}{llamadas}</p>')
    return (f'<h1 id="c{c}">{LIBRO_ES[libro]} {c}</h1>\n' + "\n".join(cuerpo)
            + '\n<section class="notas" epub:type="footnotes">' + "\n".join(notas) + "</section>")


def xhtml(titulo, cuerpo):
    return ('<?xml version="1.0" encoding="utf-8"?>\n<!DOCTYPE html>\n<html xmlns="http://www.w3.org/1999/xhtml" '
            'xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="es" lang="es"><head><meta charset="utf-8"/>'
            f'<title>{x(titulo)}</title><link rel="stylesheet" type="text/css" href="estilo.css"/></head>'
            f"<body>{cuerpo}</body></html>")


def paginas_previas(libro, us, tr_total):
    usados = [n for n in us if n["id"] in tr_total]
    autores = sorted({AUTORES.get(n["source"]["author"], n["source"]["author"]) for n in usados if n["layer"] == "padres"})
    reforma = sorted({AUTORES.get(n["source"]["author"], n["source"]["author"]) for n in usados if n["layer"] == "reforma"})
    griego = any(n["layer"] == "griego" for n in usados)
    ediciones = sorted({n["source"]["edition"] for n in usados if n["layer"] in ("padres", "reforma") and n["source"].get("edition")})
    portada = (f'<div class="portada"><h1>{LIBRO_ES[libro]}</h1><p style="text-align:center">Reina-Valera 1909</p>'
               '<p style="text-align:center">Biblia de Estudio Abierta — notas de contexto'
               + (', del texto griego' if griego else '') + ', de los Padres de la Iglesia'
               + (' y de la Reforma' if reforma else '') + '</p>'
               '<p style="text-align:center">Edición piloto</p></div>')
    fuentes = ("<h1>Fuentes y cómo leer las notas</h1>"
               "<p>Cada versículo lleva llamadas por capa: <strong>C</strong> (contexto histórico y literario), "
               + ("<strong>G</strong> (el texto griego: qué dice literalmente una frase, qué tiempo verbal usa y, cuando "
                  "admite más de una lectura, cuáles son, numeradas, con una paráfrasis de cada una), " if griego else "")
               + "<strong>P</strong> (Padres de la Iglesia) y, donde la hay, <strong>R</strong> (Reforma: el comentario de "
               "Juan Calvino). En cada cita patrística se indica la tradición (Oriente u "
               "Occidente), la obra, el pasaje y la edición inglesa de dominio público desde la que se tradujo. "
               "El nombre de cada autor lleva a su ficha en «Los autores en su contexto» (fechas, lugar y situación "
               "en que escribió).</p>"
               "<p>Texto bíblico: Reina-Valera 1909 (dominio público), con las tildes de monosílabos actualizadas "
               "(«fue», «a», «dio»); ninguna palabra cambiada. Las palabras en cursiva del texto bíblico son las que los "
               "traductores de 1909 añadieron para el sentido.</p>"
               f"<h2>Padres citados</h2><p>{x(', '.join(autores))}.</p>"
               + (f"<h2>Reforma</h2><p>{x(', '.join(reforma))}.</p>" if reforma else "")
               + "<h2>Ediciones de las traducciones</h2>" + "".join(f"<p>{x(e)}</p>" for e in ediciones))
    licencias = ("<h1>Atribuciones y licencias</h1>"
                 "<p>Notas de contexto adaptadas de <em>Aquifer Open Study Notes</em> © Mission Mutual, adaptación de "
                 "<em>Tyndale Open Study Notes</em> © 2023 Tyndale House Publishers, CC BY-SA 4.0. Traducido y modificado.</p>"
                 "<p>Citas patrísticas: compilación de Historical Christian Faith (dominio público) sobre traducciones "
                 "inglesas de dominio público; la Catena Aurea en la traducción de J. H. Newman (Oxford, 1841-45).</p>"
                 + ("<p>Capa «Reforma»: Juan Calvino, <em>Comentario a la Epístola a los Hebreos</em> (1549), en la "
                    "traducción inglesa de J. Owen (Calvin Translation Society, Edimburgo, 1853), de dominio público, según el "
                    "texto de la Christian Classics Ethereal Library.</p>" if reforma else "")
                 + ("<p>Notas sobre el texto griego (capa G) adaptadas de <em>unfoldingWord® Translation Notes</em> © 2022 "
                    "unfoldingWord, CC BY-SA 4.0, en la edición de Aquifer (release v91). Seleccionadas, abreviadas (se "
                    "quitaron las indicaciones dirigidas a traductores), traducidas y modificadas; unfoldingWord no respalda "
                    "necesariamente estos cambios.</p>" if griego else "") +
                 "<p>Esta edición (traducción al español, notas y maquetación) se publica bajo licencia Creative Commons "
                 "Atribución-CompartirIgual 4.0 Internacional (https://creativecommons.org/licenses/by-sa/4.0/). "
                 "Es gratuita y puede copiarse, adaptarse y redistribuirse con la misma licencia.</p>"
                 "<p>La introducción y las fichas «Los autores en su contexto» fueron redactadas para esta edición "
                 "(misma licencia).</p>")
    return portada, fuentes, licencias


def main():
    libro = sys.argv[1] if len(sys.argv) > 1 else "JHN"
    pedido = sys.argv[2] if len(sys.argv) > 2 else "1"
    rv = C.cargar(f"normalizado/rv1909/{libro}.json")
    us = C.unidades(libro)
    caps = sorted({C.cap(r) for r in rv}) if pedido == "todos" else [int(pedido)]
    archivos, tr_total = {}, {}
    for c in sorted({C.cap(r) for r in rv}):
        tr_total.update(C.cargar(f"traducido/{libro}/{c:02d}.json", {}))
    for i, v in tr_total.items():                      # adjudicaciones antes de comparar repeticiones
        tr_total[i] = {**v, **C.adjudicacion(i, libro, v.get("text_es"))}
    depurado, informe = sin_repeticiones(libro, us, tr_total)
    DEPURADO.clear(); DEPURADO.update(depurado)
    (C.RAIZ / "informes" / f"repeticiones_{libro}.md").write_text("# Repeticiones entre notas vecinas\n\n" + "\n".join(f"- {x}" for x in informe) + "\n")
    print(f"repeticiones: {len(informe)} ({sum('SIN' in x for x in informe)} sin quitar)")
    for c in caps:
        tr = C.cargar(f"traducido/{libro}/{c:02d}.json", {})
        archivos[f"c{c:02d}.xhtml"] = xhtml(f"{LIBRO_ES[libro]} {c}",
                                            capitulo_xhtml(libro, c, rv, [n for n in us if C.cap(n["ref"]) == c], tr))
    portada, fuentes, licencias = paginas_previas(libro, us, tr_total)
    intro = C.RAIZ / "editorial" / f"{libro}.md"
    previas = {"portada.xhtml": xhtml("Portada", portada)}
    if intro.exists():
        previas["introduccion.xhtml"] = xhtml("Introducción", md_xhtml(intro.read_text()))
    previas["fuentes.xhtml"] = xhtml("Fuentes", fuentes)
    usados = [n for n in us if n["id"] in tr_total]
    archivos = {**previas, **archivos, "padres.xhtml": xhtml("Los autores en su contexto", padres_xhtml(usados)),
                "licencias.xhtml": xhtml("Licencias", licencias)}
    items = "".join(f'<li><a href="c{c:02d}.xhtml">{LIBRO_ES[libro]} {c}</a></li>' for c in caps)
    li_intro = ('<li><a href="introduccion.xhtml">Introducción: la carta en su contexto</a></li>'
                if "introduccion.xhtml" in archivos else "")
    nav = xhtml("Índice", f'<nav epub:type="toc" id="toc"><h1>Índice</h1><ol>{li_intro}'
                '<li><a href="fuentes.xhtml">Fuentes y cómo leer las notas</a></li>'
                f'<li><a href="c{caps[0]:02d}.xhtml">{x(LIBROS[libro]["titulo"])}</a><ol>{items}</ol></li>'
                '<li><a href="padres.xhtml">Los autores en su contexto</a></li>'
                '<li><a href="licencias.xhtml">Atribuciones y licencias</a></li></ol></nav>')
    ident = f"urn:uuid:{uuid.uuid5(uuid.NAMESPACE_URL, 'biblia-abierta/' + libro)}"
    hoy = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    orden = list(archivos)
    manifest = "".join(f'<item id="i{k}" href="{f}" media-type="application/xhtml+xml"/>' for k, f in enumerate(orden))
    spine = "".join(f'<itemref idref="i{k}"/>' for k in range(len(orden)))
    opf = ('<?xml version="1.0" encoding="utf-8"?><package xmlns="http://www.idpf.org/2007/opf" version="3.0" '
           'unique-identifier="uid" xml:lang="es"><metadata xmlns:dc="http://purl.org/dc/elements/1.1/">'
           f'<dc:identifier id="uid">{ident}</dc:identifier><dc:title>{LIBRO_ES[libro]} — Biblia de Estudio Abierta (RV1909)</dc:title>'
           '<dc:language>es</dc:language><dc:rights>CC BY-SA 4.0</dc:rights>'
           f'<meta property="dcterms:modified">{hoy}</meta></metadata><manifest>'
           '<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>'
           '<item id="css" href="estilo.css" media-type="text/css"/>'
           f"{manifest}</manifest><spine>{spine}</spine></package>")
    salida = C.RAIZ / "epub" / f"{LIBRO_ES[libro]}_RV1909_estudio.epub"
    salida.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(salida, "w") as z:
        z.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        z.writestr("META-INF/container.xml", '<?xml version="1.0"?><container version="1.0" '
                   'xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles><rootfile '
                   'full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/></rootfiles></container>',
                   compress_type=zipfile.ZIP_DEFLATED)
        z.writestr("OEBPS/content.opf", opf, compress_type=zipfile.ZIP_DEFLATED)
        z.writestr("OEBPS/nav.xhtml", nav, compress_type=zipfile.ZIP_DEFLATED)
        z.writestr("OEBPS/estilo.css", CSS, compress_type=zipfile.ZIP_DEFLATED)
        for f, t in archivos.items():
            z.writestr(f"OEBPS/{f}", t, compress_type=zipfile.ZIP_DEFLATED)
    print(f"{salida.relative_to(C.RAIZ)}: {len(caps)} capítulo(s), {salida.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
