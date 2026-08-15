import random
import os
from aoc_sim.scenario import cargar_parametros, cargar_escenario
from aoc_sim.engine import ejecutar_partida

RUTA_PARAMS = os.path.join(os.path.dirname(__file__), "..", "data", "params.json")
RUTA_SCENARIO = os.path.join(os.path.dirname(__file__), "..", "data", "scenario.json")


def _pasar_siempre(jugador, partida, params, rng):
    return [{"tipo": "PASAR"}]


def test_partida_corre_al_menos_5_turnos_sin_crashear():
    partida = cargar_escenario(RUTA_SCENARIO)
    params = cargar_parametros(RUTA_PARAMS)
    rng = random.Random(42)
    logs = []
    resultado = ejecutar_partida(
        partida, params, rng, obtener_ordenes=_pasar_siempre,
        log=logs.append, turnos_minimos=5, continuar_callback=lambda p: False,
    )
    assert resultado.turno_actual >= 5
    assert any("EV_INICIO_TURNO" in linea for linea in logs)
    assert any("EV_FIN_TURNO" in linea for linea in logs)


def test_partida_es_reproducible_con_misma_semilla():
    def correr(seed):
        partida = cargar_escenario(RUTA_SCENARIO)
        params = cargar_parametros(RUTA_PARAMS)
        rng = random.Random(seed)
        ejecutar_partida(partida, params, rng, obtener_ordenes=_pasar_siempre,
                          log=lambda m: None, turnos_minimos=5, continuar_callback=lambda p: False)
        return {i: p.nivel_felicidad for i, p in partida.provincias.items()}

    assert correr(7) == correr(7)
