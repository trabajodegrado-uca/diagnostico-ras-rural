"""
Validación del motor de cálculo con trabajos de ingeniería publicados.

Para cada caso se registran:
  * los DATOS DE ENTRADA que reporta el estudio,
  * los PARÁMETROS que usó el estudio (tasa, dotación, pérdidas, k1, k2),
  * los RESULTADOS y la DECISIÓN que reporta el estudio,
  * los SUPUESTOS que fue necesario hacer porque el estudio no trae el dato.

Cada caso se corre dos veces:
  1. Réplica: con los mismos parámetros del estudio → prueba que las fórmulas
     del motor reproducen sus cálculos.
  2. Norma vigente: con los parámetros por defecto de la herramienta
     (Res. 0844/2018 y Res. 330/2017) → muestra qué recomendaría hoy la
     herramienta y por qué difiere, si difiere.

Uso por consola:   python3 -m core.casos_validacion
"""
import copy
import io

import pandas as pd

from config.parametros import valores
from core.motor import calcular

# ---------------------------------------------------------------------------
# Casos
# ---------------------------------------------------------------------------
CASOS = [
    {
        "id": "C1",
        "nombre": "Vereda Monquirá – Sogamoso (Boyacá)",
        "referencia": "Granados Segua, D. F. y López Fernández, Y. J. (2018). Propuesta de diseño de un acueducto en la vereda Monquirá "
                      "(Sogamoso, Boyacá). Trabajo de grado, Ingeniería Civil, Universidad La Gran Colombia.",
        "url": "https://repository.ugc.edu.co/server/api/core/bitstreams/38b80d34-98ff-4d26-8220-00a61ec54d5c/content",
        "norma_estudio": "Res. 0330/2017",
        "que_se_valida": "Cálculo de demanda completo y selección de tratamiento según calidad del agua",
        "ficha1": {"nombre_proyecto": "Monquirá", "departamento": "Boyacá", "municipio": "Sogamoso", "vereda": "Monquirá",
                   "altitud_msnm": 2569, "num_viviendas": 43, "num_habitantes": 200},
        "ficha3": {"componentes": ["Agua para consumo humano y doméstico"], "viviendas_beneficiar": 43, "habitantes_beneficiar": 200,
                   "distribucion_espacial": "Semi-dispersa (50 – 200 m)"},
        "fuentes": [
            {"nombre_fuente": "Río Monquirá", "tipo_fuente": "Río", "caudal_aforado_ls": round((7.75 + 8.13 + 8.26) / 3, 3),
             "metodo_aforo": "Volumétrico", "continuidad": "Permanente",
             "turbiedad_ntu": 1, "color_upc": 3.0, "coliformes_totales": 180, "e_coli": 128, "ph": 5.71, "hierro_mgl": 0.01,
             "laboratorio_acreditado": True},
        ],
        "replica": {"tasa_crecimiento": 2.91, "periodo_diseno": 25, "dotacion_neta": 120, "perdidas": 25, "k1": 1.3, "k2": 1.6},
        "reportado": {"Población futura (hab)": 410, "Dotación neta (L/hab·día)": 120, "Dotación bruta (L/hab·día)": 160,
                      "Qmd (L/s)": 0.759, "QMD (L/s)": 0.987, "QMH (L/s)": 1.579},
        "decision": {
            "Fuente": "Río Monquirá",
            "Tratamiento": "Filtración directa con coagulante y alcalinizante + desinfección",
            "Saneamiento": "No diseñado (90 % de viviendas con pozo séptico)",
        },
        "supuestos": [
            "Altitud: se usa la de la cabecera municipal (2569 m s.n.m.); el estudio no da la de la vereda.",
            "Caudal: promedio de los tres aforos reportados (7,75; 8,13; 8,26 L/s). Época del aforo no reportada.",
            "Continuidad permanente y distribución semi-dispersa: no reportadas.",
            "Población futura reportada 409,70 ≈ 410 hab.",
        ],
    },
    {
        "id": "C2",
        "nombre": "Vereda Socotá – Apulo (Cundinamarca)",
        "referencia": "Jaime Bello, A. T., Martínez Jiménez, J. A. y Torres Quintero, J. E. (2020). Análisis de viabilidad y diseño para el "
                      "abastecimiento de agua potable en la vereda Socotá, Apulo. Revista MUTIS 10(1), 79-96.",
        "url": "https://revistas.utadeo.edu.co/index.php/mutis/article/download/1604/1579/4017",
        "norma_estudio": "Res. 0330/2017",
        "que_se_valida": "Cálculo de demanda y selección de la fuente entre 4 alternativas",
        "ficha1": {"nombre_proyecto": "Socotá", "departamento": "Cundinamarca", "municipio": "Apulo", "vereda": "Socotá",
                   "altitud_msnm": 650, "num_viviendas": 16, "num_habitantes": 64},
        "ficha3": {"componentes": ["Agua para consumo humano y doméstico"], "viviendas_beneficiar": 16, "habitantes_beneficiar": 64,
                   "distribucion_espacial": "Semi-dispersa (50 – 200 m)"},
        "fuentes": [
            {"nombre_fuente": "Empoapulo S.A. E.S.P.", "tipo_fuente": "Conexión a acueducto o prestador existente", "distancia_comunidad_km": 4.75,
             "caudal_aforado_ls": 1.0, "epoca_aforo": "Seca / estiaje", "continuidad": "Permanente",
             "turbiedad_ntu": 1, "color_upc": 5, "coliformes_totales": 0, "e_coli": 0, "ph": 7.0},
            {"nombre_fuente": "Aguas del Tequendama S.A. E.S.P.", "tipo_fuente": "Conexión a acueducto o prestador existente", "distancia_comunidad_km": 2.31,
             "caudal_aforado_ls": 1.0, "epoca_aforo": "Seca / estiaje", "continuidad": "Permanente",
             "turbiedad_ntu": 1, "color_upc": 5, "coliformes_totales": 0, "e_coli": 0, "ph": 7.0},
            {"nombre_fuente": "Acueducto veredal Asuarcopsa", "tipo_fuente": "Conexión a acueducto o prestador existente", "distancia_comunidad_km": 0.95,
             "caudal_aforado_ls": 1.0, "epoca_aforo": "Seca / estiaje", "continuidad": "Permanente",
             "turbiedad_ntu": 1, "color_upc": 5, "coliformes_totales": 0, "e_coli": 0, "ph": 7.0},
            {"nombre_fuente": "Agua subterránea (excavación comunitaria)", "tipo_fuente": "Agua subterránea - aljibe", "distancia_comunidad_km": 0.79,
             "caudal_aforado_ls": 1.0, "epoca_aforo": "Seca / estiaje", "continuidad": "Permanente",
             "turbiedad_ntu": 26.5, "color_upc": 15, "conductividad": 2977, "dureza_mgl": 347.6, "hierro_mgl": 0.123,
             "manganeso_mgl": 0.98, "ph": 7.29, "laboratorio_acreditado": True},
        ],
        "replica": {"tasa_crecimiento": 2.0, "periodo_diseno": 25, "dotacion_neta": 140, "perdidas": 25, "k1": 1.3, "k2": 1.6},
        "reportado": {"Población futura (hab)": 105, "Dotación neta (L/hab·día)": 140, "Dotación bruta (L/hab·día)": 186.67,
                      "Qmd (L/s)": 0.227, "QMD (L/s)": 0.295, "QMH (L/s)": 0.472},
        "decision": {
            "Fuente": "Acueducto veredal Asuarcopsa",
            "Tratamiento": "Agua ya tratada por el prestador (conexión por gravedad, 724 m de PVC de 1\")",
            "Saneamiento": "No evaluado",
        },
        "supuestos": [
            "Altitud: punto medio del rango reportado (500–800 m s.n.m.).",
            "Población: usuarios potenciales (64 hab en 2018, 16 predios); el estudio proyecta 105 hab a 2043 con r = 2 %.",
            "Caudal de las 4 alternativas: no reportado; se asume 1,0 L/s (suficiente) en todas para que la decisión dependa de "
            "distancia y calidad, que son los criterios que usó el estudio.",
            "Calidad de los 3 acueductos: agua potable (no reportada); calidad del agua subterránea: Tabla 5 del estudio.",
        ],
    },
    {
        "id": "C3",
        "nombre": "Vereda Peña Blanca – Puente Nacional (Santander)",
        "referencia": "Contreras Parra, M. K. y Cruz Ramírez, D. C. (2015). Propuesta de acueducto rural para la vereda Peña Blanca, "
                      "municipio de Puente Nacional, Santander. Trabajo de grado, Ingeniería Civil, Universidad La Gran Colombia.",
        "url": "https://repository.ugc.edu.co/server/api/core/bitstreams/2179e193-7a08-4219-a91a-7e667797fd1e/content",
        "norma_estudio": "RAS 2000 (Res. 1096/2000)",
        "que_se_valida": "Cálculo de demanda y elección de fuente (quebrada vs. pozo excavado)",
        "ficha1": {"nombre_proyecto": "Peña Blanca", "departamento": "Santander", "municipio": "Puente Nacional", "vereda": "Peña Blanca",
                   "altitud_msnm": 2800, "num_viviendas": 130, "num_habitantes": 618},
        "ficha3": {"componentes": ["Agua para consumo humano y doméstico"], "viviendas_beneficiar": 130, "habitantes_beneficiar": 618,
                   "distribucion_espacial": "Semi-dispersa (50 – 200 m)"},
        "fuentes": [
            {"nombre_fuente": "Quebrada Otero", "tipo_fuente": "Quebrada", "caudal_aforado_ls": 44, "caudal_estiaje_ls": 44,
             "metodo_aforo": "Flotador", "epoca_aforo": "Seca / estiaje", "continuidad": "Permanente"},
            {"nombre_fuente": "Pozo excavado", "tipo_fuente": "Agua subterránea - aljibe", "caudal_aforado_ls": 0.139,
             "metodo_aforo": "Volumétrico", "continuidad": "Permanente"},
        ],
        "replica": {"tasa_crecimiento": round(((734 / 618) ** (1 / 25) - 1) * 100, 4), "periodo_diseno": 25, "dotacion_neta": 90,
                    "perdidas": 25, "k1": 1.3, "k2": 1.6},
        "reportado": {"Población futura (hab)": 734, "Dotación neta (L/hab·día)": 90, "Dotación bruta (L/hab·día)": 120,
                      "Qmd (L/s)": 1.02, "QMD (L/s)": 1.33, "QMH (L/s)": 2.12},
        "decision": {
            "Fuente": "Quebrada Otero",
            "Tratamiento": "No reportado (sin análisis de laboratorio)",
            "Saneamiento": "No evaluado",
        },
        "supuestos": [
            "Tasa de crecimiento: la que reproduce 618 → 734 hab en 25 años (el texto dice ≈ 1 % pero sus tablas implican ≈ 0,69 %).",
            "Pérdidas: 25 %, deducidas de dotación neta 90 y bruta 120 (el estudio no las reporta).",
            "Altitud 2800 m s.n.m. (el estudio también menciona 2900).",
        ],
    },
    {
        "id": "C4",
        "nombre": "Vereda Puerto Niño – Puerto Boyacá (Boyacá)",
        "referencia": "Henao Walteros, G. P. (2023). Mejoramiento del saneamiento básico en unidades sanitarias para vivienda rural dispersa "
                      "en la vereda Puerto Niño del municipio de Puerto Boyacá. Especialización en Proyectos de Desarrollo, ESAP.",
        "url": "https://repositoriocdim.esap.edu.co/bitstream/handle/20.500.14471/27599/HENAO%20WALTEROS%20GLORIA%20PATRICIA.pdf",
        "norma_estudio": "Res. 0844/2018 (RAS Rural) + Proyecto tipo DNP",
        "que_se_valida": "Esquema de saneamiento (colectivo vs. individual) y tecnología de saneamiento",
        "ficha1": {"nombre_proyecto": "Puerto Niño", "departamento": "Boyacá", "municipio": "Puerto Boyacá", "vereda": "Puerto Niño",
                   "altitud_msnm": 130, "num_viviendas": 37, "num_habitantes": 149, "tipo_asentamiento": "Viviendas dispersas"},
        "ficha3": {"componentes": ["Saneamiento / aguas residuales"], "viviendas_beneficiar": 37, "habitantes_beneficiar": 149,
                   "distribucion_espacial": "Dispersa (> 200 m)", "pendiente_terreno": "Plana (0 – 3 %)", "zona_inundable": False},
        "fuentes": [],
        "replica": {},
        "reportado": {},
        "decision": {
            "Esquema": "Soluciones individuales (se descarta alcantarillado + PTAR por dispersión y costo)",
            "Saneamiento": "Unidad sanitaria con trampa de grasas + tanque séptico + FAFA + campo de infiltración o pozo de absorción",
        },
        "supuestos": [
            "Altitud: la de la cabecera (130 m s.n.m.).",
            "Percolación y nivel freático NO medidos en el estudio (los exige como condición). Se corre sin ellos y, como "
            "sensibilidad, con los valores mínimos que exige el proyecto tipo DNP (percolación 25 min/pulg, nivel freático 1,5 m).",
            "Sin encuesta por vivienda: los criterios sociales toman valores neutros.",
        ],
        "sensibilidad": {"tasa_percolacion": 25, "nivel_freatico_m": 1.5, "tipo_suelo": "Franco / limoso"},
    },
]

CASOS.append({
    "id": "C5",
    "nombre": "Vereda El Arrayán – Caloto (Cauca)",
    "referencia": "Bonilla Castro, I., Palacios, D. M., Ramos Molina, D. y Rojas, J. S. (2025). Diseño de abasto de agua para la vereda "
                  "El Arrayán. Informe final Diseño 2, Ingeniería Civil, Pontificia Universidad Javeriana de Cali.",
    "url": "https://vitela.javerianacali.edu.co/server/api/core/bitstreams/8dd6cccc-c26b-4a98-942f-c3c38a67b5c9/content",
    "norma_estudio": "Cita Res. 0844/2018 y Res. 0330/2017 (abasto rural)",
    "que_se_valida": "Caudal pico por vivienda (dotación × habitantes × k2)",
    "ficha1": {"nombre_proyecto": "El Arrayán – vivienda tipo", "departamento": "Cauca", "municipio": "Caloto", "vereda": "El Arrayán",
               "num_viviendas": 1, "num_habitantes": 6},
    "ficha3": {"componentes": ["Agua para consumo humano y doméstico"], "viviendas_beneficiar": 1, "habitantes_beneficiar": 6,
               "distribucion_espacial": "Semi-dispersa (50 – 200 m)"},
    "fuentes": [],
    "replica": {"tasa_crecimiento": 0.0, "periodo_diseno": 25, "dotacion_neta": 140, "perdidas": 0, "k1": 1.0, "k2": 2.0},
    "reportado": {"Dotación neta (L/hab·día)": 140, "QMH (L/s)": 0.01944},
    "decision": {},
    "supuestos": [
        "El estudio calcula el caudal pico de una vivienda tipo de 6 personas (150 hab en 70 viviendas en total).",
        "No proyecta población ni aplica pérdidas ni k1: se replica con tasa 0 %, pérdidas 0 %, k1 = 1,0 y k2 = 2,0 (valor que reporta).",
        "No reporta altitud, fuente aforada ni calidad del agua: solo se valida el cálculo de caudal.",
    ],
})

CASOS.append({
    "id": "C6",
    "nombre": "Vereda Santa Bárbara – La Playa de Belén (Norte de Santander)",
    "referencia": "Quiroga Vergel, H. P. y Santiago Trigos, S. E. (2016). Diseño de un sistema de potabilización de agua para la vereda "
                  "Santa Bárbara del municipio de La Playa de Belén. Trabajo de grado, Ingeniería Ambiental, Universidad Francisco de Paula Santander Ocaña.",
    "url": "https://repositorioinstitucional.ufpso.edu.co/xmlui/bitstream/handle/20.500.14167/4016/CUERPO_TRABAJO_DISENO_SISTEMA.pdf",
    "norma_estudio": "RAS 2000 y Res. 2115/2007",
    "que_se_valida": "Caso de control (no usado para ajustar): tratamiento según calidad de una quebrada",
    "control": True,
    "ficha1": {"nombre_proyecto": "Santa Bárbara", "departamento": "Norte de Santander", "municipio": "La Playa de Belén", "vereda": "Santa Bárbara",
               "altitud_msnm": 1514, "num_viviendas": 50, "num_habitantes": 173},
    "ficha3": {"componentes": ["Agua para consumo humano y doméstico"], "viviendas_beneficiar": 50, "habitantes_beneficiar": 173,
               "distribucion_espacial": "Semi-dispersa (50 – 200 m)"},
    "fuentes": [
        {"nombre_fuente": "Quebrada La Tinta", "tipo_fuente": "Quebrada", "caudal_aforado_ls": 3.05, "caudal_estiaje_ls": 3.05,
         "metodo_aforo": "Volumétrico", "epoca_aforo": "Seca / estiaje", "continuidad": "Permanente",
         "turbiedad_ntu": 6.66, "color_upc": 79, "ph": 7.08, "hierro_mgl": 1.04, "coliformes_totales": 1100, "e_coli": 1100,
         "laboratorio_acreditado": True, "numero_muestras": 2, "caracterizacion_multiestacional": False},
    ],
    "replica": {},
    "reportado": {},
    "decision": {"Tratamiento": "Tratamiento convencional: coagulación, floculación, sedimentación, filtración y desinfección"},
    "supuestos": [
        "Calidad: valores máximos de las dos muestras de la bocatoma (15 de julio y 15 de agosto); coliformes fecales usados como E. coli.",
        "Caudal disponible: aforo volumétrico de la captación actual en época seca (3,05 L/s).",
        "Altitud 1.514 m s.n.m. (el estudio también menciona 1.450 m). Población sin población flotante.",
        "El caso no se usó para ningún ajuste de la herramienta: se incorporó después de cerrar las reglas.",
    ],
})

# Variables que no verifican nada porque son datos de entrada o quedan fijadas por construcción
POR_CONSTRUCCION = {
    "*": {"Dotación neta (L/hab·día)": "dato de entrada"},
    "C3": {"Población futura (hab)": "la tasa se calculó a partir de la población futura del estudio",
           "Dotación bruta (L/hab·día)": "las pérdidas se dedujeron de la dotación bruta del estudio"},
}
TRIVIALES = {"C5": "una sola multiplicación (6 × 140 × 2 / 86 400)"}

# Reglas del proyecto tipo DNP (basado en la Res. 0844/2018) contra las de la herramienta
REGLAS_DNP = [
    # (regla, valor DNP, entrada de prueba, resultado esperado según DNP)
    ("Nivel freático mínimo para infiltración", "≥ 1,5 m", {"nivel_freatico_m": 1.2, "tasa_percolacion": 20}, False),
    ("Nivel freático mínimo para infiltración", "≥ 1,5 m", {"nivel_freatico_m": 1.6, "tasa_percolacion": 20}, True),
    ("Percolación máxima (2,5 cm en ≤ 30 min)", "≤ 30 min/pulg", {"nivel_freatico_m": 3, "tasa_percolacion": 35}, False),
    ("Percolación máxima (2,5 cm en ≤ 30 min)", "≤ 30 min/pulg", {"nivel_freatico_m": 3, "tasa_percolacion": 28}, True),
    ("Riesgo de inundación bajo", "Sin inundación", {"nivel_freatico_m": 3, "tasa_percolacion": 20, "zona_inundable": True}, False),
]


# ---------------------------------------------------------------------------
# Ejecución
# ---------------------------------------------------------------------------
def _proyecto(caso, modo, extra_f3=None):
    f1, f3 = copy.deepcopy(caso["ficha1"]), copy.deepcopy(caso["ficha3"])
    if modo == "replica":
        f3["tasa_crecimiento"] = caso["replica"].get("tasa_crecimiento")
        f3["periodo_diseno"] = caso["replica"].get("periodo_diseno")
        f3["dotacion_neta_adoptada"] = caso["replica"].get("dotacion_neta")
        f3["perdidas_adoptadas"] = caso["replica"].get("perdidas")
        f3["k1_adoptado"] = caso["replica"].get("k1")
        f3["k2_adoptado"] = caso["replica"].get("k2")
    f3.update(extra_f3 or {})
    return {"id": 0, "nombre": caso["nombre"], "ficha1": f1, "ficha3": f3}


def _fuentes(caso):
    return [dict(f, id=i) for i, f in enumerate(caso["fuentes"], 1)]


def _resultados_numericos(res):
    if not res.get("ok"):
        return {}
    d, perd = res["demanda"]["d"], res["parametros"]["perdidas"]
    return {
        "Población futura (hab)": round(res["poblacion"]["pf"]),
        "Dotación neta (L/hab·día)": d,
        "Dotación bruta (L/hab·día)": round(d / (1 - perd / 100), 2),
        "Qmd (L/s)": round(res["demanda"]["qmd"], 5),
        "QMD (L/s)": round(res["demanda"]["QMD"], 5),
        "QMH (L/s)": round(res["demanda"]["QMH"], 5),
    }


def _mejor(alts):
    return next((a for a in alts if a.viable), None)


def _coincide_texto(nuestro, reportado, claves):
    n, r = (nuestro or "").lower(), (reportado or "").lower()
    return any(k in n and k in r for k in claves)


COMPONENTES = {"coagulación": ("coagul", "convencional", "compacto"), "filtración": ("filtr", "fime"),
               "corrección de pH": ("ph", "alcalin"), "desinfección": ("desinf", "clora")}


def _componentes(texto):
    t = (texto or "").lower()
    return {c for c, claves in COMPONENTES.items() if any(k in t for k in claves)}


def _comparar_tratamiento(nuestra, rep):
    """Compara por componentes del tren de tratamiento (coagulación, filtración, pH, desinfección)."""
    if "no reportado" in rep.lower():
        return "No comparable (el estudio no tiene análisis de calidad)"
    if "tratada por el prestador" in rep.lower():
        return "Coincide" if _componentes(nuestra) == {"desinfección"} else "Difiere"
    a, b = _componentes(nuestra), _componentes(rep)
    if a == b:
        return "Coincide"
    if len(a ^ b) == 1 and ("filtración" in a) == ("filtración" in b):
        return "Coincide parcialmente"
    return "Difiere"


def _proyecto_version(caso, modo, version, extra_f3=None):
    proy = _proyecto(caso, modo, extra_f3)
    return proy


def _fuentes_version(caso, version):
    fs = _fuentes(caso)
    if version == "v1":  # la primera versión no tenía el tipo «conexión a prestador» ni estos campos
        for f in fs:
            if f.get("tipo_fuente") == "Conexión a acueducto o prestador existente":
                f["tipo_fuente"] = "Otra"
    return fs


def decisiones_caso(caso, version="final"):
    """Decisiones de la herramienta frente al estudio. Cada decisión se cuenta una sola vez."""
    aj = {"version_reglas": version}
    res = calcular(_proyecto(caso, "norma"), _fuentes_version(caso, version), [], dict(aj))
    ma = _mejor(res.get("alternativas_agua", []))
    filas = []
    dec = caso["decision"]
    sens = res.get("sensibilidad") or {}
    est_agua = sens.get("agua") or {}
    if "Fuente" in dec:
        nuestra = ma.prediseno.get("Fuente") if ma else "Ninguna viable"
        ok = (nuestra or "").lower().startswith(dec["Fuente"].lower()[:12])
        filas.append({"Caso": caso["id"], "Decisión": "Fuente de abastecimiento", "Estudio": dec["Fuente"], "Herramienta": nuestra,
                      "Estabilidad (%)": est_agua.get("monte_carlo_primera"), "Resultado": "Coincide" if ok else "Difiere"})
    if "Tratamiento" in dec:
        nuestra = ma.prediseno.get("Tratamiento") if ma else ""
        filas.append({"Caso": caso["id"], "Decisión": "Tratamiento del agua", "Estudio": dec["Tratamiento"], "Herramienta": nuestra,
                      "Estabilidad (%)": None, "Resultado": _comparar_tratamiento(nuestra, dec["Tratamiento"])})
    if "Esquema" in dec:
        nuestra = res["esquema"]["saneamiento"] if res.get("ok") else ""
        alc = next((a for a in res.get("alternativas_saneamiento", []) if a.nombre.startswith("Alcantarillado")), None)
        ok = "individual" in nuestra.lower() and alc is not None and not alc.viable
        filas.append({"Caso": caso["id"], "Decisión": "Esquema de saneamiento", "Estudio": dec["Esquema"],
                      "Herramienta": f"{nuestra}; alcantarillado: {alc.motivo if alc else ''}", "Estabilidad (%)": None,
                      "Resultado": "Coincide" if ok else "Difiere"})
    if "Saneamiento" in dec and "no " not in dec["Saneamiento"].lower()[:3]:
        filas.append(_fila_saneamiento(caso, res, dec["Saneamiento"], "Tecnología de saneamiento"))
    return filas, res


def _fila_saneamiento(caso, res, rep, etiqueta):
    alts = res.get("alternativas_saneamiento", [])
    v = [a for a in alts if a.viable]
    m1 = v[0] if v else None
    objetivo = next((a for a in alts if "fafa" in a.nombre.lower() and "infiltración" in a.nombre.lower()), None)
    pos = f"{objetivo.posicion}.° de {len(v)} ({objetivo.total})" if objetivo and objetivo.viable else "no viable"
    p = res["parametros"]
    dif = round(round(v[0].total, 2) - round(v[1].total, 2), 2) if len(v) > 1 else None
    est = ((res.get("sensibilidad") or {}).get("saneamiento") or {}).get("monte_carlo_primera")
    empate = dif is not None and (dif <= p.get("umbral_empate", 0.2) or (est is not None and est < p.get("estabilidad_minima", 80)))
    if m1 is not None and objetivo is not None and m1.nombre == objetivo.nombre:
        r = "Empate técnico" if empate else "Coincide"
    else:
        r = "Difiere (empate técnico)" if empate else "Difiere"
    return {"Caso": caso["id"], "Decisión": etiqueta, "Estudio": rep,
            "Herramienta": f"1.°: {m1.nombre} ({m1.total}); la del estudio: {pos}; diferencia {dif}" if m1 else "—",
            "Estabilidad (%)": est, "Resultado": r}


def verificacion_caso(caso):
    """Verificación de fórmulas: réplica de cálculos con los parámetros del estudio."""
    filas = []
    if not caso["replica"]:
        return filas
    res_r = calcular(_proyecto(caso, "replica"), _fuentes(caso), [])
    nuestro = _resultados_numericos(res_r)
    excl = {**POR_CONSTRUCCION["*"], **POR_CONSTRUCCION.get(caso["id"], {})}
    for k, rep in caso["reportado"].items():
        v = nuestro.get(k)
        err = abs(v - rep) / rep * 100 if (v is not None and rep) else None
        filas.append({"Caso": caso["id"], "Variable": k, "Estudio": rep, "Herramienta (réplica)": v,
                      "Error (%)": round(err, 2) if err is not None else None,
                      "¿Coincide?": "Sí" if err is not None and err <= 1.0 else "No",
                      "Cuenta para la verificación": "No: " + excl[k] if k in excl else "Sí",
                      "Observación": TRIVIALES.get(caso["id"], "")})
    return filas


def correr_caso(caso):
    salida = {"caso": caso, "calculos": verificacion_caso(caso)}
    salida["decisiones"], salida["norma"] = decisiones_caso(caso, "final")
    salida["decisiones_v1"], _ = decisiones_caso(caso, "v1")
    if caso["reportado"]:
        nn = _resultados_numericos(salida["norma"])
        for fila in salida["calculos"]:
            fila["Herramienta (norma vigente)"] = nn.get(fila["Variable"])
    # Análisis de sensibilidad del suelo (no se cuenta como acierto)
    salida["analisis"] = []
    if caso.get("sensibilidad"):
        res_s = calcular(_proyecto(caso, "norma", caso["sensibilidad"]), _fuentes(caso), [])
        fila = _fila_saneamiento(caso, res_s, caso["decision"]["Saneamiento"], "Tecnología de saneamiento con suelo en los mínimos del DNP")
        salida["analisis"].append(fila)
    return salida


def correr_reglas():
    filas = []
    base = CASOS[3]
    for regla, valor, entrada, esperado in REGLAS_DNP:
        res = calcular(_proyecto(base, "norma", entrada), [], [])
        s1 = next(a for a in res["alternativas_saneamiento"] if a.nombre.startswith("Unidad sanitaria: trampa"))
        filas.append({"Regla (proyecto tipo DNP)": regla, "Valor DNP": valor,
                      "Entrada de prueba": ", ".join(f"{k} = {v}" for k, v in entrada.items()),
                      "DNP: ¿apto para infiltración?": "Sí" if esperado else "No",
                      "Herramienta: ¿viable?": "Sí" if s1.viable else f"No ({s1.motivo})",
                      "Resultado": "Coincide" if s1.viable == esperado else "Difiere"})
    return pd.DataFrame(filas)


def _resumen_decisiones(df):
    comp = df[~df["Resultado"].str.startswith("No comparable")]
    return {"comparables": len(comp), "coinciden": int((comp["Resultado"] == "Coincide").sum()),
            "parciales": int((comp["Resultado"] == "Coincide parcialmente").sum()),
            "empates": int(comp["Resultado"].str.contains("mpate").sum()),
            "difieren": int((comp["Resultado"] == "Difiere").sum())}


def correr_todo():
    salidas = [correr_caso(c) for c in CASOS]
    calculos = pd.DataFrame([f for s in salidas for f in s["calculos"]])
    decisiones = pd.DataFrame([f for s in salidas for f in s["decisiones"]])
    v1 = pd.DataFrame([f for s in salidas for f in s["decisiones_v1"]])
    comparacion = decisiones[["Caso", "Decisión", "Estudio"]].copy()
    comparacion["Versión 1"] = v1["Resultado"].values
    comparacion["Herramienta v1"] = v1["Herramienta"].values
    comparacion["Versión final"] = decisiones["Resultado"].values
    comparacion["Conjunto"] = ["Control" if any(c.get("control") and c["id"] == k for c in CASOS) else "Ajuste" for k in comparacion["Caso"]]
    analisis = pd.DataFrame([f for s in salidas for f in s["analisis"]])
    reglas = correr_reglas()
    casos = pd.DataFrame([{"Caso": c["id"], "Nombre": c["nombre"], "Conjunto": "Control" if c.get("control") else "Ajuste",
                           "Norma que usó el estudio": c["norma_estudio"], "Qué se valida": c["que_se_valida"],
                           "Referencia": c["referencia"], "Enlace": c["url"], "Supuestos": " | ".join(c["supuestos"])} for c in CASOS])
    norma = []
    for s in salidas:
        r = s["norma"]
        if r.get("ok"):
            ma, ms = _mejor(r["alternativas_agua"]), _mejor(r["alternativas_saneamiento"])
            n = _resultados_numericos(r)
            norma.append({"Caso": s["caso"]["id"], **n, "Esquema de agua": r["esquema"]["agua"],
                          "Abastecimiento recomendado": ma.nombre if ma else "—",
                          "Saneamiento recomendado": ms.nombre if ms else "—", "Alertas": " | ".join(r["alertas"])})
    mras = []
    for s_ in salidas:
        r_, c_ = s_["norma"], s_["caso"]
        cr = r_.get("contraste_matriz_ras") if r_.get("ok") else None
        if cr and len(c_["fuentes"]) > 1:
            est = c_["decision"].get("Fuente", "")
            mras.append({"Caso": c_["id"], "Fuente del estudio": est, "Herramienta": cr["fuente_herramienta"],
                         "Matriz RAS (1.ª o empatadas)": ", ".join(cr["empatadas"]),
                         "Puntajes Matriz RAS": "; ".join(f"{m['fuente']}: {m['puntaje']}" for m in r_["matriz_ras"]),
                         "Puntos con dato": cr["cobertura_min"],
                         "Resultado": ("Coincide" if cr["coinciden"] and not cr["empate"] else
                                       "Empate que incluye la fuente del estudio" if any(x in est for x in cr["empatadas"]) else "Difiere")})
    ver = calculos[calculos["Cuenta para la verificación"] == "Sí"] if len(calculos) else calculos
    rf, r1 = _resumen_decisiones(decisiones), _resumen_decisiones(v1)
    resumen = {
        "Valores comparados": len(calculos),
        "Valores que verifican fórmulas (sin entradas ni valores fijados por construcción)": len(ver),
        "Verificaciones que coinciden (error ≤ 1 %)": int((ver["¿Coincide?"] == "Sí").sum()) if len(ver) else 0,
        "Error máximo en la verificación (%)": float(ver["Error (%)"].max()) if len(ver) else None,
        "Decisiones comparables (versión final)": rf["comparables"],
        "Coinciden (versión final)": rf["coinciden"],
        "Coinciden parcialmente (versión final)": rf["parciales"],
        "Empate técnico (versión final)": rf["empates"],
        "Difieren (versión final)": rf["difieren"],
        "Coinciden (versión 1)": r1["coinciden"],
        "Coinciden parcialmente (versión 1)": r1["parciales"],
        "Empate técnico (versión 1)": r1["empates"],
        "Difieren (versión 1)": r1["difieren"],
        "Reglas DNP verificadas": len(reglas),
        "Reglas DNP que coinciden": int((reglas["Resultado"] == "Coincide").sum()),
    }
    return {"resumen": resumen, "casos": casos, "calculos": calculos, "verificacion": ver, "decisiones": decisiones,
            "decisiones_v1": v1, "comparacion_versiones": comparacion, "analisis": analisis,
            "norma": pd.DataFrame(norma), "reglas": reglas, "matriz_ras": pd.DataFrame(mras)}


def cargar_casos_en_bd(con):
    """Crea un proyecto por caso (con los parámetros del estudio) para revisarlo en la app."""
    from core import almacenamiento as bd
    ids = []
    for c in CASOS:
        nombre = f"Validación {c['id']} – {c['nombre']}"
        pid = bd.crear_proyecto(con, nombre)
        proy = _proyecto(c, "replica" if c["replica"] else "norma")
        bd.guardar_ficha(con, pid, "ficha1", {**proy["ficha1"], "nombre_proyecto": nombre})
        bd.guardar_ficha(con, pid, "ficha3", {k: v for k, v in proy["ficha3"].items() if v is not None})
        for f in c["fuentes"]:
            bd.agregar_registro(con, pid, "fuente", dict(f))
        ids.append(pid)
    return ids


def tabla_entradas():
    """Datos de entrada de cada caso y dónde se escriben en el programa."""
    filas = []
    donde = {"altitud_msnm": ("Ficha 1", "Altitud media de la comunidad"), "num_viviendas": ("Ficha 1", "Número de viviendas"),
             "num_habitantes": ("Ficha 1", "Número de habitantes"), "habitantes_beneficiar": ("Ficha 3", "Habitantes a beneficiar"),
             "viviendas_beneficiar": ("Ficha 3", "Viviendas a beneficiar"), "distribucion_espacial": ("Ficha 3", "Distribución espacial"),
             "pendiente_terreno": ("Ficha 3", "Pendiente predominante"), "zona_inundable": ("Ficha 3", "¿Es inundable?"),
             "tipo_asentamiento": ("Ficha 1", "Tipo de asentamiento")}
    for c in CASOS:
        for k, (ficha, campo) in donde.items():
            v = c["ficha1"].get(k, c["ficha3"].get(k))
            if v is not None:
                filas.append({"Caso": c["id"], "Dónde": ficha, "Campo": campo, "Valor": v})
        for k, campo in (("tasa_crecimiento", "Tasa de crecimiento anual (%)"), ("periodo_diseno", "Periodo de diseño (años)"),
                         ("dotacion_neta", "Dotación neta adoptada (L/hab·día)"), ("perdidas", "Pérdidas técnicas adoptadas (%)"),
                         ("k1", "Coeficiente k1 adoptado"), ("k2", "Coeficiente k2 adoptado")):
            if k in c["replica"]:
                filas.append({"Caso": c["id"], "Dónde": "Ficha 3", "Campo": campo, "Valor": round(c["replica"][k], 2)})
        for f in c["fuentes"]:
            for k, v in f.items():
                if k != "nombre_fuente":
                    filas.append({"Caso": c["id"], "Dónde": f"Fuente: {f['nombre_fuente']}", "Campo": k, "Valor": v})
    return pd.DataFrame(filas)


def exportar_excel_validacion(r=None):
    r = r or correr_todo()
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as xw:
        pd.DataFrame(list(r["resumen"].items()), columns=["Indicador", "Valor"]).to_excel(xw, sheet_name="Resumen validación", index=False)
        r["casos"].to_excel(xw, sheet_name="Casos y fuentes", index=False)
        tabla_entradas().to_excel(xw, sheet_name="Datos de entrada", index=False)
        r["calculos"].to_excel(xw, sheet_name="Verificación de cálculos", index=False)
        r["decisiones"].to_excel(xw, sheet_name="Decisiones (final)", index=False)
        r["comparacion_versiones"].to_excel(xw, sheet_name="Versión 1 vs final", index=False)
        if len(r["analisis"]):
            r["analisis"].to_excel(xw, sheet_name="Análisis de sensibilidad C4", index=False)
        r["reglas"].to_excel(xw, sheet_name="Reglas DNP", index=False)
        if len(r["matriz_ras"]):
            r["matriz_ras"].to_excel(xw, sheet_name="Contraste Matriz RAS", index=False)
        r["norma"].to_excel(xw, sheet_name="Con norma vigente", index=False)
        from core.exportar import _estilo_hoja
        for ws in xw.book.worksheets:
            _estilo_hoja(ws)
    return buf.getvalue()


if __name__ == "__main__":
    pd.set_option("display.width", 220)
    pd.set_option("display.max_colwidth", 80)
    r = correr_todo()
    for k, v in r["resumen"].items():
        print(f"{k}: {v}")
    print("\n", r["calculos"].to_string(index=False))
    print("\n", r["comparacion_versiones"].to_string(index=False))
    print("\n", r["analisis"].to_string(index=False))
    print("\n", r["reglas"].to_string(index=False))
    print("\n", r["norma"].to_string(index=False))
    with open("validacion_resultados.xlsx", "wb") as fh:
        fh.write(exportar_excel_validacion(r))
    print("\nArchivo generado: validacion_resultados.xlsx")
