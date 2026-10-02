.PHONY: ingesta normalizar informe

LIBRO ?= JHN

ingesta:
	python3 scripts/ingesta.py $(LIBRO)

normalizar: ingesta
	python3 scripts/rv1909.py $(LIBRO)
	python3 scripts/aquifer.py $(LIBRO)
	python3 scripts/hcf.py $(LIBRO)
