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

LIBRO_ES = {"JHN": "Juan"}
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
         (r"^Against Praxeas", "Contra Práxeas"), (r"^Catena Aurea.*", "Catena Aurea")]
CSS = """body { font-family: serif; line-height: 1.5; margin: 0 4%; }
h1 { font-size: 1.6em; text-align: center; font-weight: bold; margin: 1.5em 0 1em; }
h2 { font-size: 1.15em; font-weight: bold; margin: 1.4em 0 0.6em; }
p { margin: 0 0 0.35em; text-indent: 0; text-align: justify; }
.v sup.n { font-size: 0.65em; color: #8a1c1c; font-weight: bold; margin-right: 0.15em; }
a.ll { text-decoration: none; font-size: 0.7em; vertical-align: super; line-height: 0; font-family: sans-serif; }
a.ll.c { color: #1f5a8a; } a.ll.p { color: #7a4b00; }
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
"""


def x(t):
    return html.escape(t, quote=False)


def inline(t):
    """Escapa, normaliza citas bíblicas y convierte ⸢…⸣ en cursiva."""
    t = B.normalizar(t)
    t = x(t).replace("⸢", "<em>").replace("⸣", "</em>")
    t = t.replace("\n\n", "</p><p>")
    return t + "</em>" * (t.count("<em>") - t.count("</em>"))


def obra_es(w):
    for pat, rep in OBRAS:
        if re.match(pat, w):
            return re.sub(pat, rep, w).strip()
    return w


def atribucion(n):
    s = n["source"]
    autor = AUTORES.get(s["author"], s["author"])
    trad = "Oriente" if n["tradition"] == "oriente" else "Occidente"
    if s["work"].startswith("Catena"):
        donde = (f"<em>{x(s['passage'])}</em>, " if s.get("passage") and s["passage"] != s["work"] else "") + "en la <em>Catena Aurea</em> de santo Tomás de Aquino"
    else:
        donde = f"<em>{x(obra_es(s['work']))}</em>"
    ed = s.get("edition") or ""
    if s["work"].startswith("Catena"):            # la edición repite autor y obra: queda solo «trad. …»
        ed = re.sub(r"^.*?Catena Aurea,?\s*", "", ed)
        donde, ed = (f"{donde}, {x(ed)}", "") if ed else (donde, "")
    return (f'<span class="autor">{x(autor)}</span> <span class="trad">({trad})</span>',
            f'<p class="fuente">{donde}.' + (f" {x(ed)}" if ed else "") + "</p>")


def capitulo_xhtml(libro, c, rv, ns, tr):
    por = {}
    for n in ns:
        t = dict(tr.get(n["id"], {}))
        t.update(C.adjudicacion(n["id"], libro))
        if not t.get("text_es"):
            continue
        ancla = n["ref"]
        anclas = t.get("lemas_rv1909") or []
        if anclas and anclas[0].get("ref"):
            ancla = anclas[0]["ref"]
        capa = "c" if n["layer"] == "contexto" else "p"
        por.setdefault((ancla, capa), []).append((n, t))
    cuerpo, notas = [], []
    for ref in [r for r in rv if C.cap(r) == c]:
        v = C.ver(ref)
        llamadas = ""
        for capa, letra in (("c", "C"), ("p", "P")):
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
                    else:
                        quien, fuente = atribucion(n)
                        bloques.append(f"<p>{quien}: {inline(t['text_es'])}</p>{fuente}")
                titulo = ("Contexto" if capa == "c" else "Padres de la Iglesia") + f" — {LIBRO_ES[libro]} {c}:{v}"
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
    ediciones = sorted({n["source"]["edition"] for n in usados if n["layer"] == "padres" and n["source"].get("edition")})
    portada = (f'<div class="portada"><h1>{LIBRO_ES[libro]}</h1><p style="text-align:center">Reina-Valera 1909</p>'
               '<p style="text-align:center">Biblia de Estudio Abierta — notas de contexto y de los Padres de la Iglesia</p>'
               '<p style="text-align:center">Edición piloto</p></div>')
    fuentes = ("<h1>Fuentes y cómo leer las notas</h1>"
               "<p>Cada versículo lleva llamadas por capa: <strong>C</strong> (contexto histórico y literario) y "
               "<strong>P</strong> (Padres de la Iglesia). En cada cita patrística se indica la tradición (Oriente u "
               "Occidente), la obra, el pasaje y la edición inglesa de dominio público desde la que se tradujo.</p>"
               "<p>Texto bíblico: Reina-Valera 1909 (dominio público), con las tildes de monosílabos actualizadas "
               "(«fue», «a», «dio»); ninguna palabra cambiada. Las palabras en cursiva del texto bíblico son las que los "
               "traductores de 1909 añadieron para el sentido.</p>"
               f"<h2>Padres citados</h2><p>{x(', '.join(autores))}.</p>"
               "<h2>Ediciones de las traducciones</h2>" + "".join(f"<p>{x(e)}</p>" for e in ediciones))
    licencias = ("<h1>Atribuciones y licencias</h1>"
                 "<p>Notas de contexto adaptadas de <em>Aquifer Open Study Notes</em> © Mission Mutual, adaptación de "
                 "<em>Tyndale Open Study Notes</em> © 2023 Tyndale House Publishers, CC BY-SA 4.0. Traducido y modificado.</p>"
                 "<p>Citas patrísticas: compilación de Historical Christian Faith (dominio público) sobre traducciones "
                 "inglesas de dominio público; la Catena Aurea en la traducción de J. H. Newman (Oxford, 1841-45).</p>"
                 "<p>Esta edición (traducción al español, notas y maquetación) se publica bajo licencia Creative Commons "
                 "Atribución-CompartirIgual 4.0 Internacional (https://creativecommons.org/licenses/by-sa/4.0/). "
                 "Es gratuita y puede copiarse, adaptarse y redistribuirse con la misma licencia.</p>")
    return portada, fuentes, licencias


def main():
    libro = sys.argv[1] if len(sys.argv) > 1 else "JHN"
    pedido = sys.argv[2] if len(sys.argv) > 2 else "1"
    rv = C.cargar(f"normalizado/rv1909/{libro}.json")
    us = C.unidades(libro)
    caps = sorted({C.cap(r) for r in rv}) if pedido == "todos" else [int(pedido)]
    archivos, tr_total = {}, {}
    for c in caps:
        tr = C.cargar(f"traducido/{libro}/{c:02d}.json", {})
        tr_total.update(tr)
        archivos[f"c{c:02d}.xhtml"] = xhtml(f"{LIBRO_ES[libro]} {c}",
                                            capitulo_xhtml(libro, c, rv, [n for n in us if C.cap(n["ref"]) == c], tr))
    portada, fuentes, licencias = paginas_previas(libro, us, tr_total)
    archivos = {"portada.xhtml": xhtml("Portada", portada), "fuentes.xhtml": xhtml("Fuentes", fuentes),
                **archivos, "licencias.xhtml": xhtml("Licencias", licencias)}
    items = "".join(f'<li><a href="c{c:02d}.xhtml">{LIBRO_ES[libro]} {c}</a></li>' for c in caps)
    nav = xhtml("Índice", '<nav epub:type="toc" id="toc"><h1>Índice</h1><ol><li><a href="fuentes.xhtml">Fuentes y cómo leer las notas</a></li>'
                f'<li><a href="c{caps[0]:02d}.xhtml">Evangelio según {LIBRO_ES[libro]}</a><ol>{items}</ol></li>'
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
