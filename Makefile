.PHONY: ingesta normalizar seleccion capitulo test

LIBRO ?= JHN

ingesta:
	python3 scripts/ingesta.py $(LIBRO)

normalizar: ingesta
	python3 scripts/rv1909.py $(LIBRO)
	python3 scripts/aquifer.py $(LIBRO)
	python3 scripts/hcf.py $(LIBRO)
	python3 scripts/griego.py $(LIBRO)

CAP ?= 1

seleccion:
	cd scripts && python3 seleccion.py $(LIBRO)

capitulo:
	cd scripts && python3 traducir.py $(LIBRO) $(CAP) && python3 juez.py $(LIBRO) $(CAP) && python3 anclar.py $(LIBRO) $(CAP) && python3 verificar.py $(LIBRO) $(CAP); python3 epub.py $(LIBRO) $(CAP)

test:
	python3 -m unittest discover -s tests -t .
