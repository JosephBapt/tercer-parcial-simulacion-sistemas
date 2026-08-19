import random
import os
from types import SimpleNamespace
from aoc_sim.events import TipoEvento
from aoc_sim.models import Partida, Jugador, Provincia, Ejercito, TipoControl, ObjetivoVictoria
from aoc_sim.scenario import cargar_parametros, cargar_escenario
from aoc_sim.engine import ejecutar_partida, _h_fase_ordenes

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


def test_jugador_eliminado_sin_territorio_no_detiene_la_cadena_de_eventos():
    j1 = Jugador(id_jugador=1, oro_tesoro=0.0, puntos_accion=0.0, nivel_impuesto=20.0,
                 tipo_control=TipoControl.IA, puesto_clasificacion=1,
                 provincias_controladas=[], felicidad_nacional=1.0)
    j2 = Jugador(id_jugador=2, oro_tesoro=0.0, puntos_accion=0.0, nivel_impuesto=20.0,
                 tipo_control=TipoControl.IA, puesto_clasificacion=2, provincias_controladas=[1])
    p1 = Provincia(id_provincia=1, id_propietario=2, poblacion_base=1000, nivel_felicidad=80,
                   nivel_infraestructura=1, tropas_guarnicion=10, nodos_vecinos=[])
    partida = Partida(objetivo_victoria=ObjetivoVictoria.ANIQUILACION, turno_limite=50,
                       jugadores={1: j1, 2: j2}, provincias={1: p1}, ejercitos={},
                       jugadores_activos=[1, 2])
    evento = SimpleNamespace(tiempo=0.0, entidades={"id_jugador": 1})
    contexto = {"obtener_ordenes": _pasar_siempre, "ingreso_impuesto": {}, "turnos_completados": 0}

    nuevos = _h_fase_ordenes(partida, SimpleNamespace(), evento, random.Random(1), lambda m: None, contexto)

    assert 1 not in partida.jugadores_activos
    assert len(nuevos) == 1
    assert nuevos[0][1] == TipoEvento.FIN_TURNO


def test_rotacion_respeta_puesto_clasificacion_no_orden_de_insercion():
    p1 = Provincia(id_provincia=1, id_propietario=1, poblacion_base=1000, nivel_felicidad=80,
                   nivel_infraestructura=1, tropas_guarnicion=10, nodos_vecinos=[])
    p2 = Provincia(id_provincia=2, id_propietario=2, poblacion_base=1000, nivel_felicidad=80,
                   nivel_infraestructura=1, tropas_guarnicion=10, nodos_vecinos=[])
    p3 = Provincia(id_provincia=3, id_propietario=3, poblacion_base=1000, nivel_felicidad=80,
                   nivel_infraestructura=1, tropas_guarnicion=10, nodos_vecinos=[])
    # Insertados como J1, J2, J3 pero clasificados en orden inverso: J3 primero, J1 al final.
    j1 = Jugador(id_jugador=1, oro_tesoro=500.0, puntos_accion=10.0, nivel_impuesto=20.0,
                 tipo_control=TipoControl.IA, puesto_clasificacion=3, provincias_controladas=[1])
    j2 = Jugador(id_jugador=2, oro_tesoro=500.0, puntos_accion=10.0, nivel_impuesto=20.0,
                 tipo_control=TipoControl.IA, puesto_clasificacion=2, provincias_controladas=[2])
    j3 = Jugador(id_jugador=3, oro_tesoro=500.0, puntos_accion=10.0, nivel_impuesto=20.0,
                 tipo_control=TipoControl.IA, puesto_clasificacion=1, provincias_controladas=[3])
    partida = Partida(objetivo_victoria=ObjetivoVictoria.ANIQUILACION, turno_limite=50,
                       jugadores={1: j1, 2: j2, 3: j3}, provincias={1: p1, 2: p2, 3: p3},
                       ejercitos={}, jugadores_activos=[1, 2, 3])
    logs = []
    params = SimpleNamespace(puntos_accion_max=10.0, c_m=0.05, m_min=1.0,
                              per_anual=12, g_anual=0.05, r_base=0.01, gamma=0.05,
                              p_guerra=1, p_tau=2, tau_max=100, ratio_min=0.0004,
                              f_revuelta=50, cap_adm=0.69, p_banca=15, r_banca=0.85,
                              comercio_por_poblacion=0.3)

    ejecutar_partida(partida, params, random.Random(1), obtener_ordenes=_pasar_siempre,
                      log=logs.append, turnos_minimos=1, continuar_callback=lambda p: False)

    orden_observado = [linea.split()[-1] for linea in logs if "EV_INICIO_TURNO" in linea]
    assert orden_observado[:3] == ["J3", "J2", "J1"]


def test_eliminacion_a_mitad_de_partida_no_rompe_rotacion_de_turnos():
    def _ordenes_j1_mata_rey_j2(jugador, partida, params, rng):
        if jugador.id_jugador == 1 and 3 in partida.provincias:
            return [{"tipo": "MOVER", "id_ejercito": 1, "provincia_destino": 3}]
        return [{"tipo": "PASAR"}]

    p1 = Provincia(id_provincia=1, id_propietario=1, poblacion_base=1000, nivel_felicidad=80,
                   nivel_infraestructura=1, tropas_guarnicion=100, nodos_vecinos=[3], tiene_rey=True)
    p2 = Provincia(id_provincia=2, id_propietario=2, poblacion_base=1000, nivel_felicidad=80,
                   nivel_infraestructura=1, tropas_guarnicion=100, nodos_vecinos=[], tiene_rey=True)
    p3 = Provincia(id_provincia=3, id_propietario=3, poblacion_base=1000, nivel_felicidad=80,
                   nivel_infraestructura=1, tropas_guarnicion=10, nodos_vecinos=[1], tiene_rey=True)
    j1 = Jugador(id_jugador=1, oro_tesoro=500.0, puntos_accion=10.0, nivel_impuesto=20.0,
                 tipo_control=TipoControl.IA, puesto_clasificacion=1, provincias_controladas=[1])
    j2 = Jugador(id_jugador=2, oro_tesoro=500.0, puntos_accion=10.0, nivel_impuesto=20.0,
                 tipo_control=TipoControl.IA, puesto_clasificacion=2, provincias_controladas=[2])
    j3 = Jugador(id_jugador=3, oro_tesoro=500.0, puntos_accion=10.0, nivel_impuesto=20.0,
                 tipo_control=TipoControl.IA, puesto_clasificacion=3, provincias_controladas=[3])
    ej1 = Ejercito(id_ejercito=1, id_propietario=1, cantidad_fuerza=60, nodo_posicion_id=1)
    partida = Partida(objetivo_victoria=ObjetivoVictoria.ANIQUILACION, turno_limite=50,
                       jugadores={1: j1, 2: j2, 3: j3}, provincias={1: p1, 2: p2, 3: p3},
                       ejercitos={1: ej1}, jugadores_activos=[1, 2, 3])
    logs = []

    ejecutar_partida(partida, SimpleNamespace(puntos_accion_max=10.0, c_m=0.05, m_min=1.0,
                                               per_anual=12, g_anual=0.05, r_base=0.01, gamma=0.05,
                                               p_guerra=1, p_tau=2, tau_max=100, ratio_min=0.0004,
                                               f_revuelta=50, cap_adm=0.69, p_banca=15, r_banca=0.85,
                                               b_fort=1.0, b_rey_atk=1.0, b_rey_def=0.30, p_barco=0.30,
                                               p_conquista=25, comercio_por_poblacion=0.3),
                      random.Random(1), obtener_ordenes=_ordenes_j1_mata_rey_j2,
                      log=logs.append, turnos_minimos=3, continuar_callback=lambda p: False)

    assert 3 not in partida.jugadores_activos
    # J2 nunca deberia jugar dos turnos seguidos sin que J1 o J3 (mientras viva) intervengan.
    turnos_j2 = [i for i, linea in enumerate(logs) if "EV_INICIO_TURNO J2" in linea]
    assert len(turnos_j2) >= 2
