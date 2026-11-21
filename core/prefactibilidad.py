"""
Concepto de prefactibilidad del proyecto.

Reúne en un solo dictamen los resultados del motor de cálculo. Cada criterio se
califica como CUMPLE, CONDICIONADO o NO CUMPLE, con la evidencia que lo sustenta
y el artículo de la norma. El concepto final se obtiene en dos pasos:

  1. Información (P1 a P3). Si falta la información mínima del perfil, del
     diagnóstico o de la encuesta, el concepto es INFORMACIÓN INSUFICIENTE y se
     reporta un concepto técnico preliminar con los datos disponibles.
  2. Criterios técnicos y sociales (P4 a P12):
       NO PREFACTIBLE                si algún criterio CRÍTICO no se cumple;
       PREFACTIBLE CON CONDICIONES   si no hay fallas críticas, pero algún
                                     criterio no se cumple o queda condicionado;
       PREFACTIBLE                   si todos los criterios se cumplen.

Los criterios críticos son los que hacen inviable el proyecto aunque se
complete la información: no hay fuente con agua suficiente, no hay alternativa
viable de abastecimiento o de saneamiento, o no existe la información mínima
para formular el proyecto.

El costo no se usa para el concepto: en prefactibilidad se califica de forma
cualitativa dentro de las matrices; la comparación de costos a 25 años y su
efecto en la tarifa (Res. 0844, art. 15) corresponden a la etapa siguiente.
"""
from config.variables import campos_de
from core.validacion import completitud, tamano_muestra

CUMPLE, CONDICIONADO, NO_CUMPLE, INFORMATIVO = "Cumple", "Condicionado", "No cumple", "Informativo"
INFORMACION = ("P1", "P2", "P3")       # criterios de información mínima
AGUA = "Agua para consumo humano y doméstico"
SANEAMIENTO = "Saneamiento / aguas residuales"


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _criterio(lista, codigo, nombre, norma, resultado, evidencia, critico=False, accion=""):
    lista.append({"Código": codigo, "Criterio": nombre, "Norma": norma, "Resultado": resultado,
                  "Evidencia": evidencia, "Crítico": critico, "Acción requerida": accion if resultado != CUMPLE else ""})


def _fila_de(alt, filas_fuentes):
    """Fila de la fuente que usa una alternativa de abastecimiento (por su nombre)."""
    if not alt:
        return None
    for f in filas_fuentes:
        if f["Fuente"] and f["Fuente"] in alt.nombre:
            return f
    return None


def concepto(proyecto, fuentes, viviendas, res):
    """Devuelve {'concepto', 'criterios', 'condiciones', 'resumen'} a partir del resultado de motor.calcular."""
    from core.motor import _empate  # evita importación circular
    f1, f3 = proyecto["ficha1"], proyecto["ficha3"]
    p = res["parametros"]
    componentes = f3.get("componentes") or [AGUA, SANEAMIENTO]
    cr = []

    # 1-2. Información mínima (arts. 9 y 14)
    for codigo, form, nombre, art in (("P1", "ficha1", "Información mínima del perfil (Ficha 1)", "Res. 0844, art. 9"),
                                      ("P2", "ficha3", "Información del diagnóstico integral (Ficha 3)", "Res. 0844, art. 14")):
        datos = f1 if form == "ficha1" else f3
        comp = completitud(form, datos)
        faltan = [c["label"] for c in campos_de(form) if c.get("req") and datos.get(c["id"]) in (None, "", [])]
        estado = CUMPLE if comp >= 100 else CONDICIONADO if comp >= 80 else NO_CUMPLE
        _criterio(cr, codigo, nombre, art, estado, f"{comp:.0f} % de los campos obligatorios diligenciados",
                  critico=True, accion="Completar: " + "; ".join(faltan[:6]) + ("…" if len(faltan) > 6 else ""))

    # 3. Representatividad de la encuesta (Cochran)
    viv = [v for v in viviendas if v.get("tipo_predio", "Vivienda") == "Vivienda"]
    N = _num(f1.get("num_viviendas")) or len(viv)
    n_req = tamano_muestra(int(N)) if N else 0
    if not viv:
        estado, ev = NO_CUMPLE, "No hay encuestas de vivienda"
    else:
        estado = CUMPLE if len(viv) >= n_req else CONDICIONADO
        ev = f"{len(viv)} encuestas de {n_req} requeridas (Cochran, 95 %, e = 10 %, N = {N:.0f})"
    _criterio(cr, "P3", "Representatividad de la encuesta por vivienda", "Res. 0844, arts. 9 y 14", estado, ev,
              critico=not viv, accion=f"Aplicar {max(n_req - len(viv), 0)} encuestas más")

    alt_agua = res.get("alternativas_agua") or []
    ffs = res.get("fuentes") or []
    sens = res.get("sensibilidad") or {}
    umbral, est_min = p.get("umbral_empate", 0.2), p.get("estabilidad_minima", 80)

    if AGUA in componentes:
        # 4. Oferta de agua
        aptas = [f for f in ffs if f["_indice"] is not None and f["_indice"] >= 1 and f["Continuidad"] != "Estacional (se seca)"]
        suma = sum(f["_indice"] or 0 for f in ffs if f["Continuidad"] != "Estacional (se seca)")
        lluvia = res.get("lluvia") or {}
        if aptas:
            estado = CUMPLE
            ev = "Fuentes con índice oferta/demanda ≥ 1: " + ", ".join(f"{f['Fuente']} ({f['_indice']:.2f})" for f in aptas)
        elif suma >= 1 or (lluvia.get("cobertura") or 0) >= 0.9:
            estado, ev = CONDICIONADO, f"Ninguna fuente basta sola; sumando fuentes el índice es {suma:.2f}"
        else:
            estado, ev = NO_CUMPLE, f"Oferta total insuficiente: índice oferta/demanda acumulado {suma:.2f}"
        _criterio(cr, "P4", "Oferta de agua suficiente para el caudal máximo diario", "Res. 0844, arts. 13 y 32; Res. 0330, art. 47",
                  estado, ev, critico=True, accion="Aforar en época seca o buscar fuentes adicionales")

        viables = [a for a in alt_agua if a.viable]
        mejor = viables[0] if viables else None
        fila = _fila_de(mejor, ffs)

        # 5. Calidad del agua caracterizada
        if fila is None:
            estado, ev = CONDICIONADO, "La alternativa recomendada no usa una fuente con análisis de calidad"
        else:
            f = fila["_f"]
            n_m = _num(f.get("numero_muestras"))
            multi = f.get("caracterizacion_multiestacional") is True
            if fila["_cod"] == "SIN_DATOS":
                estado, ev = CONDICIONADO, f"«{fila['Fuente']}» sin análisis de laboratorio"
            elif multi:
                estado, ev = CUMPLE, f"«{fila['Fuente']}» con muestras en época seca y de lluvias"
            else:
                estado, ev = CONDICIONADO, f"«{fila['Fuente']}» con {int(n_m) if n_m else 1} muestra(s), sin caracterización multiestacional"
        _criterio(cr, "P5", "Calidad del agua de la fuente caracterizada", "Res. 0844, art. 13.3; Res. 2115/2007", estado, ev,
                  accion="Tomar muestras en época seca y en época de lluvias en laboratorio acreditado")

        # 6. Tratamiento factible
        if fila is None:
            estado, ev = CONDICIONADO, "Sin fuente con calidad conocida"
        elif fila["_cod"] == "ESPECIAL":
            estado, ev = CONDICIONADO, f"«{fila['Fuente']}» requiere tratamiento especial: {fila['Tratamiento requerido']}"
        else:
            estado, ev = CUMPLE, f"{fila['Tratamiento requerido']}"
        _criterio(cr, "P6", "Tratamiento del agua técnicamente factible en zona rural", "Res. 0844, arts. 31 y 36", estado, ev,
                  accion="Estudio de tratabilidad antes de la factibilidad")

        # 7. Alternativa de abastecimiento
        if not mejor:
            estado, ev = NO_CUMPLE, "Ninguna alternativa de abastecimiento es viable"
        else:
            emp = _empate(alt_agua, umbral, sens.get("agua"), est_min)
            estado = CONDICIONADO if (emp or mejor.motivo) else CUMPLE
            ev = f"{mejor.nombre} ({mejor.total:.2f} de 5)" + (f". {emp}" if emp else "") + (f". Condición: {mejor.motivo}" if mejor.motivo else "")
        _criterio(cr, "P7", "Alternativa de abastecimiento viable y estable", "Res. 0844, arts. 15, 16 y 31", estado, ev,
                  critico=True, accion="Decidir con la comunidad entre las alternativas empatadas o atender la condición")

        # 8. Permisos de la fuente
        if fila is not None:
            f = fila["_f"]
            pend = []
            if f.get("concesion_aguas") is False:
                pend.append("concesión de aguas")
            if f.get("propiedad_predio_captacion") == "Privado sin permiso, sin título o no se sabe":
                pend.append("permiso o título del predio de la captación")
            estado = CONDICIONADO if pend else CUMPLE
            ev = ("Pendiente: " + " y ".join(pend)) if pend else "Sin trámites pendientes registrados"
            _criterio(cr, "P8", "Situación legal de la fuente y del predio", "Decreto 1076/2015; Matriz RAS (MVCT)", estado, ev,
                      accion="Tramitar ante la autoridad ambiental y el propietario")

    if SANEAMIENTO in componentes:
        alt_san = res.get("alternativas_saneamiento") or []
        viables = [a for a in alt_san if a.viable]
        if not viables:
            estado, ev = NO_CUMPLE, "Ninguna alternativa de saneamiento es viable"
        else:
            ms = viables[0]
            emp = _empate(alt_san, umbral, sens.get("saneamiento"), est_min)
            estado = CONDICIONADO if (emp or ms.motivo) else CUMPLE
            ev = f"{ms.nombre} ({ms.total:.2f} de 5)" + (f". {emp}" if emp else "") + (f". Condición: {ms.motivo}" if ms.motivo else "")
        _criterio(cr, "P9", "Alternativa de saneamiento viable y estable", "Res. 0844, arts. 37 y 38; proyecto tipo DNP", estado, ev,
                  critico=True, accion="Prueba de percolación y nivel freático; decidir con la comunidad si hay empate")

    # 10. Gestión del riesgo
    amenazas = set(f1.get("amenazas") or []) - {"Ninguna identificada"}
    graves = amenazas & {"Avenida torrencial", "Remoción en masa / deslizamiento", "Inundación"}
    inund = f3.get("zona_inundable") is True
    estado = CONDICIONADO if (graves or inund) else CUMPLE
    ev = ("Amenazas: " + ", ".join(sorted(graves)) + ("; zona inundable" if inund else "")) if estado == CONDICIONADO else (
        "Sin amenazas de inundación, avenida o remoción en masa reportadas")
    _criterio(cr, "P10", "Gestión del riesgo de desastres", "Res. 0844, art. 9; Ley 1523/2012", estado, ev,
              accion="Ubicar la infraestructura fuera de la zona de amenaza o diseñar protección")

    # 11. Aceptación y voluntad de pago
    resp = [v for v in viv if v.get("voluntad_pago") in (True, False)]
    if resp:
        pct = 100 * sum(v.get("voluntad_pago") is True for v in resp) / len(resp)
        estado = CUMPLE if pct >= 50 else CONDICIONADO
        ev = f"{pct:.0f} % de los hogares encuestados está dispuesto a pagar por el servicio"
    else:
        estado, ev = CONDICIONADO, "Sin datos de voluntad de pago"
    _criterio(cr, "P11", "Aceptación comunitaria y voluntad de pago", "Res. 0844, arts. 15 y 16", estado, ev,
              accion="Socializar el proyecto y concertar el esquema tarifario con la comunidad")

    # 12. Organización para operar el sistema
    org = set(f3.get("organizacion") or []) - {"Ninguna"}
    prest = f1.get("prestador_cercano") is True
    estado = CUMPLE if (org or prest) else CONDICIONADO
    ev = ("Organización: " + ", ".join(sorted(org))) if org else ("Hay un prestador cercano" if prest else "No hay organización comunitaria ni prestador")
    _criterio(cr, "P12", "Capacidad de gestión para operar el sistema", "Res. 0844, art. 16", estado, ev,
              accion="Conformar o fortalecer una organización comunitaria prestadora")

    # 13. Costos (informativo)
    _criterio(cr, "P13", "Costos de inversión, operación y tarifa", "Res. 0844, art. 15", INFORMATIVO,
              "Calificación cualitativa dentro de las matrices; la comparación de costos a 25 años corresponde a la factibilidad")

    return _dictamen(cr)


def _veredicto(criterios):
    fallas = [c for c in criterios if c["Crítico"] and c["Resultado"] == NO_CUMPLE]
    pendientes = [c for c in criterios if c["Resultado"] in (CONDICIONADO, NO_CUMPLE)]
    if fallas:
        return "NO PREFACTIBLE", fallas, pendientes
    return ("PREFACTIBLE CON CONDICIONES" if pendientes else "PREFACTIBLE"), fallas, pendientes


def _dictamen(cr):
    """Paso 1: criterios de información (P1 a P3). Paso 2: criterios técnicos y sociales (P4 a P12)."""
    evaluados = [c for c in cr if c["Resultado"] != INFORMATIVO]
    info = [c for c in evaluados if c["Código"] in INFORMACION]
    tecnicos = [c for c in evaluados if c["Código"] not in INFORMACION]
    tecnico, fallas_t, _ = _veredicto(tecnicos)
    info_faltante = [c for c in info if c["Resultado"] == NO_CUMPLE]
    if info_faltante:
        dictamen = "INFORMACIÓN INSUFICIENTE"
    else:
        dictamen, _, _ = _veredicto(evaluados)
    pendientes = [c for c in evaluados if c["Resultado"] in (CONDICIONADO, NO_CUMPLE)]
    conteo = {k: sum(c["Resultado"] == k for c in evaluados) for k in (CUMPLE, CONDICIONADO, NO_CUMPLE)}
    resumen = (f"{conteo[CUMPLE]} criterios se cumplen, {conteo[CONDICIONADO]} quedan condicionados y {conteo[NO_CUMPLE]} no se cumplen"
               + (" (" + ", ".join(c["Código"] for c in fallas_t) + ", críticos)" if fallas_t else "") + ".")
    if info_faltante:
        resumen = (f"No se emite concepto: falta información mínima ({', '.join(c['Código'] for c in info_faltante)}). "
                   f"Concepto técnico preliminar con los datos disponibles: {tecnico}. " + resumen)
    return {"concepto": dictamen, "concepto_tecnico": tecnico, "criterios": cr, "conteo": conteo, "resumen": resumen,
            "condiciones": [f"{c['Código']}. {c['Acción requerida']}" for c in pendientes if c["Acción requerida"]]}
