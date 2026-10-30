"""
Matriz RAS oficial del Ministerio de Vivienda (hoja «Fuentes»).

El Ministerio publica en su página de requisitos técnicos para el área rural
un libro de Excel llamado Matriz RAS, con «ejemplos de matrices de selección
multicriterio» para fuentes, captación y desarenador, sistemas de tratamiento
y dispositivos de potabilización. Este módulo reproduce la matriz de FUENTES,
con sus criterios, sus puntajes y sus pesos (suman 100 puntos), y la califica
con los datos del diagnóstico.

Se usa como contraste de la matriz propia de la herramienta: si las dos
matrices eligen la misma fuente, la recomendación no depende de los pesos de
referencia de los autores.

Los criterios sin dato no se califican; el puntaje se reescala a los criterios
que sí tienen dato y se reporta la cobertura (% de los 100 puntos evaluados).
"""

# (clave, factor, criterio, peso máximo, campo del formulario, {opción: puntaje})
CRITERIOS_FUENTES = [
    ("acceso", "Acceso a bienes y servicios (20 %)", "Accesibilidad física a la fuente en el punto de captación", 10, "acceso_captacion",
     {"Hay camino y es fácil llegar": 10, "Se puede llegar con dificultad": 5, "No hay camino": 1}),
    ("propiedad", "Acceso a bienes y servicios (20 %)", "Propiedad del terreno de la captación y el desarenador", 10, "propiedad_predio_captacion",
     {"Del municipio o del operador, con títulos al día": 10, "Privado con permiso explícito o de la comunidad": 6,
      "Privado sin permiso, sin título o no se sabe": 1}),
    ("aceptacion", "Aceptabilidad social (20 %)", "Aceptabilidad de la comunidad frente al uso de la fuente", 10, "aceptacion_fuente",
     {"La comunidad ya la usa sin reparos": 10, "Hay reparos o problemas con la fuente": 6, "Hay problemas graves": 1}),
    ("conflictos", "Aceptabilidad social (20 %)", "Conflictos por usos de la fuente", 5, "conflictos_uso",
     {"No hay": 5, "Algunos": 3, "Graves": 1}),
    ("acuerdos", "Aceptabilidad social (20 %)", "Acuerdos o alianzas para la conservación en la zona de la captación", 5, "acuerdos_conservacion",
     {"Existen": 5, "Hay interés": 3, "No hay interés": 1}),
    ("microcuenca", "Ambiental (40 %)", "Estado de conservación de la microcuenca", 15, "estado_microcuenca",
     {"Conservada": 15, "Con deforestación o pastoreo": 10, "Altamente intervenida": 5}),
    ("cauce", "Ambiental (40 %)", "Estabilidad del cauce frente a las amenazas", 10, "estabilidad_cauce",
     {"Sin amenazas": 10, "Reptaciones o turbiedad alta en invierno": 5, "Cárcavas, desprendimientos o agua insuficiente en verano": 1}),
    ("ica", "Ambiental (40 %)", "Calidad del agua (ICA)", 15, "ica", None),
    ("variacion", "Flexibilidad (20 %)", "Variación de caudal entre invierno y verano", 10, None, None),
    ("suficiencia", "Flexibilidad (20 %)", "Suficiencia de una sola fuente para la demanda", 10, None, None),
]

# Diferencia que se considera empate: 4 de 100 puntos, equivalente a 0,20 en la escala de 1 a 5 de la herramienta.
UMBRAL_EMPATE = 4

# Aproximación del ICA cuando no se calculó: según el tratamiento que exige la fuente.
ICA_POR_TRATAMIENTO = {"DESINF": 15, "FLA": 10, "FIME": 10, "SIN_DATOS": 10, "CONV": 5, "ESPECIAL": 5}


def _puntaje(clave, peso, campo, escala, f, fila):
    """Devuelve (puntaje o None, nota)."""
    if clave == "ica":
        ica = f.get("ica")
        if ica not in (None, ""):
            ica = float(ica)
            return (15 if ica >= 0.6 else 10 if ica >= 0.3 else 5), f"ICA = {ica:g}"
        return ICA_POR_TRATAMIENTO.get(fila.get("_cod"), 10), "aproximado según el tratamiento requerido (sin ICA)"
    if clave == "variacion":
        cont = f.get("continuidad")
        if not cont:
            return None, "sin dato de continuidad"
        if cont != "Permanente":
            return 1, f"fuente {cont.lower()}"
        aforo, estiaje = f.get("caudal_aforado_ls"), f.get("caudal_estiaje_ls")
        if aforo and estiaje:
            r = float(estiaje) / float(aforo)
            return (10 if r >= 0.7 else 5), f"estiaje / aforo = {r:.2f}"
        return 5, "permanente, sin caudal de estiaje para medir la variación"
    if clave == "suficiencia":
        ind = fila.get("_indice")
        if ind is None:
            return None, "sin caudal"
        return (10 if ind >= 1 else 5 if ind >= 0.5 else 1), f"índice oferta/demanda = {ind:.2f}"
    v = f.get(campo)
    if v in (None, ""):
        return None, "sin dato"
    return escala.get(v), v


def evaluar_fuentes(filas_fuentes):
    """Califica cada fuente con la Matriz RAS. filas_fuentes = resultado['fuentes'] del motor."""
    salida = []
    for fila in filas_fuentes:
        f = fila.get("_f", {})
        detalle, obtenido, evaluado = [], 0.0, 0
        for clave, factor, criterio, peso, campo, escala in CRITERIOS_FUENTES:
            pts, nota = _puntaje(clave, peso, campo, escala, f, fila)
            detalle.append({"Factor": factor, "Criterio": criterio, "Peso": peso, "Puntaje": pts, "Base": nota})
            if pts is not None:
                obtenido += pts
                evaluado += peso
        salida.append({
            "fuente": fila["Fuente"],
            "puntaje": round(100 * obtenido / evaluado, 1) if evaluado else None,
            "cobertura": evaluado,
            "detalle": detalle,
        })
    salida.sort(key=lambda x: -(x["puntaje"] or 0))
    return salida


def contraste(matriz_ras, alternativas_agua):
    """Compara la fuente elegida por la Matriz RAS con la de la matriz de la herramienta."""
    if not matriz_ras:
        return None
    viables = [a for a in alternativas_agua if a.viable]
    propia = None
    if viables:
        for m in matriz_ras:
            if m["fuente"] in viables[0].nombre:
                propia = m["fuente"]
                break
    ras = matriz_ras[0]["fuente"]
    tope = matriz_ras[0]["puntaje"] or 0
    empatadas = [m["fuente"] for m in matriz_ras if m["puntaje"] is not None and tope - m["puntaje"] <= UMBRAL_EMPATE]
    return {"fuente_matriz_ras": ras, "fuente_herramienta": propia, "coinciden": propia == ras,
            "empatadas": empatadas, "empate": len(empatadas) > 1, "compatible": propia in empatadas,
            "cobertura_min": min(m["cobertura"] for m in matriz_ras)}
