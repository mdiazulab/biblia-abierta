cap.1: sensibilidad 18/19 = 95%; marcadas 1, corregidas 1, quedan 0; extremo superior ajustado 2.2% -> APROBADO
cap.2: sensibilidad 15/15 = 100%; marcadas 5, corregidas 5, quedan 0; extremo superior ajustado 4.5% -> REVISAR
cap.3: sensibilidad 17/17 = 100%; marcadas 5, corregidas 3, quedan 2; extremo superior ajustado 5.8% -> REVISAR
cap.4: sensibilidad 14/14 = 100%; marcadas 4, corregidas 4, quedan 0; extremo superior ajustado 2.9% -> APROBADO
cap.5: sensibilidad 20/20 = 100%; marcadas 6, corregidas 5, quedan 1; extremo superior ajustado 4.1% -> REVISAR
cap.6: sensibilidad 18/18 = 100%; marcadas 8, corregidas 7, quedan 1; extremo superior ajustado 2.6% -> APROBADO
cap.7: sensibilidad 16/16 = 100%; marcadas 3, corregidas 2, quedan 1; extremo superior ajustado 4.1% -> REVISAR
cap.8: sensibilidad 17/17 = 100%; marcadas 8, corregidas 8, quedan 0; extremo superior ajustado 2.1% -> APROBADO
Traceback (most recent call last):
  File "/home/runner/work/periodico_kindle/periodico_kindle/biblia_abierta/scripts/juez.py", line 116, in <module>
    main()
  File "/home/runner/work/periodico_kindle/periodico_kindle/biblia_abierta/scripts/juez.py", line 88, in main
    for i, (ok, motivo, modelo) in juzgar(pend).items():
                                   ^^^^^^^^^^^^
  File "/home/runner/work/periodico_kindle/periodico_kindle/biblia_abierta/scripts/juez.py", line 47, in juzgar
    r, modelo = C.llamar(prompt(pares[k:k + LOTE]), C.CONTROL, temperatura=0)
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/periodico_kindle/periodico_kindle/biblia_abierta/scripts/comun.py", line 127, in llamar
    raise RuntimeError(f"ningún modelo respondió ({cadena}): {error}")
RuntimeError: ningún modelo respondió (['gemini-3.6-flash', 'gemini-3.1-flash-lite', 'gemini-2.5-flash']): 404 Client Error: Not Found for url: https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=***
