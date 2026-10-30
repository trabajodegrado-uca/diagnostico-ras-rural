"""
Parámetros del motor de cálculo (entregable 2).

Cada parámetro indica su fuente. Hay dos tipos:
  * NORMA       -> valor tomado de la normativa (Res. 0844/2018, Res. 330/2017).
  * REFERENCIA  -> valor técnico de referencia (literatura / práctica de
                   prediseño) con su fuente citada; puede reemplazarse por
                   datos locales (estudio de suelos, PGIRS municipal, etc.).

Para cambiar un valor basta con editarlo aquí; la app también permite
ajustar los principales desde la pestaña «Cálculos y alternativas».
"""

PARAMETROS = {
    # ---------------- Población ----------------
    "tasa_crecimiento": {"valor": 0.5, "unidad": "% anual", "tipo": "NORMA",
                         "ref": "Res. 0844/2018 Art. 5 (tasa de 0,5 % anual cuando hay tendencia de crecimiento)"},
    "periodo_diseno": {"valor": 25, "unidad": "años", "tipo": "NORMA",
                       "ref": "Res. 0844/2018 Art. 5 y Art. 15.7; Res. 330/2017 Art. 40"},

    # ---------------- Demanda ----------------
    "dotacion_mayor_2000": {"valor": 120, "unidad": "L/hab·día", "tipo": "NORMA",
                            "ref": "Res. 330/2017 Art. 43, Tabla 1 (> 2000 m s.n.m.)"},
    "dotacion_1000_2000": {"valor": 130, "unidad": "L/hab·día", "tipo": "NORMA",
                           "ref": "Res. 330/2017 Art. 43, Tabla 1 (1000 – 2000 m s.n.m.)"},
    "dotacion_menor_1000": {"valor": 140, "unidad": "L/hab·día", "tipo": "NORMA",
                            "ref": "Res. 330/2017 Art. 43, Tabla 1 (< 1000 m s.n.m.)"},
    "dotacion_neta": {"valor": None, "unidad": "L/hab·día", "tipo": "OPCIONAL",
                      "ref": "Vacío = se toma de la Res. 330 Art. 43 según altitud. Úselo solo para replicar un estudio o por decisión justificada"},
    "dotacion_min_abasto": {"valor": 20, "unidad": "L/hab·día", "tipo": "NORMA", "ref": "Res. 0844/2018 Art. 32.1"},
    "dotacion_max_abasto": {"valor": 200, "unidad": "L/hab·día", "tipo": "NORMA", "ref": "Res. 0844/2018 Art. 32.1"},
    "perdidas": {"valor": 25, "unidad": "%", "tipo": "NORMA",
                 "ref": "Res. 0844/2018 Art. 32.2.a; Res. 330/2017 Art. 44 (máximo 25 %)"},
    "k1": {"valor": 1.3, "unidad": "-", "tipo": "NORMA",
           "ref": "Res. 0330/2017 – coeficiente de consumo máximo diario (no modificado por la Res. 0799/2021); valor aplicado en los estudios C1 y C2"},
    "k2": {"valor": 1.6, "unidad": "-", "tipo": "NORMA",
           "ref": "Res. 0330/2017 – coeficiente de consumo máximo horario (no modificado por la Res. 0799/2021); valor aplicado en los estudios C1 y C2"},
    "umbral_viviendas_acueducto": {"valor": 600, "unidad": "viviendas", "tipo": "NORMA",
                                   "ref": "Res. 0844/2018 Art. 25.b (núcleos de más de 600 viviendas → acueducto)"},

    # Agua para la subsistencia de la familia rural (Art. 3, 31.1 y 32.2.a)
    "consumo_bovino": {"valor": 40, "unidad": "L/animal·día", "tipo": "REFERENCIA",
                       "ref": "Ward y McKague (OMAFRA, 2023): vacas secas y novillas 22–54 L/día (prom. 38); las vacas en ordeño consumen más"},
    "consumo_equino": {"valor": 35, "unidad": "L/animal·día", "tipo": "REFERENCIA", "ref": "Ward y McKague (OMAFRA, 2023): caballo mediano 26–39 L/día (prom. 32,5)"},
    "consumo_porcino": {"valor": 12, "unidad": "L/animal·día", "tipo": "REFERENCIA",
                        "ref": "Ward y McKague (OMAFRA, 2023): cerdo de engorde 7,3–10 L/día; cerdas 13,6–22,7 L/día (valor intermedio)"},
    "consumo_ave": {"valor": 0.25, "unidad": "L/animal·día", "tipo": "REFERENCIA", "ref": "Ward y McKague (OMAFRA, 2023): gallinas ponedoras 0,18–0,32 L/día (prom. 0,25)"},
    "riego_huerta": {"valor": 2.0, "unidad": "L/m²·día", "tipo": "REFERENCIA",
                     "ref": "Riego suplementario ≈ 50 % de una evapotranspiración de cultivo de 4 mm/día (FAO-56, Allen et al., 1998)"},
    "picos_en_subsistencia": {"valor": 0, "unidad": "0 = no / 1 = sí", "tipo": "CRITERIO",
                              "ref": "Res. 0844 art. 32.2.a aplica las pérdidas al agua de subsistencia (QE) pero no coeficientes de pico; por defecto k1 y k2 se aplican solo al consumo doméstico"},

    # ---------------- Fuentes ----------------
    "margen_gravedad": {"valor": 15, "unidad": "m", "tipo": "REFERENCIA",
                        "ref": "Desnivel mínimo fuente–comunidad para conducir por gravedad (presión mín. 5 m.c.a., Res. 0844 Art. 27.5, + pérdidas)"},
    "coef_escorrentia_techo": {"valor": 0.8, "unidad": "-", "tipo": "REFERENCIA", "ref": "Coeficiente de escorrentía de cubierta (Título J, captación de agua lluvia)"},
    "area_techo_tipica": {"valor": 50, "unidad": "m²", "tipo": "REFERENCIA", "ref": "Área de cubierta típica de una vivienda rural – ajustar con el levantamiento"},

    # ---------------- Calidad / tratamiento ----------------
    "turbiedad_filtro_lento": {"valor": 10, "unidad": "UNT", "tipo": "REFERENCIA",
                               "ref": "Límite de entrada a filtración lenta en arena sin pretratamiento (criterios FiME – Cinara / Título J)"},
    "turbiedad_fime": {"valor": 70, "unidad": "UNT", "tipo": "REFERENCIA",
                       "ref": "Límite de aplicación de FiME (filtración gruesa + filtración lenta)"},
    "version_reglas": {"valor": "final", "unidad": "-", "tipo": "CRITERIO",
                       "ref": "«final» = reglas vigentes; «v1» = reglas de la primera versión, solo para comparar en la validación"},
    "umbral_empate": {"valor": 0.20, "unidad": "puntos", "tipo": "CRITERIO",
                      "ref": "Diferencia de puntaje entre la 1.ª y la 2.ª alternativa igual o menor a este valor = empate técnico (Res. 0844 art. 16)"},
    "estabilidad_minima": {"valor": 80, "unidad": "%", "tipo": "CRITERIO",
                           "ref": "Porcentaje mínimo de corridas Monte Carlo de pesos (±50 %) en que la 1.ª alternativa se mantiene para considerarla robusta"},
    "turbiedad_sodis": {"valor": 30, "unidad": "UNT", "tipo": "REFERENCIA", "ref": "Límite de turbiedad para desinfección solar (SODIS)"},

    # ---------------- Saneamiento ----------------
    "coef_retorno": {"valor": 0.85, "unidad": "-", "tipo": "NORMA", "ref": "Res. 330/2017 – coeficiente de retorno de aguas residuales"},
    "percolacion_min": {"valor": 1, "unidad": "min/pulg", "tipo": "REFERENCIA", "ref": "Suelo demasiado permeable: riesgo de contaminar el acuífero (criterio EPA / Título J)"},
    "percolacion_max": {"valor": 30, "unidad": "min/pulg", "tipo": "REFERENCIA",
                        "ref": "DNP–MVCT Proyecto tipo Unidades Sanitarias Vivienda Rural Dispersa (2020, basado en Res. 0844): > 30 min por 2,5 cm → suelo inapropiado para infiltración"},
    "nf_min_infiltracion": {"valor": 1.5, "unidad": "m", "tipo": "REFERENCIA",
                            "ref": "DNP–MVCT Proyecto tipo Unidades Sanitarias (2020): nivel freático mínimo 1,5 m bajo la superficie"},
    "agua_minima_arrastre": {"valor": 45, "unidad": "L/hab·día", "tipo": "REFERENCIA",
                             "ref": "DNP–MVCT Proyecto tipo Unidades Sanitarias (2020): oferta mínima de 45 L/hab·día para sistemas con arrastre hidráulico"},
    "nf_min_letrina": {"valor": 3.0, "unidad": "m", "tipo": "REFERENCIA",
                       "ref": "Profundidad mínima del nivel freático: hoyo de 1,5 m + 1,5 m de separación"},
    "lodo_fresco": {"valor": 1.0, "unidad": "L/hab·día", "tipo": "REFERENCIA", "ref": "NBR 7229 – contribución de lodo fresco (prediseño de tanque séptico)"},

    # ---------------- Aseo ----------------
    "ppc_residuos": {"valor": 0.35, "unidad": "kg/hab·día", "tipo": "REFERENCIA",
                     "ref": "Producción per cápita rural de referencia – reemplazar por el valor del PGIRS municipal"},
    "densidad_residuos": {"valor": 250, "unidad": "kg/m³", "tipo": "REFERENCIA", "ref": "Densidad suelta de residuos ordinarios"},
}

# ---------------------------------------------------------------------------
# Pesos de la matriz multicriterio
# Res. 0844/2018 Art. 16 recomienda metodología multicriterio; los criterios
# combinan los pilares de sostenibilidad del Título J con los del Art. 36.
# REEMPLAZAR por los pesos de la Matriz RAS oficial cuando se tenga.
# ---------------------------------------------------------------------------
PESOS_COLECTIVO = {
    "Eficiencia técnica": 0.25,
    "Costo y capacidad de pago": 0.20,
    "Operación y mantenimiento": 0.20,
    "Aceptabilidad social": 0.15,
    "Sostenibilidad ambiental": 0.10,
    "Gestión del riesgo": 0.10,
}

# Res. 0844/2018 Art. 36: criterios para dispositivos de tratamiento en la vivienda
PESOS_PUNTO_USO = {
    "Eficiencia frente a las necesidades de tratamiento": 0.20,
    "Acceso a bienes y servicios": 0.20,
    "Aceptabilidad social": 0.20,
    "Administración, operación y mantenimiento": 0.20,
    "Costos de la tecnología y consumibles": 0.20,
}

# Puntajes base (1 a 5) de las opciones de tratamiento en el punto de uso.
# Juicio técnico de referencia; el motor los ajusta con los datos del diagnóstico.
PUNTO_USO_BASE = {
    "Filtro cerámico (olla o vela) + almacenamiento seguro": {"ef": 4.0, "acc": 3.0, "aom": 4.0, "cos": 4.0, "habito": "Filtro casero"},
    "Filtro de bioarena + almacenamiento seguro": {"ef": 4.0, "acc": 4.0, "aom": 3.0, "cos": 4.0, "habito": "Filtro casero"},
    "Cloración domiciliar (hipoclorito)": {"ef": 3.5, "acc": 4.0, "aom": 4.0, "cos": 5.0, "habito": "Cloro"},
    "Desinfección solar (SODIS)": {"ef": 3.0, "acc": 5.0, "aom": 3.0, "cos": 5.0, "habito": "Desinfección solar"},
    "Filtro de membrana (ultrafiltración) portátil": {"ef": 5.0, "acc": 2.0, "aom": 4.0, "cos": 2.0, "habito": "Filtro casero"},
}


def valores(sobrescribir=None):
    """Diccionario simple nombre -> valor, con posibles cambios del usuario."""
    v = {k: p["valor"] for k, p in PARAMETROS.items()}
    v.update({k: x for k, x in (sobrescribir or {}).items() if x is not None and k in v})
    return v
