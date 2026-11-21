"""
Validación de la información capturada.

Tres niveles:
1. Campo   : obligatorio, tipo y rango (definidos en config/variables.py).
2. Registro: coherencia interna (ej. menores de 5 <= habitantes).
3. Proyecto: completitud del diagnóstico antes de pasar al motor de cálculo.

Cada hallazgo es un dict {nivel: 'error' | 'alerta', campo, mensaje}.
Los 'error' impiden guardar; las 'alerta' se guardan pero se reportan.
"""
from config.variables import campos_de, mapa_campos

LIMITES_2115 = {  # Res. 2115/2007 – valores máximos aceptables
    "turbiedad_ntu": (2, "UNT"),
    "color_upc": (15, "UPC"),
    "conductividad": (1000, "µS/cm"),
    "coliformes_totales": (0, "UFC/100 mL"),
    "e_coli": (0, "UFC/100 mL"),
    "hierro_mgl": (0.3, "mg/L"),
    "manganeso_mgl": (0.1, "mg/L"),
    "dureza_mgl": (300, "mg/L CaCO₃"),
}


def vacio(v):
    return v is None or v == "" or v == [] or (isinstance(v, float) and v != v)


def validar_campos(formulario, datos):
    hallazgos = []
    for c in campos_de(formulario):
        v = datos.get(c["id"])
        if vacio(v):
            if c.get("req"):
                hallazgos.append({"nivel": "error", "campo": c["id"], "mensaje": f"«{c['label']}» es obligatorio."})
            continue
        if c["tipo"] in ("entero", "decimal"):
            try:
                num = float(v)
            except (TypeError, ValueError):
                hallazgos.append({"nivel": "error", "campo": c["id"], "mensaje": f"«{c['label']}» debe ser numérico."})
                continue
            if c["tipo"] == "entero" and num != int(num):
                hallazgos.append({"nivel": "error", "campo": c["id"], "mensaje": f"«{c['label']}» debe ser un número entero."})
            if "min" in c and num < c["min"]:
                hallazgos.append({"nivel": "error", "campo": c["id"], "mensaje": f"«{c['label']}» no puede ser menor que {c['min']}."})
            if "max" in c and num > c["max"]:
                hallazgos.append({"nivel": "error", "campo": c["id"], "mensaje": f"«{c['label']}» no puede ser mayor que {c['max']}."})
        elif c["tipo"] == "opcion" and v not in c["opciones"]:
            hallazgos.append({"nivel": "error", "campo": c["id"], "mensaje": f"Valor no válido en «{c['label']}»."})
        elif c["tipo"] == "multiple":
            invalidos = [x for x in v if x not in c["opciones"]]
            if invalidos:
                hallazgos.append({"nivel": "error", "campo": c["id"], "mensaje": f"Opciones no válidas en «{c['label']}»: {invalidos}"})
    return hallazgos


def _n(d, k):
    v = d.get(k)
    return None if vacio(v) else float(v)


def _excluyente(d, campo, opcion_nula, etiqueta):
    """Una opción tipo 'Ninguno' no puede marcarse junto a otras."""
    sel = d.get(campo) or []
    if opcion_nula in sel and len(sel) > 1:
        return [{"nivel": "error", "campo": campo, "mensaje": f"En «{etiqueta}» no puede marcar «{opcion_nula}» junto con otras opciones."}]
    return []


def validar_coherencia(formulario, d):
    h = []
    if formulario == "ficha1":
        if d.get("sistema_agua_existente") == "Ninguno" and d.get("estado_sistema_agua") not in (None, "", "No aplica"):
            h.append({"nivel": "error", "campo": "estado_sistema_agua", "mensaje": "Si no hay sistema de agua, el estado debe ser «No aplica»."})
        if d.get("sistema_saneamiento_existente") == "Ninguno" and d.get("estado_sistema_saneamiento") not in (None, "", "No aplica"):
            h.append({"nivel": "error", "campo": "estado_sistema_saneamiento", "mensaje": "Si no hay saneamiento, el estado debe ser «No aplica»."})
        viv, hab = _n(d, "num_viviendas"), _n(d, "num_habitantes")
        if viv and hab:
            ppv = hab / viv
            if ppv < 1 or ppv > 10:
                h.append({"nivel": "alerta", "campo": "num_habitantes", "mensaje": f"Densidad de {ppv:.1f} hab/vivienda fuera del rango usual (1 – 10). Verifique."})
        h += _excluyente(d, "entornos", "Ninguno", "Entornos")
        h += _excluyente(d, "enfermedades", "Ninguna reportada", "Enfermedades")
        h += _excluyente(d, "amenazas", "Ninguna identificada", "Amenazas")
        h += _excluyente(d, "componentes_aseo", "Ninguno", "Componentes de aseo")
        if d.get("alertas_sanitarias") is True and d.get("enfermedades") in (None, [], ["Ninguna reportada"]):
            h.append({"nivel": "alerta", "campo": "enfermedades", "mensaje": "Marcó alertas sanitarias pero no registró enfermedades asociadas."})

    elif formulario == "ficha3":
        if _n(d, "tasa_crecimiento") is None:
            h.append({"nivel": "alerta", "campo": "tasa_crecimiento", "mensaje": "Sin tasa de crecimiento: el motor usará 0,5 % anual (Art. 5, Res. 0844/2018)."})
        if _n(d, "periodo_diseno") is None:
            h.append({"nivel": "alerta", "campo": "periodo_diseno", "mensaje": "Sin periodo de diseño: el motor usará 25 años (Art. 5, Res. 0844/2018)."})
        if _n(d, "tasa_percolacion") is None:
            h.append({"nivel": "alerta", "campo": "tasa_percolacion", "mensaje": "Falta la prueba de percolación: es necesaria para seleccionar sistemas de infiltración."})
        nf = _n(d, "nivel_freatico_m")
        if nf is not None and nf < 1.2:
            h.append({"nivel": "alerta", "campo": "nivel_freatico_m", "mensaje": "Nivel freático somero (< 1,2 m): limita campos de infiltración y letrinas de hoyo."})
        h += _excluyente(d, "organizacion", "Ninguna", "Organización comunitaria")
        h += _excluyente(d, "restricciones", "Ninguna", "Restricciones")

    elif formulario == "fuente":
        qa, qe = _n(d, "caudal_aforado_ls"), _n(d, "caudal_estiaje_ls")
        if qa is not None and qe is not None and qe > qa and d.get("epoca_aforo") == "Seca / estiaje":
            h.append({"nivel": "error", "campo": "caudal_estiaje_ls", "mensaje": "El caudal de estiaje no puede superar el caudal aforado en época seca."})
        if d.get("epoca_aforo") in ("Lluvias", "Transición") and qe is None:
            h.append({"nivel": "alerta", "campo": "caudal_estiaje_ls", "mensaje": "Aforo fuera de época seca: estime el caudal de estiaje para el diseño."})
        if d.get("tipo_fuente") == "Agua lluvia" and _n(d, "precipitacion_mm_anual") is None:
            h.append({"nivel": "error", "campo": "precipitacion_mm_anual", "mensaje": "Para agua lluvia la precipitación media anual es obligatoria."})
        for k, (lim, und) in LIMITES_2115.items():
            v = _n(d, k)
            if v is not None and v > lim:
                h.append({"nivel": "alerta", "campo": k, "mensaje": f"{k} = {v:g} {und} supera el límite de la Res. 2115/2007 ({lim:g} {und}): requiere tratamiento."})
        ph = _n(d, "ph")
        if ph is not None and not (6.5 <= ph <= 9.0):
            h.append({"nivel": "alerta", "campo": "ph", "mensaje": f"pH {ph:g} fuera del rango 6,5 – 9,0 (Res. 2115/2007)."})
        if not d.get("laboratorio_acreditado") and any(_n(d, k) is not None for k in LIMITES_2115):
            h.append({"nivel": "alerta", "campo": "laboratorio_acreditado", "mensaje": "Resultados sin laboratorio acreditado: úselos como indicativos (Art. 13.3.b)."})
        h += _excluyente(d, "actividades_afectan", "Ninguna identificada", "Actividades que afectan")

    elif formulario == "vivienda":
        hab = _n(d, "habitantes") or 0
        for k, txt in (("menores_5", "menores de 5"), ("mayores_60", "mayores de 60"), ("personas_discapacidad", "personas con discapacidad")):
            v = _n(d, k)
            if v is not None and v > hab:
                h.append({"nivel": "error", "campo": k, "mensaje": f"Hay más {txt} ({v:g}) que habitantes ({hab:g})."})
        if (_n(d, "menores_5") or 0) + (_n(d, "mayores_60") or 0) > hab:
            h.append({"nivel": "error", "campo": "menores_5", "mensaje": "Menores de 5 + mayores de 60 supera el total de habitantes."})
        if d.get("consentimiento") is False:
            h.append({"nivel": "error", "campo": "consentimiento", "mensaje": "Sin autorización de tratamiento de datos no se puede registrar la encuesta."})
        cons = _n(d, "consumo_l_dia")
        if cons is not None and d.get("tipo_predio") == "Vivienda" and hab > 0:
            pc = cons / hab
            if pc < 20:
                h.append({"nivel": "alerta", "campo": "consumo_l_dia", "mensaje": f"Consumo de {pc:.0f} L/hab·día: por debajo del mínimo vital; verifique o registre como déficit."})
            elif pc > 300:
                h.append({"nivel": "alerta", "campo": "consumo_l_dia", "mensaje": f"Consumo de {pc:.0f} L/hab·día: muy alto, puede incluir usos productivos."})
        if d.get("voluntad_pago") is True and _n(d, "monto_dispuesto") is None:
            h.append({"nivel": "alerta", "campo": "monto_dispuesto", "mensaje": "Indicó voluntad de pago pero no el monto."})
        if d.get("voluntad_pago") is False and (_n(d, "monto_dispuesto") or 0) > 0:
            h.append({"nivel": "error", "campo": "monto_dispuesto", "mensaje": "Indicó que no pagaría pero registró un monto."})
        if d.get("tipo_saneamiento") == "No tiene (campo abierto)" and d.get("estado_saneamiento") not in (None, "No aplica"):
            h.append({"nivel": "error", "campo": "estado_saneamiento", "mensaje": "Sin sanitario, el estado debe ser «No aplica»."})
        if d.get("almacenamiento") == "No almacena" and (_n(d, "capacidad_almacenamiento_l") or 0) > 0:
            h.append({"nivel": "error", "campo": "capacidad_almacenamiento_l", "mensaje": "Indicó que no almacena pero registró capacidad."})
        h += _excluyente(d, "tratamiento_casa", "No la trata", "Tratamiento del agua")
        h += _excluyente(d, "lavado_manos", "No es habitual", "Lavado de manos")
    return h


def validar(formulario, datos):
    return validar_campos(formulario, datos) + validar_coherencia(formulario, datos)


def hay_errores(hallazgos):
    return any(x["nivel"] == "error" for x in hallazgos)


def completitud(formulario, datos):
    """% de campos obligatorios diligenciados."""
    req = [c for c in campos_de(formulario) if c.get("req")]
    if not req:
        return 100.0
    ok = sum(1 for c in req if not vacio(datos.get(c["id"])))
    return round(100 * ok / len(req), 1)


def tamano_muestra(N, z=1.96, p=0.5, e=0.10):
    """Tamaño de muestra para estimar una proporción (Cochran, 1977) con corrección por población finita."""
    import math
    n0 = z ** 2 * p * (1 - p) / e ** 2
    return min(int(N), math.ceil(n0 / (1 + (n0 - 1) / N)))


def validar_proyecto(proyecto, fuentes, viviendas):
    """Revisión global antes de pasar al motor de cálculo (entregable 2)."""
    h = []
    f1, f3 = proyecto["ficha1"], proyecto["ficha3"]
    for nombre, form, datos in (("Ficha 1", "ficha1", f1), ("Ficha 3", "ficha3", f3)):
        for x in validar(form, datos):
            h.append({**x, "mensaje": f"[{nombre}] {x['mensaje']}"})
    componentes = f3.get("componentes") or []
    if "Agua para consumo humano y doméstico" in componentes and not fuentes:
        h.append({"nivel": "error", "campo": "fuentes", "mensaje": "El proyecto incluye agua pero no hay fuentes registradas (Art. 14)."})
    if not viviendas:
        h.append({"nivel": "error", "campo": "viviendas", "mensaje": "No hay encuestas de vivienda registradas."})
    else:
        n_viv = _n(f3, "viviendas_beneficiar") or _n(f1, "num_viviendas")
        if n_viv:
            n_enc = len([v for v in viviendas if v.get("tipo_predio") == "Vivienda"])
            n_req = tamano_muestra(n_viv)
            if n_enc < n_req:
                h.append({"nivel": "alerta", "campo": "viviendas",
                          "mensaje": f"Se encuestaron {n_enc} de {int(n_viv)} viviendas; para un nivel de confianza del 95 % y un margen de error "
                                     f"del 10 % se requieren al menos {n_req} (Cochran, con corrección por población finita)."})
    for i, f in enumerate(fuentes, 1):
        for x in validar("fuente", f):
            if x["nivel"] == "error":
                h.append({**x, "mensaje": f"[Fuente {f.get('nombre_fuente', i)}] {x['mensaje']}"})
    for v in viviendas:
        for x in validar("vivienda", v):
            if x["nivel"] == "error":
                h.append({**x, "mensaje": f"[Vivienda {v.get('codigo_vivienda', v.get('id'))}] {x['mensaje']}"})
    codigos = [v.get("codigo_vivienda") for v in viviendas]
    duplicados = sorted({c for c in codigos if c and codigos.count(c) > 1})
    if duplicados:
        h.append({"nivel": "error", "campo": "codigo_vivienda", "mensaje": f"Códigos de vivienda repetidos: {', '.join(duplicados)}"})
    return h
