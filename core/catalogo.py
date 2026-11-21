"""
Catálogo detallado y auditoría automática de las variables de la herramienta.

Para cada una de las variables de config/variables.py genera:
  - su clasificación (cuantitativa continua o discreta, cualitativa nominal o
    dicotómica, texto, fecha), su unidad, rango u opciones y su base normativa;
  - el uso que le da la herramienta (motor de cálculo, concepto de
    prefactibilidad, Matriz RAS, reglas de coherencia o solo registro), que se
    obtiene buscando el identificador de la variable en el código fuente;
  - el resultado de una batería de pruebas automáticas de validación:
      O  obligatoriedad: si es obligatoria, dejarla vacía debe dar un error;
      T  tipo: un texto en un campo numérico debe dar un error;
      R  rango: un valor bajo el mínimo y otro sobre el máximo deben dar error;
      E  enteros: un decimal en un campo entero debe dar un error;
      C  catálogo cerrado: una opción que no está en la lista debe dar error;
      V  valor válido: un valor correcto no debe generar ningún error.

Uso:  python3 -m core.catalogo   → genera docs/catalogo_variables.xlsx
"""
import os
import re

import pandas as pd

from config.variables import FORMULARIOS, campos_de
from core.validacion import validar_campos

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODULOS_USO = [  # (archivo, nombre del uso)
    ("core/motor.py", "Motor de cálculo"),
    ("core/prefactibilidad.py", "Concepto de prefactibilidad"),
    ("core/matriz_ras.py", "Matriz RAS"),
    ("core/validacion.py", "Reglas de coherencia"),
]
CLASE = {
    "decimal": "Cuantitativa continua", "entero": "Cuantitativa discreta",
    "opcion": "Cualitativa nominal (una opción)", "multiple": "Cualitativa nominal (varias opciones)",
    "si_no": "Cualitativa dicotómica (sí/no)", "texto": "Texto corto", "parrafo": "Texto largo", "fecha": "Fecha",
}


def _fuentes():
    return {nombre: open(os.path.join(RAIZ, ruta), encoding="utf-8").read() for ruta, nombre in MODULOS_USO}


def usos(var_id, codigo=None):
    codigo = codigo or _fuentes()
    patron = re.compile(r"[\"']" + re.escape(var_id) + r"[\"']")
    return [nombre for nombre, src in codigo.items() if patron.search(src)]


def _valido(c):
    t = c["tipo"]
    if t in ("decimal", "entero"):
        lo = c.get("min", 0)
        hi = c.get("max", lo + 10)
        v = (lo + hi) / 2
        return int(v) if t == "entero" else v
    return {"opcion": lambda: c["opciones"][0], "multiple": lambda: [c["opciones"][0]], "si_no": lambda: True,
            "texto": lambda: "Texto de prueba", "parrafo": lambda: "Texto de prueba", "fecha": lambda: "2026-01-15"}[t]()


def _errores(form, var_id, valor):
    return [h for h in validar_campos(form, {var_id: valor}) if h["campo"] == var_id and h["nivel"] == "error"]


def auditar_variable(form, c):
    pruebas, fallas = [], []

    def prueba(codigo, valor, espera_error):
        pruebas.append(codigo)
        if bool(_errores(form, c["id"], valor)) != espera_error:
            fallas.append(codigo)

    if c.get("req"):
        prueba("O", None, True)
    if c["tipo"] in ("decimal", "entero"):
        prueba("T", "abc", True)
        if "min" in c:
            prueba("R", c["min"] - 1, True)
        if "max" in c:
            prueba("R", c["max"] + 1, True)
        if c["tipo"] == "entero":
            prueba("E", (c.get("min", 0) or 0) + 0.5, True)
    if c["tipo"] == "opcion":
        prueba("C", "Opción inexistente", True)
    if c["tipo"] == "multiple":
        prueba("C", ["Opción inexistente"], True)
    prueba("V", _valido(c), False)
    return "".join(sorted(set(pruebas), key="OTREC V".index)), ("Superada" if not fallas else "Falla: " + "".join(fallas))


def _rango(c):
    if c["tipo"] in ("decimal", "entero"):
        lo, hi = c.get("min"), c.get("max")
        r = f"{lo:g} a {hi:g}" if lo is not None and hi is not None else (f"≥ {lo:g}" if lo is not None else "")
        return (r + (f" {c['unidad']}" if c.get("unidad") else "")).strip()
    if c["tipo"] in ("opcion", "multiple"):
        return f"{len(c['opciones'])} opciones: " + "; ".join(c["opciones"])
    return {"si_no": "Sí / No", "fecha": "AAAA-MM-DD"}.get(c["tipo"], "Libre")


def catalogo():
    """DataFrame con una fila por variable."""
    codigo = _fuentes()
    filas = []
    for form, f in FORMULARIOS.items():
        n = 0
        for s in f["secciones"]:
            for c in s["campos"]:
                n += 1
                u = usos(c["id"], codigo)
                if form in ("ficha1", "ficha3") and c.get("req") and "Concepto de prefactibilidad" not in u:
                    u.append("Concepto de prefactibilidad (completitud)")
                pr, res = auditar_variable(form, c)
                filas.append({
                    "Formulario": f["titulo"], "N.º": n, "Sección": re.sub(r"^[A-Z0-9]{1,2}\. ", "", s["seccion"]),
                    "Identificador": c["id"], "Pregunta": c["label"], "Tipo de dato": c["tipo"], "Clase": CLASE[c["tipo"]],
                    "Unidad, rango u opciones": _rango(c), "Obligatoria": "Sí" if c.get("req") else "No",
                    "Base normativa": c.get("ref", ""), "Uso en la herramienta": "; ".join(u) if u else "Registro y reporte",
                    "Pruebas": pr, "Resultado": res,
                })
    return pd.DataFrame(filas)


def resumen(df=None):
    df = catalogo() if df is None else df
    tab = pd.crosstab(df["Formulario"], df["Clase"], margins=True, margins_name="Total")
    return tab


if __name__ == "__main__":
    df = catalogo()
    ruta = os.path.join(RAIZ, "docs", "catalogo_variables.xlsx")
    with pd.ExcelWriter(ruta) as xw:
        df.to_excel(xw, sheet_name="Catálogo", index=False)
        resumen(df).to_excel(xw, sheet_name="Resumen por clase")
    print(f"{len(df)} variables; pruebas superadas: {(df['Resultado'] == 'Superada').sum()} → {ruta}")
