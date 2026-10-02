# biblia-abierta -- instrucciones para Claude

Leer `HANDOVER.md` al empezar: estado, pendientes y las mejores prácticas obligatorias.

- No abrir con Read/Grep las descargas crudas de `fuentes/` ni los JSON grandes de `normalizado/`
  (padres.json pesa ~8 MB): se trabaja con los informes cortos de `informes/` y con scripts.
- Fuentes solo desde el commit fijado en `manifest.json`; nunca editar `fuentes/`.
- Licencia por obra en `glosario/obras.json`; lo dudoso a `cuarentena/`, nunca se traduce.
- Regla del usuario (teología/Biblia): revisión final de TODAS las citas bíblicas (forma única,
  capítulo existente, texto que corresponde al versículo).
- Desde este entorno solo se alcanza GitHub: lo que necesite otras webs o los modelos corre en
  GitHub Actions.
