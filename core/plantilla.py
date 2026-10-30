"""
Plantilla Excel para encuestas de vivienda y su importación.

Sirve cuando el levantamiento se hace sin computador (formato impreso, tablet
con Excel, o un formulario externo exportado a Excel): se diligencia la
plantilla y luego se importa, pasando por las mismas validaciones.
"""
import io

import pandas as pd
from openpyxl.styles import Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.utils import get_column_letter

from config.variables import campos_de


def _encabezado(c):
    return c["label"] + (f" ({c['unidad']})" if c.get("unidad") else "") + (" *" if c.get("req") else "")


def plantilla_excel(formulario="vivienda"):
    campos = campos_de(formulario)
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as xw:
        pd.DataFrame(columns=[_encabezado(c) for c in campos]).to_excel(xw, sheet_name="Encuestas", index=False)
        pd.DataFrame([{
            "Columna": _encabezado(c), "ID": c["id"], "Tipo": c["tipo"],
            "Valores permitidos": "Sí / No" if c["tipo"] == "si_no" else "; ".join(c.get("opciones", [])),
            "Cómo diligenciar": {
                "multiple": "Separe varias opciones con punto y coma (;)",
                "fecha": "AAAA-MM-DD",
                "si_no": "Sí o No",
            }.get(c["tipo"], c.get("ayuda", "")),
        } for c in campos]).to_excel(xw, sheet_name="Instrucciones", index=False)

        ws = xw.book["Encuestas"]
        listas = xw.book.create_sheet("Listas")
        listas.sheet_state = "hidden"
        col_lista = 1
        for i, c in enumerate(campos, 1):
            letra = get_column_letter(i)
            celda = ws.cell(row=1, column=i)
            celda.font = Font(bold=True, color="FFFFFF")
            celda.fill = PatternFill("solid", fgColor="C00000" if c.get("req") else "1F4E79")
            ws.column_dimensions[letra].width = max(14, min(40, len(celda.value) + 2))
            opciones = ["Sí", "No"] if c["tipo"] == "si_no" else c.get("opciones") if c["tipo"] == "opcion" else None
            if opciones:
                ll = get_column_letter(col_lista)
                for j, o in enumerate(opciones, 1):
                    listas.cell(row=j, column=col_lista, value=o)
                dv = DataValidation(type="list", formula1=f"=Listas!${ll}$1:${ll}${len(opciones)}", allow_blank=True)
                dv.add(f"{letra}2:{letra}1000")
                ws.add_data_validation(dv)
                col_lista += 1
            elif c["tipo"] in ("entero", "decimal"):
                dv = DataValidation(type="whole" if c["tipo"] == "entero" else "decimal", operator="between",
                                    formula1=str(c.get("min", -1e9)), formula2=str(c.get("max", 1e9)), allow_blank=True)
                dv.error = f"Valor entre {c.get('min')} y {c.get('max')}"
                dv.add(f"{letra}2:{letra}1000")
                ws.add_data_validation(dv)
        ws.freeze_panes = "B2"
    return buffer.getvalue()


def _convertir(c, v):
    if v is None or (isinstance(v, float) and v != v) or (isinstance(v, str) and not v.strip()):
        return None
    t = c["tipo"]
    if t == "si_no":
        s = str(v).strip().lower()
        return True if s in ("sí", "si", "s", "1", "true", "x") else False if s in ("no", "n", "0", "false") else v
    if t == "entero":
        return int(float(v))
    if t == "decimal":
        return float(str(v).replace(",", "."))
    if t == "multiple":
        return [x.strip() for x in str(v).split(";") if x.strip()]
    if t == "fecha":
        return pd.to_datetime(v).date().isoformat()
    return str(v).strip()


def leer_excel(contenido, formulario="vivienda"):
    """Devuelve lista de dicts listos para validar. Acepta encabezados con o sin ' *'."""
    df = pd.read_excel(io.BytesIO(contenido), sheet_name=0)
    campos = campos_de(formulario)
    por_columna = {}
    for c in campos:
        for alias in (_encabezado(c), _encabezado(c).rstrip(" *"), c["label"], c["id"]):
            por_columna[alias.strip().lower()] = c
    registros, errores = [], []
    for idx, fila in df.iterrows():
        if fila.isna().all():
            continue
        r = {}
        for col, v in fila.items():
            c = por_columna.get(str(col).strip().lower())
            if c is None:
                continue
            try:
                r[c["id"]] = _convertir(c, v)
            except (ValueError, TypeError):
                errores.append(f"Fila {idx + 2}: valor no válido en «{c['label']}» ({v!r})")
                r[c["id"]] = v
        registros.append(r)
    return registros, errores
