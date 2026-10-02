#!/usr/bin/env python3
"""Paso 3-4 (padres): HCF -> normalizado/<LIBRO>/padres.json (dominio público) y cuarentena/<LIBRO>_padres.json.

Cada cita queda con autor, obra y pasaje, edición de la traducción y tradición (Oriente/Occidente).
La decisión de licencia por obra está en glosario/obras.json (reglas en orden, la primera gana);
lo dudoso NO se traduce: va a cuarentena con su motivo.

Uso: python3 scripts/hcf.py [JHN]
"""
import collections
import json
import pathlib
import re
import sys
import tomllib
import urllib.parse

RAIZ = pathlib.Path(__file__).resolve().parent.parent
NOMBRE = {"JHN": "John"}
CFG = json.loads((RAIZ / "glosario" / "obras.json").read_text())
ORIENTE = set(CFG["tradicion"]["oriente"])


def coincide(si, e):
    if si.get("catena") and not e["catena"]:
        return False
    if si.get("titulo_mayusculas") and not (e["titulo"] and e["titulo"][:12].isupper()):
        return False
    if si.get("sin_url") and e["url"]:
        return False
    a = si.get("autor")
    if a and e["autor"] not in (a if isinstance(a, list) else [a]):
        return False
    t = si.get("titulo")
    if t and not e["titulo"].startswith(t):
        return False
    return True


def decidir(e):
    for r in CFG["reglas"]:
        if coincide(r["si"], e):
            return r
    raise AssertionError("sin regla")


def rango(libro, nombre_archivo):
    """«John 1_1-3» -> (JHN.1.1, JHN.1.3); «John 6_51-7_2» también."""
    m = re.match(r".* (\d+)_(\d+)(?:-(?:(\d+)_)?(\d+))?\.toml$", nombre_archivo)
    c, v, c2, v2 = m.groups()
    return f"{libro}.{int(c)}.{int(v)}", f"{libro}.{int(c2 or c)}.{int(v2 or v)}"


def pasaje_catena(q):
    m = re.match(r"\s*\(([^)]{2,80})\)", q)
    return m.group(1).strip() if m else None


def main():
    libro = sys.argv[1] if len(sys.argv) > 1 else "JHN"
    base = RAIZ / "fuentes" / "hcf"
    sha = json.loads((RAIZ / "manifest.json").read_text())["fuentes"]["hcf"]["sha"]
    buenas, malas, excl = [], [], collections.Counter()
    for f in sorted(base.glob(f"*/{NOMBRE[libro]} [0-9]*.toml")):
        autor = f.parent.name
        if autor in CFG["excluir_autores"]:
            excl[autor] += 1
            continue
        ini, fin = rango(libro, f.name)
        for k, c in enumerate(tomllib.load(open(f, "rb")).get("commentary", [])):
            e = {"autor": autor, "titulo": c.get("source_title", ""), "url": c.get("source_url", ""),
                 "catena": "Aquinas" in c.get("append_to_author_name", "")}
            r = decidir(e)
            q = c.get("quote", "").strip()
            nota = {
                "id": f"hcf:{autor}/{f.stem}#{k}", "ref": ini, "ref_fin": fin, "layer": "padres",
                "tradition": "oriente" if autor in ORIENTE else "occidente",
                "lemma_src": [], "lemma_rv1909": [], "text_src": q, "text_es": None,
                "source": {"work": "Catena Aurea (Tomás de Aquino)" if e["catena"] else e["titulo"],
                           "author": autor, "passage": pasaje_catena(q) if e["catena"] else e["titulo"],
                           "url": urllib.parse.unquote(e["url"]), "edition": r.get("edicion")},
                "license": "Dominio público" if r["estado"] == "dominio_publico" else None,
                "provenance": {"repo": "HistoricalChristianFaith/Commentaries-Database", "sha": sha,
                               "file": f"{autor}/{f.name}", "index": k},
                "translation": None, "review": {"human": False, "status": "pendiente"},
            }
            if r["estado"] == "dominio_publico":
                buenas.append(nota)
            else:
                nota["cuarentena"] = r["motivo"]
                malas.append(nota)
    (RAIZ / "normalizado" / libro).mkdir(parents=True, exist_ok=True)
    (RAIZ / "normalizado" / libro / "padres.json").write_text(json.dumps(buenas, ensure_ascii=False, indent=1))
    (RAIZ / "cuarentena").mkdir(exist_ok=True)
    (RAIZ / "cuarentena" / f"{libro}_padres.json").write_text(json.dumps(
        [{k: v for k, v in n.items() if k != "text_src"} for n in malas], ensure_ascii=False, indent=1))
    pal = lambda ns: sum(len(n["text_src"].split()) for n in ns)
    por = collections.Counter((n["source"]["author"], n["source"]["work"].split(",")[0]) for n in buenas)
    lin = [f"# Padres {libro} (HCF)", "",
           f"- dominio público: {len(buenas)} citas, {pal(buenas):,} palabras (inglés)",
           f"- cuarentena: {len(malas)} citas, {pal(malas):,} palabras (no se traducen)",
           f"- excluidos (autores modernos): {dict(excl)}",
           f"- Oriente / Occidente (dominio público): {sum(n['tradition'] == 'oriente' for n in buenas)} / "
           f"{sum(n['tradition'] == 'occidente' for n in buenas)}",
           f"- versículos con al menos una cita de dominio público: "
           f"{len({n['ref'] for n in buenas})}", "", "## Por autor y obra (dominio público)", ""]
    lin += [f"- {a} — {w}: {n}" for (a, w), n in por.most_common()]
    lin += ["", "## Cuarentena por motivo", ""]
    lin += [f"- {n}: {m}" for m, n in collections.Counter(n["cuarentena"] for n in malas).most_common()]
    (RAIZ / "informes" / f"padres_{libro}.md").write_text("\n".join(lin) + "\n")
    print("\n".join(lin[2:8]))


if __name__ == "__main__":
    main()
