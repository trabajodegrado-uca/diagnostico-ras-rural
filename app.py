"""
Herramienta de diagnóstico RAS Rural – Resolución 0844 de 2018.
Entregable 1: captura y validación de la información (Ficha 1, Ficha 3,
fuentes de agua y encuesta por vivienda).
Entregable 2: motor de cálculo (población, demanda, oferta, tratamiento,
saneamiento, aseo, matrices multicriterio y ficha de proyecto).

Ejecutar:   streamlit run app.py
"""
from datetime import date

import pandas as pd
import streamlit as st

from config.parametros import PARAMETROS, PESOS_COLECTIVO, PESOS_PUNTO_USO
from config.variables import FORMULARIOS
from core import almacenamiento as bd
from core.exportar import (exportar_excel, exportar_json, indicadores, registros_a_tabla, tabla_alternativas,
                           tabla_fuentes)
from core.motor import calcular
from core.plantilla import leer_excel, plantilla_excel
from core.validacion import completitud, hay_errores, validar, validar_proyecto

st.set_page_config(page_title="Diagnóstico RAS Rural", page_icon="💧", layout="wide")


@st.cache_resource
def conexion():
    return bd.conectar()


con = conexion()


# ---------------------------------------------------------------------------
# Generación de widgets a partir del catálogo de variables
# ---------------------------------------------------------------------------
def widget(c, valor, clave):
    etiqueta = c["label"] + (f" ({c['unidad']})" if c.get("unidad") else "") + (" *" if c.get("req") else "")
    ayuda = " · ".join(x for x in (c.get("ayuda"), c.get("ref") and f"Ref.: {c['ref']}") if x) or None
    t = c["tipo"]
    if t == "texto":
        return st.text_input(etiqueta, value=valor or "", help=ayuda, key=clave).strip() or None
    if t == "parrafo":
        return st.text_area(etiqueta, value=valor or "", help=ayuda, key=clave, height=90).strip() or None
    if t in ("entero", "decimal"):
        es_entero = t == "entero"
        conv = int if es_entero else float
        return st.number_input(
            etiqueta, value=None if valor is None else conv(valor), min_value=conv(c["min"]) if "min" in c else None,
            max_value=conv(c["max"]) if "max" in c else None, step=1 if es_entero else None,
            format=None if es_entero else "%.6f" if c["id"].startswith(("lat", "lon")) else "%.2f",
            help=ayuda, key=clave, placeholder="Sin dato",
        )
    if t == "opcion":
        opciones = ["— Seleccione —"] + c["opciones"]
        idx = opciones.index(valor) if valor in opciones else 0
        sel = st.selectbox(etiqueta, opciones, index=idx, help=ayuda, key=clave)
        return None if sel == opciones[0] else sel
    if t == "multiple":
        return st.multiselect(etiqueta, c["opciones"], default=[x for x in (valor or []) if x in c["opciones"]],
                              help=ayuda, key=clave, placeholder="Seleccione una o varias") or None
    if t == "si_no":
        opciones = ["Sin dato", "Sí", "No"]
        idx = 1 if valor is True else 2 if valor is False else 0
        sel = st.radio(etiqueta, opciones, index=idx, horizontal=True, help=ayuda, key=clave)
        return {"Sí": True, "No": False}.get(sel)
    if t == "fecha":
        v = date.fromisoformat(valor) if valor else None
        r = st.date_input(etiqueta, value=v, help=ayuda, key=clave, format="YYYY-MM-DD")
        return r.isoformat() if r else None
    raise ValueError(f"Tipo de campo desconocido: {t}")


def formulario(nombre, valores, prefijo, columnas=2):
    """Pinta todas las secciones de un formulario y devuelve las respuestas."""
    datos = {}
    for s in FORMULARIOS[nombre]["secciones"]:
        st.markdown(f"##### {s['seccion']}")
        cols = st.columns(columnas)
        for i, c in enumerate(s["campos"]):
            ancho_total = c["tipo"] in ("parrafo", "multiple") and columnas > 1
            destino = st.container() if ancho_total else cols[i % columnas]
            with destino:
                datos[c["id"]] = widget(c, valores.get(c["id"]), f"{prefijo}_{c['id']}")
    return datos


def mostrar_hallazgos(hallazgos, exito="Sin observaciones."):
    if not hallazgos:
        st.success(exito)
        return
    for h in hallazgos:
        (st.error if h["nivel"] == "error" else st.warning)(h["mensaje"])


# ---------------------------------------------------------------------------
# Barra lateral: proyectos
# ---------------------------------------------------------------------------
with st.sidebar:
    st.title("💧 Diagnóstico RAS Rural")
    st.caption("Resolución 0844 de 2018 · Ficha 1 · Ficha 3")
    proyectos = bd.listar_proyectos(con)
    nombres = {p["id"]: p["nombre"] for p in proyectos}
    pid = st.selectbox("Proyecto", list(nombres), format_func=nombres.get, index=0 if nombres else None,
                       placeholder="Cree un proyecto") if nombres else None

    with st.expander("➕ Nuevo proyecto", expanded=not nombres):
        with st.form("nuevo", clear_on_submit=True):
            nuevo = st.text_input("Nombre del proyecto")
            if st.form_submit_button("Crear") and nuevo.strip():
                bd.crear_proyecto(con, nuevo.strip())
                st.rerun()
        if st.button("Cargar proyecto de demostración"):
            from core.demo import cargar_demo
            cargar_demo(con)
            st.rerun()
        if st.button("Cargar casos de validación (6 estudios)"):
            from core.casos_validacion import cargar_casos_en_bd
            cargar_casos_en_bd(con)
            st.rerun()

    if pid:
        with st.expander("🗑️ Eliminar proyecto"):
            if st.checkbox("Confirmo que deseo eliminarlo con todas sus encuestas"):
                if st.button("Eliminar definitivamente", type="primary"):
                    bd.eliminar_proyecto(con, pid)
                    st.rerun()

if not pid:
    st.info("Cree un proyecto en la barra lateral (o cargue el de demostración) para empezar.")
    st.stop()

proyecto = bd.obtener_proyecto(con, pid)
fuentes = bd.listar_registros(con, pid, "fuente")
viviendas = bd.listar_registros(con, pid, "vivienda")

st.header(proyecto["nombre"])
m = st.columns(4)
m[0].metric("Ficha 1 completa", f"{completitud('ficha1', proyecto['ficha1'])} %")
m[1].metric("Ficha 3 completa", f"{completitud('ficha3', proyecto['ficha3'])} %")
m[2].metric("Fuentes registradas", len(fuentes))
m[3].metric("Encuestas de vivienda", len(viviendas))

tabs = st.tabs(["Ficha 1 · Perfil", "Ficha 3 · Diagnóstico", "Fuentes de agua", "Encuesta por vivienda",
                "Cálculos y alternativas", "Validación y exportación"])


# ---------------------------------------------------------------------------
# Fichas 1 y 3 (se pueden guardar como borrador)
# ---------------------------------------------------------------------------
def pestaña_ficha(nombre, tab):
    with tab:
        st.caption(
            "Contenido mínimo del perfil de proyecto (Art. 9, Res. 0844/2018)." if nombre == "ficha1"
            else "Contenido mínimo del diagnóstico integral (Art. 14, Res. 0844/2018). Las viviendas y fuentes se registran en sus pestañas."
        )
        with st.form(f"form_{nombre}"):
            datos = formulario(nombre, proyecto[nombre], f"{nombre}_{pid}")
            guardar = st.form_submit_button("💾 Guardar", type="primary")
        if guardar:
            hallazgos = validar(nombre, datos)
            graves = [h for h in hallazgos if h["nivel"] == "error" and "obligatorio" not in h["mensaje"]]
            if graves:
                st.error("No se guardó. Corrija lo siguiente:")
                mostrar_hallazgos(graves)
            else:
                bd.guardar_ficha(con, pid, nombre, datos)
                st.success("Guardado. Los campos obligatorios pendientes se listan abajo." if hallazgos else "Guardado sin observaciones.")
                mostrar_hallazgos(hallazgos)


pestaña_ficha("ficha1", tabs[0])
pestaña_ficha("ficha3", tabs[1])


# ---------------------------------------------------------------------------
# Fuentes y viviendas (registros múltiples)
# ---------------------------------------------------------------------------
def pestaña_registros(tipo, tab, campo_codigo):
    registros = fuentes if tipo == "fuente" else viviendas
    with tab:
        aviso = st.session_state.pop(f"aviso_{tipo}", None)
        if aviso:
            st.success("Registro guardado.")
            mostrar_hallazgos(aviso, exito="")
        if registros:
            st.dataframe(registros_a_tabla(tipo, registros), use_container_width=True, hide_index=True, height=230)
        opciones = {0: "➕ Nuevo registro"} | {r["id"]: f"{r.get(campo_codigo) or 'Sin código'} (#{r['id']})" for r in registros}
        rid = st.selectbox("Registro a diligenciar / editar", list(opciones), format_func=opciones.get, key=f"sel_{tipo}")
        actual = next((r for r in registros if r["id"] == rid), {})
        version = st.session_state.setdefault(f"version_{tipo}", 0)  # cambia la clave para limpiar el formulario
        with st.form(f"form_{tipo}_{rid}"):
            datos = formulario(tipo, actual, f"{tipo}_{pid}_{rid}_{version}")
            guardar = st.form_submit_button("💾 Guardar registro", type="primary")
        if guardar:
            hallazgos = validar(tipo, datos)
            if tipo == "vivienda" and datos.get("codigo_vivienda") in {r.get("codigo_vivienda") for r in registros if r["id"] != rid}:
                hallazgos.append({"nivel": "error", "campo": "codigo_vivienda", "mensaje": "Ese código de vivienda ya existe."})
            if hay_errores(hallazgos):
                st.error("No se guardó. Corrija lo siguiente:")
                mostrar_hallazgos([h for h in hallazgos if h["nivel"] == "error"])
            else:
                if rid:
                    bd.actualizar_registro(con, rid, datos)
                else:
                    bd.agregar_registro(con, pid, tipo, datos)
                st.session_state[f"aviso_{tipo}"] = [h for h in hallazgos if h["nivel"] == "alerta"]
                st.session_state[f"version_{tipo}"] = version + 1
                st.rerun()
        if rid and st.button("🗑️ Eliminar este registro", key=f"del_{tipo}_{rid}"):
            bd.eliminar_registro(con, rid)
            st.rerun()


pestaña_registros("fuente", tabs[2], "nombre_fuente")
pestaña_registros("vivienda", tabs[3], "codigo_vivienda")

with tabs[3]:
    with st.expander("📥 Trabajo de campo sin computador: plantilla Excel e importación"):
        st.download_button("Descargar plantilla de encuesta (.xlsx)", plantilla_excel("vivienda"),
                           file_name="plantilla_encuesta_vivienda.xlsx")
        archivo = st.file_uploader("Importar encuestas diligenciadas", type=["xlsx"])
        if archivo:
            registros, errores = leer_excel(archivo.getvalue(), "vivienda")
            existentes = {v.get("codigo_vivienda") for v in viviendas}
            validos, rechazados = [], []
            for r in registros:
                h = validar("vivienda", r)
                if r.get("codigo_vivienda") in existentes:
                    h.append({"nivel": "error", "mensaje": "código ya registrado"})
                (rechazados if hay_errores(h) else validos).append((r, h))
            st.write(f"Filas leídas: {len(registros)} · válidas: {len(validos)} · con errores: {len(rechazados)}")
            for e in errores:
                st.error(e)
            for r, h in rechazados:
                st.error(f"{r.get('codigo_vivienda', 'Sin código')}: " + "; ".join(x["mensaje"] for x in h if x["nivel"] == "error"))
            if validos and st.button(f"Importar {len(validos)} encuestas válidas", type="primary"):
                for r, _ in validos:
                    bd.agregar_registro(con, pid, "vivienda", r)
                st.rerun()


# ---------------------------------------------------------------------------
# Cálculos y alternativas (entregable 2)
# ---------------------------------------------------------------------------
AJUSTABLES = ["tasa_crecimiento", "perdidas", "k1", "k2", "consumo_bovino", "consumo_equino", "consumo_porcino",
              "consumo_ave", "riego_huerta", "ppc_residuos", "area_techo_tipica"]

with tabs[4]:
    st.caption("Procesamiento automático del diagnóstico: cada resultado indica su fórmula y su referencia normativa.")
    with st.expander("⚙️ Ajustar parámetros y pesos de la matriz"):
        st.caption("Por defecto se usan los valores de config/parametros.py. Los cambios aplican solo a esta sesión.")
        ajustes = {}
        cols = st.columns(3)
        for i, k in enumerate(AJUSTABLES):
            meta = PARAMETROS[k]
            ajustes[k] = cols[i % 3].number_input(f"{k} ({meta['unidad']})", value=float(meta["valor"]), min_value=0.0,
                                                  help=f"{meta['tipo']}: {meta['ref']}", key=f"par_{k}")
        st.markdown("**Pesos de la matriz multicriterio** (se normalizan para sumar 100 %)")
        cols = st.columns(3)
        pesos = {crit: cols[i % 3].slider(crit, 0, 50, int(w * 100), key=f"peso_{crit}") for i, (crit, w) in enumerate(PESOS_COLECTIVO.items())}
        ajustes = {k: v for k, v in ajustes.items() if v != PARAMETROS[k]["valor"]}
        if pesos != {k: int(w * 100) for k, w in PESOS_COLECTIVO.items()}:
            ajustes["pesos"] = {k: v / 100 for k, v in pesos.items()}
    st.session_state["ajustes"] = ajustes

    res = calcular(proyecto, fuentes, viviendas, dict(ajustes))
    if not res["ok"]:
        st.error("No hay datos suficientes para calcular.")
        mostrar_hallazgos([{"nivel": "error", "mensaje": a} for a in res["alertas"]], exito="")
    else:
        dem, pob = res["demanda"], res["poblacion"]
        k = st.columns(4)
        k[0].metric("Población futura", f"{pob['pf']:.0f} hab", f"+{pob['pf'] - pob['p0']:.0f} en {pob['n']} años")
        k[1].metric("Dotación neta", f"{dem['d']:g} L/hab·día")
        k[2].metric("Caudal máximo diario (QMD)", f"{dem['QMD']:.3f} L/s")
        k[3].metric("Caudal máximo horario (QMH)", f"{dem['QMH']:.3f} L/s")
        for a in res["alertas"]:
            st.warning(a)

        st.subheader("📄 Ficha de proyecto")
        for seccion, items in res["ficha"]:
            with st.expander(seccion, expanded=seccion in ("Abastecimiento recomendado", "Saneamiento recomendado")):
                for item, valor in items:
                    if valor not in (None, ""):
                        st.markdown(f"**{item}:** {valor}")

        st.subheader("💧 Oferta vs. demanda")
        st.dataframe(tabla_fuentes(res), use_container_width=True, hide_index=True)

        st.subheader("⚖️ Matrices multicriterio")
        for titulo, clave, pz in (("Abastecimiento", "alternativas_agua", res["pesos"]),
                                  ("Tratamiento en la vivienda (Art. 36)", "alternativas_punto_uso", PESOS_PUNTO_USO),
                                  ("Saneamiento", "alternativas_saneamiento", res["pesos"])):
            if not res[clave]:
                continue
            st.markdown(f"**{titulo}**")
            df = tabla_alternativas(res[clave], pz)
            st.dataframe(df.drop(columns=["Justificación"]), use_container_width=True, hide_index=True)
            graf = df[df["Puntaje total (1–5)"] != ""][["Alternativa", "Puntaje total (1–5)"]].set_index("Alternativa")
            if not graf.empty:
                try:
                    st.bar_chart(graf.astype(float), horizontal=True, height=60 + 40 * len(graf))
                except TypeError:  # versiones de Streamlit sin barras horizontales
                    st.bar_chart(graf.astype(float))

        st.subheader("🎲 Sensibilidad de los pesos")
        st.caption("Cada peso se varía ±50 % uno a la vez y en 2.000 corridas Monte Carlo (todos a la vez, renormalizados). "
                   "Se reporta en qué porcentaje de las corridas se mantiene la alternativa ganadora y el ranking completo.")
        filas = []
        for clave, titulo in (("agua", "Abastecimiento"), ("saneamiento", "Saneamiento"), ("punto_uso", "Tratamiento en la vivienda")):
            e = (res.get("sensibilidad") or {}).get(clave)
            if e:
                filas.append({"Matriz": titulo, "Ganadora": e["ranking_base"][0],
                              "Misma ganadora ±50 % uno a uno (%)": round(e["uno_a_uno_primera"], 1),
                              "Misma ganadora Monte Carlo (%)": round(e["monte_carlo_primera"], 1),
                              "Mismo ranking Monte Carlo (%)": round(e["monte_carlo_ranking"], 1)})
        if filas:
            st.dataframe(pd.DataFrame(filas), use_container_width=True, hide_index=True)

        if res.get("matriz_ras"):
            st.subheader("🏛️ Contraste con la Matriz RAS del Ministerio (fuentes)")
            st.caption("Matriz de ejemplo publicada por Minvivienda (hoja «Fuentes», 100 puntos). Los criterios sin dato se omiten "
                       "y el puntaje se reescala; llene la sección «Entorno de la fuente» de cada fuente para completarla.")
            from core.exportar import tabla_matriz_ras
            st.dataframe(tabla_matriz_ras(res).astype(str), use_container_width=True, hide_index=True)
            c = res.get("contraste_matriz_ras") or {}
            if c:
                from core.motor import _texto_ras
                (st.success if c["compatible"] else st.warning)(_texto_ras(c))

        with st.expander("🧮 Memoria de cálculo completa"):
            st.dataframe(pd.DataFrame(res["memoria"]).astype(str), use_container_width=True, hide_index=True)


# ---------------------------------------------------------------------------
# Validación global y exportación
# ---------------------------------------------------------------------------
with tabs[5]:
    st.subheader("Revisión del diagnóstico")
    hallazgos = validar_proyecto(proyecto, fuentes, viviendas)
    if not hay_errores(hallazgos):
        st.success("El diagnóstico está completo y listo para el procesamiento (motor de cálculo).")
    mostrar_hallazgos(hallazgos, exito="")

    st.subheader("Indicadores de la captura")
    st.dataframe(pd.DataFrame(indicadores(proyecto, fuentes, viviendas), columns=["Indicador", "Valor", "Unidad"]).astype(str),
                 use_container_width=True, hide_index=True)

    with st.expander("✅ Validación de la herramienta con casos publicados"):
        st.caption("Se cargan los datos de trabajos de grado y estudios publicados, se corren en el motor y se comparan "
                   "cálculos y decisiones. Detalle de fuentes y supuestos en la hoja «Casos y fuentes» del Excel.")
        from core.casos_validacion import correr_todo, exportar_excel_validacion
        val = correr_todo()
        cols = st.columns(3)
        rs = val["resumen"]
        cols[0].metric("Verificación de fórmulas", f"{rs['Verificaciones que coinciden (error ≤ 1 %)']} de {rs['Valores que verifican fórmulas (sin entradas ni valores fijados por construcción)']}",
                       f"error máx. {rs['Error máximo en la verificación (%)']} %", delta_color="off")
        cols[1].metric("Decisiones (versión final)",
                       f"{rs['Coinciden (versión final)']} coinciden · {rs['Coinciden parcialmente (versión final)']} parcial · {rs['Difieren (versión final)'] + rs['Empate técnico (versión final)']} difieren",
                       f"de {rs['Decisiones comparables (versión final)']} comparables", delta_color="off")
        cols[2].metric("Reglas DNP que coinciden", f"{rs['Reglas DNP que coinciden']} de {rs['Reglas DNP verificadas']}")
        st.markdown("**Verificación de fórmulas** (las filas marcadas «No» son datos de entrada o valores fijados por construcción)")
        st.dataframe(val["calculos"], use_container_width=True, hide_index=True)
        st.markdown("**Validación de decisiones: versión 1 frente a versión final** (C6 es el caso de control, no usado para ajustar)")
        st.dataframe(val["comparacion_versiones"], use_container_width=True, hide_index=True)
        if len(val["analisis"]):
            st.markdown("**Análisis de sensibilidad del suelo en C4** (no se cuenta como acierto)")
            st.dataframe(val["analisis"], use_container_width=True, hide_index=True)
        st.download_button("Descargar validación (.xlsx)", exportar_excel_validacion(val), file_name="validacion_herramienta.xlsx")

    st.subheader("Exportar")
    nombre_archivo = "".join(ch if ch.isalnum() else "_" for ch in proyecto["nombre"])[:50]
    c1, c2 = st.columns(2)
    res_exp = calcular(proyecto, fuentes, viviendas, dict(st.session_state.get("ajustes", {})))
    c1.download_button("📊 Diagnóstico y cálculos en Excel", exportar_excel(proyecto, fuentes, viviendas, res_exp),
                       file_name=f"diagnostico_{nombre_archivo}.xlsx", type="primary", use_container_width=True)
    c2.download_button("🧮 Datos y resultados (JSON)", exportar_json(proyecto, fuentes, viviendas, res_exp),
                       file_name=f"diagnostico_{nombre_archivo}.json", use_container_width=True)
