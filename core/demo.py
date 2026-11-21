"""
Carga un proyecto de DEMOSTRACIÓN con datos ficticios para probar la
herramienta y el motor de cálculo.   Uso:  python -m core.demo
"""
import random
from datetime import date

from config.variables import mapa_campos
from core import almacenamiento as bd
from core.validacion import hay_errores, validar


def cargar_demo(con, n_viviendas=25, semilla=7):
    rnd = random.Random(semilla)
    pid = bd.crear_proyecto(con, "Demostración – Vereda La Esperanza")
    hoy = date.today().isoformat()
    bd.guardar_ficha(con, pid, "ficha1", {
        "nombre_proyecto": "Demostración – Vereda La Esperanza", "departamento": "Cundinamarca",
        "municipio": "Municipio de prueba", "vereda": "La Esperanza", "latitud": 4.85, "longitud": -74.25,
        "altitud_msnm": 2350, "responsable": "Equipo de trabajo de grado", "fecha_perfil": hoy,
        "clasificacion_suelo": "Rural", "tipo_asentamiento": "Mixto (núcleo + dispersas)", "instrumento_ot": "EOT",
        "num_viviendas": 60, "num_habitantes": 210, "entornos": ["Escuela / colegio", "Salón comunal"], "num_estudiantes": 35,
        "descripcion_area": "Ladera de montaña, vía destapada de 12 km a la cabecera, clima frío.",
        "alertas_sanitarias": True, "enfermedades": ["Enfermedad diarreica aguda (EDA)", "Parasitismo intestinal"],
        "fuente_salud": "Secretaría de salud", "inspeccion_sanitaria_fuente": False, "municipio_pdet": False,
        "etnia_mayoritaria": "Campesina / sin pertenencia étnica", "distancia_minima_viviendas": "Menos de 100 m entre casa y casa",
        "actividad_suelo_rural": "Viviendas con huertas o cría de animales menores", "via_acceso": ["Carretera terciaria", "Camino de herradura"],
        "recuperacion_costos": "Cuotas o aportes extraordinarios de la comunidad", "sistema_agua_existente": "Abasto / solución alternativa colectiva",
        "estado_sistema_agua": "Funciona parcialmente", "sistema_saneamiento_existente": "Soluciones individuales (tanque séptico, letrina, unidad seca)",
        "estado_sistema_saneamiento": "Funciona parcialmente", "prestador_cercano": False,
        "tipos_fuente_preliminar": ["Nacimiento / manantial", "Quebrada"], "nombres_fuentes": "Nacimiento El Roble; Quebrada Honda",
        "amenazas": ["Remoción en masa / deslizamiento", "Sequía / desabastecimiento"], "componentes_aseo": ["Ninguno"],
        "problematica_agua": "Abasto sin tratamiento; desabastecimiento en verano.",
        "problematica_saneamiento": "Pozos sépticos artesanales colapsados y descargas a la quebrada.",
        "esquema_preliminar": ["Solución alternativa colectiva de agua (abasto / punto de suministro / aguas lluvias)", "Solución individual de saneamiento"],
    })
    bd.guardar_ficha(con, pid, "ficha3", {
        "alcance": "Mejorar el abastecimiento de agua y dotar de soluciones individuales de saneamiento.",
        "componentes": ["Agua para consumo humano y doméstico", "Saneamiento / aguas residuales"],
        "viviendas_beneficiar": 60, "habitantes_beneficiar": 210, "tasa_crecimiento": 0.5, "periodo_diseno": 25,
        "distribucion_espacial": "Semi-dispersa (50 – 200 m)", "distancia_media_viviendas_m": 120, "estrato": "1",
        "usos_actuales_suelo": ["Agrícola", "Pecuario"], "pendiente_terreno": "Inclinada (12 – 25 %)",
        "organizacion": ["Junta de Acción Comunal", "Junta administradora de acueducto"], "organizacion_legal": True,
        "capacidad_gestion": "Media", "mano_obra_local": True, "acceso_repuestos": "Media (en la cabecera municipal)",
        "energia_electrica": "Red eléctrica intermitente", "problemas_necesidades": "Agua no apta, falta de saneamiento.",
        "restricciones": ["Financieras", "Ambientales"], "tipo_suelo": "Franco / limoso", "tasa_percolacion": 18,
        "nivel_freatico_m": 3.5, "zona_inundable": False, "fuente_receptora": "Quebrada Honda",
        "receptora_alta_vulnerabilidad": True, "sitios_presentacion": "No existen", "frecuencia_recoleccion": "No hay recolección",
        "pgirs": False, "disposicion_final_residuos": "Quema, enterramiento o botadero", "fuentes_secundarias": ["POT / PBOT / EOT", "SIASAR", "Sivigila", "PGIRS"],
    })
    for f in (
        {"nombre_fuente": "Nacimiento El Roble", "tipo_fuente": "Nacimiento / manantial", "cota_fuente_msnm": 2480,
         "distancia_comunidad_km": 1.8, "concesion_aguas": False, "caudal_aforado_ls": 1.6, "metodo_aforo": "Volumétrico",
         "fecha_aforo": hoy, "epoca_aforo": "Seca / estiaje", "caudal_estiaje_ls": 1.6, "continuidad": "Permanente",
         "turbiedad_ntu": 3.1, "color_upc": 12, "ph": 6.9, "conductividad": 85, "coliformes_totales": 120, "e_coli": 8,
         "hierro_mgl": 0.1, "laboratorio_acreditado": True, "actividades_afectan": ["Ganadería"],
         "acceso_captacion": "Se puede llegar con dificultad", "propiedad_predio_captacion": "Privado con permiso explícito o de la comunidad",
         "aceptacion_fuente": "La comunidad ya la usa sin reparos", "conflictos_uso": "No hay", "acuerdos_conservacion": "Hay interés",
         "estado_microcuenca": "Con deforestación o pastoreo", "estabilidad_cauce": "Sin amenazas", "proteccion_fuente": False},
        {"nombre_fuente": "Quebrada Honda", "tipo_fuente": "Quebrada", "cota_fuente_msnm": 2300,
         "distancia_comunidad_km": 0.6, "concesion_aguas": False, "caudal_aforado_ls": 12.0, "metodo_aforo": "Flotador",
         "fecha_aforo": hoy, "epoca_aforo": "Lluvias", "caudal_estiaje_ls": 4.5, "continuidad": "Permanente",
         "turbiedad_ntu": 25, "color_upc": 40, "ph": 7.2, "coliformes_totales": 2400, "e_coli": 350,
         "laboratorio_acreditado": True, "actividades_afectan": ["Ganadería", "Vertimientos domésticos"],
         "acceso_captacion": "Hay camino y es fácil llegar", "propiedad_predio_captacion": "Privado con permiso explícito o de la comunidad",
         "aceptacion_fuente": "Hay reparos o problemas con la fuente", "conflictos_uso": "Algunos", "acuerdos_conservacion": "No hay interés",
         "estado_microcuenca": "Con deforestación o pastoreo", "estabilidad_cauce": "Reptaciones o turbiedad alta en invierno", "proteccion_fuente": False},
    ):
        bd.agregar_registro(con, pid, "fuente", f)

    opc = lambda k: mapa_campos("vivienda")[k]["opciones"]
    for i in range(1, n_viviendas + 1):
        hab = rnd.choice([1, 2, 3, 3, 4, 4, 5, 6])
        voluntad = rnd.random() < 0.7
        san = rnd.choices(opc("tipo_saneamiento"), weights=[0, 6, 3, 4, 1, 3, 2])[0]
        alm = rnd.choice(opc("almacenamiento"))
        d = {
            "codigo_vivienda": f"V-{i:03d}", "tipo_predio": "Vivienda", "lat_viv": 4.85 + rnd.uniform(-0.01, 0.01),
            "lon_viv": -74.25 + rnd.uniform(-0.01, 0.01), "altitud_viv": rnd.randint(2280, 2420), "fecha_encuesta": hoy,
            "consentimiento": True, "habitantes": hab, "menores_5": rnd.randint(0, min(1, hab - 1)), "mayores_60": rnd.randint(0, min(1, hab - 1)),
            "personas_discapacidad": 0,
            "fuente_agua_actual": rnd.choices(opc("fuente_agua_actual"), weights=[5, 1, 1, 6, 2, 1, 0, 1])[0],
            "distancia_fuente_m": rnd.randint(0, 400), "tiempo_acarreo_min": rnd.choice([0, 0, 15, 30, 45]),
            "consumo_l_dia": hab * rnd.randint(45, 110), "horas_servicio": rnd.choice([4, 8, 12, 24]),
            "almacenamiento": alm, "capacidad_almacenamiento_l": 0 if alm == "No almacena" else rnd.choice([250, 500, 1000]),
            "tratamiento_casa": rnd.choice([["Hierve"], ["No la trata"], ["Hierve", "Filtro casero"], ["Cloro"]]),
            "percepcion_calidad": rnd.choice(opc("percepcion_calidad")),
            "bovinos": rnd.choice([0, 0, 2, 4]), "porcinos": rnd.choice([0, 1, 2]), "aves": rnd.choice([0, 10, 20]), "equinos": rnd.choice([0, 0, 1]),
            "huerta_m2": rnd.choice([0, 20, 50, 100]),
            "tipo_saneamiento": san,
            "estado_saneamiento": "No aplica" if san == "No tiene (campo abierto)" else rnd.choice(["Bueno", "Regular", "Malo / colapsado"]),
            "aguas_grises": rnd.choice(opc("aguas_grises")[1:]), "lavamanos_jabon": rnd.random() < 0.6,
            "lavado_manos": ["Después de ir al baño", "Antes de comer"], "eda_ultimo_mes": rnd.random() < 0.2,
            "espacio_disponible_m2": rnd.choice([20, 50, 100, 300]),
            "manejo_residuos": rnd.choice([["La quema"], ["La quema", "Compostaje de orgánicos"], ["La entierra"], ["Alimento para animales", "La quema"]]),
            "ingreso_rango": rnd.choice(opc("ingreso_rango")[:4]), "gasto_agua_mes": rnd.choice([0, 0, 5000, 10000]),
            "voluntad_pago": voluntad, "monto_dispuesto": rnd.choice([5000, 8000, 10000, 15000]) if voluntad else None,
            "aporte_mano_obra": rnd.random() < 0.8, "participa_om": rnd.random() < 0.6,
        }
        assert not hay_errores(validar("vivienda", d)), validar("vivienda", d)
        bd.agregar_registro(con, pid, "vivienda", d)
    return pid


if __name__ == "__main__":
    c = bd.conectar()
    print("Proyecto de demostración creado con id", cargar_demo(c))
