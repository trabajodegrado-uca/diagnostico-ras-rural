# Herramienta de diagnóstico RAS Rural (Resolución 0844 de 2018)

Entregable 1 del trabajo de grado: **captura y validación** de la información
del diagnóstico para proyectos de agua y saneamiento básico rural, en un solo
flujo que luego alimenta el motor de cálculo (entregable 2).

## Cómo ejecutarla

```bash
pip install -r requirements.txt
streamlit run app.py
```

Se abre en el navegador (http://localhost:8501). Funciona sin internet una vez
instalada, por lo que sirve en campo con un portátil. En la barra lateral se
puede cargar un **proyecto de demostración** con datos ficticios para probarla.

## Qué captura

| Formulario | Nivel | Base normativa |
|---|---|---|
| Ficha 1 · Perfil del proyecto | Comunidad | Res. 0844/2018, Art. 9 (y Art. 10 info. secundaria) |
| Ficha 3 · Diagnóstico integral | Comunidad | Res. 0844/2018, Art. 14 y Art. 5 (periodo de diseño, crecimiento) |
| Fuentes de agua (una por fuente) | Fuente | Art. 13.3 (verificación en campo), Art. 14; calidad según Res. 2115/2007 |
| Encuesta por vivienda (una por vivienda o entorno) | Hogar | Art. 14: demanda, hábitos, higiene, capacidad y voluntad de pago; Art. 3 agua para subsistencia |

Además se capturan las variables que necesitan las **matrices multicriterio
de selección de tecnologías (Matriz RAS / Título J)**: distribución espacial,
pendiente, tipo de suelo, tasa de percolación, nivel freático, zona inundable,
energía, disponibilidad de repuestos y mano de obra, espacio disponible en el
predio, etc.

## Validación automática

1. **Por campo**: obligatorios, tipo y rangos.
2. **Por registro**: coherencia (p. ej. menores de 5 ≤ habitantes, voluntad de
   pago vs. monto, caudal de estiaje ≤ aforado, “Ninguno” no combinable).
   Alertas por calidad de agua fuera de la Res. 2115/2007.
3. **Por proyecto**: que existan fuentes si el proyecto incluye agua, que haya
   encuestas, cobertura de la muestra, códigos de vivienda repetidos.

Las fichas se pueden guardar como borrador; fuentes y viviendas no se guardan
si tienen errores.

## Salidas

- **Excel** con hojas: Resumen (indicadores), Ficha 1, Ficha 3, Fuentes,
  Viviendas, Validación y Diccionario de variables (cada pregunta con su
  referencia normativa).
- **JSON**: paquete limpio de datos que será la entrada del motor de cálculo.
- **Plantilla Excel** de encuesta por vivienda (con listas desplegables) para
  levantar datos sin computador e importarlos después con las mismas
  validaciones.

## Estructura del código

```
app.py                  Interfaz (Streamlit)
config/variables.py     Catálogo de TODAS las preguntas  ← aquí se ajusta la encuesta
core/almacenamiento.py  Base de datos local SQLite (datos/diagnostico.db)
core/validacion.py      Reglas de validación
core/exportar.py        Excel, JSON e indicadores
core/plantilla.py       Plantilla de campo e importación
core/demo.py            Proyecto de demostración
```

La interfaz se genera a partir de `config/variables.py`: para agregar,
eliminar o renombrar una pregunta se edita solo ese archivo. No cambie el `id`
de una pregunta que ya tenga datos.

## Entregable 2: motor de cálculo

Pestaña **«Cálculos y alternativas»** (código en `core/motor.py`, parámetros en
`config/parametros.py`). Con los datos capturados calcula automáticamente:

| Paso | Qué calcula | Base |
|---|---|---|
| 1. Población | Pf = P₀·(1 + r)ⁿ, viviendas futuras | Res. 0844 Art. 5 (r = 0,5 %, n = 25 años) |
| 2. Esquema | Acueducto / abasto colectivo / soluciones individuales | Res. 0844 Arts. 24, 25.b, 32, 38 |
| 3. Demanda | Dotación según altitud, agua para subsistencia (animales y huerta), Qmd, QMD, QMH, almacenamiento | Res. 330 Arts. 43–44; Res. 0844 Arts. 31–32 |
| 4. Oferta | Índice oferta/demanda por fuente, gravedad o bombeo, combinación de fuentes | Res. 0844 Art. 14 |
| 5. Calidad | Nivel de tratamiento: desinfección, filtración lenta, FiME o convencional | Res. 2115/2007; criterios FiME |
| 6. Agua lluvia | Oferta por m² de techo y cobertura de la dotación | Res. 0844 Arts. 31.2 y 34 |
| 7. Saneamiento | Viabilidad según percolación, nivel freático, inundación y pendiente; prediseño de tanque séptico (NBR 7229) y área de infiltración (USPHS) | Res. 0844 Art. 38; Título J |
| 8. Aseo | Producción de residuos y volumen del sitio de almacenamiento colectivo | Res. 0844 Arts. 13.1.g y 53 |
| 9. Matrices | Puntaje multicriterio de cada alternativa y orden de preferencia | Res. 0844 Arts. 16 y 36; Título J |
| 10. Ficha de proyecto | Alternativa recomendada con prediseño, alertas y pendientes | Res. 0844 Art. 15 |

El Excel exportado incluye las hojas: Ficha de proyecto, Memoria de cálculo,
Oferta vs demanda, Matriz – Abastecimiento, Matriz – Punto de uso,
Matriz – Saneamiento y Parámetros de cálculo.

**Importante:** los parámetros marcados como REFERENCIA (consumo de animales,
umbrales de tratamiento, puntajes base, pesos de la matriz, producción de
residuos) tienen la fuente indicada en `config/parametros.py` y pueden
reemplazarse por datos locales o del PGIRS. Falta el análisis de costos a 25 años
y tarifas (Art. 15.5 y 15.7), que requiere costos unitarios.

## Verificación y validación con casos publicados

`core/casos_validacion.py` carga 6 trabajos publicados (veredas Monquirá, Socotá,
Peña Blanca, Puerto Niño, El Arrayán y Santa Bárbara), los corre en el motor y
separa dos cosas:

- **Verificación** (¿las fórmulas se aplican bien?): de 20 valores comparados se
  excluyen los que son datos de entrada o quedan fijados por construcción; los
  14 restantes coinciden con error máximo de 0,35 %.
- **Validación** (¿las decisiones coinciden con las del estudio?): de 8
  decisiones comparables, en la versión final 5 coinciden, 2 coinciden
  parcialmente y 1 difiere (C4). En la versión 1 (antes de los ajustes):
  5 coinciden, 1 parcial y 2 difieren. El caso C6 (Santa Bárbara) es de control:
  no se usó para ajustar reglas.

También prueba las 5 reglas de suelo del proyecto tipo DNP (5/5). Se ve en la app
(pestaña «Validación y exportación» → «Validación de la herramienta») o por consola:
`python3 -m core.casos_validacion` (genera `validacion_resultados.xlsx`).

Para revisarlos en la app: barra lateral → «Nuevo proyecto» → «Cargar casos de
validación». Cada caso queda como un proyecto con los parámetros del estudio
escritos en la Ficha 3.

## Pruebas unitarias

```bash
python3 -m pytest -q          # si tiene pytest instalado
python3 -m tests.ejecutar     # sin instalar nada (18 pruebas)
```

## Versión, licencia y usabilidad

- Versión actual: ver `VERSION` (2.0.0); cambios en `CHANGELOG.md`.
- Licencia: MIT (`LICENSE`).
- Prueba de usabilidad: `docs/prueba_usabilidad_SUS.xlsx` (cuestionario SUS de 10 ítems y tareas; calcula el puntaje solo).

## Fichas oficiales y Matriz RAS

El catálogo (157 variables) se contrastó con la Ficha 1 (v2) y la Ficha 3 que
publica Minvivienda; se agregaron las variables que faltaban. La Ficha 2
(condiciones sociales y económicas) es del manual del Título J y no se publica
en Excel; su contenido está en la encuesta por vivienda. La hoja «Fuentes» de la
Matriz RAS se programó en `core/matriz_ras.py` y se usa como contraste de la
fuente elegida (hoja «Matriz RAS - Fuentes» del Excel). Lo que no se captura es
el inventario por componente de la infraestructura existente con códigos SIASAR.
