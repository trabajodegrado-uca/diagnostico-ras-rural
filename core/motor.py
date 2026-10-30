"""
Motor de cálculo – Entregable 2.

Toma la información capturada (Ficha 1, Ficha 3, fuentes y viviendas) y:
  1. Proyecta la población al horizonte de diseño.
  2. Calcula la demanda de agua (consumo humano y doméstico + subsistencia).
  3. Compara oferta vs. demanda en cada fuente.
  4. Define el nivel de tratamiento según la calidad del agua.
  5. Evalúa la viabilidad de las soluciones de saneamiento según el suelo.
  6. Estima la producción de residuos sólidos (aseo).
  7. Califica las alternativas con matrices multicriterio y las ordena.
  8. Arma la ficha de proyecto con la alternativa recomendada.

Todo resultado se registra en la «memoria de cálculo» con su fórmula y su
referencia normativa, para que sea trazable en el documento de grado.

Uso:
    from core.motor import calcular
    r = calcular(proyecto, fuentes, viviendas)
"""
import math
from dataclasses import dataclass, field
from statistics import median

from config.parametros import PARAMETROS, PESOS_COLECTIVO, PESOS_PUNTO_USO, PUNTO_USO_BASE, valores


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------
def _num(v):
    if v is None or v == "" or (isinstance(v, float) and v != v):
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _clip(x, lo=1.0, hi=5.0):
    return max(lo, min(hi, x))


def _pct(lista, cond):
    return 100 * sum(1 for x in lista if cond(x)) / len(lista) if lista else None


def _r(x, n=2):
    return None if x is None else round(x, n)


@dataclass
class Alternativa:
    nombre: str
    componente: str
    viable: bool = True
    motivo: str = ""                     # por qué no es viable / condición
    puntajes: dict = field(default_factory=dict)
    justificacion: dict = field(default_factory=dict)
    prediseno: dict = field(default_factory=dict)
    total: float = 0.0
    posicion: int = 0

    def calificar(self, pesos):
        if not self.viable:
            self.total = 0.0
            return
        self.puntajes = {k: round(_clip(self.puntajes.get(k, 3.0)), 2) for k in pesos}
        self.total = round(sum(self.puntajes[k] * w for k, w in pesos.items()), 2)


class Memoria:
    """Memoria de cálculo: filas (bloque, concepto, valor, unidad, cálculo/referencia)."""

    def __init__(self):
        self.filas = []
        self.alertas = []

    def add(self, bloque, concepto, valor, unidad="", calculo=""):
        self.filas.append({"Bloque": bloque, "Concepto": concepto, "Valor": valor, "Unidad": unidad, "Cálculo / referencia": calculo})
        return valor

    def alerta(self, txt):
        if txt not in self.alertas:
            self.alertas.append(txt)


def _ordenar(alternativas, pesos):
    for a in alternativas:
        a.calificar(pesos)
    viables = sorted([a for a in alternativas if a.viable], key=lambda a: -a.total)
    for i, a in enumerate(viables, 1):
        a.posicion = i
    return viables + [a for a in alternativas if not a.viable]


# ---------------------------------------------------------------------------
# 1. Población
# ---------------------------------------------------------------------------
def poblacion(f1, f3, viviendas, p, m):
    B = "1. Población"
    viv = [v for v in viviendas if v.get("tipo_predio") == "Vivienda" and _num(v.get("habitantes"))]
    ppv_enc = sum(_num(v["habitantes"]) for v in viv) / len(viv) if viv else None
    n_viv = _num(f3.get("viviendas_beneficiar")) or _num(f1.get("num_viviendas"))
    p0 = _num(f3.get("habitantes_beneficiar")) or _num(f1.get("num_habitantes"))
    origen = "Ficha 3 / Ficha 1"
    if p0 is None and n_viv and ppv_enc:
        p0, origen = n_viv * ppv_enc, "viviendas × personas por vivienda de la encuesta"
    if p0 is None:
        m.alerta("No hay número de habitantes: complete la Ficha 1 o la Ficha 3.")
        return None
    # Densidad coherente con P₀: si hay viviendas en la ficha se usa P₀ / viviendas
    ppv = (p0 / n_viv) if n_viv else (ppv_enc or 4.0)
    if ppv_enc and n_viv and abs(ppv_enc - p0 / n_viv) / (p0 / n_viv) > 0.2:
        m.alerta(f"La densidad de la encuesta ({ppv_enc:.2f} hab/viv) difiere más de 20 % de la de la ficha ({p0 / n_viv:.2f}): revise habitantes o viviendas.")
    tasa = _num(f3.get("tasa_crecimiento"))
    if tasa is None:
        tasa = p["tasa_crecimiento"]
        fuente_tasa = PARAMETROS["tasa_crecimiento"]["ref"]
    else:
        fuente_tasa = "Ficha 3 (dato del proyecto)"
    if "tasa_crecimiento" in p.get("_usuario", {}):
        tasa, fuente_tasa = p["tasa_crecimiento"], "Ajustado por el usuario"
    n = int(_num(f3.get("periodo_diseno")) or p["periodo_diseno"])
    pf = p0 * (1 + tasa / 100) ** n
    nvf = math.ceil(pf / ppv)

    m.add(B, "Población actual (P₀)", round(p0), "hab", origen)
    m.add(B, "Viviendas actuales", int(n_viv) if n_viv else "", "viv", "Ficha 3 / Ficha 1")
    m.add(B, "Personas por vivienda", _r(ppv), "hab/viv", "P₀ / viviendas" if n_viv else "Promedio de las encuestas de vivienda")
    if ppv_enc:
        m.add(B, "Personas por vivienda según encuesta (control)", _r(ppv_enc), "hab/viv", "Promedio de las encuestas de vivienda")
    m.add(B, "Tasa de crecimiento (r)", tasa, "% anual", fuente_tasa)
    m.add(B, "Periodo de diseño (n)", n, "años", PARAMETROS["periodo_diseno"]["ref"])
    m.add(B, "Población futura (Pf)", round(pf), "hab", f"Pf = P₀·(1 + r)ⁿ = {p0:.0f}·(1 + {tasa / 100:g})^{n}")
    m.add(B, "Viviendas futuras", nvf, "viv", "Pf / personas por vivienda (redondeo hacia arriba)")
    return {"p0": p0, "pf": pf, "ppv": ppv, "n_viv": n_viv, "viviendas_futuras": nvf, "n": n, "tasa": tasa}


# ---------------------------------------------------------------------------
# 2. Esquema y demanda
# ---------------------------------------------------------------------------
def esquema(f1, f3, pob, p, m):
    B = "2. Esquema de prestación"
    dist = f3.get("distribucion_espacial") or ""
    asent = f1.get("tipo_asentamiento") or ""
    n_viv = pob["n_viv"] or pob["viviendas_futuras"]
    if "Centro poblado" in asent and n_viv > p["umbral_viviendas_acueducto"]:
        agua, motivo = "Acueducto", f"Núcleo de más de {p['umbral_viviendas_acueducto']:.0f} viviendas (Res. 0844 Art. 25.b)"
    elif dist.startswith("Dispersa"):
        agua, motivo = "Soluciones individuales", "Viviendas dispersas (Res. 0844 Art. 24.3 y Art. 38)"
    elif dist:
        agua, motivo = "Solución alternativa colectiva (abasto)", "Viviendas concentradas o semi-dispersas (Res. 0844 Art. 24.2 y Art. 32)"
    else:
        agua, motivo = "Solución alternativa colectiva (abasto)", "Sin dato de distribución espacial: se asume colectiva"
        m.alerta("Falta la distribución espacial de las viviendas (Ficha 3): el esquema se asumió colectivo.")
    saneamiento = ("Alcantarillado o soluciones individuales (comparar)" if dist.startswith("Concentrada")
                   else "Soluciones individuales de saneamiento")
    m.add(B, "Esquema de agua", agua, "", motivo)
    m.add(B, "Esquema de saneamiento", saneamiento, "", "Según dispersión de viviendas, geografía y topografía (Res. 0844 Art. 38)")
    return {"agua": agua, "saneamiento": saneamiento, "distribucion": dist}


def dotacion_norma(altitud, p):
    if altitud is None:
        return p["dotacion_menor_1000"], "Sin altitud: se toma el máximo de la Tabla 1 (verificar)"
    if altitud > 2000:
        return p["dotacion_mayor_2000"], PARAMETROS["dotacion_mayor_2000"]["ref"]
    if altitud >= 1000:
        return p["dotacion_1000_2000"], PARAMETROS["dotacion_1000_2000"]["ref"]
    return p["dotacion_menor_1000"], PARAMETROS["dotacion_menor_1000"]["ref"]


def demanda(f1, viviendas, pob, esq, p, m, f3=None):
    B = "3. Demanda de agua"
    alt = _num(f1.get("altitud_msnm"))
    d, ref = dotacion_norma(alt, p)
    d_f3 = _num((f3 or {}).get("dotacion_neta_adoptada"))
    if p.get("dotacion_neta"):
        d, ref = p["dotacion_neta"], "Dotación fijada en el panel de ajustes"
    elif d_f3 is not None:
        d, ref = d_f3, "Dotación adoptada en la Ficha 3 (justificación del proyecto)"
    elif esq["agua"] != "Acueducto":
        d = min(max(d, p["dotacion_min_abasto"]), p["dotacion_max_abasto"])
        ref += f"; dentro del rango {p['dotacion_min_abasto']:g}–{p['dotacion_max_abasto']:g} L/hab·día (Res. 0844 Art. 32.1)"
    m.add(B, "Altitud de la comunidad", alt if alt is not None else "", "m s.n.m.", "Ficha 1")
    m.add(B, "Dotación neta de diseño (d)", d, "L/hab·día", ref)

    viv = [v for v in viviendas if v.get("tipo_predio") == "Vivienda"]
    con_cons = [v for v in viv if _num(v.get("consumo_l_dia")) is not None and _num(v.get("habitantes"))]
    if con_cons:
        pc = sum(_num(v["consumo_l_dia"]) for v in con_cons) / sum(_num(v["habitantes"]) for v in con_cons)
        m.add(B, "Consumo actual medido (referencia)", round(pc, 1), "L/hab·día", "Σ consumo / Σ habitantes de las encuestas")
        if pc < d * 0.5:
            m.alerta(f"El consumo actual ({pc:.0f} L/hab·día) es menos de la mitad de la dotación de diseño: hay déficit de abastecimiento.")
    else:
        pc = None

    # Agua para la subsistencia de la familia rural (QE)
    claves = (("bovinos", "consumo_bovino"), ("equinos", "consumo_equino"), ("porcinos", "consumo_porcino"),
              ("aves", "consumo_ave"), ("huerta_m2", "riego_huerta"))
    if viv:
        litros_viv = [sum((_num(v.get(c)) or 0) * p[k] for c, k in claves) for v in viv]
        qe_viv = sum(litros_viv) / len(viv)
    else:
        qe_viv = 0.0
    qe_total = qe_viv * pob["viviendas_futuras"]
    m.add(B, "Agua para subsistencia por vivienda", round(qe_viv, 1), "L/viv·día",
          "Promedio encuestas: Σ animales × consumo + huerta × riego (Res. 0844 Art. 3 y 31.1; consumos de referencia)")
    m.add(B, "Agua para subsistencia total (QE)", round(qe_total), "L/día", "QE por vivienda × viviendas futuras")

    perd = p["perdidas"] / 100
    # Res. 0330/2017 Art. 47, parágrafo 2: k1 y k2 se calculan con registros de macromedición; sin ellos se justifican,
    # y no pueden superar 1,3 y 1,6 (Pf ≤ 12.500 hab) ni 1,2 y 1,5 (Pf > 12.500 hab).
    max_k1, max_k2 = (1.3, 1.6) if pob["pf"] <= 12500 else (1.2, 1.5)
    for k, tope in (("k1", max_k1), ("k2", max_k2)):
        if p[k] > tope:
            if p.get("_origen_" + k) or k in p.get("_usuario", {}):
                m.alerta(f"{k} = {p[k]:g} supera el máximo de {tope:g} del Art. 47 de la Res. 0330/2017 para una población futura de {pob['pf']:.0f} hab.")
            else:
                p[k] = tope
                p["_origen_" + k] = f"Máximo del Art. 47 de la Res. 0330/2017 para Pf > 12.500 hab"
    q_dom = d * pob["pf"]
    qmd = (q_dom + qe_total) / (1 - perd) / 86400
    if p.get("picos_en_subsistencia") or p.get("version_reglas") == "v1":
        QMD = p["k1"] * qmd
        QMH = p["k2"] * QMD
        txt_qmd, txt_qmh = "QMD = k1 · Qmd", "QMH = k2 · QMD"
    else:
        QMD = (p["k1"] * q_dom + qe_total) / (1 - perd) / 86400
        QMH = (p["k2"] * p["k1"] * q_dom + qe_total) / (1 - perd) / 86400
        txt_qmd = "QMD = (k1·d·Pf + QE) / (1 − %p) / 86 400 (picos solo en el consumo doméstico)"
        txt_qmh = "QMH = (k2·k1·d·Pf + QE) / (1 − %p) / 86 400"
    m.add(B, "Demanda doméstica", round(q_dom), "L/día", f"d × Pf = {d:g} × {pob['pf']:.0f}")
    m.add(B, "Pérdidas técnicas (%p)", p["perdidas"], "%", p.get("_origen_perdidas") or PARAMETROS["perdidas"]["ref"])
    m.add(B, "Dotación bruta", round(d / (1 - perd), 1), "L/hab·día", "d / (1 − %p)")
    m.add(B, "Caudal medio diario (Qmd)", round(qmd, 5) if qmd < 0.1 else round(qmd, 3), "L/s", "Qmd = (d·Pf + QE) / (1 − %p) / 86 400 = caudal de diseño del abasto (Res. 0844 Art. 32.2.a)")
    if qe_total:
        m.add(B, "Participación del agua de subsistencia", round(100 * qe_total / q_dom, 1), "% del consumo doméstico", "QE / (d·Pf)")
    m.add(B, "Coeficiente k1", p["k1"], "-", p.get("_origen_k1") or PARAMETROS["k1"]["ref"])
    m.add(B, "Caudal máximo diario (QMD)", round(QMD, 5) if QMD < 0.1 else round(QMD, 3), "L/s", txt_qmd + "  → caudal de diseño de captación y conducción")
    m.add(B, "Coeficiente k2", p["k2"], "-", p.get("_origen_k2") or PARAMETROS["k2"]["ref"])
    m.add(B, "Caudal máximo horario (QMH)", round(QMH, 5) if QMH < 0.1 else round(QMH, 3), "L/s", txt_qmh + "  → caudal de diseño de la red de distribución")
    m.add(B, "Volumen de almacenamiento orientativo", round(qmd * 86400 / 3 / 1000, 1), "m³",
          "1/3 del consumo medio diario (criterio de prediseño; ajustar con curva de consumo)")
    return {"d": d, "pc_actual": pc, "qe_total": qe_total, "qmd": qmd, "QMD": QMD, "QMH": QMH,
            "q_viv_ls": (d * pob["ppv"] + qe_viv) / (1 - perd) / 86400}


# ---------------------------------------------------------------------------
# 3. Fuentes: oferta y calidad
# ---------------------------------------------------------------------------
def nivel_tratamiento(f, p):
    """Devuelve (código, descripción, costo relativo 0-3, complejidad 0-3)."""
    turb, color = _num(f.get("turbiedad_ntu")), _num(f.get("color_upc"))
    ecoli, colit = _num(f.get("e_coli")), _num(f.get("coliformes_totales"))
    hierro, ph = _num(f.get("hierro_mgl")), _num(f.get("ph"))
    if all(x is None for x in (turb, color, ecoli, colit)):
        return "SIN_DATOS", "Sin análisis de calidad: se asume FiME + desinfección hasta tener laboratorio", 1.5, 1.5
    extras, especial = [], 0.0
    v1 = p.get("version_reglas") == "v1"
    if hierro is not None and hierro > 0.3:
        extras.append("aireación para hierro")
    mn = None if v1 else _num(f.get("manganeso_mgl"))
    if mn is not None and mn > 0.1:
        extras.append("oxidación y filtración para manganeso")
        especial = max(especial, 1.0)
    dureza = None if v1 else _num(f.get("dureza_mgl"))
    if dureza is not None and dureza > 300:
        extras.append("ablandamiento (dureza)")
        especial = max(especial, 1.0)
    cond = None if v1 else _num(f.get("conductividad"))
    if cond is not None and cond > 1000:
        extras.append("remoción de sales disueltas (ósmosis inversa o fuente alterna)")
        especial = max(especial, 2.5)
    if ph is not None and not (6.5 <= ph <= 9.0):
        extras.append("ajuste de pH")
    turb = turb or 0
    if turb <= 2 and (color or 0) <= 15:
        cod, txt, costo, comp = "DESINF", "Desinfección (cloración)", 0.0, 0.0
    elif turb <= p["turbiedad_filtro_lento"]:
        cod, txt, costo, comp = "FLA", "Filtración lenta en arena + desinfección", 1.0, 1.0
    elif turb <= p["turbiedad_fime"]:
        cod, txt, costo, comp = "FIME", "FiME: filtración gruesa dinámica + gruesa ascendente + filtración lenta + desinfección", 1.5, 1.5
    else:
        cod, txt, costo, comp = "CONV", "Tratamiento convencional o compacto (coagulación–floculación–sedimentación–filtración) + desinfección", 3.0, 3.0
    if extras:
        txt += " + " + " + ".join(extras)
        costo, comp = costo + 0.5 + especial, comp + 0.5 + especial
    if especial >= 2.5:
        cod = "ESPECIAL"
    return cod, txt, costo, comp


TIPO_CONEXION = "Conexión a acueducto o prestador existente"
SUPERFICIALES = {"Quebrada", "Río", "Lago / laguna / embalse"}

TRAT_CORTO = {
    "DESINF": "desinfección",
    "FLA": "filtración lenta + desinfección",
    "FIME": "FiME + desinfección",
    "CONV": "tratamiento convencional",
    "SIN_DATOS": "tratamiento por definir (falta análisis de calidad)",
    "ESPECIAL": "tratamiento especial (sales disueltas)",
}


def caudal_disponible(f):
    qe = _num(f.get("caudal_estiaje_ls"))
    if qe is not None:
        return qe, "estiaje"
    qa = _num(f.get("caudal_aforado_ls"))
    if qa is None:
        return None, ""
    return qa, "aforado en " + (f.get("epoca_aforo") or "época sin dato").lower()


def analizar_fuentes(f1, fuentes, dem, p, m):
    B = "4. Oferta de las fuentes"
    alt = _num(f1.get("altitud_msnm"))
    filas = []
    for f in fuentes:
        if f.get("tipo_fuente") == "Agua lluvia":
            continue
        q, base = caudal_disponible(f)
        cota = _num(f.get("cota_fuente_msnm"))
        if cota is not None and alt is not None:
            desnivel = cota - alt
            modo = "Gravedad" if desnivel >= p["margen_gravedad"] else "Bombeo"
        else:
            desnivel, modo = None, "Por verificar"
        cod, trat, costo_t, comp_t = nivel_tratamiento(f, p)
        if p.get("version_reglas") != "v1" and cod not in ("SIN_DATOS",):
            nombre = f.get("nombre_fuente")
            n_m = _num(f.get("numero_muestras"))
            multi = f.get("caracterizacion_multiestacional") is True
            if not multi and (n_m is None or n_m <= 1):
                m.alerta(f"La calidad de «{nombre}» se basa en una sola muestra o no se indicó el número de muestras: tomar muestras en época seca y en época de lluvias (Res. 0844 art. 13.3).")
            if f.get("tipo_fuente") in SUPERFICIALES and not multi and cod == "DESINF":
                cod, costo_t, comp_t = "FLA", costo_t + 1.0, comp_t + 1.0
                trat = trat.replace("Desinfección (cloración)", "Filtración lenta en arena + desinfección") + \
                    " (mínimo exigido a fuentes superficiales sin caracterización en época seca y de lluvias)"
        indice = q / dem["QMD"] if q is not None and dem["QMD"] else None
        if indice is None:
            suf = "Sin aforo"
        elif indice >= 1:
            suf = "Suficiente"
        else:
            suf = f"Insuficiente (cubre {indice * 100:.0f} %)"
        if base.startswith("aforado en") and "seca" not in base:
            m.alerta(f"La fuente «{f.get('nombre_fuente')}» se aforó fuera de época seca y no tiene caudal de estiaje: la oferta puede estar sobreestimada.")
        if f.get("concesion_aguas") is False:
            m.alerta(f"La fuente «{f.get('nombre_fuente')}» no tiene concesión de aguas: debe tramitarse ante la autoridad ambiental.")
        if f.get("continuidad") == "Estacional (se seca)":
            suf = "No apta como fuente principal (se seca)"
        filas.append({
            "Fuente": f.get("nombre_fuente"), "Tipo": f.get("tipo_fuente"), "Caudal disponible (L/s)": _r(q, 3),
            "Base del caudal": base, "QMD requerido (L/s)": _r(dem["QMD"], 3), "Índice oferta/demanda": _r(indice),
            "Suficiencia": suf, "Uso de la fuente (%)": _r(100 / indice, 1) if indice else None,
            "Desnivel fuente–comunidad (m)": _r(desnivel, 1), "Conducción": modo, "Distancia (km)": _num(f.get("distancia_comunidad_km")),
            "Continuidad": f.get("continuidad"), "Tratamiento requerido": trat, "_cod": cod, "_costo_t": costo_t, "_comp_t": comp_t,
            "_q": q, "_indice": indice, "_f": f,
        })
        m.add(B, f"{f.get('nombre_fuente')}: índice oferta/demanda", _r(indice) if indice is not None else "sin aforo", "-",
              f"Q disponible ({base}) / QMD = {q if q is not None else '–'} / {dem['QMD']:.3f}")
    if not filas:
        m.alerta("No hay fuentes superficiales o subterráneas con datos: no se puede evaluar la oferta.")
    return filas


def agua_lluvia(f1, fuentes, viviendas, dem, pob, p, m):
    B = "5. Agua lluvia"
    precs = [_num(f.get("precipitacion_mm_anual")) for f in fuentes if _num(f.get("precipitacion_mm_anual"))]
    if not precs:
        return None
    P = max(precs)
    oferta_m2 = P * p["coef_escorrentia_techo"] / 365
    demanda_viv = dem["d"] * pob["ppv"]
    area = demanda_viv / oferta_m2
    cobertura = min(1.0, p["area_techo_tipica"] * oferta_m2 / demanda_viv)
    m.add(B, "Precipitación media anual", P, "mm/año", "Registro de fuentes (dato IDEAM recomendado)")
    m.add(B, "Oferta por m² de cubierta", round(oferta_m2, 2), "L/m²·día", "P × Ce / 365")
    m.add(B, "Área de cubierta para cubrir la dotación", round(area, 1), "m²/viv", "d × hab/viv ÷ oferta por m²")
    m.add(B, "Cobertura con techo típico", round(cobertura * 100), "%", f"Techo de {p['area_techo_tipica']:g} m² (Res. 0844 Art. 31.2 y 34)")
    return {"P": P, "area": area, "cobertura": cobertura}


# ---------------------------------------------------------------------------
# 4. Indicadores sociales y de gestión usados por la matriz
# ---------------------------------------------------------------------------
def contexto(f1, f3, viviendas):
    viv = [v for v in viviendas if v.get("tipo_predio") == "Vivienda"]
    montos = [_num(v.get("monto_dispuesto")) for v in viv if v.get("voluntad_pago") and _num(v.get("monto_dispuesto"))]
    hab = lambda v: v.get("tratamiento_casa") or []
    san = lambda v: v.get("tipo_saneamiento") or ""
    return {
        "voluntad": _pct(viv, lambda v: v.get("voluntad_pago") is True) or 50,
        "participa": _pct(viv, lambda v: v.get("participa_om") is True) or 50,
        "mano_obra_aporte": _pct(viv, lambda v: v.get("aporte_mano_obra") is True) or 50,
        "monto_mediana": median(montos) if montos else None,
        "habitos": {h: _pct(viv, lambda v, h=h: h in hab(v)) or 0 for h in ("Hierve", "Cloro", "Filtro casero", "Desinfección solar", "No la trata")},
        "pct_inodoro": _pct(viv, lambda v: san(v).startswith("Inodoro")) or 0,
        "pct_seco": _pct(viv, lambda v: san(v) in ("Letrina", "Unidad sanitaria seca")) or 0,
        "discapacidad": any((_num(v.get("personas_discapacidad")) or 0) > 0 for v in viv),
        "espacio_mediana": median([_num(v["espacio_disponible_m2"]) for v in viv if _num(v.get("espacio_disponible_m2")) is not None] or [0]) or None,
        "hab_p90": _p90([_num(v.get("habitantes")) for v in viv if _num(v.get("habitantes"))]),
        "capacidad": {"Alta": 5.0, "Media": 4.0, "Baja": 2.5}.get(f3.get("capacidad_gestion"), 3.5),
        "repuestos": {"Alta (en la vereda)": 0.0, "Media (en la cabecera municipal)": -0.3, "Baja (fuera del municipio)": -1.0}.get(f3.get("acceso_repuestos"), -0.3),
        "mano_obra_local": f3.get("mano_obra_local") is not False,
        "energia": f3.get("energia_electrica") or "",
        "organizacion": bool(set(f3.get("organizacion") or []) - {"Ninguna"}),
        "amenazas": set(f1.get("amenazas") or []),
        "inundable": f3.get("zona_inundable") is True,
        "pendiente": f3.get("pendiente_terreno") or "",
        "receptora_vulnerable": f3.get("receptora_alta_vulnerabilidad") is True,
    }


def _p90(xs):
    if not xs:
        return 5
    xs = sorted(xs)
    return xs[int(round(0.9 * (len(xs) - 1)))]


def _social_base(c):
    s = 3.0 + (c["voluntad"] - 50) / 25 + (c["participa"] - 50) / 50 + (0.5 if c["organizacion"] else -0.5)
    return s


# ---------------------------------------------------------------------------
# 5. Alternativas de abastecimiento
# ---------------------------------------------------------------------------
def alternativas_agua(filas_fuentes, lluvia, esq, dem, c, m):
    alts = []
    sup = {"Quebrada", "Río", "Lago / laguna / embalse"}
    for fx in filas_fuentes:
        f, q, ind = fx["_f"], fx["_q"], fx["_indice"]
        prefijo = "Acueducto" if esq["agua"] == "Acueducto" else "Abasto"
        conduccion = "conducción por verificar" if fx["Conducción"] == "Por verificar" else f"por {fx['Conducción'].lower()}"
        conexion = fx["Tipo"] == TIPO_CONEXION
        nombre = (f"Conexión al prestador existente «{fx['Fuente']}» {conduccion} + {TRAT_CORTO[fx['_cod']]} de refuerzo" if conexion
                  else f"{prefijo} desde {fx['Fuente']} {conduccion} + {TRAT_CORTO[fx['_cod']]}")
        a = Alternativa(nombre, "Abastecimiento")
        a.prediseno = {"Fuente": fx["Fuente"], "Caudal de diseño QMD (L/s)": _r(dem["QMD"], 3), "Caudal disponible (L/s)": fx["Caudal disponible (L/s)"],
                       "Conducción": fx["Conducción"], "Tratamiento": fx["Tratamiento requerido"], "Distancia (km)": fx["Distancia (km)"]}
        if q is None:
            a.viable, a.motivo = False, "Fuente sin aforo"
        elif fx["Continuidad"] == "Estacional (se seca)":
            a.viable, a.motivo = False, "La fuente se seca en algún periodo del año"
        elif ind < 1:
            a.viable, a.motivo = False, f"Caudal insuficiente: cubre {ind * 100:.0f} % del QMD"
        elif fx["Conducción"] == "Bombeo" and c["energia"] == "Sin energía":
            a.viable, a.motivo = False, "Requiere bombeo y no hay energía (evaluar bombeo solar)"
        if esq["agua"] == "Soluciones individuales":
            a.motivo = (a.motivo + "; " if a.motivo else "") + "Viviendas dispersas: la red colectiva tiene alto costo por vivienda"
        if fx["_cod"] == "ESPECIAL":
            m.alerta(f"La fuente «{fx['Fuente']}» tiene sales disueltas altas (conductividad > 1000 µS/cm): requiere tratamiento costoso; preferir otra fuente.")
        dist = fx["Distancia (km)"] or 1.0
        bombeo = fx["Conducción"] == "Bombeo"

        ef = 5 if ind and ind >= 2 else 4 if ind and ind >= 1.3 else 3
        ef -= 1 if fx["Continuidad"] == "Intermitente" else 0
        ef -= 0.5 if fx["_cod"] == "SIN_DATOS" else 0
        cos = 5 - fx["_costo_t"] - (1.5 if bombeo else 0) - (1 if dist > 3 else 0.5 if dist > 1 else 0) - (0.5 if c["voluntad"] < 50 else 0)
        cos -= 1.5 if esq["agua"] == "Soluciones individuales" else 0
        cos -= 0.75 if fx["Conducción"] == "Por verificar" else 0  # sin topografía, se asume posible bombeo
        aom = c["capacidad"] + c["repuestos"] - 0.5 * fx["_comp_t"] - (0 if c["mano_obra_local"] else 1)
        if bombeo:
            aom -= {"Red eléctrica continua": 0.5, "Red eléctrica intermitente": 1.5}.get(c["energia"], 1.0)
        uso = 1 / ind if ind else 1
        amb = (5 if uso <= 0.3 else 4 if uso <= 0.5 else 3 if uso <= 0.8 else 2)
        afect = [x for x in (f.get("actividades_afectan") or []) if x != "Ninguna identificada"]
        amb -= min(1.5, 0.5 * len(afect))
        rie = 5.0
        if "Sequía / desabastecimiento" in c["amenazas"]:
            rie -= 1.5 if fx["Tipo"] in sup else 1.0
        if "Remoción en masa / deslizamiento" in c["amenazas"] and dist > 1:
            rie -= 1.0
        if {"Inundación", "Avenida torrencial"} & c["amenazas"] and fx["Tipo"] in sup:
            rie -= 1.0
        a.puntajes = {"Eficiencia técnica": ef, "Costo y capacidad de pago": cos, "Operación y mantenimiento": aom,
                      "Aceptabilidad social": _social_base(c), "Sostenibilidad ambiental": amb, "Gestión del riesgo": rie}
        a.justificacion = {
            "Eficiencia técnica": f"Índice oferta/demanda {fx['Índice oferta/demanda']}; continuidad {fx['Continuidad']}",
            "Costo y capacidad de pago": f"{fx['Conducción']}, {dist:g} km, tratamiento: {fx['_cod']}; voluntad de pago {c['voluntad']:.0f} %",
            "Operación y mantenimiento": f"Capacidad de gestión, repuestos, energía ({c['energia'] or 'sin dato'})",
            "Aceptabilidad social": f"Voluntad de pago {c['voluntad']:.0f} %, participación en O&M {c['participa']:.0f} %",
            "Sostenibilidad ambiental": f"Uso del {uso * 100:.0f} % del caudal; presiones: {', '.join(afect) or 'ninguna'}",
            "Gestión del riesgo": ", ".join(sorted(c["amenazas"] - {"Ninguna identificada"})) or "Sin amenazas",
        }
        alts.append(a)

    # Combinación de fuentes si ninguna alcanza sola
    perm = [fx for fx in filas_fuentes if fx["_q"] and fx["Continuidad"] == "Permanente"]
    if perm and not any(fx["_indice"] and fx["_indice"] >= 1 for fx in perm):
        qsum = sum(fx["_q"] for fx in perm)
        a = Alternativa("Abasto combinando fuentes: " + " + ".join(fx["Fuente"] for fx in perm), "Abastecimiento")
        if qsum < dem["QMD"]:
            a.viable, a.motivo = False, f"Aun sumando las fuentes se cubre solo el {100 * qsum / dem['QMD']:.0f} % del QMD"
        a.puntajes = {"Eficiencia técnica": 3, "Costo y capacidad de pago": 2.5, "Operación y mantenimiento": c["capacidad"] - 1,
                      "Aceptabilidad social": _social_base(c), "Sostenibilidad ambiental": 2.5, "Gestión del riesgo": 3.5}
        a.prediseno = {"Caudal combinado (L/s)": round(qsum, 3), "QMD (L/s)": round(dem["QMD"], 3)}
        alts.append(a)

    if lluvia:
        cob = lluvia["cobertura"]
        a = Alternativa("Captación de agua lluvia en cada vivienda + tratamiento en punto de uso", "Abastecimiento")
        a.motivo = "" if cob >= 0.9 else f"Cubre ≈ {cob * 100:.0f} % de la dotación: usar como complemento (Res. 0844 Art. 31.2)"
        a.puntajes = {"Eficiencia técnica": 1 + 4 * cob, "Costo y capacidad de pago": 4, "Operación y mantenimiento": 4,
                      "Aceptabilidad social": _social_base(c) - 0.5, "Sostenibilidad ambiental": 5,
                      "Gestión del riesgo": 2.5 if "Sequía / desabastecimiento" in c["amenazas"] else 4}
        a.prediseno = {"Área de cubierta requerida (m²/viv)": round(lluvia["area"], 1), "Cobertura con techo típico (%)": round(cob * 100)}
        alts.append(a)
    return alts


# ---------------------------------------------------------------------------
# 6. Tratamiento en el punto de uso (Res. 0844 Art. 36: mínimo 3 opciones)
# ---------------------------------------------------------------------------
def alternativas_punto_uso(filas_fuentes, c, p):
    turbs = [_num(fx["_f"].get("turbiedad_ntu")) for fx in filas_fuentes if _num(fx["_f"].get("turbiedad_ntu")) is not None]
    turb = min(turbs) if turbs else None
    alts = []
    for nombre, b in PUNTO_USO_BASE.items():
        a = Alternativa(nombre, "Tratamiento en la vivienda")
        ef, acc, aom, cos = b["ef"], b["acc"], b["aom"], b["cos"]
        if turb is not None and turb > p["turbiedad_filtro_lento"]:
            if "Cloración" in nombre:
                ef -= 1.5
            if "cerámico" in nombre or "membrana" in nombre:
                aom -= 0.5
        if "SODIS" in nombre and turb is not None and turb > p["turbiedad_sodis"]:
            a.viable, a.motivo = False, f"Turbiedad {turb:g} UNT > {p['turbiedad_sodis']:g} UNT"
        acc += c["repuestos"] if "membrana" in nombre or "cerámico" in nombre else 0
        soc = 3.0 + c["habitos"].get(b["habito"], 0) / 25 - (0.5 if "SODIS" in nombre else 0)
        a.puntajes = {"Eficiencia frente a las necesidades de tratamiento": ef, "Acceso a bienes y servicios": acc,
                      "Aceptabilidad social": soc, "Administración, operación y mantenimiento": aom,
                      "Costos de la tecnología y consumibles": cos}
        a.justificacion = {"Aceptabilidad social": f"{c['habitos'].get(b['habito'], 0):.0f} % de hogares ya usa «{b['habito']}»",
                           "Eficiencia frente a las necesidades de tratamiento": f"Turbiedad de referencia: {turb if turb is not None else 'sin dato'} UNT"}
        alts.append(a)
    return alts


# ---------------------------------------------------------------------------
# 7. Saneamiento
# ---------------------------------------------------------------------------
def temperatura_estimada(alt):
    return 28 - 0.006 * (alt or 0)


def prediseno_tanque(N, C, alt, p):
    """Volumen útil del tanque séptico (NBR 7229): V = 1000 + N(C·T + K·Lf)."""
    contrib = N * C
    T = 1.0 if contrib <= 1500 else 0.92 if contrib <= 3000 else 0.83
    t = temperatura_estimada(alt)
    K = 94 if t <= 10 else 65 if t <= 20 else 57
    V = 1000 + N * (C * T + K * p["lodo_fresco"])
    return V, T, K, t


def saneamiento(f1, f3, dem, c, p, m):
    B = "6. Saneamiento"
    alt = _num(f1.get("altitud_msnm"))
    perc, nf = _num(f3.get("tasa_percolacion")), _num(f3.get("nivel_freatico_m"))
    suelo = f3.get("tipo_suelo") or ""
    N = max(int(math.ceil(c["hab_p90"] or 5)), 4)
    C = dem["d"] * p["coef_retorno"]
    V, T, K, t = prediseno_tanque(N, C, alt, p)
    m.add(B, "Personas de diseño por vivienda (N)", N, "hab", "Percentil 90 de habitantes por vivienda (mín. 4)")
    m.add(B, "Aporte de aguas residuales (C)", round(C, 1), "L/hab·día", f"d × coef. de retorno = {dem['d']:g} × {p['coef_retorno']:g}")
    m.add(B, "Temperatura media estimada", round(t, 1), "°C", "28 − 0,006 × altitud (aprox. para Colombia; verificar con IDEAM)")
    m.add(B, "Volumen útil tanque séptico", round(V / 1000, 2), "m³", f"NBR 7229: V = 1000 + N(C·T + K·Lf); T = {T} d, K = {K}, Lf = {p['lodo_fresco']:g}")
    area_inf = None
    if perc:
        q_ap = 204 / math.sqrt(perc)
        area_inf = N * C / q_ap
        m.add(B, "Tasa de aplicación al suelo", round(q_ap, 1), "L/m²·día", f"q = 204 / √t (USPHS), t = {perc:g} min/pulg")
        m.add(B, "Área de infiltración requerida", round(area_inf, 1), "m²/viv", "N·C / q")
    else:
        m.alerta("Sin prueba de percolación no se puede dimensionar el campo de infiltración.")

    escarpado = c["pendiente"].startswith("Escarpada")
    espacio = c["espacio_mediana"]
    agua_escasa = (dem["pc_actual"] is not None and dem["pc_actual"] < p["agua_minima_arrastre"])
    alts = []

    # S1 Unidad sanitaria con arrastre hidráulico: tren del proyecto tipo DNP (basado en la Res. 0844/2018)
    a = Alternativa("Unidad sanitaria: trampa de grasas + tanque séptico + FAFA + campo de infiltración", "Saneamiento")
    motivos, condiciones = [], []
    if perc is None:
        condiciones.append("prueba de percolación")
    elif not (p["percolacion_min"] <= perc <= p["percolacion_max"]):
        motivos.append(f"percolación {perc:g} min/pulg fuera de {p['percolacion_min']:g}–{p['percolacion_max']:g}")
    if nf is None:
        condiciones.append("medición del nivel freático")
    elif nf < p["nf_min_infiltracion"]:
        motivos.append(f"nivel freático a {nf:g} m (< {p['nf_min_infiltracion']:g} m)")
    if c["inundable"]:
        motivos.append("zona inundable")
    if escarpado:
        motivos.append("pendiente > 25 %")
    if area_inf and espacio is not None and espacio < area_inf + 6:
        motivos.append(f"espacio disponible ({espacio:g} m²) menor al requerido (≈ {area_inf + 6:.0f} m²)")
    a.viable = not motivos
    a.motivo = "; ".join(motivos) if motivos else (
        "Condicionado a " + " y ".join(condiciones) + " (requisito del proyecto tipo DNP)" if condiciones else "")
    ef = 5 if perc and 5 <= perc <= p["percolacion_max"] else 4.5
    ef -= 0.5 if condiciones else 0
    a.puntajes = {"Eficiencia técnica": ef - (1 if agua_escasa else 0), "Costo y capacidad de pago": 2.75,
                  "Operación y mantenimiento": 3.75 + c["repuestos"], "Aceptabilidad social": 3 + c["pct_inodoro"] / 50,
                  "Sostenibilidad ambiental": 4.5 if (nf or 0) >= p["nf_min_infiltracion"] + 1 else 4,
                  "Gestión del riesgo": 4 - (1 if "Remoción en masa / deslizamiento" in c["amenazas"] and c["pendiente"].startswith("Inclinada") else 0)}
    a.justificacion = {"Eficiencia técnica": "Tren de tratamiento del proyecto tipo DNP para vivienda rural dispersa",
                       "Costo y capacidad de pago": "Requiere caseta, tanque séptico, FAFA y campo de infiltración"}
    a.prediseno = {"Volumen útil tanque (m³)": round(V / 1000, 2),
                   "Área de infiltración (m²)": _r(area_inf, 1) if area_inf else "por dimensionar con la prueba de percolación",
                   "Personas de diseño": N}
    alts.append(a)

    # S2 Tanque séptico + FAFA con vertimiento (cuando el suelo no permite infiltrar)
    a = Alternativa("Tanque séptico + FAFA + vertimiento a fuente con permiso", "Saneamiento")
    a.viable = not c["inundable"]
    a.motivo = "zona inundable" if c["inundable"] else "Requiere permiso de vertimiento ante la autoridad ambiental"
    a.puntajes = {"Eficiencia técnica": 5 - (1 if agua_escasa else 0), "Costo y capacidad de pago": 2.75,
                  "Operación y mantenimiento": 3.75 + c["repuestos"] - 0.5, "Aceptabilidad social": 3 + c["pct_inodoro"] / 50,
                  "Sostenibilidad ambiental": 1.5 if c["receptora_vulnerable"] else 2.5, "Gestión del riesgo": 3.5}
    a.justificacion = {"Sostenibilidad ambiental": "Descarga a un cuerpo de agua" + (" de alta vulnerabilidad" if c["receptora_vulnerable"] else "")}
    a.prediseno = {"Volumen útil tanque (m³)": round(V / 1000, 2), "Disposición": "Vertimiento con permiso"}
    alts.append(a)

    if p.get("version_reglas") == "v1":
        alts = saneamiento_v1(perc, nf, c, p, V, area_inf, espacio, escarpado, agua_escasa, N)

    # S3 Unidad sanitaria seca
    a = Alternativa("Unidad sanitaria seca con separación de orina + manejo de aguas grises", "Saneamiento")
    a.motivo = "En zona inundable debe construirse elevada" if c["inundable"] else ""
    a.puntajes = {"Eficiencia técnica": 4 + (1 if agua_escasa else 0), "Costo y capacidad de pago": 4,
                  "Operación y mantenimiento": 3 + (0.5 if c["participa"] >= 60 else 0),
                  "Aceptabilidad social": 2.5 + c["pct_seco"] / 40 - c["pct_inodoro"] / 100,
                  "Sostenibilidad ambiental": 5, "Gestión del riesgo": 4.5 if not c["inundable"] else 4}
    a.prediseno = {"Requiere": "Capacitación en uso y manejo de excretas; trampa de grasas y zanja para aguas grises"}
    alts.append(a)

    # S4 Letrina de hoyo seco ventilado
    a = Alternativa("Letrina de hoyo seco ventilado (VIP)", "Saneamiento")
    motivos = []
    if nf is not None and nf < p["nf_min_letrina"]:
        motivos.append(f"nivel freático a {nf:g} m (< {p['nf_min_letrina']:g} m)")
    if c["inundable"]:
        motivos.append("zona inundable")
    if suelo == "Rocoso":
        motivos.append("suelo rocoso")
    if perc is not None and perc < p["percolacion_min"]:
        motivos.append("suelo muy permeable: riesgo para el acuífero")
    a.viable, a.motivo = not motivos, "; ".join(motivos)
    a.puntajes = {"Eficiencia técnica": 2.5, "Costo y capacidad de pago": 5, "Operación y mantenimiento": 4,
                  "Aceptabilidad social": 2.5 + c["pct_seco"] / 50 - (0.5 if c["discapacidad"] else 0),
                  "Sostenibilidad ambiental": 2.5, "Gestión del riesgo": 3}
    alts.append(a)

    # S5 Colectivo
    a = Alternativa("Alcantarillado de pequeño diámetro + planta de tratamiento colectiva", "Saneamiento")
    if not c_distribucion_concentrada(f3):
        a.viable, a.motivo = False, "Viviendas no concentradas: alto costo por vivienda (Res. 0844 Art. 38)"
    a.puntajes = {"Eficiencia técnica": 5, "Costo y capacidad de pago": 1.5, "Operación y mantenimiento": c["capacidad"] - 1.5,
                  "Aceptabilidad social": 3 + c["pct_inodoro"] / 50, "Sostenibilidad ambiental": 2.5 if c["receptora_vulnerable"] else 3.5,
                  "Gestión del riesgo": 3}
    alts.append(a)
    # Asentamiento concentrado: muchas soluciones in situ juntas saturan el suelo,
    # y el alcantarillado gana economía de escala (Res. 0844 Art. 38).
    if c_distribucion_concentrada(f3):
        n_viv = c.get("n_viv") or 0
        for a in alts:
            if a.nombre.startswith(("Unidad sanitaria: trampa", "Letrina")):
                a.puntajes["Sostenibilidad ambiental"] -= 1
                a.puntajes["Gestión del riesgo"] -= 0.5
                a.justificacion["Sostenibilidad ambiental"] = "Densidad alta de infiltración en asentamiento concentrado"
            if a.nombre.startswith("Alcantarillado") and n_viv >= 100:
                a.puntajes["Costo y capacidad de pago"] += 1.5
                a.puntajes["Eficiencia técnica"] = 5
                a.justificacion["Costo y capacidad de pago"] = f"Economía de escala con {n_viv:.0f} viviendas concentradas"
            if a.nombre.startswith("Unidad sanitaria seca") and n_viv >= 100:
                a.puntajes["Operación y mantenimiento"] -= 1
                a.justificacion["Operación y mantenimiento"] = "Manejo de excretas de muchas viviendas en espacio reducido"
    return alts


def saneamiento_v1(perc, nf, c, p, V, area_inf, espacio, escarpado, agua_escasa, N):
    """Alternativas con tanque séptico de la primera versión (antes de la validación). Solo para comparar."""
    alts = []
    a = Alternativa("Tanque séptico + campo de infiltración", "Saneamiento")
    motivos = []
    if perc is None:
        motivos.append("falta prueba de percolación")
    elif not (p["percolacion_min"] <= perc <= p["percolacion_max"]):
        motivos.append(f"percolación {perc:g} min/pulg fuera de {p['percolacion_min']:g}–{p['percolacion_max']:g}")
    if nf is not None and nf < p["nf_min_infiltracion"]:
        motivos.append(f"nivel freático a {nf:g} m (< {p['nf_min_infiltracion']:g} m)")
    if c["inundable"]:
        motivos.append("zona inundable")
    if escarpado:
        motivos.append("pendiente > 25 %")
    if area_inf and espacio is not None and espacio < area_inf + 6:
        motivos.append("espacio insuficiente")
    a.viable, a.motivo = not motivos, "; ".join(motivos)
    ef = 5 if perc and 5 <= perc <= 30 else 4
    a.puntajes = {"Eficiencia técnica": ef - (1 if agua_escasa else 0), "Costo y capacidad de pago": 3,
                  "Operación y mantenimiento": 4 + c["repuestos"], "Aceptabilidad social": 3 + c["pct_inodoro"] / 50,
                  "Sostenibilidad ambiental": 4 if (nf or 0) >= p["nf_min_infiltracion"] + 1 else 3,
                  "Gestión del riesgo": 4 - (1 if "Remoción en masa / deslizamiento" in c["amenazas"] and c["pendiente"].startswith("Inclinada") else 0)}
    a.prediseno = {"Volumen útil tanque (m³)": round(V / 1000, 2), "Área de infiltración (m²)": _r(area_inf, 1), "Personas de diseño": N}
    alts.append(a)
    a = Alternativa("Tanque séptico + filtro anaerobio de flujo ascendente (FAFA) + infiltración o vertimiento", "Saneamiento")
    vertimiento = perc is None or perc > p["percolacion_max"] or (nf is not None and nf < p["nf_min_infiltracion"])
    a.viable = not c["inundable"]
    a.motivo = "zona inundable" if c["inundable"] else ("Requiere permiso de vertimiento ante la autoridad ambiental" if vertimiento else "")
    a.puntajes = {"Eficiencia técnica": 5 - (1 if agua_escasa else 0), "Costo y capacidad de pago": 2.5,
                  "Operación y mantenimiento": c["capacidad"] - 1 + c["repuestos"], "Aceptabilidad social": 3 + c["pct_inodoro"] / 50,
                  "Sostenibilidad ambiental": 2 if (vertimiento and c["receptora_vulnerable"]) else 3.5, "Gestión del riesgo": 3.5}
    a.prediseno = {"Volumen útil tanque (m³)": round(V / 1000, 2), "Disposición": "Vertimiento con permiso" if vertimiento else "Infiltración"}
    alts.append(a)
    return alts


def c_distribucion_concentrada(f3):
    return (f3.get("distribucion_espacial") or "").startswith("Concentrada")


# ---------------------------------------------------------------------------
# 8. Aseo
# ---------------------------------------------------------------------------
def aseo(f3, viviendas, pob, p, m):
    B = "7. Aseo"
    viv = [v for v in viviendas if v.get("tipo_predio") == "Vivienda"]
    g = pob["pf"] * p["ppc_residuos"]
    vol_sem = g * 7 / p["densidad_residuos"]
    m.add(B, "Producción de residuos (horizonte)", round(g, 1), "kg/día", f"Pf × PPC = {pob['pf']:.0f} × {p['ppc_residuos']:g} (reemplazar PPC por el del PGIRS)")
    m.add(B, "Volumen semanal a almacenar", round(vol_sem, 2), "m³/semana", f"Producción × 7 / densidad ({p['densidad_residuos']:g} kg/m³)")
    quema = _pct(viv, lambda v: bool({"La quema", "La entierra", "La bota a campo abierto / fuente"} & set(v.get("manejo_residuos") or [])))
    comp = _pct(viv, lambda v: bool({"Compostaje de orgánicos", "Alimento para animales"} & set(v.get("manejo_residuos") or [])))
    rec = []
    if quema is not None:
        m.add(B, "Viviendas con disposición inadecuada", round(quema), "%", "Quema, entierro o bota a campo abierto")
        if quema >= 30:
            rec.append(f"Implementar un sitio de almacenamiento colectivo rural de ≈ {vol_sem:.1f} m³ útiles por semana de recolección (Res. 0844 Art. 13.1.g)")
    if f3.get("frecuencia_recoleccion") in (None, "No hay recolección"):
        rec.append("Gestionar con el municipio la inclusión de la vereda en la ruta de recolección del PGIRS")
    if comp is not None and comp < 50:
        rec.append("Promover compostaje domiciliario de residuos orgánicos para reducir el volumen a recolectar")
    rec.append("Campañas de separación en la fuente y aprovechamiento de reciclables")
    return {"generacion": g, "volumen_semanal": vol_sem, "recomendaciones": rec}


# ---------------------------------------------------------------------------
# Orquestador
# ---------------------------------------------------------------------------
def calcular(proyecto, fuentes, viviendas, ajustes=None):
    """
    Ejecuta todo el procesamiento.
    ajustes: dict opcional {parametro: valor} y/o {'pesos': {...}}.
    """
    ajustes = dict(ajustes or {})
    pesos = {**PESOS_COLECTIVO, **ajustes.pop("pesos", {})}
    s = sum(pesos.values()) or 1
    pesos = {k: v / s for k, v in pesos.items()}
    p = valores(ajustes)
    p["_usuario"] = ajustes
    f1, f3 = proyecto["ficha1"], proyecto["ficha3"]
    m = Memoria()
    # Valores adoptados en la Ficha 3 (si el usuario no los cambió en el panel de ajustes)
    for campo, param in (("perdidas_adoptadas", "perdidas"), ("k1_adoptado", "k1"), ("k2_adoptado", "k2")):
        v = _num(f3.get(campo))
        if v is not None and param not in ajustes:
            p[param] = v
            p["_origen_" + param] = "Valor adoptado en la Ficha 3"
    if p["perdidas"] > 25:
        m.alerta(f"Pérdidas de {p['perdidas']:g} %: superan el máximo de 25 % de la Res. 330/2017 Art. 44.")
    if p.get("version_reglas") == "v1":
        # Umbrales de la primera versión (antes de la validación), solo para comparar
        p.update({"percolacion_max": 60, "nf_min_infiltracion": 2.0, "agua_minima_arrastre": 50})

    pob = poblacion(f1, f3, viviendas, p, m)
    if pob is None:
        return {"ok": False, "alertas": m.alertas, "memoria": m.filas}
    esq = esquema(f1, f3, pob, p, m)
    dem = demanda(f1, viviendas, pob, esq, p, m, f3)
    ffs = analizar_fuentes(f1, fuentes, dem, p, m)
    llu = agua_lluvia(f1, fuentes, viviendas, dem, pob, p, m)
    c = contexto(f1, f3, viviendas)
    c["n_viv"] = pob["n_viv"] or pob["viviendas_futuras"]

    componentes = f3.get("componentes") or ["Agua para consumo humano y doméstico", "Saneamiento / aguas residuales", "Aseo / residuos sólidos"]
    alt_agua = _ordenar(alternativas_agua(ffs, llu, esq, dem, c, m), pesos) if "Agua para consumo humano y doméstico" in componentes else []
    alt_pu = _ordenar(alternativas_punto_uso(ffs, c, p), PESOS_PUNTO_USO)
    alt_san = _ordenar(saneamiento(f1, f3, dem, c, p, m), pesos) if "Saneamiento / aguas residuales" in componentes else []
    res_aseo = aseo(f3, viviendas, pob, p, m)

    if alt_agua and not any(a.viable for a in alt_agua):
        m.alerta("Ninguna alternativa de abastecimiento es viable con las fuentes registradas: busque fuentes adicionales o complemente con agua lluvia.")

    from core.sensibilidad import estabilidad
    sens = {"agua": estabilidad(alt_agua, pesos), "saneamiento": estabilidad(alt_san, pesos),
            "punto_uso": estabilidad(alt_pu, PESOS_PUNTO_USO)}
    from core.matriz_ras import evaluar_fuentes, contraste
    mras = evaluar_fuentes(ffs) if alt_agua and len(ffs) else []
    cras = contraste(mras, alt_agua)
    ficha = ficha_proyecto(proyecto, pob, esq, dem, ffs, alt_agua, alt_pu, alt_san, res_aseo, m, sens, p, cras)
    return {"ok": True, "matriz_ras": mras, "contraste_matriz_ras": cras, "parametros": {k: v for k, v in p.items() if not k.startswith("_")}, "pesos": pesos, "sensibilidad": sens,
            "poblacion": pob, "esquema": esq, "demanda": dem, "fuentes": ffs, "lluvia": llu,
            "alternativas_agua": alt_agua, "alternativas_punto_uso": alt_pu, "alternativas_saneamiento": alt_san,
            "aseo": res_aseo, "memoria": m.filas, "alertas": m.alertas, "ficha": ficha}


def _texto_ras(c):
    if not c:
        return ""
    if c["empate"]:
        t = "La Matriz RAS del Ministerio deja empatadas (diferencia ≤ 4 de 100 puntos) a " + ", ".join(f"«{x}»" for x in c["empatadas"])
        t += "; la elección de la herramienta está entre ellas" if c["compatible"] else f"; la herramienta elige «{c['fuente_herramienta']}», que no está entre ellas"
    else:
        t = f"La Matriz RAS del Ministerio elige «{c['fuente_matriz_ras']}»"
        t += ": coincide con la herramienta" if c["coinciden"] else f"; la herramienta elige «{c['fuente_herramienta']}»"
    if c["cobertura_min"] < 100:
        t += f". Criterios con dato: {c['cobertura_min']} de 100 puntos; llene el «Entorno de la fuente» para completarla"
    return t


def _mejor(alts):
    return next((a for a in alts if a.viable), None)


def _empate(alts, margen=0.2, estabilidad=None, est_min=80):
    """Empate técnico: diferencia ≤ umbral (puntajes redondeados a 2 decimales) o 1.ª alternativa poco estable ante los pesos."""
    v = [a for a in alts if a.viable]
    if len(v) < 2:
        return ""
    dif = round(round(v[0].total, 2) - round(v[1].total, 2), 2)
    est = (estabilidad or {}).get("monte_carlo_primera")
    motivos = []
    if dif <= margen:
        motivos.append(f"diferencia de {dif:.2f} ≤ {margen:.2f}")
    if est is not None and est < est_min:
        motivos.append(f"la 1.ª alternativa se mantiene solo en el {est:.0f} % de las variaciones de pesos")
    if motivos:
        return f"Empate técnico con «{v[1].nombre}» ({v[1].total}): " + " y ".join(motivos) + ". Decidir con la comunidad (Res. 0844 Art. 16)"
    return ""


def ficha_proyecto(proyecto, pob, esq, dem, ffs, alt_agua, alt_pu, alt_san, res_aseo, m, sens=None, p=None, cras=None):
    sens, p = sens or {}, p or {}
    umbral, est_min = p.get("umbral_empate", 0.2), p.get("estabilidad_minima", 80)
    f1, f3 = proyecto["ficha1"], proyecto["ficha3"]
    ma, mp, ms = _mejor(alt_agua), _mejor(alt_pu), _mejor(alt_san)
    secciones = [
        ("Identificación", [
            ("Proyecto", f1.get("nombre_proyecto") or proyecto.get("nombre")),
            ("Localización", f"{f1.get('vereda', '')}, {f1.get('municipio', '')}, {f1.get('departamento', '')}"),
            ("Altitud (m s.n.m.)", f1.get("altitud_msnm")),
            ("Componentes", "; ".join(f3.get("componentes") or [])),
        ]),
        ("Población y demanda", [
            ("Población actual / futura (hab)", f"{pob['p0']:.0f} / {pob['pf']:.0f} (horizonte {pob['n']} años)"),
            ("Viviendas futuras", pob["viviendas_futuras"]),
            ("Esquema de agua", esq["agua"]),
            ("Dotación neta (L/hab·día)", dem["d"]),
            ("Qmd / QMD / QMH (L/s)", f"{dem['qmd']:.3f} / {dem['QMD']:.3f} / {dem['QMH']:.3f}"),
        ]),
        ("Abastecimiento recomendado", [
            ("Alternativa", ma.nombre if ma else "Ninguna viable – ver alertas"),
            ("Puntaje multicriterio (1–5)", ma.total if ma else ""),
            ("Prediseño", "; ".join(f"{k}: {v}" for k, v in (ma.prediseno if ma else {}).items())),
            ("Condición", ma.motivo if ma else ""),
            ("Estabilidad ante los pesos", f"{sens['agua']['monte_carlo_primera']:.0f} % de 2.000 variaciones de ±50 %" if sens.get("agua") else ""),
            ("Observación", _empate(alt_agua, umbral, sens.get("agua"), est_min)),
            ("Contraste con la Matriz RAS (fuentes)", _texto_ras(cras)),
        ]),
        ("Tratamiento en la vivienda (Art. 36)", [
            ("Opción recomendada", mp.nombre if mp else ""),
            ("Puntaje (1–5)", mp.total if mp else ""),
            ("Uso", "Barrera de seguridad en el punto de consumo" + (" (obligatoria: viviendas dispersas)" if esq["agua"] == "Soluciones individuales" else "")),
        ]),
        ("Saneamiento recomendado", [
            ("Alternativa", ms.nombre if ms else "Ninguna viable – ver alertas"),
            ("Puntaje multicriterio (1–5)", ms.total if ms else ""),
            ("Prediseño", "; ".join(f"{k}: {v}" for k, v in (ms.prediseno if ms else {}).items())),
            ("Condición", ms.motivo if ms else ""),
            ("Estabilidad ante los pesos", f"{sens['saneamiento']['monte_carlo_primera']:.0f} % de 2.000 variaciones de ±50 %" if sens.get("saneamiento") else ""),
            ("Observación", _empate(alt_san, umbral, sens.get("saneamiento"), est_min)),
        ]),
        ("Aseo", [
            ("Producción de residuos (kg/día)", round(res_aseo["generacion"], 1)),
            ("Recomendaciones", " · ".join(res_aseo["recomendaciones"])),
        ]),
        ("Alertas del procesamiento", [(f"Alerta {i}", a) for i, a in enumerate(m.alertas, 1)] or [("—", "Sin alertas")]),
        ("Pendientes normativos", [
            ("Res. 0844 Art. 15.5 y 15.7", "Estimar tarifas o aportes y costos a 25 años de cada alternativa (requiere costos unitarios)"),
            ("Res. 0844 Art. 36 (parágrafo)", "La opción de tratamiento en la vivienda debe contar con la aceptación expresa de la comunidad"),
            ("Pesos de la matriz", "Pesos de referencia: revisar el análisis de sensibilidad antes de decidir"),
            ("Criterio de costo", "Se califica de forma cualitativa, sin presupuesto; requiere el análisis de costos del art. 15"),
        ]),
    ]
    return secciones
