# HANDOVER — Biblia de Estudio Abierta (RV1909)

## Estado (02-10-2026)

Hecho (paso 1-4 del piloto de Juan):
- Repositorio armado; fuentes fijadas por SHA en `manifest.json`; `make normalizar LIBRO=JHN` reproduce todo.
- RV1909 Juan: 879 versículos / 21 capítulos (`normalizado/rv1909/JHN.json`); 484 tildes obsoletas
  modernizadas (decisión del usuario: solo acentos, ninguna palabra; el texto de 1909 queda en `texto_1909`).
  Palabras añadidas por los traductores de 1909 (`<add>`) marcadas ⸢ ⸣ (cursiva).
- Aquifer Juan: 493 notas, 25.584 palabras en inglés (revisión "Professional"); el español existente
  (sin revisión) está emparejado por `reference_id`, pero corresponde a una versión ANTERIOR del inglés
  y usa «la Palabra» (la RV1909 dice «el Verbo») -> se traduce desde el inglés y el español existente
  sirve solo como referencia.
- Padres (HCF): 5.246 citas de dominio público (1,26 M palabras en inglés; 858 de 879 versículos;
  Oriente 2.715 / Occidente 2.531) y 4.370 en cuarentena (no se traducen). Decisión por obra en
  `glosario/obras.json`, verificada por el estilo del texto:
  - dominio público: Catena Aurea (Newman 1841-45; incluye a Teofilacto, Crisóstomo, Agustín,
    Orígenes, Alcuino, Beda, Hilario, Gregorio), Agustín *Tractatus in Ioannem* (NPNF 1888),
    Crisóstomo *Homilías sobre Juan* (NPNF 1889), Cirilo de Alejandría *Comentario a Juan*
    (Pusey 1874 / Randell 1885), ANF y NPNF;
  - cuarentena: extractos ACCS (títulos en MAYÚSCULAS), Aquino *Comentario a Juan* (Larcher),
    Buenaventura (Karris), Teofilacto *Comentario a Juan* (Chrysostom Press 2007), Gregorio y Beda
    homilías (Hurst), Orígenes *Comentario a Juan* de procedencia desconocida.
  - La capa «Oriente» queda cubierta en dominio público (Teofilacto vía Catena, Crisóstomo, Cirilo)
    aunque la Tolkovaya Bibliya no pase la verificación de derechos.

Pendiente (siguiente sesión):
1. Selección por versículo (tope de palabras por capa para buena lectura): Catena completa
   (1.578 citas, 176 mil palabras, 773 versículos) + Crisóstomo/Agustín/Cirilo donde la Catena no
   cubre o en versículos sensibles.
2. Capa «Reforma» (Calvino, Wesley): dominio público vía CrossWire SWORD / HelloAO en CI
   (desde este entorno solo se alcanza GitHub; open-christian-data es CC BY-NC y NO se usa).
3. Traducción (DeepSeek, glosario en el prompt) + juez doble calibrado + compuerta Wilson (< 3 %),
   reutilizando `periodico_kindle/calidad/{juez,mutaciones,estadistica}.py`; corre en GitHub Actions.
4. Re-anclaje de lemas a la RV1909 (alineamiento automático primero; Claude solo el residuo).
5. EPUB (reutilizar `pdf-a-epub/motor/epub.py`: notas emergentes, índice, control de presentación).

Decisiones del usuario: acentos modernizados (a); repo propio `biblia-abierta` (b); misma licencia
CC BY-SA 4.0, gratuito, sin venta; objetivo: patrística y referencias de alto nivel.

## Mejores prácticas obligatorias (copiar completas en cada actualización de este archivo)

**Extracción**
- Toda fuente se descarga desde un commit o release fijado; el SHA queda en `manifest.json`.
- Nunca se extrae desde páginas web ni desde ediciones modernas cuando existe la original.
- Cada entrada conserva id, obra, URL y el texto original intacto; las descargas crudas nunca se editan.
- Licencia decidida por OBRA (traducción), no por autor; lo dudoso va a `cuarentena/` y no se traduce.

**Traducción**
- Una nota es una unidad; nunca se fusionan ni se dividen notas al traducir.
- El prompt incluye siempre el glosario (`periodico_kindle/libro_traduccion/glosario.json`, anclado en
  Meyendorff) y la regla de preservar referencias bíblicas, palabras griegas/hebreas/latinas y números.
- Terminología de la RV1909 en las notas: «el Verbo» (no «la Palabra»), nombres y libros como en 1909.
- La salida es JSON con el mismo id de entrada; texto fuera del JSON se descarta.
- Tuteo neutro en notas pastorales; registro académico en notas técnicas.
- Una traducción por nota; doble traducción solo en versículos sensibles y en lo que el juez marque.

**Aplicación por reemplazo único**
- La traducción va en `text_es`; el campo original nunca se sobrescribe.
- Una escritura por id; volver a ejecutar un paso no duplica entradas (idempotencia).
- Caché de veredictos por nota: una nota idéntica no se vuelve a juzgar.

**Verificación (por capítulo; un fallo bloquea)**
1. Mismo número de notas en origen y destino; cada id exactamente una vez.
2. Mismas referencias bíblicas en cada nota, comparadas DESPUÉS de normalizarlas (forma única
   ⸢[I/II] Libro⸣ cap:vers, misma lógica que `biblia.py`).
3. Números, fechas y términos griegos/latinos preservados.
4. Glosario: ningún término prohibido, todos los obligatorios, y sin uso forzado fuera de contexto
   (lección de Staniloae: «put into operation» -> «poner en energía increada»).
5. Sin inglés residual (corrector ortográfico, como `pdf-a-epub/motor/ortografia.py`), sin entidades
   HTML, sin comentarios del modelo dentro del texto.
6. Razón de longitud español/inglés entre 0,9 y 1,4.
7. Cada nota con `license` y `provenance` válidos; citas patrísticas con obra, pasaje y edición.
8. Cada lema re-anclado existe literalmente en el versículo RV1909 (el tramo se toma del propio
   versículo; si no hay coincidencia, la nota va al versículo completo «v. N:»).
9. Compuerta estadística del juez doble (< 3 % de error en el extremo superior); revisión humana
   SOLO de los versículos sensibles (1,1; 1,14; 1,18; 3,5; 6,51-58; 14,6; 20,22-23; 20,28; 21,15-17)
   y de lo que la compuerta no pueda decidir. Ítems de "revisión humana" los resuelve Claude leyendo
   el original; al usuario solo lo ambiguo o lo teológico/de estilo.

**Ids, anclas y EPUB**
- Cada nota resuelve a un versículo RV1909 existente; cero huérfanas.
- Cada enlace nota↔versículo funciona en ambas direcciones; llamadas de nota fuera de las citas.
- epubcheck 0/0/0; índice sin numeración automática ni justificado; títulos en negrita.

**Eficiencia (lecciones de Staniloae y Ware)**
- Reglas deterministas sobre todo el libro primero; modelo/recortes solo para el residuo.
- Un error encontrado es una CLASE: se agrega un control y se corrige en todo lo hecho.
- Nunca entregar con un residuo conocido; el residuo se vuelve un control en 0.
- Capítulo 1 de punta a punta primero; luego los 20 restantes en una sola corrida de CI.

**Cuándo declarar completo**
- Capítulo: pasa los nueve puntos, versículos sensibles firmados, manifiesto actualizado.
- Piloto: 21 capítulos completos, EPUB con epubcheck 0/0/0 y métricas (≥ 90 % de versículos con nota;
  > 26.800 palabras de notas; 100 % de citas patrísticas con obra y pasaje; ≤ 2 % de errores
  sustantivos; batería 100 %).
- Cada sesión cierra actualizando este archivo con estado, pendientes y esta sección completa.
