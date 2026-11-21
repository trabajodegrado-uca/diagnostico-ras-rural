"""
Catálogo de variables de la herramienta de diagnóstico RAS Rural.

Toda la encuesta se genera a partir de este archivo: para agregar, quitar o
renombrar una pregunta basta con editar la lista correspondiente, sin tocar
la interfaz (app.py) ni la base de datos.

Base normativa
--------------
- Resolución 0844 de 2018 (MVCT) – RAS Rural.
    * Art. 9  -> Perfil de proyecto           (FICHA 1 · Perfil proyecto rural)
    * Art. 10 -> Fuentes de información secundaria
    * Art. 13 -> Verificación en campo
    * Art. 14 -> Diagnóstico integral          (FICHA 3 · Etapa de diagnóstico)
- Resolución 330 de 2017 (RAS) y Título J (2021): variables que alimentan las
  matrices multicriterio de selección de tecnologías (Matriz RAS).
- Resolución 2115 de 2007: parámetros de calidad de agua para consumo humano.

Estructura de cada campo
------------------------
id        : nombre interno (sin espacios). No cambiarlo una vez haya datos.
label     : texto de la pregunta.
tipo      : texto | parrafo | entero | decimal | opcion | multiple | si_no | fecha
opciones  : lista (solo para 'opcion' y 'multiple').
req       : True si es obligatorio.
min / max : rango válido (numéricos).
unidad    : unidad que se muestra junto al campo.
ayuda     : texto de ayuda para el encuestador.
ref       : artículo o fuente normativa que exige la variable.
"""

# ---------------------------------------------------------------------------
# Listas de opciones reutilizables
# ---------------------------------------------------------------------------
DEPARTAMENTOS = [
    "Amazonas", "Antioquia", "Arauca", "Atlántico", "Bogotá D.C.", "Bolívar",
    "Boyacá", "Caldas", "Caquetá", "Casanare", "Cauca", "Cesar", "Chocó",
    "Córdoba", "Cundinamarca", "Guainía", "Guaviare", "Huila", "La Guajira",
    "Magdalena", "Meta", "Nariño", "Norte de Santander", "Putumayo", "Quindío",
    "Risaralda", "San Andrés y Providencia", "Santander", "Sucre", "Tolima",
    "Valle del Cauca", "Vaupés", "Vichada",
]

TIPOS_FUENTE = [
    "Nacimiento / manantial", "Quebrada", "Río", "Lago / laguna / embalse",
    "Agua subterránea - pozo profundo", "Agua subterránea - aljibe",
    "Agua lluvia", "Conexión a acueducto o prestador existente", "Otra",
]

AMENAZAS = [
    "Inundación", "Avenida torrencial", "Remoción en masa / deslizamiento",
    "Sequía / desabastecimiento", "Sismo", "Incendio forestal",
    "Erosión", "Erupción volcánica", "Vendaval / huracán / tormenta tropical",
    "Desertificación del suelo", "Acciones violentas", "Ninguna identificada",
]

ESQUEMAS_DIFERENCIALES = [
    "Acueducto con esquema diferencial",
    "Alcantarillado con esquema diferencial",
    "Aseo con esquema diferencial",
    "Solución alternativa colectiva de agua (abasto / punto de suministro / aguas lluvias)",
    "Solución alternativa individual de agua",
    "Solución individual de saneamiento",
    "Por definir",
]

# ---------------------------------------------------------------------------
# FICHA 1 · PERFIL DE PROYECTO RURAL (Res. 0844/2018, Art. 9)
# ---------------------------------------------------------------------------
FICHA_1 = [
    {
        "seccion": "1. Identificación del proyecto",
        "campos": [
            {"id": "nombre_proyecto", "label": "Nombre del proyecto", "tipo": "texto", "req": True, "ref": "Art. 9"},
            {"id": "departamento", "label": "Departamento", "tipo": "opcion", "opciones": DEPARTAMENTOS, "req": True, "ref": "Art. 9"},
            {"id": "municipio", "label": "Municipio", "tipo": "texto", "req": True, "ref": "Art. 9"},
            {"id": "vereda", "label": "Vereda / centro poblado / corregimiento", "tipo": "texto", "req": True, "ref": "Art. 9"},
            {"id": "municipio_pdet", "label": "¿El municipio es PDET?", "tipo": "si_no", "ref": "Ficha 1 oficial (MVCT)"},
            {"id": "territorio_etnico", "label": "Resguardo indígena o consejo comunitario (si aplica)", "tipo": "texto", "ref": "Ficha 1 oficial (MVCT)"},
            {"id": "etnia_mayoritaria", "label": "Etnia mayoritaria de la comunidad", "tipo": "opcion",
             "opciones": ["Campesina / sin pertenencia étnica", "Indígena", "Negra / afrocolombiana", "Raizal", "Palenquera", "Rom", "Sin información"], "ref": "Ficha 1 oficial (MVCT)"},
            {"id": "latitud", "label": "Latitud (punto de referencia)", "tipo": "decimal", "min": -5.0, "max": 14.0, "unidad": "° (WGS84)", "ref": "Art. 9"},
            {"id": "longitud", "label": "Longitud (punto de referencia)", "tipo": "decimal", "min": -82.0, "max": -66.0, "unidad": "° (WGS84)", "ref": "Art. 9"},
            {"id": "altitud_msnm", "label": "Altitud media de la comunidad", "tipo": "decimal", "min": 0, "max": 5500, "unidad": "m s.n.m.", "req": True,
             "ayuda": "Se usa en el motor de cálculo para fijar la dotación neta.", "ref": "Res. 330/2017 – dotación"},
            {"id": "responsable", "label": "Responsable del levantamiento", "tipo": "texto", "req": True},
            {"id": "fecha_perfil", "label": "Fecha de elaboración", "tipo": "fecha", "req": True},
        ],
    },
    {
        "seccion": "2. Uso y clasificación del suelo rural",
        "campos": [
            {"id": "clasificacion_suelo", "label": "Clasificación del suelo según el POT/PBOT/EOT", "tipo": "opcion",
             "opciones": ["Rural", "Suburbano", "Rural - centro poblado", "Protección", "Sin información"], "req": True, "ref": "Art. 9 / Art. 10"},
            {"id": "tipo_asentamiento", "label": "Tipo de asentamiento", "tipo": "opcion",
             "opciones": ["Centro poblado (nucleado)", "Viviendas dispersas", "Mixto (núcleo + dispersas)"], "req": True, "ref": "Art. 9"},
            {"id": "instrumento_ot", "label": "Instrumento de ordenamiento consultado", "tipo": "opcion",
             "opciones": ["POT", "PBOT", "EOT", "Ninguno disponible"], "ref": "Art. 10"},
            {"id": "distancia_minima_viviendas", "label": "Distancia mínima entre viviendas", "tipo": "opcion",
             "opciones": ["Menos de 100 m entre casa y casa", "Más de 100 m entre casa y casa"], "ref": "Ficha 1 oficial (MVCT)"},
            {"id": "actividad_suelo_rural", "label": "Actividad que predomina en el suelo rural", "tipo": "opcion",
             "opciones": ["Viviendas en centros poblados u otros núcleos de población", "Viviendas con huertas o cría de animales menores",
                          "Viviendas en parcelación campestre con usos recreativos", "Vivienda dispersa en áreas de producción agrícola, forestal o minera",
                          "Vivienda dispersa en áreas protegidas o de conservación"], "ref": "Ficha 1 oficial (MVCT)"},
            {"id": "via_acceso", "label": "Tipo de vía de acceso desde la cabecera municipal", "tipo": "multiple",
             "opciones": ["Carretera primaria", "Carretera secundaria", "Carretera terciaria", "Camino de herradura", "Vía fluvial", "Vía marítima", "Vía aérea"],
             "ref": "Ficha 1 oficial (MVCT)"},
        ],
    },
    {
        "seccion": "3. Población y entornos",
        "campos": [
            {"id": "num_viviendas", "label": "Número de viviendas", "tipo": "entero", "min": 1, "max": 20000, "req": True, "ref": "Art. 9"},
            {"id": "num_habitantes", "label": "Número de habitantes (estimado)", "tipo": "entero", "min": 1, "max": 100000, "req": True, "ref": "Art. 9"},
            {"id": "entornos", "label": "Entornos presentes en la comunidad", "tipo": "multiple",
             "opciones": ["Escuela / colegio", "Puesto de salud", "Hogar comunitario / ICBF", "Salón comunal", "Iglesia",
                          "Unidad productiva comunitaria", "Ninguno"], "ref": "Art. 9"},
            {"id": "num_estudiantes", "label": "Número de estudiantes (si hay escuela)", "tipo": "entero", "min": 0, "max": 5000, "ref": "Art. 9"},
            {"id": "descripcion_area", "label": "Descripción del área donde habita la comunidad", "tipo": "parrafo", "req": True,
             "ayuda": "Topografía, vías de acceso, distancia a la cabecera, clima.", "ref": "Art. 9"},
        ],
    },
    {
        "seccion": "4. Salud pública",
        "campos": [
            {"id": "alertas_sanitarias", "label": "¿Existen alertas sanitarias asociadas al agua o al saneamiento?", "tipo": "si_no", "req": True, "ref": "Art. 9"},
            {"id": "enfermedades", "label": "Enfermedades asociadas reportadas", "tipo": "multiple",
             "opciones": ["Enfermedad diarreica aguda (EDA)", "Parasitismo intestinal", "Hepatitis A", "Fiebre tifoidea",
                          "Enfermedades de la piel", "Dengue / vectores", "Ninguna reportada"], "ref": "Art. 9 / Sivigila"},
            {"id": "fuente_salud", "label": "Fuente de la información de salud", "tipo": "opcion",
             "opciones": ["Sivigila", "Secretaría de salud", "Puesto de salud", "Reporte comunitario", "Sin información"], "ref": "Art. 10"},
            {"id": "inspeccion_sanitaria_fuente", "label": "¿La autoridad sanitaria ha hecho inspección ocular a la fuente?", "tipo": "si_no", "ref": "Ficha 1 oficial (MVCT)"},
        ],
    },
    {
        "seccion": "5. Sistemas existentes y prestadores",
        "campos": [
            {"id": "sistema_agua_existente", "label": "Sistema de agua existente", "tipo": "opcion",
             "opciones": ["Ninguno", "Acueducto", "Abasto / solución alternativa colectiva", "Soluciones individuales"], "req": True, "ref": "Art. 9"},
            {"id": "estado_sistema_agua", "label": "Estado operativo del sistema de agua", "tipo": "opcion",
             "opciones": ["No aplica", "Funciona", "Funciona parcialmente", "No funciona"], "req": True, "ref": "Art. 9"},
            {"id": "sistema_saneamiento_existente", "label": "Sistema de saneamiento existente", "tipo": "opcion",
             "opciones": ["Ninguno", "Alcantarillado", "Soluciones individuales (tanque séptico, letrina, unidad seca)", "Mixto"], "req": True, "ref": "Art. 9"},
            {"id": "estado_sistema_saneamiento", "label": "Estado operativo del sistema de saneamiento", "tipo": "opcion",
             "opciones": ["No aplica", "Funciona", "Funciona parcialmente", "No funciona"], "req": True, "ref": "Art. 9"},
            {"id": "prestador_cercano", "label": "¿Hay un prestador de servicios próximo que pueda atender la comunidad?", "tipo": "si_no", "ref": "Art. 9"},
            {"id": "nombre_prestador", "label": "Nombre del prestador próximo", "tipo": "texto", "ref": "Art. 9"},
            {"id": "distancia_prestador_km", "label": "Distancia al prestador", "tipo": "decimal", "min": 0, "max": 500, "unidad": "km", "ref": "Art. 9"},
            {"id": "irca", "label": "IRCA del agua que se suministra hoy (si hay sistema)", "tipo": "decimal", "min": 0, "max": 100, "unidad": "%",
             "ayuda": "Índice de riesgo de la calidad del agua (Res. 2115/2007), reportado por la secretaría de salud.", "ref": "Ficha 1 oficial (MVCT)"},
            {"id": "recuperacion_costos", "label": "Cómo se recuperan hoy los costos del servicio", "tipo": "opcion",
             "opciones": ["Tarifa por consumo", "Tarifa fija", "Cuotas o aportes extraordinarios de la comunidad", "No hay cobro", "No aplica"],
             "ref": "Ficha 1 oficial (MVCT)"},
        ],
    },
    {
        "seccion": "6. Fuentes abastecedoras (identificación preliminar)",
        "campos": [
            {"id": "tipos_fuente_preliminar", "label": "Tipos de fuente identificados", "tipo": "multiple", "opciones": TIPOS_FUENTE, "req": True, "ref": "Art. 9"},
            {"id": "nombres_fuentes", "label": "Nombre(s) de las fuentes", "tipo": "texto", "ref": "Art. 9"},
        ],
    },
    {
        "seccion": "7. Amenazas y vulnerabilidad",
        "campos": [
            {"id": "amenazas", "label": "Amenazas identificadas en la localidad", "tipo": "multiple", "opciones": AMENAZAS, "req": True, "ref": "Art. 9"},
            {"id": "antecedentes_riesgo", "label": "Antecedentes / eventos ocurridos", "tipo": "parrafo", "ref": "Art. 9"},
        ],
    },
    {
        "seccion": "8. Servicio de aseo",
        "campos": [
            {"id": "componentes_aseo", "label": "Componentes del servicio de aseo que se prestan", "tipo": "multiple",
             "opciones": ["Recolección", "Transporte", "Disposición final", "Aprovechamiento", "Ninguno"], "req": True, "ref": "Art. 9"},
        ],
    },
    {
        "seccion": "9. Conclusiones del perfil",
        "campos": [
            {"id": "problematica_agua", "label": "Descripción de la problemática de agua", "tipo": "parrafo", "req": True, "ref": "Art. 9"},
            {"id": "problematica_saneamiento", "label": "Descripción de la problemática de saneamiento", "tipo": "parrafo", "req": True, "ref": "Art. 9"},
            {"id": "esquema_preliminar", "label": "Esquema diferencial preliminar aplicable", "tipo": "multiple",
             "opciones": ESQUEMAS_DIFERENCIALES, "req": True, "ref": "Art. 9 / Dec. 1077/2015"},
        ],
    },
]

# ---------------------------------------------------------------------------
# FICHA 3 · DIAGNÓSTICO INTEGRAL – nivel comunidad (Res. 0844/2018, Art. 14)
# ---------------------------------------------------------------------------
FICHA_3 = [
    {
        "seccion": "1. Alcance del proyecto",
        "campos": [
            {"id": "alcance", "label": "Alcance del proyecto", "tipo": "parrafo", "req": True, "ref": "Art. 14"},
            {"id": "componentes", "label": "Componentes que abarca", "tipo": "multiple",
             "opciones": ["Agua para consumo humano y doméstico", "Saneamiento / aguas residuales", "Aseo / residuos sólidos"], "req": True, "ref": "Art. 14"},
            {"id": "viviendas_beneficiar", "label": "Viviendas a beneficiar", "tipo": "entero", "min": 1, "max": 20000, "req": True, "ref": "Art. 14"},
            {"id": "habitantes_beneficiar", "label": "Habitantes a beneficiar", "tipo": "entero", "min": 1, "max": 100000, "req": True, "ref": "Art. 14"},
            {"id": "tasa_crecimiento", "label": "Tasa de crecimiento anual adoptada", "tipo": "decimal", "min": 0, "max": 5, "unidad": "%",
             "ayuda": "Si no hay información, el RAS Rural admite 0,5 % anual.", "ref": "Art. 5"},
            {"id": "periodo_diseno", "label": "Periodo de diseño", "tipo": "entero", "min": 5, "max": 30, "unidad": "años", "ref": "Art. 5"},
            {"id": "dotacion_neta_adoptada", "label": "Dotación neta adoptada (opcional)", "tipo": "decimal", "min": 5, "max": 200, "unidad": "L/hab·día",
             "ayuda": "Dejar vacío para usar la Res. 330/2017 Art. 43 según la altitud. Llenar solo con justificación técnica o para replicar un estudio.",
             "ref": "Res. 0844 Art. 32.1 (20–200 L/hab·día en abastos)"},
            {"id": "perdidas_adoptadas", "label": "Pérdidas técnicas adoptadas (opcional)", "tipo": "decimal", "min": 0, "max": 50, "unidad": "%",
             "ayuda": "Vacío = 25 % (máximo de la Res. 330 Art. 44 y Res. 0844 Art. 32.2). Valores mayores a 25 % no cumplen la norma vigente.",
             "ref": "Res. 330/2017 Art. 44"},
            {"id": "k1_adoptado", "label": "Coeficiente k1 adoptado (opcional)", "tipo": "decimal", "min": 1.0, "max": 2.0,
             "ayuda": "Vacío = 1,3. Llenar solo para replicar un estudio o con justificación.", "ref": "Res. 330/2017"},
            {"id": "k2_adoptado", "label": "Coeficiente k2 adoptado (opcional)", "tipo": "decimal", "min": 1.0, "max": 3.0,
             "ayuda": "Vacío = 1,6. Llenar solo para replicar un estudio o con justificación.", "ref": "Res. 330/2017"},
        ],
    },
    {
        "seccion": "2. Distribución espacial y suelo",
        "campos": [
            {"id": "distribucion_espacial", "label": "Distribución espacial de viviendas y entornos", "tipo": "opcion",
             "opciones": ["Concentrada (distancia media < 50 m)", "Semi-dispersa (50 – 200 m)", "Dispersa (> 200 m)"], "req": True,
             "ayuda": "Define si conviene una solución colectiva o individual.", "ref": "Art. 14"},
            {"id": "distancia_media_viviendas_m", "label": "Distancia media entre viviendas", "tipo": "decimal", "min": 0, "max": 10000, "unidad": "m", "ref": "Art. 14"},
            {"id": "estrato", "label": "Estratificación socioeconómica asignada", "tipo": "opcion",
             "opciones": ["1", "2", "3", "4", "5", "6", "Sin estratificar"], "req": True, "ref": "Art. 14"},
            {"id": "usos_actuales_suelo", "label": "Usos actuales del suelo", "tipo": "multiple",
             "opciones": ["Agrícola", "Pecuario", "Forestal", "Conservación", "Minero", "Turístico", "Residencial"], "req": True, "ref": "Art. 14"},
            {"id": "usos_potenciales_suelo", "label": "Usos potenciales del suelo", "tipo": "parrafo", "ref": "Art. 14"},
            {"id": "pendiente_terreno", "label": "Pendiente predominante del terreno", "tipo": "opcion",
             "opciones": ["Plana (0 – 3 %)", "Ondulada (3 – 12 %)", "Inclinada (12 – 25 %)", "Escarpada (> 25 %)"], "req": True, "ref": "Título J"},
        ],
    },
    {
        "seccion": "3. Organización comunitaria y gestión",
        "campos": [
            {"id": "organizacion", "label": "Organización comunitaria existente", "tipo": "multiple",
             "opciones": ["Junta de Acción Comunal", "Junta administradora de acueducto", "Asociación de usuarios", "Cabildo / consejo comunitario", "Ninguna"],
             "req": True, "ref": "Art. 14"},
            {"id": "organizacion_legal", "label": "¿La organización está legalmente constituida?", "tipo": "si_no", "ref": "Art. 14"},
            {"id": "capacidad_gestion", "label": "Capacidad de la comunidad para gestionar y operar el servicio", "tipo": "opcion",
             "opciones": ["Alta", "Media", "Baja"], "req": True, "ref": "Art. 14"},
            {"id": "mano_obra_local", "label": "¿Hay mano de obra local para operación y mantenimiento?", "tipo": "si_no", "req": True, "ref": "Título J – sostenibilidad técnica"},
            {"id": "acceso_repuestos", "label": "Disponibilidad local de materiales y repuestos", "tipo": "opcion",
             "opciones": ["Alta (en la vereda)", "Media (en la cabecera municipal)", "Baja (fuera del municipio)"], "req": True, "ref": "Título J – sostenibilidad técnica"},
            {"id": "energia_electrica", "label": "Disponibilidad de energía eléctrica", "tipo": "opcion",
             "opciones": ["Red eléctrica continua", "Red eléctrica intermitente", "Solo fuentes no convencionales (solar)", "Sin energía"],
             "req": True, "ref": "Título J"},
        ],
    },
    {
        "seccion": "4. Problemas, necesidades y restricciones",
        "campos": [
            {"id": "problemas_necesidades", "label": "Problemas y necesidades identificados con la comunidad", "tipo": "parrafo", "req": True, "ref": "Art. 14"},
            {"id": "restricciones", "label": "Restricciones identificadas", "tipo": "multiple",
             "opciones": ["Sociales", "Culturales", "Financieras", "Económicas", "Ambientales", "Ninguna"], "req": True, "ref": "Art. 14"},
            {"id": "descripcion_restricciones", "label": "Descripción de las restricciones", "tipo": "parrafo", "ref": "Art. 14"},
        ],
    },
    {
        "seccion": "5. Saneamiento – condiciones del sitio",
        "campos": [
            {"id": "tipo_suelo", "label": "Tipo de suelo predominante", "tipo": "opcion",
             "opciones": ["Arenoso", "Franco-arenoso", "Franco / limoso", "Arcilloso", "Rocoso", "Sin información"], "req": True, "ref": "Título J – saneamiento"},
            {"id": "tasa_percolacion", "label": "Tasa de percolación (prueba de infiltración)", "tipo": "decimal", "min": 0, "max": 300, "unidad": "min/pulgada",
             "ayuda": "Resultado del test de percolación. Dejar vacío si no se ha realizado.", "ref": "Título J / Res. 330"},
            {"id": "nivel_freatico_m", "label": "Profundidad del nivel freático (época de lluvias)", "tipo": "decimal", "min": 0, "max": 100, "unidad": "m", "req": True, "ref": "Título J – saneamiento"},
            {"id": "zona_inundable", "label": "¿El área de las viviendas es inundable?", "tipo": "si_no", "req": True, "ref": "Título J"},
            {"id": "fuente_receptora", "label": "Fuente receptora de aguas residuales (nombre / tipo)", "tipo": "texto", "ref": "Art. 14"},
            {"id": "receptora_alta_vulnerabilidad", "label": "¿Hay cuerpos de agua de alta vulnerabilidad?", "tipo": "si_no", "ref": "Art. 14"},
            {"id": "puntos_vertimiento", "label": "Problemas de evacuación y puntos de vertimiento actuales", "tipo": "parrafo", "ref": "Art. 14"},
        ],
    },
    {
        "seccion": "6. Aseo – residuos sólidos",
        "campos": [
            {"id": "sitios_presentacion", "label": "Sitios de presentación de residuos sólidos", "tipo": "opcion",
             "opciones": ["Domiciliaria", "Sitio de almacenamiento colectivo rural", "No existen"], "ref": "Art. 14 / Art. 53"},
            {"id": "frecuencia_recoleccion", "label": "Frecuencia de recolección", "tipo": "opcion",
             "opciones": ["No hay recolección", "Mensual", "Quincenal", "Semanal", "Más de una vez por semana"], "ref": "Art. 53"},
            {"id": "pgirs", "label": "¿El PGIRS municipal incluye la zona rural?", "tipo": "si_no", "ref": "Art. 10"},
            {"id": "disposicion_final_residuos", "label": "Disposición final de los residuos recolectados", "tipo": "opcion",
             "opciones": ["Relleno sanitario regional", "Relleno sanitario local", "Quema, enterramiento o botadero", "Cuerpo de agua", "Sin información"],
             "ref": "Ficha 3 oficial (MVCT)"},
        ],
    },
    {
        "seccion": "7. Información secundaria consultada",
        "campos": [
            {"id": "fuentes_secundarias", "label": "Fuentes secundarias consultadas", "tipo": "multiple",
             "opciones": ["POT / PBOT / EOT", "SINAS", "SIASAR", "Mapa de riesgo sanitario (Res. 4716/2010)", "Sivigila", "Sisbén",
                          "Plan de Desarrollo / PDET", "POMCA / PORH / PMA", "PGIRS", "Plan municipal de gestión del riesgo"],
             "req": True, "ref": "Art. 10"},
        ],
    },
]

# ---------------------------------------------------------------------------
# REGISTRO DE FUENTES DE AGUA (una fila por fuente) – Art. 13.3 y Art. 14
# ---------------------------------------------------------------------------
FUENTE = [
    {
        "seccion": "Identificación de la fuente",
        "campos": [
            {"id": "nombre_fuente", "label": "Nombre de la fuente", "tipo": "texto", "req": True, "ref": "Art. 14"},
            {"id": "tipo_fuente", "label": "Tipo de fuente", "tipo": "opcion", "opciones": TIPOS_FUENTE, "req": True, "ref": "Art. 14"},
            {"id": "lat_fuente", "label": "Latitud", "tipo": "decimal", "min": -5.0, "max": 14.0, "unidad": "°"},
            {"id": "lon_fuente", "label": "Longitud", "tipo": "decimal", "min": -82.0, "max": -66.0, "unidad": "°"},
            {"id": "cota_fuente_msnm", "label": "Cota de la captación", "tipo": "decimal", "min": 0, "max": 5500, "unidad": "m s.n.m.",
             "ayuda": "Comparada con la altitud de la comunidad indica si es posible conducir por gravedad.", "ref": "Título J"},
            {"id": "distancia_comunidad_km", "label": "Distancia a la comunidad", "tipo": "decimal", "min": 0, "max": 100, "unidad": "km", "req": True, "ref": "Título J"},
            {"id": "concesion_aguas", "label": "¿Tiene concesión de aguas o permiso de la autoridad ambiental?", "tipo": "si_no", "req": True, "ref": "Art. 14"},
        ],
    },
    {
        "seccion": "Cantidad y continuidad",
        "campos": [
            {"id": "caudal_aforado_ls", "label": "Caudal aforado", "tipo": "decimal", "min": 0, "max": 100000, "unidad": "L/s", "req": True, "ref": "Art. 13.3 / Art. 14"},
            {"id": "metodo_aforo", "label": "Método de aforo", "tipo": "opcion",
             "opciones": ["Volumétrico", "Flotador", "Molinete / correntómetro", "Vertedero", "Prueba de bombeo", "Estimado / información secundaria"], "req": True, "ref": "Art. 13.3"},
            {"id": "fecha_aforo", "label": "Fecha del aforo", "tipo": "fecha", "req": True},
            {"id": "epoca_aforo", "label": "Época del aforo", "tipo": "opcion", "opciones": ["Seca / estiaje", "Lluvias", "Transición"], "req": True,
             "ayuda": "Para diseño se debe usar el caudal de estiaje.", "ref": "Art. 14"},
            {"id": "caudal_estiaje_ls", "label": "Caudal mínimo (estiaje) estimado", "tipo": "decimal", "min": 0, "max": 100000, "unidad": "L/s", "ref": "Art. 14"},
            {"id": "continuidad", "label": "Continuidad de la fuente", "tipo": "opcion", "opciones": ["Permanente", "Intermitente", "Estacional (se seca)"], "req": True, "ref": "Art. 14"},
            {"id": "precipitacion_mm_anual", "label": "Precipitación media anual (si es agua lluvia)", "tipo": "decimal", "min": 0, "max": 13000, "unidad": "mm/año", "ref": "Título J"},
        ],
    },
    {
        "seccion": "Calidad del agua (Res. 2115/2007)",
        "campos": [
            {"id": "turbiedad_ntu", "label": "Turbiedad", "tipo": "decimal", "min": 0, "max": 10000, "unidad": "UNT", "ref": "Res. 2115/2007 (máx. 2 UNT)"},
            {"id": "color_upc", "label": "Color aparente", "tipo": "decimal", "min": 0, "max": 2000, "unidad": "UPC", "ref": "Res. 2115/2007 (máx. 15 UPC)"},
            {"id": "ph", "label": "pH", "tipo": "decimal", "min": 0, "max": 14, "ref": "Res. 2115/2007 (6,5 – 9,0)"},
            {"id": "conductividad", "label": "Conductividad", "tipo": "decimal", "min": 0, "max": 100000, "unidad": "µS/cm", "ref": "Res. 2115/2007 (máx. 1000)"},
            {"id": "coliformes_totales", "label": "Coliformes totales", "tipo": "decimal", "min": 0, "max": 1e7, "unidad": "UFC/100 mL", "ref": "Res. 2115/2007 (0)"},
            {"id": "e_coli", "label": "Escherichia coli", "tipo": "decimal", "min": 0, "max": 1e7, "unidad": "UFC/100 mL", "ref": "Res. 2115/2007 (0)"},
            {"id": "hierro_mgl", "label": "Hierro total", "tipo": "decimal", "min": 0, "max": 100, "unidad": "mg/L", "ref": "Res. 2115/2007 (máx. 0,3)"},
            {"id": "manganeso_mgl", "label": "Manganeso", "tipo": "decimal", "min": 0, "max": 100, "unidad": "mg/L", "ref": "Res. 2115/2007 (máx. 0,1)"},
            {"id": "dureza_mgl", "label": "Dureza total", "tipo": "decimal", "min": 0, "max": 5000, "unidad": "mg/L CaCO₃", "ref": "Res. 2115/2007 (máx. 300)"},
            {"id": "laboratorio_acreditado", "label": "¿Análisis en laboratorio acreditado (ONAC / IDEAM)?", "tipo": "si_no", "req": True, "ref": "Art. 13.3.b"},
            {"id": "numero_muestras", "label": "Número de muestras de calidad analizadas", "tipo": "entero", "min": 1, "max": 100,
             "ayuda": "Con una sola muestra la herramienta genera una alerta: la calidad de las fuentes varía entre época seca y de lluvias.", "ref": "Art. 13.3.b"},
            {"id": "caracterizacion_multiestacional", "label": "¿Hay muestras en época seca y en época de lluvias?", "tipo": "si_no",
             "ayuda": "Si es una fuente superficial y no hay caracterización en ambas épocas, se exige como mínimo filtración.", "ref": "Res. 2115/2007; Título J"},
            {"id": "actividades_afectan", "label": "Actividades que afectan cantidad o calidad", "tipo": "multiple",
             "opciones": ["Ganadería", "Agricultura / agroquímicos", "Vertimientos domésticos", "Minería", "Deforestación", "Ninguna identificada"],
             "req": True, "ref": "Art. 13.3.b"},
        ],
    },
    {
        "seccion": "Entorno de la fuente (Matriz RAS)",
        "campos": [
            {"id": "acceso_captacion", "label": "Acceso físico al sitio de captación", "tipo": "opcion",
             "opciones": ["Hay camino y es fácil llegar", "Se puede llegar con dificultad", "No hay camino"], "ref": "Matriz RAS (MVCT) – Fuentes"},
            {"id": "propiedad_predio_captacion", "label": "Propiedad del predio de la captación", "tipo": "opcion",
             "opciones": ["Del municipio o del operador, con títulos al día", "Privado con permiso explícito o de la comunidad",
                          "Privado sin permiso, sin título o no se sabe"], "ref": "Matriz RAS (MVCT) – Fuentes"},
            {"id": "aceptacion_fuente", "label": "Aceptación de la comunidad frente al uso de la fuente", "tipo": "opcion",
             "opciones": ["La comunidad ya la usa sin reparos", "Hay reparos o problemas con la fuente", "Hay problemas graves"], "ref": "Matriz RAS (MVCT) – Fuentes"},
            {"id": "conflictos_uso", "label": "Conflictos por el uso de la fuente", "tipo": "opcion",
             "opciones": ["No hay", "Algunos", "Graves"], "ref": "Matriz RAS (MVCT) – Fuentes"},
            {"id": "acuerdos_conservacion", "label": "Acuerdos o programas de conservación en la zona de la captación", "tipo": "opcion",
             "opciones": ["Existen", "Hay interés", "No hay interés"], "ref": "Matriz RAS (MVCT) – Fuentes"},
            {"id": "estado_microcuenca", "label": "Estado de conservación de la microcuenca", "tipo": "opcion",
             "opciones": ["Conservada", "Con deforestación o pastoreo", "Altamente intervenida"], "ref": "Matriz RAS (MVCT) – Fuentes; Ficha 1 (ZPA)"},
            {"id": "estabilidad_cauce", "label": "Estabilidad del cauce frente a amenazas", "tipo": "opcion",
             "opciones": ["Sin amenazas", "Reptaciones o turbiedad alta en invierno", "Cárcavas, desprendimientos o agua insuficiente en verano"],
             "ref": "Matriz RAS (MVCT) – Fuentes"},
            {"id": "proteccion_fuente", "label": "¿La fuente o la captación está protegida (cerca o aislamiento)?", "tipo": "si_no", "ref": "Ficha 1 y Ficha 3 oficiales (MVCT)"},
            {"id": "ica", "label": "Índice de calidad del agua (ICA), si se calculó", "tipo": "decimal", "min": 0, "max": 1,
             "ayuda": "Índice de 0 a 1 (IDEAM). Si no se tiene, la herramienta usa una aproximación según el tratamiento requerido.", "ref": "Matriz RAS (MVCT) – Fuentes"},
        ],
    },
]

# ---------------------------------------------------------------------------
# ENCUESTA POR VIVIENDA (una fila por vivienda o entorno) – Art. 14
# Hábitos, higiene, demanda, capacidad y voluntad de pago.
# ---------------------------------------------------------------------------
VIVIENDA = [
    {
        "seccion": "A. Identificación",
        "campos": [
            {"id": "codigo_vivienda", "label": "Código de la vivienda", "tipo": "texto", "req": True,
             "ayuda": "Use un código (ej. V-001) en lugar del nombre del jefe de hogar para proteger los datos personales (Ley 1581/2012)."},
            {"id": "tipo_predio", "label": "Tipo de predio", "tipo": "opcion",
             "opciones": ["Vivienda", "Escuela", "Puesto de salud", "Salón comunal", "Otro entorno"], "req": True, "ref": "Art. 14"},
            {"id": "lat_viv", "label": "Latitud", "tipo": "decimal", "min": -5.0, "max": 14.0, "unidad": "°"},
            {"id": "lon_viv", "label": "Longitud", "tipo": "decimal", "min": -82.0, "max": -66.0, "unidad": "°"},
            {"id": "altitud_viv", "label": "Altitud", "tipo": "decimal", "min": 0, "max": 5500, "unidad": "m s.n.m."},
            {"id": "fecha_encuesta", "label": "Fecha de la encuesta", "tipo": "fecha", "req": True},
            {"id": "consentimiento", "label": "¿El encuestado autoriza el tratamiento de sus datos?", "tipo": "si_no", "req": True, "ref": "Ley 1581/2012"},
        ],
    },
    {
        "seccion": "B. Habitantes",
        "campos": [
            {"id": "habitantes", "label": "Personas que viven en la vivienda", "tipo": "entero", "min": 0, "max": 60, "req": True, "ref": "Art. 14"},
            {"id": "menores_5", "label": "De ellas, menores de 5 años", "tipo": "entero", "min": 0, "max": 30},
            {"id": "mayores_60", "label": "De ellas, mayores de 60 años", "tipo": "entero", "min": 0, "max": 30},
            {"id": "personas_discapacidad", "label": "Personas con discapacidad", "tipo": "entero", "min": 0, "max": 30,
             "ayuda": "Importante para el diseño accesible de la solución sanitaria."},
        ],
    },
    {
        "seccion": "C. Abastecimiento de agua",
        "campos": [
            {"id": "fuente_agua_actual", "label": "¿De dónde obtiene el agua?", "tipo": "opcion",
             "opciones": ["Acueducto / red", "Pila o punto público", "Pozo / aljibe propio", "Nacimiento / quebrada / río (manguera)",
                          "Nacimiento / quebrada / río (acarreo)", "Agua lluvia", "Carrotanque", "Agua embotellada"], "req": True, "ref": "Art. 14"},
            {"id": "distancia_fuente_m", "label": "Distancia de la vivienda al punto de agua", "tipo": "decimal", "min": 0, "max": 20000, "unidad": "m"},
            {"id": "tiempo_acarreo_min", "label": "Tiempo diario dedicado a traer agua", "tipo": "decimal", "min": 0, "max": 600, "unidad": "min/día"},
            {"id": "consumo_l_dia", "label": "Consumo estimado del hogar", "tipo": "decimal", "min": 0, "max": 10000, "unidad": "L/día", "req": True,
             "ayuda": "Pregunte cuántos recipientes (y de qué tamaño) usan al día.", "ref": "Art. 14 – demanda"},
            {"id": "horas_servicio", "label": "Horas al día con agua disponible", "tipo": "decimal", "min": 0, "max": 24, "unidad": "h/día", "ref": "Art. 14 – continuidad"},
            {"id": "almacenamiento", "label": "Almacenamiento en la vivienda", "tipo": "opcion",
             "opciones": ["Tanque elevado", "Tanque a nivel", "Canecas / baldes", "No almacena"], "req": True},
            {"id": "capacidad_almacenamiento_l", "label": "Capacidad de almacenamiento", "tipo": "decimal", "min": 0, "max": 100000, "unidad": "L"},
            {"id": "tratamiento_casa", "label": "¿Cómo trata el agua para beber?", "tipo": "multiple",
             "opciones": ["Hierve", "Cloro", "Filtro casero", "Desinfección solar", "Compra agua tratada", "No la trata"], "req": True, "ref": "Art. 14 – hábitos"},
            {"id": "percepcion_calidad", "label": "Percepción de la calidad del agua", "tipo": "opcion",
             "opciones": ["Buena", "Regular (turbia en lluvias)", "Mala (color, olor o sabor)"], "req": True},
        ],
    },
    {
        "seccion": "D. Agua para la subsistencia de la familia rural",
        "campos": [
            {"id": "bovinos", "label": "Bovinos", "tipo": "entero", "min": 0, "max": 5000, "ref": "Art. 3 / Art. 14.b"},
            {"id": "porcinos", "label": "Porcinos", "tipo": "entero", "min": 0, "max": 5000, "ref": "Art. 3 / Art. 14.b"},
            {"id": "aves", "label": "Aves de corral", "tipo": "entero", "min": 0, "max": 50000, "ref": "Art. 3 / Art. 14.b"},
            {"id": "equinos", "label": "Equinos", "tipo": "entero", "min": 0, "max": 500, "ref": "Art. 3 / Art. 14.b"},
            {"id": "huerta_m2", "label": "Área de huerta o cultivo de pancoger regado", "tipo": "decimal", "min": 0, "max": 50000, "unidad": "m²", "ref": "Art. 3 / Art. 14.b"},
        ],
    },
    {
        "seccion": "E. Saneamiento e higiene",
        "campos": [
            {"id": "tipo_saneamiento", "label": "Tipo de sanitario", "tipo": "opcion",
             "opciones": ["Inodoro conectado a alcantarillado", "Inodoro conectado a tanque séptico", "Inodoro con descarga a pozo / zanja",
                          "Letrina", "Unidad sanitaria seca", "Descarga directa a fuente de agua", "No tiene (campo abierto)"],
             "req": True, "ref": "Art. 14"},
            {"id": "estado_saneamiento", "label": "Estado del sistema sanitario", "tipo": "opcion",
             "opciones": ["No aplica", "Bueno", "Regular", "Malo / colapsado"], "req": True},
            {"id": "aguas_grises", "label": "Disposición de aguas grises (cocina, lavadero, ducha)", "tipo": "opcion",
             "opciones": ["Al alcantarillado", "Al tanque séptico", "A campo de infiltración / zanja", "A la superficie del terreno", "A una fuente de agua"],
             "req": True, "ref": "Art. 14"},
            {"id": "lavamanos_jabon", "label": "¿Tiene lugar para lavado de manos con agua y jabón?", "tipo": "si_no", "req": True, "ref": "Art. 14 – higiene"},
            {"id": "lavado_manos", "label": "Momentos en que se lavan las manos", "tipo": "multiple",
             "opciones": ["Después de ir al baño", "Antes de comer", "Antes de cocinar", "Después de cambiar pañales", "No es habitual"], "ref": "Art. 14 – higiene"},
            {"id": "eda_ultimo_mes", "label": "¿Algún menor de 5 años tuvo diarrea en el último mes?", "tipo": "si_no", "ref": "Art. 9 / Art. 14"},
            {"id": "espacio_disponible_m2", "label": "Área libre disponible en el predio para la solución de saneamiento", "tipo": "decimal",
             "min": 0, "max": 100000, "unidad": "m²", "ref": "Título J – selección"},
        ],
    },
    {
        "seccion": "F. Residuos sólidos",
        "campos": [
            {"id": "manejo_residuos", "label": "¿Qué hace con la basura?", "tipo": "multiple",
             "opciones": ["La recoge el servicio de aseo", "La quema", "La entierra", "La bota a campo abierto / fuente", "Compostaje de orgánicos",
                          "Alimento para animales", "Separa y vende reciclables"], "req": True, "ref": "Art. 14 / Art. 53"},
        ],
    },
    {
        "seccion": "G. Capacidad y voluntad de pago",
        "campos": [
            {"id": "ingreso_rango", "label": "Ingreso mensual del hogar", "tipo": "opcion",
             "opciones": ["Menos de 0,5 SMMLV", "0,5 a 1 SMMLV", "1 a 2 SMMLV", "Más de 2 SMMLV", "Prefiere no responder"], "req": True, "ref": "Art. 14"},
            {"id": "gasto_agua_mes", "label": "Gasto actual en agua (tarifa, carrotanque, botellones)", "tipo": "decimal", "min": 0, "max": 2000000, "unidad": "COP/mes", "ref": "Art. 14"},
            {"id": "voluntad_pago", "label": "¿Estaría dispuesto a pagar por un servicio mejorado?", "tipo": "si_no", "req": True, "ref": "Art. 14"},
            {"id": "monto_dispuesto", "label": "¿Cuánto estaría dispuesto a pagar al mes?", "tipo": "decimal", "min": 0, "max": 500000, "unidad": "COP/mes", "ref": "Art. 14"},
            {"id": "aporte_mano_obra", "label": "¿Aportaría mano de obra para la construcción?", "tipo": "si_no", "req": True, "ref": "Art. 14 – participación"},
            {"id": "participa_om", "label": "¿Participaría en la operación y mantenimiento?", "tipo": "si_no", "req": True, "ref": "Art. 14 – participación"},
            {"id": "observaciones", "label": "Observaciones del encuestador", "tipo": "parrafo"},
        ],
    },
]

# Agrupación usada por la app y por el exportador
FORMULARIOS = {
    "ficha1": {"titulo": "Ficha 1 · Perfil del proyecto", "secciones": FICHA_1},
    "ficha3": {"titulo": "Ficha 3 · Diagnóstico integral", "secciones": FICHA_3},
    "fuente": {"titulo": "Fuentes de agua", "secciones": FUENTE},
    "vivienda": {"titulo": "Encuesta por vivienda", "secciones": VIVIENDA},
}


def campos_de(formulario: str):
    """Devuelve la lista plana de campos de un formulario."""
    return [c for s in FORMULARIOS[formulario]["secciones"] for c in s["campos"]]


def mapa_campos(formulario: str):
    """Diccionario id -> campo."""
    return {c["id"]: c for c in campos_de(formulario)}
