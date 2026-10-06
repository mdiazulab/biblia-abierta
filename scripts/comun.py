"""Utilidades compartidas: rutas, carga de notas, glosario y llamadas a modelos.

Modelos (misma convención que periodico_kindle/src/providers.py):
  "deepseek:<modelo>"  API nativa de DeepSeek (DEEPSEEK_API_KEY)
  "gemini-<modelo>"    API nativa de Gemini (GEMINI_API_KEY), por REST
  MODELO_FALSO=1       modelo falso determinista para pruebas sin red
"""
import hashlib
import json
import os
import pathlib
import re
import time

import requests

RAIZ = pathlib.Path(__file__).resolve().parent.parent
TERMINOS = json.loads((RAIZ / "glosario" / "terminos.json").read_text())
from libros import LIBROS
SENSIBLES = [f"{k}.{r}" for k, v in LIBROS.items() for r in v["sensibles"]]


def cap(ref):
    return int(ref.split(".")[1])


def ver(ref):
    return int(ref.split(".")[2])


def huella(texto):
    return hashlib.sha1(texto.encode()).hexdigest()[:12]


def cargar(ruta, defecto=None):
    p = RAIZ / ruta
    return json.loads(p.read_text()) if p.exists() else defecto


def guardar(ruta, datos):
    p = RAIZ / ruta
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(datos, ensure_ascii=False, indent=1))


def unidades(libro="JHN"):
    """Notas seleccionadas (normalizado/<libro>/seleccion.json) con su contenido."""
    sel = set(cargar(f"normalizado/{libro}/seleccion.json", []))
    todas = (cargar(f"normalizado/{libro}/aquifer.json", []) + cargar(f"normalizado/{libro}/padres.json", [])
             + cargar(f"normalizado/{libro}/reforma.json", []) + cargar(f"normalizado/{libro}/griego.json", []))
    return [n for n in todas if n["id"] in sel]


_ADJ = {}


def adjudicacion(i, libro, texto=None):
    """Correcciones decididas por Claude leyendo el original (revision/adjudicaciones_<LIBRO>.json), con evidencia:
    {id: {"text_es": ...} | {"reemplazos": [[mal, bien], ...]}, "motivo": ..., "evidencia": <frase inglesa>}.
    «text_es» pisa la traducción; «reemplazos» se aplican sobre el texto actual (sobreviven a una retraducción).
    Si un reemplazo ya no encuentra su texto, devuelve «adjudicacion_pendiente» para que verificar.py lo marque."""
    if libro not in _ADJ:
        _ADJ[libro] = cargar(f"revision/adjudicaciones_{libro}.json", {})
    a = _ADJ[libro].get(i)
    if not a:
        return {}
    if "text_es" in a:
        return {"text_es": a["text_es"]}
    texto = texto or ""
    faltan = [mal for mal, _ in a.get("reemplazos", []) if mal not in texto]
    for mal, bien in a.get("reemplazos", []):
        texto = texto.replace(mal, bien)
    return {"text_es": texto, **({"adjudicacion_pendiente": faltan} if faltan else {})}


def es_sensible(n):
    a, b = n["ref"], n.get("ref_fin", n["ref"])
    return any(s.split(".")[0] == a.split(".")[0] and (cap(a), ver(a)) <= (cap(s), ver(s)) <= (cap(b), ver(b))
               for s in SENSIBLES)


def glosario_para(texto):
    return [t for t in TERMINOS["terminos"] if re.search(t["en"], texto, re.I)]


# ---------------------------------------------------------------- modelos

def _deepseek(prompt, modelo, temperatura):
    razona = "reasoner" in modelo          # el razonador cuenta su cadena en max_tokens; JSON se extrae del texto
    r = requests.post("https://api.deepseek.com/chat/completions",
                      headers={"Authorization": f"Bearer {os.environ['DEEPSEEK_API_KEY']}"},
                      json={"model": modelo, "messages": [{"role": "user", "content": prompt}],
                            "temperature": temperatura, "max_tokens": 32000 if razona else 8000,
                            **({} if razona else {"response_format": {"type": "json_object"}})}, timeout=600)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]


def _gemini(prompt, modelo, temperatura):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent"
    # clave en cabecera, nunca en la URL: los errores de requests imprimen la URL y terminan en los informes
    r = requests.post(url, headers={"x-goog-api-key": os.environ["GEMINI_API_KEY"]},
                      json={"contents": [{"parts": [{"text": prompt}]}],
                            "generationConfig": {"temperature": temperatura, "responseMimeType": "application/json",
                                                 "maxOutputTokens": 16000}}, timeout=300)
    r.raise_for_status()
    return r.json()["candidates"][0]["content"]["parts"][0]["text"]


def _falso(prompt, modelo, temperatura):
    """Devuelve el JSON pedido con el texto marcado «[ES] …»: sirve para probar la cadena sin red."""
    entrada = json.loads(prompt[prompt.index("<<<JSON") + 7:prompt.index("JSON>>>")])
    if "veredicto" in prompt[:400]:
        return json.dumps({"resultados": [{"id": u["id"], "veredicto": "SI", "motivo": ""} for u in entrada]})
    return json.dumps({"notas": [{"id": u["id"], "texto": "[ES] " + u["texto"],
                                  "lemas": ["[ES] " + l for l in u.get("lemas", [])]} for u in entrada]})


def llamar(prompt, cadena, temperatura=0.2, intentos=3):
    """Prueba los modelos de la cadena en orden; devuelve (respuesta JSON parseada, modelo)."""
    if os.getenv("MODELO_FALSO"):
        return json.loads(_falso(prompt, "falso", temperatura)), "falso"
    errores = {}
    vivos = [m for m in cadena if m not in _CAIDOS] or list(cadena)
    for modelo in vivos:
        acceso = False                                   # el último error fue de acceso o cupo (no de formato)
        for k in range(intentos):
            try:
                if modelo.startswith("deepseek:"):
                    if not os.getenv("DEEPSEEK_API_KEY"):
                        break
                    txt = _deepseek(prompt, modelo.split(":", 1)[1], temperatura)
                else:
                    if not os.getenv("GEMINI_API_KEY"):
                        break
                    txt = _gemini(prompt, modelo, temperatura)
                return _json(txt), modelo
            except requests.HTTPError as e:
                errores[modelo] = _sin_claves(str(e))[:200]
                codigo = e.response.status_code if e.response is not None else 0
                acceso = codigo in (400, 401, 403, 404, 429)
                if codigo in (400, 401, 403, 404):       # modelo inexistente o sin permiso: no se reintenta
                    break
                time.sleep(15 * (k + 1) if codigo in (429, 503) else 4 * (k + 1))
            except Exception as e:  # noqa: BLE001 -- red o JSON mal formado: se reintenta
                errores[modelo] = _sin_claves(str(e))[:200]
                acceso = False
                time.sleep(4 * (k + 1))
        # solo un modelo sin acceso o sin cupo queda fuera del resto de la corrida (03-10-2026). Un JSON mal
        # formado NO lo descarta: el 06-10-2026 un solo lote mal formado de DeepSeek cortó la traducción de Hebreos
        # en el cap. 8 porque el modelo había quedado «caído» para todos los lotes siguientes.
        if acceso:
            _CAIDOS.add(modelo)
    raise RuntimeError(f"ningún modelo respondió: {errores}")


def _json(txt):
    """Objeto JSON de la respuesta: sin cercas de código; si no hay objeto, error (se reintenta)."""
    txt = re.sub(r"^```(?:json)?|```$", "", (txt or "").strip(), flags=re.M)
    m = re.search(r"\{.*\}", txt, re.S)
    if not m:
        raise ValueError("respuesta sin objeto JSON")
    return json.loads(m.group(0))


_CAIDOS = set()


def _sin_claves(s):
    """Quita cualquier clave de un mensaje antes de que llegue a un log o informe."""
    for v in ("GEMINI_API_KEY", "DEEPSEEK_API_KEY"):
        if os.getenv(v):
            s = s.replace(os.environ[v], "***")
    return re.sub(r"(?i)(key=|Bearer\s+)[\w.\-]+", r"\1***", s)


TRADUCTOR = ["deepseek:deepseek-chat"]
# juez de otra familia que el traductor; si Gemini agota su cupo diario (02-10-2026, cap. 9 de Juan), sigue
# deepseek-reasoner (de pago, sin cupo; mismo criterio que periodico_kindle/config.json "verificador2"): la
# calibración con errores sembrados de cada capítulo mide si comparte puntos ciegos con el traductor
# gemini-3.1-flash-lite salió de la cadena el 03-10-2026: detectó solo 62-80 % de los errores sembrados
# (caps. 7, 8, 15, 16 de Juan), por debajo de la compuerta de sensibilidad (80 %)
CONTROL = ["gemini-3.6-flash", "deepseek:deepseek-reasoner"]
