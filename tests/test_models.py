from aoc_sim.models import Partida, Jugador, Provincia, Ejercito, TipoControl, ObjetivoVictoria, SIN_DUENO


def _jugador(id_jugador, provincias):
    return Jugador(
        id_jugador=id_jugador, oro_tesoro=100.0, puntos_accion=10.0,
        nivel_impuesto=20.0, tipo_control=TipoControl.IA,
        puesto_clasificacion=id_jugador, provincias_controladas=list(provincias),
    )


def _provincia(id_provincia, id_propietario):
    return Provincia(
        id_provincia=id_provincia, id_propietario=id_propietario,
        poblacion_base=1000.0, nivel_felicidad=80.0, nivel_infraestructura=1,
        tropas_guarnicion=50, nodos_vecinos=[],
    )


def test_eliminar_jugador_lo_saca_de_activos_y_mata_rey():
    j1 = _jugador(1, [1])
    j2 = _jugador(2, [2])
    partida = Partida(
        objetivo_victoria=ObjetivoVictoria.ANIQUILACION, turno_limite=50,
        jugadores={1: j1, 2: j2}, provincias={1: _provincia(1, 1), 2: _provincia(2, 2)},
        ejercitos={}, jugadores_activos=[1, 2],
    )
    partida.eliminar_jugador(1)
    assert 1 not in partida.jugadores_activos
    assert j1.rey_vivo is False


def test_victoria_por_aniquilacion_un_solo_activo():
    j2 = _jugador(2, [2])
    partida = Partida(
        objetivo_victoria=ObjetivoVictoria.ANIQUILACION, turno_limite=50,
        jugadores={2: j2}, provincias={2: _provincia(2, 2)}, ejercitos={},
        jugadores_activos=[2],
    )
    partida.evaluar_condicion_victoria()
    assert partida.finalizada is True
    assert partida.ganador == 2


def test_victoria_por_puntos_al_llegar_turno_limite():
    j1 = _jugador(1, [1, 2])
    j2 = _jugador(2, [3])
    partida = Partida(
        objetivo_victoria=ObjetivoVictoria.ANIQUILACION, turno_limite=10,
        jugadores={1: j1, 2: j2},
        provincias={1: _provincia(1, 1), 2: _provincia(2, 1), 3: _provincia(3, 2)},
        ejercitos={}, jugadores_activos=[1, 2], turno_actual=10,
    )
    partida.evaluar_condicion_victoria()
    assert partida.finalizada is True
    assert partida.ganador == 1


def test_empate_por_puntos_iguales():
    j1 = _jugador(1, [1])
    j2 = _jugador(2, [2])
    partida = Partida(
        objetivo_victoria=ObjetivoVictoria.ANIQUILACION, turno_limite=10,
        jugadores={1: j1, 2: j2},
        provincias={1: _provincia(1, 1), 2: _provincia(2, 2)},
        ejercitos={}, jugadores_activos=[1, 2], turno_actual=10,
    )
    partida.evaluar_condicion_victoria()
    assert partida.finalizada is True
    assert partida.ganador is None


def test_sin_dueno_es_cero():
    assert SIN_DUENO == 0
