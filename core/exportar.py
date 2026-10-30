"""
Exportación del diagnóstico.

- Excel con: Resumen, Ficha 1, Ficha 3, Fuentes, Viviendas, Validación y
  Diccionario de variables (trazabilidad normativa de cada pregunta).
- Hojas del motor de cálculo (entregable 2): Ficha de proyecto, Memoria de
  cálculo, Oferta vs demanda, matrices multicriterio y parámetros.
- JSON estructurado con datos y resultados.
"""
import io
import json
from datetime import datetime

import pandas as pd
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from config.variables import FORMULARIOS, campos_de
from config.parametros import PARAMETROS
from core.motor import calcular
from core.validacion import completitud, validar_proyecto, vacio

AZUL = "1F4E79"
GRIS = "F2F2F2"


def fmt(v):
    if vacio(v):
        return ""
    if v is True:
        return "Sí"
    if v is False:
        return "No"
    if isinstance(v, list):
        return "; ".join(map(str, v))
    return v


def ficha_a_tabla(formulario, datos):
    filas = []
    for s in FORMULARIOS[formulario]["secciones"]:
        for c in s["campos"]:
            filas.append({
                "Sección": s["seccion"],
                "Variable": c["label"],
                "Valor": fmt(datos.get(c["id"])),
                "Unidad": c.get("unidad", ""),
                "Obligatorio": "Sí" if c.get("req") else "",
                "Referencia normativa": c.get("ref", ""),
            })
    return pd.DataFrame(filas)


def registros_a_tabla(formulario, registros):
    campos = campos_de(formulario)
    cols = {c["id"]: c["label"] + (f" ({c['unidad']})" if c.get("unidad") else "") for c in campos}
    filas = [{cols[k]: fmt(r.get(k)) for k in cols} for r in registros]
    return pd.DataFrame(filas, columns=list(cols.values()))


def diccionario():
    filas = []
    for clave, form in FORMULARIOS.items():
        for s in form["secciones"]:
            for c in s["campos"]:
                filas.append({
                    "Formulario": form["titulo"], "Sección": s["seccion"], "ID": c["id"], "Pregunta": c["label"],
                    "Tipo": c["tipo"], "Opciones": "; ".join(c.get("opciones", [])),
                    "Mínimo": c.get("min", ""), "Máximo": c.get("max", ""), "Unidad": c.get("unidad", ""),
                    "Obligatorio": "Sí" if c.get("req") else "", "Referencia": c.get("ref", ""),
                })
    return pd.DataFrame(filas)


def _prop(lista, cond):
    return round(100 * sum(1 for x in lista if cond(x)) / len(lista), 1) if lista else None


def indicadores(proyecto, fuentes, viviendas):
    """Estadística descriptiva de la captura (no reemplaza el motor de cálculo)."""
    viv = [v for v in viviendas if v.get("tipo_predio") == "Vivienda"]
    hab = sum(v.get("habitantes") or 0 for v in viv)
    cons = sum(v.get("consumo_l_dia") or 0 for v in viv if v.get("consumo_l_dia") is not None)
    hab_cons = sum(v.get("habitantes") or 0 for v in viv if v.get("consumo_l_dia") is not None)
    montos = [v["monto_dispuesto"] for v in viv if v.get("voluntad_pago") and not vacio(v.get("monto_dispuesto"))]
    sin_mejorado = {"Descarga directa a fuente de agua", "No tiene (campo abierto)", "Inodoro con descarga a pozo / zanja"}
    fuente_no_mejorada = {"Nacimiento / quebrada / río (manguera)", "Nacimiento / quebrada / río (acarreo)", "Carrotanque"}
    return [
        ("Encuestas registradas (viviendas y entornos)", len(viviendas), ""),
        ("Viviendas encuestadas", len(viv), ""),
        ("Viviendas del proyecto (Ficha 3)", proyecto["ficha3"].get("viviendas_beneficiar") or proyecto["ficha1"].get("num_viviendas") or "", ""),
        ("Habitantes en viviendas encuestadas", hab, "hab"),
        ("Personas por vivienda (promedio)", round(hab / len(viv), 2) if viv else "", "hab/viv"),
        ("Consumo actual per cápita (promedio ponderado)", round(cons / hab_cons, 1) if hab_cons else "", "L/hab·día"),
        ("Viviendas que se abastecen de fuente superficial sin tratar o carrotanque", _prop(viv, lambda v: v.get("fuente_agua_actual") in fuente_no_mejorada), "%"),
        ("Viviendas que no tratan el agua de bebida", _prop(viv, lambda v: "No la trata" in (v.get("tratamiento_casa") or [])), "%"),
        ("Viviendas sin saneamiento adecuado", _prop(viv, lambda v: v.get("tipo_saneamiento") in sin_mejorado), "%"),
        ("Viviendas sin lugar de lavado de manos con jabón", _prop(viv, lambda v: v.get("lavamanos_jabon") is False), "%"),
        ("Viviendas que queman o botan la basura", _prop(viv, lambda v: bool(set(v.get("manejo_residuos") or []) & {"La quema", "La bota a campo abierto / fuente"})), "%"),
        ("Viviendas con voluntad de pago", _prop(viv, lambda v: v.get("voluntad_pago") is True), "%"),
        ("Monto dispuesto a pagar (mediana)", float(pd.Series(montos).median()) if montos else "", "COP/mes"),
        ("Viviendas que aportarían mano de obra", _prop(viv, lambda v: v.get("aporte_mano_obra") is True), "%"),
        ("Fuentes registradas", len(fuentes), ""),
        ("Caudal total disponible (estiaje o aforado)", round(sum((f.get("caudal_estiaje_ls") if not vacio(f.get("caudal_estiaje_ls")) else f.get("caudal_aforado_ls") or 0) for f in fuentes), 3), "L/s"),
        ("Completitud Ficha 1 (campos obligatorios)", completitud("ficha1", proyecto["ficha1"]), "%"),
        ("Completitud Ficha 3 (campos obligatorios)", completitud("ficha3", proyecto["ficha3"]), "%"),
    ]


# ---------------------------------------------------------------------------
# Tablas del motor de cálculo
# ---------------------------------------------------------------------------
def tabla_ficha_proyecto(res):
    filas = []
    for seccion, items in res["ficha"]:
        for k, v in items:
            filas.append({"Sección": seccion, "Ítem": k, "Contenido": v})
    return pd.DataFrame(filas)


def tabla_fuentes(res):
    return pd.DataFrame([{k: v for k, v in f.items() if not k.startswith("_")} for f in res["fuentes"]])


def tabla_alternativas(alts, pesos):
    filas = []
    for a in alts:
        fila = {"Posición": a.posicion or "No viable", "Alternativa": a.nombre}
        for crit, w in pesos.items():
            fila[f"{crit} ({w * 100:.0f} %)"] = a.puntajes.get(crit) if a.viable else ""
        fila["Puntaje total (1–5)"] = a.total if a.viable else ""
        fila["Condición / motivo"] = a.motivo
        fila["Prediseño"] = "; ".join(f"{k}: {v}" for k, v in a.prediseno.items())
        fila["Justificación"] = " | ".join(f"{k}: {v}" for k, v in a.justificacion.items())
        filas.append(fila)
    return pd.DataFrame(filas)


def tabla_parametros(res):
    filas = []
    for k, v in res["parametros"].items():
        meta = PARAMETROS.get(k, {})
        filas.append({"Parámetro": k, "Valor usado": v, "Unidad": meta.get("unidad", ""),
                      "Tipo": meta.get("tipo", ""), "Fuente": meta.get("ref", "")})
    for k, w in res["pesos"].items():
        filas.append({"Parámetro": f"Peso – {k}", "Valor usado": round(w, 3), "Unidad": "-", "Tipo": "REFERENCIA",
                      "Fuente": "Matriz multicriterio (reemplazar por Matriz RAS oficial)"})
    return pd.DataFrame(filas)


def tabla_sensibilidad(res):
    filas = []
    for clave, titulo in (("agua", "Abastecimiento"), ("saneamiento", "Saneamiento"), ("punto_uso", "Tratamiento en la vivienda")):
        e = (res.get("sensibilidad") or {}).get(clave)
        if not e:
            continue
        filas.append({"Matriz": titulo, "Prueba": "Monte Carlo (2.000 corridas, pesos ×U[0,5; 1,5])", "Criterio variado": "todos",
                      "Ganadora": e["ranking_base"][0], "Misma ganadora (%)": round(e["monte_carlo_primera"], 1),
                      "Mismo ranking (%)": round(e["monte_carlo_ranking"], 1)})
        for x in e["uno_a_uno"]:
            filas.append({"Matriz": titulo, "Prueba": f"Uno a la vez ×{x['factor']:.1f}", "Criterio variado": x["criterio"],
                          "Ganadora": x["primera"], "Misma ganadora (%)": 100 if x["misma_primera"] else 0,
                          "Mismo ranking (%)": 100 if x["mismo_ranking"] else 0})
    return pd.DataFrame(filas)


def tabla_matriz_ras(res):
    """Matriz RAS oficial (hoja Fuentes): criterios en filas y una columna de puntaje por fuente."""
    mr = res.get("matriz_ras") or []
    if not mr:
        return pd.DataFrame({"Nota": ["No aplica: el proyecto no incluye abastecimiento o no hay fuentes registradas."]})
    filas = []
    for i, d in enumerate(mr[0]["detalle"]):
        fila = {"Factor": d["Factor"], "Criterio": d["Criterio"], "Peso": d["Peso"]}
        for m in mr:
            x = m["detalle"][i]
            fila[m["fuente"]] = "sin dato" if x["Puntaje"] is None else x["Puntaje"]
            fila[m["fuente"] + " – base"] = x["Base"]
        filas.append(fila)
    tot = {"Factor": "TOTAL (reescalado a 100)", "Criterio": "Puntos con dato", "Peso": 100}
    for m in mr:
        tot[m["fuente"]] = m["puntaje"]
        tot[m["fuente"] + " – base"] = f"{m['cobertura']} de 100 puntos evaluados"
    filas.append(tot)
    return pd.DataFrame(filas)


def hojas_calculo(res):
    """Lista (nombre_hoja, DataFrame) con los resultados del motor."""
    from config.parametros import PESOS_PUNTO_USO
    if not res.get("ok"):
        return [("Ficha de proyecto", pd.DataFrame({"Alerta": res.get("alertas") or ["Datos insuficientes para calcular"]}))]
    return [
        ("Ficha de proyecto", tabla_ficha_proyecto(res)),
        ("Memoria de cálculo", pd.DataFrame(res["memoria"])),
        ("Oferta vs demanda", tabla_fuentes(res)),
        ("Matriz - Abastecimiento", tabla_alternativas(res["alternativas_agua"], res["pesos"])),
        ("Matriz - Punto de uso", tabla_alternativas(res["alternativas_punto_uso"], PESOS_PUNTO_USO)),
        ("Matriz - Saneamiento", tabla_alternativas(res["alternativas_saneamiento"], res["pesos"])),
        ("Sensibilidad de pesos", tabla_sensibilidad(res)),
        ("Matriz RAS - Fuentes", tabla_matriz_ras(res)),
        ("Parámetros de cálculo", tabla_parametros(res)),
    ]


def _estilo_hoja(ws, ancho_max=60):
    borde = Border(*(Side(style="thin", color="BFBFBF"),) * 4)
    for celda in ws[1]:
        celda.font = Font(bold=True, color="FFFFFF")
        celda.fill = PatternFill("solid", fgColor=AZUL)
        celda.alignment = Alignment(wrap_text=True, vertical="center")
    for fila in ws.iter_rows(min_row=2):
        for celda in fila:
            celda.alignment = Alignment(wrap_text=True, vertical="top")
            celda.border = borde
    for i, col in enumerate(ws.columns, 1):
        largo = max((len(str(c.value)) for c in col if c.value is not None), default=10)
        ws.column_dimensions[get_column_letter(i)].width = min(max(12, largo + 2), ancho_max)
    ws.freeze_panes = "A2"


def exportar_excel(proyecto, fuentes, viviendas, resultado=None):
    buffer = io.BytesIO()
    hallazgos = validar_proyecto(proyecto, fuentes, viviendas)
    resultado = resultado or calcular(proyecto, fuentes, viviendas)
    with pd.ExcelWriter(buffer, engine="openpyxl") as xw:
        pd.DataFrame(indicadores(proyecto, fuentes, viviendas), columns=["Indicador", "Valor", "Unidad"]).to_excel(xw, sheet_name="Resumen", index=False)
        for nombre, df in hojas_calculo(resultado):
            df.to_excel(xw, sheet_name=nombre, index=False)
        ficha_a_tabla("ficha1", proyecto["ficha1"]).to_excel(xw, sheet_name="Ficha 1 - Perfil", index=False)
        ficha_a_tabla("ficha3", proyecto["ficha3"]).to_excel(xw, sheet_name="Ficha 3 - Diagnóstico", index=False)
        registros_a_tabla("fuente", fuentes).to_excel(xw, sheet_name="Fuentes", index=False)
        registros_a_tabla("vivienda", viviendas).to_excel(xw, sheet_name="Viviendas", index=False)
        pd.DataFrame(hallazgos or [{"nivel": "ok", "campo": "", "mensaje": "Sin observaciones"}]) \
            .rename(columns={"nivel": "Nivel", "campo": "Campo", "mensaje": "Observación"}).to_excel(xw, sheet_name="Validación", index=False)
        diccionario().to_excel(xw, sheet_name="Diccionario de variables", index=False)

        ws = xw.book["Resumen"]
        ws.insert_rows(1, 3)
        ws["A1"] = f"Diagnóstico RAS Rural – {proyecto['ficha1'].get('nombre_proyecto', proyecto['nombre'])}"
        ws["A1"].font = Font(bold=True, size=14, color=AZUL)
        f1 = proyecto["ficha1"]
        ws["A2"] = f"{f1.get('vereda', '')} · {f1.get('municipio', '')} · {f1.get('departamento', '')}   |   Generado: {datetime.now():%Y-%m-%d %H:%M}"
        for hoja in xw.book.worksheets:
            if hoja.title == "Resumen":
                continue
            _estilo_hoja(hoja)
        # Encabezado del resumen quedó en la fila 4
        for celda in ws[4]:
            celda.font = Font(bold=True, color="FFFFFF")
            celda.fill = PatternFill("solid", fgColor=AZUL)
        ws.column_dimensions["A"].width = 70
        ws.column_dimensions["B"].width = 18
        ws.column_dimensions["C"].width = 14
    return buffer.getvalue()


def exportar_json(proyecto, fuentes, viviendas, resultado=None):
    """Paquete con los datos del diagnóstico y los resultados del motor."""
    resultado = resultado or calcular(proyecto, fuentes, viviendas)
    paquete = {
        "metadatos": {
            "herramienta": "Diagnóstico RAS Rural",
            "norma_base": "Resolución 0844 de 2018 (MVCT)",
            "generado": datetime.now().isoformat(timespec="seconds"),
            "proyecto_id": proyecto["id"],
        },
        "ficha1": proyecto["ficha1"],
        "ficha3": proyecto["ficha3"],
        "fuentes": [{k: v for k, v in f.items() if k not in ("creado",)} for f in fuentes],
        "viviendas": [{k: v for k, v in v_.items() if k not in ("creado",)} for v_ in viviendas],
        "resultados": {
            "ficha_proyecto": [{"seccion": sec, "items": dict((str(k), v) for k, v in items)} for sec, items in resultado.get("ficha", [])],
            "memoria_calculo": resultado.get("memoria", []),
            "alertas": resultado.get("alertas", []),
        },
    }
    return json.dumps(paquete, ensure_ascii=False, indent=2, default=str).encode("utf-8")
