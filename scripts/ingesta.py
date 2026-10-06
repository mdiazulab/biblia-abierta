#!/usr/bin/env python3
"""Paso 2: descarga cada fuente EXACTAMENTE en el commit de manifest.json (sparse + shallow).

Las descargas crudas quedan en fuentes/<nombre>/ (fuera de git, nunca se editan).
Idempotente: si fuentes/<nombre> ya está en el SHA pedido, no hace nada.

Uso: python3 scripts/ingesta.py [LIBRO_OSIS=JHN]
"""
import json
import pathlib
import subprocess
import sys

RAIZ = pathlib.Path(__file__).resolve().parent.parent
from libros import LIBROS


def git(*a, cwd=None):
    return subprocess.run(["git", *a], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


def traer(nombre, f, libro):
    num, nombre_en = LIBROS[libro]["aquifer"], LIBROS[libro]["hcf"]
    destino = RAIZ / "fuentes" / nombre
    rutas = [r.format(libro=num, nombre=nombre_en) for r in f["rutas"]]
    if not (destino / ".git").exists():
        destino.parent.mkdir(exist_ok=True)
        git("clone", "-q", "--filter=blob:none", "--no-checkout", "--depth", "1", f["repo"], str(destino))
    if git("rev-parse", "HEAD", cwd=destino) != f["sha"]:
        git("fetch", "-q", "--depth", "1", "origin", f["sha"], cwd=destino)
    git("sparse-checkout", "set", "--no-cone", *rutas, cwd=destino)
    git("checkout", "-q", f["sha"], cwd=destino)
    print(f"{nombre}: {f['sha'][:10]} ({', '.join(rutas)})")


def main():
    libro = sys.argv[1] if len(sys.argv) > 1 else "JHN"
    m = json.loads((RAIZ / "manifest.json").read_text())
    for nombre, f in m["fuentes"].items():
        traer(nombre, f, libro)


if __name__ == "__main__":
    main()
