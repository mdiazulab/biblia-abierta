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

Cadena completa construida y probada sin red (modelo falso, `make test`), 02-10-2026:
- `seleccion.py`: 2.526 notas, 262.507 palabras en inglés, 879/879 versículos con nota.
  Aquifer completo + Catena Aurea completa + complemento por versículo (Crisóstomo/Cirilo para
  Oriente donde la Catena no trae voz oriental; Agustín donde la Catena no llega; ambos en
  versículos sensibles), máx. 350 palabras por texto de complemento.
  Oriente 98.838 / Occidente 138.085 / contexto 25.584 palabras.
- `traducir.py` (DeepSeek; Gemini como 2.ª traducción en versículos sensibles), `juez.py`
  (Gemini sobre todas las notas, errores sembrados para medir sensibilidad, corrector con el
  motivo del juez, compuerta Wilson < 3 %, cola para Claude), `anclar.py` (lemas a la RV1909,
  determinista), `verificar.py` (batería 1-8 + citas bíblicas), `epub.py` (notas emergentes C/P
  por versículo, fuentes, licencias; epubcheck 0/0/0).
- Workflow `.github/workflows/piloto.yml`: se dispara al cambiar `ordenes/piloto.txt` («JHN 1»).
  Necesita los secretos DEEPSEEK_API_KEY y GEMINI_API_KEY en este repositorio.

Capítulo 1 corrido en CI (espejo en periodico_kindle, rama claude/repo-connection-check-rkrl75, porque los
secretos están allí), 02-10-2026: 182 notas, 31 segundas traducciones; juez: sensibilidad 18/19, 10 marcadas,
9 corregidas por el corrector y 1 resuelta por Claude (`revision/adjudicaciones_JHN.json`, Cirilo 1,51
«one another» -> «unas a otras», con la frase inglesa como evidencia); verificación 182/182; epubcheck 0/0/0.
Clases encontradas y corregidas en toda la cadena (cada una con prueba en `tests/test_cadena.py`):
- llamadas de nota de la edición inglesa pegadas a palabras («life1»): se quitan antes y después de traducir;
- nombres/abreviaturas inglesas de libros en las citas («John 5:26», «Exod. 7:1», «1 Ped.»): alias en
  `biblia.py` + control «cita sin forma única» en `verificar.py`;
- tildes obsoletas que el mapa no cubría: demostrativos («éste», «aquél»), «sólo» y pretérito + un enclítico
  («Respondióles» -> «Respondioles»): 603 cambios en Juan (antes 484);
- razón de longitud solo para textos > 300 caracteres (falso positivo en frases cortas);
- atribución de la Catena sin repetir autor y obra.

«JHN todos» corrido en CI (02-10-2026, 50 min): 2.526 notas traducidas (117 con segunda traducción);
juez caps. 1-8 completo (sensibilidad 95-100 %); en el cap. 9 Gemini agotó su cupo diario y el traceback
escribió la URL con la clave en informes/juez_JHN.md (repositorio privado; tapada; el usuario debe rotar la
clave). Arreglos: clave de Gemini en cabecera, mensajes de error sin claves (`comun._sin_claves`),
deepseek-reasoner al final de la cadena del juez (sin cupo diario), juez por capítulo con caché por tramos.
Clases nuevas, con prueba y control (todas aplicadas a los 21 capítulos):
- «Palabra» con mayúscula: el Hijo es «el Verbo» (2 casos en Agustín), si no minúscula (5); control 4;
- «the Word» solo exige «Verbo» en contexto cristológico (`CRISTO_EN`);
- «I Am» (Jn 8,58) ya no cuenta como «1»; «has» es español (no inglés residual);
- citas de capítulo entero «(Sal. 33)» y alias que faltaban (Amos, Mar., Filip., Colos., abreviaturas inglesas);
- razón de longitud: mínimo 0,78 para los Padres (inglés del s. XIX; 26 pares leídos completos) y control
  nuevo de oraciones faltantes (sin contar abreviaturas de referencia ni «i. e.»).
Cola del juez caps. 1-8: 5 ítems resueltos por Claude (4 en `revision/adjudicaciones_JHN.json`, 1 aceptado en
`revision/aceptados_JHN.json`). Verificación 21/21; EPUB completo (620 KB) epubcheck 0/0/0.

Juez completo (03-10-2026). Con la clave nueva de Gemini, gemini-3.6-flash no respondía y flash-lite
mostró sensibilidad 62-80 % (retirado del juez); caps. 1-8 juzgados por gemini-3.6-flash, caps. 9-21 por
deepseek-reasoner (lotes en paralelo, ~35 min). Calibración con el mismo modelo del censo, guardada en la
caché («_calibracion»). Compuerta del LIBRO (con < ~130 notas por capítulo el extremo de Wilson no baja de 3 %
ni con cero errores): 2.526 notas, sensibilidad 342/345 = 99 %, pendientes 0, extremo superior 0,15 % ->
APROBADO. Cola final: 9 ítems; 6 corregidos con evidencia (incluida la cita «Ps. 41:7» del original, que es
Sal 40,5), 2 son citas en texto RV1909 (norma de la edición), 1 falso positivo del juez.
Verificación 21/21; EPUB completo de Juan (620 KB) epubcheck 0/0/0, revisado en pantalla. PILOTO COMPLETO.

Hebreos (06-10-2026, pedido del usuario: patrística + contexto, «los Padres también escriben en su contexto»):
- `scripts/libros.py`: datos por libro en un solo lugar (Aquifer, HCF, nombre, versículos sensibles, base patrística).
  `es_sensible` ahora compara también el libro (antes, Hebreos 2:10 habría marcado Juan 2:10).
- Licencias por obra para Hebreos (`glosario/obras.json`): Crisóstomo *Homilías sobre Hebreos* (NPNF 1889), Confesiones,
  Ciudad de Dios, Basilio, Ambrosio (NPNF/LF), Padres apostólicos y ANF, verificados por estilo. Cuarentena:
  Ecumenio (traducción literal moderna de HCF), Teofilacto (moderna), Aquino (Larcher/Baer), extractos ACCS
  (Teodoreto, Efrén, Severiano…), y obras sin URL.
- Selección HEB: 795 notas, 106.300 palabras (Aquifer 284; Crisóstomo completo 333 como base; 178 de otras voces,
  hasta 2 por versículo y 4 en sensibles); 303/303 versículos.
- Contexto: `editorial/HEB.md` (introducción: género, autor, fecha, destinatarios, trasfondo, plan; cómo leer a los
  Padres en su contexto; textos discutidos entre tradiciones, presentados con las dos lecturas) y
  `glosario/autores.json` (ficha de cada Padre: fechas, lugar, situación; el nombre en cada nota enlaza a la ficha).
- Clases nuevas aplicadas también a Juan: vocabulario RV1909 («pontífice», no «sumo sacerdote»; «Melchisedec»),
  31 casos en Juan corregidos; circunflejos («Melchîsedec», «Sichâr»), tildes de hiato («oír», «creíste»);
  errata de la fuente en Hebreos 12:2 («en al autor» -> «en el autor»).

Hebreos completo (06-10-2026, tres corridas en el espejo): 795 notas traducidas; juez deepseek-reasoner en los
13 capítulos (gemini-3.6-flash sin cupo con la clave nueva), sensibilidad 229/229; cola resuelta con evidencia
(`revision/adjudicaciones_HEB.json` con «reemplazos», `revision/aceptados_HEB.json`); compuerta del libro:
pendientes 0, extremo superior 0,48 % -> APROBADO. Verificación 13/13 (Juan 21/21). EPUB 276 KB, epubcheck 0/0/0.
Clases encontradas y corregidas en los dos libros (cada una con prueba):
- un JSON mal formado descartaba el modelo para toda la corrida (cortó la traducción en el cap. 8);
- lotes sin veredicto: no rompen el capítulo y las notas sin juzgar impiden aprobar;
- lemas en inglés dentro de cursivas (regla del prompt + control);
- adjudicaciones por reemplazo (sobreviven a retraducciones) y aviso cuando dejan de aplicarse: el corrector
  del juez re-tradujo 5 notas ya adjudicadas y el aviso lo detectó;
- comillas rectas -> españolas «…» / “…” (2.588 en los dos libros; huellas del juez actualizadas);
- títulos de obras en español; párrafos repetidos por HCF en versículos vecinos (44 quitados al armar el EPUB,
  informe en `informes/repeticiones_<LIBRO>.md`);
- citas: romanos de la edición inglesa, libros de un capítulo («Judas 19» = 1:19), «Hageo», capítulo entero en
  listas con «;», «En 11:35» no es libro; tildes «constituído», errata de Hebreos 12:2.

Capas nuevas de Hebreos (06-10-2026):
- R «Reforma»: Calvino, Comentario a Hebreos (trad. Owen 1853, CCEL; `scripts/reforma.py`, SHA-256 en
  manifest.json «fuentes_web»; lo descarga el workflow «Biblia abierta (fuentes web)» del espejo).
- G «El texto griego»: unfoldingWord® Translation Notes (CC BY-SA 4.0, Aquifer `UWTranslationNotes`, release
  v91; `scripts/griego.py`). De 1.767 notas quedan 471 (19,5 mil palabras, 245/303 versículos): las que exponen
  lecturas posibles «(1)…(2)…» y las de trasfondo/variantes/sin categoría; fuera las de técnica de traducción y
  toda oración dirigida al traductor (si eso rompe una lista de opciones, la nota entera se descarta). La frase
  griega va aparte ("griego") y no se traduce; la glosa es el lema y se ancla a la RV1909.
- Volumen complementario «Hebreos: el texto griego explicado» (pedido del usuario 06-10-2026: «las sugerencias
  para traductores podrían ir en un trabajo aparte… le ilumina las ideas detrás»): TODAS las notas de unfoldingWord
  (1.767, con lo dirigido a traductores), introducciones al libro y a cada capítulo (121 secciones) y glosario de
  las 63 categorías citadas (sección «Description» de unfoldingWord® Translation Academy, `uwtm` en manifest.json).
  `scripts/griego_completo.py` -> capas griego_c / griego_intro / glosario_g (pasan por traducción, juez y
  verificación como el resto; la Biblia de estudio no las muestra); `scripts/epub_griego.py` arma
  `epub/Hebreos_griego_explicado.epub`; presentación en `editorial/HEB_griego.md`.
- Evaluadas y NO usadas: SBLGNT (el repo de GitHub no trae el aparato, solo marcas ⸂⸃); Biblica Study Notes
  (CC BY-SA, hay español, pero son 20 notas por perícopa que repiten el enfoque de Tyndale); Versión Biblia Libre
  (CC BY-SA 4.0, verificada en eBible.org: paráfrasis con decisiones que borran justo los términos en disputa:
  10:14 «justificó» por τετελείωκεν, 12:1 sin «testigos», 12:23 sin «espíritus»).

Calvino (corrida del 06-10-2026): 1.046 notas, sin traducir 0, sensibilidad 229/229; cola resuelta con evidencia
(17 adjudicaciones). Clase nueva: «the Word of God» = la Escritura (Owen, Agustín) traducido «Verbo»/«Palabra»;
barrida en Juan (17 casos, todos del Hijo: bien) y Hebreos (4 corregidos). CRISTO_EN ya no confunde «was the
Word of God» (Escritura) con el Hijo. epubcheck se corre de a un archivo (con varios solo mostraba la ayuda).

Capa G y volumen griego (corrida del 06-10-2026, espejo): traducción completa (0 sin traducir); el saldo de
DeepSeek se agotó en el juez (HTTP 402) desde el cap. 10: 586 notas sin juzgar y 13 notas del cap. 13 con frases
en inglés quitadas de traducido/ para retraducir. Cola resuelta con evidencia (22 adjudicaciones). Clases nuevas,
aplicadas a Juan y Hebreos: comillas curvas “…” -> «…» (291 notas), remisiones «[[rc://…]]» de unfoldingWord
(40, quitadas en origen y en el español; huellas actualizadas sin retraducir), adjudicación ya aplicada no queda
pendiente, 402 corta la corrida, ejemplos ULT del glosario se traducen del inglés (regla del glosario).
Siguiente: con saldo, orden «HEB todos» en biblia-abierta (repo público) -> juez de lo pendiente y retraducción.

Notas emergentes en Kindle (08-10-2026, reporte del usuario): el Kindle muestra solo el primer bloque de la nota;
con un <h3> de título se veía el título y nada más. Cada nota va ahora en un único <p class="nota"> (título-enlace
de vuelta, texto y fuentes separados por <br/>); prueba test_nota_emergente_en_un_solo_bloque.
Luego (pedido del usuario): la ventana muestra un ADELANTO (~40 palabras, los demás autores nombrados) y el vínculo
«Leer la nota completa →»; las notas completas van en notasNN.xhtml después de cada capítulo, con el título como
vínculo de vuelta al versículo.

«Esencia y energías» (guía y antología) pasó al repositorio privado periodico_kindle/lecturas_privadas/ por
decisión del usuario (08-10-2026): es de uso personal. biblia-abierta sigue público.

Pendiente:
1. Wesley (Explanatory Notes) como segunda voz de la Reforma/avivamiento, si se quiere.
2. Solo DeepSeek (decisión del usuario 06-10-2026: Gemini sin créditos): TRADUCTOR deepseek-chat, CONTROL
   deepseek-reasoner; los veredictos de gemini-3.6-flash (Juan 1-8) siguen valiendo (JUECES_VALIDOS).

Decisiones del usuario (06-10-2026): escalar a toda la Biblia con el CANON ORTODOXO (deuterocanónicos y
anagignoskomena: Tobías, Judit, adiciones a Ester y Daniel, I-III Macabeos, Sabiduría, Eclesiástico, Baruc y
Carta de Jeremías, III Esdras, Oración de Manasés, Salmo 151; IV Macabeos en apéndice), entre los Testamentos
como Valera 1602; y hacer público el repositorio (la cadena corre en .github/workflows/cadena.yml cuando el
repositorio tenga sus secretos; mientras, en el espejo). cuarentena/ salió de git y del historial antes de publicar.
Texto base deuterocanónico (verificado 06-10-2026 en el catálogo de eBible, fuentes_ci/): no hay Reina 1569 ni
Torres Amat digitales y libres en eBible. Candidata: «Santa Biblia libre para el mundo» (spablm, CC0, «borrador»,
traducida de la World English Bible; registro con «vosotros»; trae todo el canon ortodoxo: TOB JDT ESG WIS SIR BAR
1MA 2MA 1ES MAN PS2 3MA 4MA DAG). Descartada «Biblia libre Latinoamericana» (spabll: paráfrasis coloquial,
«se la pasa orando» en II Mac 15:14). Control: Septuaginta griega de Brenton (grcbrent, dominio público).
Condición de la licencia de spablm: si se cambia el texto, cambiar el nombre.
Orden propuesto: cerrar Hebreos -> NT (Romanos, Gálatas…) -> piloto deuterocanónico (II Macabeos, Tobías) -> AT.

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
