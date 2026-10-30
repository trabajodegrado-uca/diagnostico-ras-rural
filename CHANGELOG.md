# Historial de versiones

## 2.0.0 (octubre de 2026): versión final, después de la revisión del director
- Toda fuente superficial (quebrada, río, lago) exige como mínimo filtración lenta (FLA o FiME), salvo que tenga caracterización multiestacional.
- Alerta cuando la calidad del agua se basa en una sola muestra.
- Parámetros de calidad adicionales: manganeso, dureza y conductividad.
- Los coeficientes k1 y k2 se aplican solo al consumo doméstico; el agua de subsistencia entra sin pico (parámetro `picos_en_subsistencia`).
- Umbrales de saneamiento del proyecto tipo DNP–MVCT: percolación ≤ 30 min/pulg, nivel freático ≥ 1,5 m, agua mínima de arrastre 45 L/hab·día.
- Análisis de sensibilidad de los pesos: ±50 % uno a la vez y Monte Carlo (2000 corridas).
- Empate técnico cuando la diferencia es ≤ 0,20 puntos o la estabilidad Monte Carlo de la primera alternativa es < 80 %.
- Tamaño de muestra de Cochran (95 %, e = 10 %) en lugar del umbral del 30 %.
- Verificación (fórmulas) separada de validación (decisiones); caso de control C6 no usado para ajustar.
- Topes de k1 y k2 del Art. 47 de la Res. 0330/2017 (1,3 y 1,6 hasta 12.500 hab; 1,2 y 1,5 por encima), con alerta si un valor adoptado los supera.
- Pruebas unitarias en `tests/` (18).
- Contraste con las fichas oficiales del Ministerio: 19 variables nuevas (municipio PDET, territorio étnico, etnia, distancia mínima entre viviendas, actividad del suelo, vía de acceso, inspección sanitaria, IRCA, recuperación de costos, disposición final de residuos y la sección «Entorno de la fuente»). Escenarios de amenaza completos.
- Hoja «Fuentes» de la Matriz RAS oficial programada como contraste (`core/matriz_ras.py`), con hoja propia en el Excel y fila en la ficha de proyecto.

## 1.0.0 (septiembre de 2026): primera versión, antes de la validación
- Captura de Ficha 1, Ficha 3, fuentes y encuesta de viviendas; motor de cálculo y matrices multicriterio.
- Se puede reproducir con el parámetro `version_reglas = "v1"`.
