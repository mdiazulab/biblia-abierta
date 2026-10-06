#!/usr/bin/env python3
"""Volumen complementario «<Libro>: el texto griego explicado» (EPUB 3): todas las notas de unfoldingWord®
Translation Notes traducidas (griego_completo.py), con el texto de la RV1909 de cada versículo, las introducciones
al libro y a cada capítulo, y el glosario de categorías.

Uso: python3 scripts/epub_griego.py HEB  -> epub/<Libro>_griego_explicado.epub
"""
import datetime
import sys
import uuid
import zipfile

import comun as C
import epub as E
from epub import x, xhtml
from griego_completo import CATEGORIAS
from libros import LIBROS


def ancla(cat):
    return "g-" + "".join(c if c.isalnum() else "-" for c in cat.lower()).strip("-")


def seccion(n, t):
    """Sección de introducción: los primeros párrafos son los títulos (h2/h3); «• ◦ ▪» son viñetas por nivel."""
    ps = t["text_es"].split("\n\n")
    niveles = n.get("niveles") or []
    if len(ps) != len(n["text_src"].split("\n\n")):        # la verificación lo marca; no se adivinan títulos
        niveles = []
    out = [f"<h{k}>{E.inline(p)}</h{k}>" for k, p in zip(niveles, ps)]
    for p in ps[len(niveles):]:
        if p[:2] in ("• ", "◦ ", "▪ "):
            out.append(f'<p class="li{"•◦▪".index(p[0]) + 1}">{x(p[0])} {E.inline(p[2:])}</p>')
        else:
            out.append(f"<p>{E.inline(p)}</p>")
    return "\n".join(out)


def nota_xhtml(n, t):
    cab = E.griego_cab(n, t)
    cat = n.get("categoria")
    rotulo = (f' <a class="cat" href="glosario.xhtml#{ancla(cat)}">[{x(CATEGORIAS[cat])}]</a>' if cat else "")
    return f'<div class="nota"><p>{cab.rstrip(": ")}{rotulo}{":" if n.get("griego") else ""} {E.inline(t["text_es"])}</p></div>'


CSS_EXTRA = """
.nota { margin: 0.2em 0 0.6em 1.2em; font-size: 0.92em; }
a.cat { color: #6a2c7a; text-decoration: none; font-size: 0.85em; font-family: sans-serif; }
p.li1 { margin-left: 1em; } p.li2 { margin-left: 2.2em; } p.li3 { margin-left: 3.4em; }
p.v { margin-top: 0.9em; }
"""


def main():
    libro = sys.argv[1] if len(sys.argv) > 1 else "HEB"
    es = LIBROS[libro]["es"]
    rv = C.cargar(f"normalizado/rv1909/{libro}.json")
    us = [n for n in C.unidades(libro) if n["layer"] in ("griego_c", "griego_intro", "glosario_g")]
    if not us:
        print("sin volumen complementario para", libro); return
    tr = {}
    for c in sorted({C.cap(r) for r in rv}):
        tr.update(C.cargar(f"traducido/{libro}/{c:02d}.json", {}))
    for i, v in tr.items():
        tr[i] = {**v, **C.adjudicacion(i, libro, v.get("text_es"))}
    hecho = lambda n: (tr.get(n["id"]) or {}).get("text_es")
    faltan = [n["id"] for n in us if not hecho(n)]
    orden = lambda n: (C.cap(n["ref"]), C.ver(n["ref"]), n.get("orden", 0))
    intro = lambda cap: [seccion(n, tr[n["id"]]) for n in sorted(us, key=orden)
                         if n["layer"] == "griego_intro" and n["capitulo"] == cap and hecho(n)]
    archivos = {"portada.xhtml": xhtml("Portada", f'<div class="portada"><h1>{x(es)}</h1>'
                                       '<p style="text-align:center"><strong>El texto griego explicado</strong></p>'
                                       '<p style="text-align:center">Notas de traducción de unfoldingWord®, en español</p>'
                                       '<p style="text-align:center">Complemento de la Biblia de Estudio Abierta (Reina-Valera 1909)</p></div>')}
    pres = C.RAIZ / "editorial" / f"{libro}_griego.md"
    if pres.exists():
        archivos["presentacion.xhtml"] = xhtml("Presentación", E.md_xhtml(pres.read_text()))
    archivos["introduccion.xhtml"] = xhtml("Introducción", f"<h1>Introducción a {x(LIBROS[libro]['titulo'])}</h1>\n" + "\n".join(intro(0)))
    caps = sorted({C.cap(r) for r in rv})
    for c in caps:
        cuerpo = [f'<h1 id="c{c}">{x(es)} {c}</h1>']
        ic = intro(c)
        if ic:
            cuerpo += ['<div class="intro-cap">'] + ic + ["</div>", '<h2>Versículo por versículo</h2>']
        for ref in [r for r in rv if C.cap(r) == c]:
            ns = sorted((n for n in us if n["layer"] == "griego_c" and n["ref"] == ref and hecho(n)), key=orden)
            if not ns:
                continue
            texto = x(rv[ref]["texto"]).replace("⸢", "<em>").replace("⸣", "</em>")
            cuerpo.append(f'<p class="v" id="v{c}-{C.ver(ref)}"><sup class="n">{C.ver(ref)}</sup>{texto}</p>')
            cuerpo += [nota_xhtml(n, tr[n["id"]]) for n in ns]
        archivos[f"c{c:02d}.xhtml"] = xhtml(f"{es} {c}", "\n".join(cuerpo))
    glos = ["<h1>Glosario de figuras y problemas de traducción</h1>",
            "<p>Definiciones de <em>unfoldingWord® Translation Academy</em> (sección «Descripción» de cada artículo). "
            "Cada nota del volumen remite aquí con el nombre entre corchetes.</p>"]
    for n in sorted((n for n in us if n["layer"] == "glosario_g" and hecho(n)), key=lambda n: CATEGORIAS[n["categoria"]]):
        glos.append(f'<h2 id="{ancla(n["categoria"])}">{x(CATEGORIAS[n["categoria"]])} '
                    f'<span class="trad">({x(n["categoria"])})</span></h2>')
        glos += [f"<p>{E.inline(p)}</p>" for p in tr[n["id"]]["text_es"].split("\n\n")]
    archivos["glosario.xhtml"] = xhtml("Glosario", "\n".join(glos))
    archivos["licencias.xhtml"] = xhtml("Licencias", (
        "<h1>Atribuciones y licencias</h1>"
        "<p>Notas: <em>unfoldingWord® Translation Notes</em> © 2022 unfoldingWord, CC BY-SA 4.0, en la edición de Aquifer "
        "(release v91). Glosario: <em>unfoldingWord® Translation Academy</em> © 2022 unfoldingWord, CC BY-SA 4.0, edición "
        "de Aquifer (sección «Description» de cada artículo). Traducidos al español y adaptados (formato, remisiones); "
        "unfoldingWord no respalda necesariamente estos cambios.</p>"
        "<p>Texto bíblico: Reina-Valera 1909 (dominio público), con las tildes de monosílabos actualizadas.</p>"
        "<p>Esta edición (traducción, presentación y maquetación) se publica bajo licencia Creative Commons "
        "Atribución-CompartirIgual 4.0 Internacional (https://creativecommons.org/licenses/by-sa/4.0/). Es gratuita y "
        "puede copiarse, adaptarse y redistribuirse con la misma licencia.</p>"))
    items = "".join(f'<li><a href="c{c:02d}.xhtml">{x(es)} {c}</a></li>' for c in caps)
    nav = xhtml("Índice", '<nav epub:type="toc" id="toc"><h1>Índice</h1><ol>'
                + ('<li><a href="presentacion.xhtml">Presentación</a></li>' if "presentacion.xhtml" in archivos else "")
                + f'<li><a href="introduccion.xhtml">Introducción a {x(LIBROS[libro]["titulo"])}</a></li>'
                f'<li><a href="c01.xhtml">Versículo por versículo</a><ol>{items}</ol></li>'
                '<li><a href="glosario.xhtml">Glosario de figuras y problemas de traducción</a></li>'
                '<li><a href="licencias.xhtml">Atribuciones y licencias</a></li></ol></nav>')
    ident = f"urn:uuid:{uuid.uuid5(uuid.NAMESPACE_URL, 'biblia-abierta/griego/' + libro)}"
    hoy = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    lista = list(archivos)
    opf = ('<?xml version="1.0" encoding="utf-8"?><package xmlns="http://www.idpf.org/2007/opf" version="3.0" '
           'unique-identifier="uid" xml:lang="es"><metadata xmlns:dc="http://purl.org/dc/elements/1.1/">'
           f'<dc:identifier id="uid">{ident}</dc:identifier><dc:title>{x(es)} — El texto griego explicado</dc:title>'
           '<dc:language>es</dc:language><dc:rights>CC BY-SA 4.0</dc:rights>'
           f'<meta property="dcterms:modified">{hoy}</meta></metadata><manifest>'
           '<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>'
           '<item id="css" href="estilo.css" media-type="text/css"/>'
           + "".join(f'<item id="i{k}" href="{f}" media-type="application/xhtml+xml"/>' for k, f in enumerate(lista))
           + "</manifest><spine>" + "".join(f'<itemref idref="i{k}"/>' for k in range(len(lista))) + "</spine></package>")
    salida = C.RAIZ / "epub" / f"{es}_griego_explicado.epub"
    salida.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(salida, "w") as z:
        z.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        z.writestr("META-INF/container.xml", '<?xml version="1.0"?><container version="1.0" '
                   'xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles><rootfile '
                   'full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/></rootfiles></container>',
                   compress_type=zipfile.ZIP_DEFLATED)
        z.writestr("OEBPS/content.opf", opf, compress_type=zipfile.ZIP_DEFLATED)
        z.writestr("OEBPS/nav.xhtml", nav, compress_type=zipfile.ZIP_DEFLATED)
        z.writestr("OEBPS/estilo.css", E.CSS + CSS_EXTRA, compress_type=zipfile.ZIP_DEFLATED)
        for f, t in archivos.items():
            z.writestr(f"OEBPS/{f}", t, compress_type=zipfile.ZIP_DEFLATED)
    print(f"{salida.relative_to(C.RAIZ)}: {len(us) - len(faltan)}/{len(us)} unidades traducidas, "
          f"{salida.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
