# Biblia de Estudio Abierta (RV1909)

Biblia RV1909 (dominio público) con notas en capas, cada una con su etiqueta de tradición:
**Contexto** (Aquifer / Tyndale Open Study Notes), **Padres** (Oriente y Occidente, con obra,
pasaje y edición de la traducción), **Reforma** (Calvino, Wesley) y, si se aclaran sus derechos,
la *Tolkovaya Bibliya* rusa. Gratuita y abierta: notas bajo CC BY-SA 4.0.

Piloto: Evangelio de Juan (21 capítulos, 879 versículos).

| Paso | Script | Resultado |
|---|---|---|
| Ingesta (fuentes fijadas por SHA en `manifest.json`) | `scripts/ingesta.py` | `fuentes/` (fuera de git) |
| Texto RV1909 con ids OSIS, acentos modernizados | `scripts/rv1909.py` | `normalizado/rv1909/JHN.json` |
| Notas de contexto (inglés + español existente) | `scripts/aquifer.py` | `normalizado/JHN/aquifer.json` |
| Padres: filtro de licencia por obra | `scripts/hcf.py` + `glosario/obras.json` | `normalizado/JHN/padres.json`, `cuarentena/` |
| Traducción, adjudicación, re-anclaje, verificación, EPUB | (siguientes pasos) | `traducido/`, `epub/` |

`make normalizar LIBRO=JHN` corre los cuatro primeros pasos. Informes cortos en `informes/`.
Ver `HANDOVER.md` para el estado y las reglas obligatorias.
