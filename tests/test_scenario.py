import json
import os
import tempfile
import pytest
from aoc_sim.scenario import cargar_parametros, cargar_escenario
from aoc_sim.models import TipoControl

RUTA_PARAMS = os.path.join(os.path.dirname(__file__), "..", "data", "params.json")
RUTA_SCENARIO = os.path.join(os.path.dirname(__file__), "..", "data", "scenario.json")


def test_cargar_parametros_desde_json_real():
    params = cargar_parametros(RUTA_PARAMS)
    assert params.c_m == 0.05
    assert params.per_anual == 12


def test_cargar_escenario_desde_json_real():
    partida = cargar_escenario(RUTA_SCENARIO)
    assert len(partida.jugadores) == 3
    assert partida.jugadores[1].tipo_control == TipoControl.HUMANO
    assert 1 in partida.jugadores[1].provincias_controladas
    assert partida.turno_limite == 50
    assert set(partida.jugadores_activos) == {1, 2, 3}


def test_cargar_escenario_valida_vecino_inexistente():
    datos = json.load(open(RUTA_SCENARIO, encoding="utf-8"))
    datos["provincias"][0]["nodos_vecinos"] = [999]
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(datos, f)
        ruta_invalida = f.name
    with pytest.raises(ValueError):
        cargar_escenario(ruta_invalida)
    os.unlink(ruta_invalida)
