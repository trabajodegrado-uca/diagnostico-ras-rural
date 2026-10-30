"""
Pruebas unitarias del motor de cálculo y de las reglas de validación.

Ejecutar con pytest:            python3 -m pytest -q
o sin instalar nada:            python3 -m tests.ejecutar
"""
import math

from config.parametros import valores
from core.motor import calcular, dotacion_norma, nivel_tratamiento, prediseno_tanque, _empate, Alternativa
from core.sensibilidad import estabilidad
from core.validacion import tamano_muestra, validar


def proyecto(f1=None, f3=None):
    base1 = {"nombre_proyecto": "Prueba", "altitud_msnm": 2350, "num_viviendas": 60, "num_habitantes": 210}
    base3 = {"componentes": ["Agua para consumo humano y doméstico", "Saneamiento / aguas residuales"],
             "distribucion_espacial": "Semi-dispersa (50 – 200 m)"}
    base1.update(f1 or {}); base3.update(f3 or {})
    return {"id": 1, "nombre": "Prueba", "ficha1": base1, "ficha3": base3}


# ---------------- Población y demanda ----------------
def test_poblacion_geometrica_res_0844():
    r = calcular(proyecto(), [], [])
    assert round(r["poblacion"]["pf"]) == 238                      # 210 · 1,005^25


def test_dotacion_segun_altitud_res_0330():
    p = valores()
    assert dotacion_norma(2350, p)[0] == 120
    assert dotacion_norma(1500, p)[0] == 130
    assert dotacion_norma(500, p)[0] == 140


def test_caudales_caso_monquira():
    r = calcular(proyecto({"altitud_msnm": 2569, "num_viviendas": 43, "num_habitantes": 200},
                          {"tasa_crecimiento": 2.91, "periodo_diseno": 25}), [], [])
    d = r["demanda"]
    assert abs(d["qmd"] - 0.759) / 0.759 < 0.01
    assert abs(d["QMD"] - 0.987) / 0.987 < 0.01
    assert abs(d["QMH"] - 1.579) / 1.579 < 0.01


def test_picos_no_se_aplican_al_agua_de_subsistencia():
    viv = [{"tipo_predio": "Vivienda", "habitantes": 4, "bovinos": 10, "consumo_l_dia": 400}]
    r = calcular(proyecto(), [], viv)
    d = r["demanda"]
    assert d["QMD"] < 1.3 * d["qmd"]                                # QE sin coeficiente de pico


# ---------------- Calidad y tratamiento ----------------
def test_fuente_superficial_sin_caracterizacion_exige_filtracion():
    f = {"nombre_fuente": "Q", "tipo_fuente": "Quebrada", "caudal_aforado_ls": 5, "caudal_estiaje_ls": 5,
         "continuidad": "Permanente", "turbiedad_ntu": 1, "color_upc": 3, "e_coli": 10, "numero_muestras": 1}
    r = calcular(proyecto(), [f], [])
    fila = r["fuentes"][0]
    assert fila["_cod"] == "FLA"
    assert any("una sola muestra" in a for a in r["alertas"])


def test_fuente_superficial_multiestacional_puede_quedar_en_desinfeccion():
    f = {"nombre_fuente": "Q", "tipo_fuente": "Quebrada", "caudal_aforado_ls": 5, "caudal_estiaje_ls": 5, "continuidad": "Permanente",
         "turbiedad_ntu": 1, "color_upc": 3, "e_coli": 0, "numero_muestras": 4, "caracterizacion_multiestacional": True}
    r = calcular(proyecto(), [f], [])
    assert r["fuentes"][0]["_cod"] == "DESINF"


def test_conductividad_alta_exige_tratamiento_especial():
    cod, _, costo, _ = nivel_tratamiento({"turbiedad_ntu": 1, "color_upc": 5, "conductividad": 2977}, valores())
    assert cod == "ESPECIAL" and costo >= 3


# ---------------- Saneamiento ----------------
def test_tanque_septico_nbr7229():
    V, T, K, _ = prediseno_tanque(5, 102, 2350, valores())
    assert (T, K) == (1.0, 65)
    assert math.isclose(V, 1835, abs_tol=0.5)                       # 1000 + 5(102·1 + 65·1)


def test_reglas_dnp_infiltracion():
    for nf, perc, viable in ((1.2, 20, False), (1.6, 20, True), (3, 35, False), (3, 28, True)):
        r = calcular(proyecto(f3={"nivel_freatico_m": nf, "tasa_percolacion": perc}), [], [])
        s1 = next(a for a in r["alternativas_saneamiento"] if a.nombre.startswith("Unidad sanitaria: trampa"))
        assert s1.viable is viable, (nf, perc)


# ---------------- Decisión ----------------
def _alt(nombre, total):
    a = Alternativa(nombre, "x")
    a.total = total
    return a


def test_empate_tecnico_inclusivo():
    assert _empate([_alt("A", 3.64), _alt("B", 3.44)], 0.20) != ""   # diferencia = 0,20 → empate
    assert _empate([_alt("A", 3.99), _alt("B", 3.44)], 0.20) == ""


def test_sensibilidad_alternativa_dominante_es_estable():
    pesos = {"c1": 0.5, "c2": 0.5}
    a, b = _alt("A", 0), _alt("B", 0)
    a.puntajes, b.puntajes = {"c1": 5, "c2": 5}, {"c1": 2, "c2": 2}
    e = estabilidad([a, b], pesos, n=200)
    assert e["monte_carlo_primera"] == 100 and e["uno_a_uno_primera"] == 100


# ---------------- Validación de datos ----------------
def test_tamano_muestra_cochran():
    assert tamano_muestra(60) == 38
    assert tamano_muestra(10) == 10


def test_validacion_rechaza_incoherencias():
    errores = [h for h in validar("vivienda", {"codigo_vivienda": "V-1", "tipo_predio": "Vivienda", "fecha_encuesta": "2026-01-01",
                                               "consentimiento": True, "habitantes": 2, "menores_5": 3}) if h["nivel"] == "error"]
    assert any("menores de 5" in h["mensaje"] for h in errores)


def test_verificacion_con_casos_publicados():
    from core.casos_validacion import correr_todo
    v = correr_todo()["verificacion"]
    assert len(v) > 0 and (v["Error (%)"] <= 1.0).all()


# ---------------- Matriz RAS oficial ----------------
def test_matriz_ras_pesos_suman_100():
    from core.matriz_ras import CRITERIOS_FUENTES
    assert sum(c[3] for c in CRITERIOS_FUENTES) == 100


def test_matriz_ras_reescala_sin_datos_y_marca_cobertura():
    f = {"nombre_fuente": "N", "tipo_fuente": "Nacimiento / manantial", "caudal_aforado_ls": 2, "caudal_estiaje_ls": 2,
         "continuidad": "Permanente", "turbiedad_ntu": 1, "color_upc": 3, "e_coli": 0, "numero_muestras": 3}
    r = calcular(proyecto(), [f], [])
    m = r["matriz_ras"][0]
    assert m["cobertura"] == 35                                     # solo ICA, variación y suficiencia
    assert m["puntaje"] == 100.0                                    # 35 de 35 puntos posibles


def test_matriz_ras_coincide_en_el_proyecto_de_demostracion():
    from core import almacenamiento as bd
    from core.demo import cargar_demo
    con = bd.conectar(":memory:"); pid = cargar_demo(con)
    r = calcular(bd.obtener_proyecto(con, pid), bd.listar_registros(con, pid, "fuente"), bd.listar_registros(con, pid, "vivienda"))
    assert [m["puntaje"] for m in r["matriz_ras"]] == [79.0, 66.0]
    assert r["contraste_matriz_ras"]["coinciden"]
