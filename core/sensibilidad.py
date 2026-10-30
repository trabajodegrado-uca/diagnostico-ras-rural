"""
Análisis de sensibilidad de los pesos de las matrices multicriterio.

Como los pesos son de referencia, se mide qué tan estable es el ordenamiento:
  1. Uno a la vez: cada peso se multiplica por 0,5 y por 1,5 (los demás se
     renormalizan) y se revisa si cambia la primera alternativa o el ranking.
  2. Monte Carlo: en cada corrida todos los pesos se multiplican por un factor
     aleatorio uniforme entre 0,5 y 1,5 y se renormalizan; se reporta en qué
     porcentaje de las corridas se mantienen la primera alternativa y el
     ranking completo.

Las calificaciones (1 a 5) de cada alternativa no cambian: solo cambian los pesos.
"""
import random


def _orden(alts, pesos):
    tot = {a.nombre: sum(a.puntajes.get(k, 0) * w for k, w in pesos.items()) for a in alts}
    return [n for n, _ in sorted(tot.items(), key=lambda x: -x[1])]


def _normalizar(pesos):
    s = sum(pesos.values()) or 1
    return {k: v / s for k, v in pesos.items()}


def estabilidad(alts, pesos, n=2000, rango=0.5, semilla=2026):
    viables = [a for a in alts if a.viable]
    if len(viables) < 2:
        return None
    base = _orden(viables, pesos)

    uno_a_uno = []
    for crit in pesos:
        for factor in (1 - rango, 1 + rango):
            w = _normalizar({k: (v * factor if k == crit else v) for k, v in pesos.items()})
            o = _orden(viables, w)
            uno_a_uno.append({"criterio": crit, "factor": factor, "primera": o[0], "misma_primera": o[0] == base[0], "mismo_ranking": o == base})

    rnd = random.Random(semilla)
    misma_primera = mismo_ranking = 0
    ganadoras = {}
    for _ in range(n):
        w = _normalizar({k: v * rnd.uniform(1 - rango, 1 + rango) for k, v in pesos.items()})
        o = _orden(viables, w)
        misma_primera += o[0] == base[0]
        mismo_ranking += o == base
        ganadoras[o[0]] = ganadoras.get(o[0], 0) + 1

    return {
        "ranking_base": base,
        "uno_a_uno": uno_a_uno,
        "uno_a_uno_primera": 100 * sum(x["misma_primera"] for x in uno_a_uno) / len(uno_a_uno),
        "uno_a_uno_ranking": 100 * sum(x["mismo_ranking"] for x in uno_a_uno) / len(uno_a_uno),
        "monte_carlo_primera": 100 * misma_primera / n,
        "monte_carlo_ranking": 100 * mismo_ranking / n,
        "ganadoras": {k: 100 * v / n for k, v in sorted(ganadoras.items(), key=lambda x: -x[1])},
        "corridas": n,
    }
