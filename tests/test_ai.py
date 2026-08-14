import random
from types import SimpleNamespace
from aoc_sim.models import Partida, Jugador, Provincia, Ejercito, TipoControl, ObjetivoVictoria
from aoc_sim.ai import decidir_ordenes_ia

PARAMS = SimpleNamespace(
    margen_ia=1.2, b_fort=1.0, b_rey_atk=1.0, b_rey_def=0.30, p_barco=0.30,
    costo_fortificacion=100.0, costo_reclutamiento_por_tropa=2.0,
)


def _partida_basica(tropas_propias, tropas_enemigas, oro=500.0, fortificada_propia=False):
    p1 = Provincia(id_provincia=1, id_propietario=1, poblacion_base=1000, nivel_felicidad=80,
                    nivel_infraestructura=1, tropas_guarnicion=0, nodos_vecinos=[2],
                    fortificada=fortificada_propia)
    p2 = Provincia(id_provincia=2, id_propietario=2, poblacion_base=1000, nivel_felicidad=80,
                    nivel_infraestructura=1, tropas_guarnicion=tropas_enemigas, nodos_vecinos=[1])
    j1 = Jugador(id_jugador=1, oro_tesoro=oro, puntos_accion=10.0, nivel_impuesto=20.0,
                 tipo_control=TipoControl.IA, puesto_clasificacion=1,
                 provincias_controladas=[1])
    ej = Ejercito(id_ejercito=1, id_propietario=1, cantidad_fuerza=tropas_propias, nodo_posicion_id=1)
    return Partida(
        objetivo_victoria=ObjetivoVictoria.ANIQUILACION, turno_limite=50,
        jugadores={1: j1, 2: Jugador(id_jugador=2, oro_tesoro=0, puntos_accion=0,
                                      nivel_impuesto=0, tipo_control=TipoControl.IA,
                                      puesto_clasificacion=2, provincias_controladas=[2])},
        provincias={1: p1, 2: p2}, ejercitos={1: ej}, jugadores_activos=[1, 2],
    ), j1


def test_ia_ataca_si_supera_margen():
    partida, jugador = _partida_basica(tropas_propias=100, tropas_enemigas=50)
    ordenes = decidir_ordenes_ia(jugador, partida, PARAMS, random.Random(1))
    assert ordenes[0]["tipo"] == "MOVER"
    assert ordenes[0]["provincia_destino"] == 2


def test_ia_no_ataca_si_no_supera_margen_y_fortifica():
    partida, jugador = _partida_basica(tropas_propias=50, tropas_enemigas=50, oro=500.0)
    ordenes = decidir_ordenes_ia(jugador, partida, PARAMS, random.Random(1))
    assert ordenes[0]["tipo"] == "FORTIFICAR"
    assert ordenes[0]["id_provincia"] == 1


def test_ia_recluta_si_no_puede_fortificar():
    partida, jugador = _partida_basica(tropas_propias=50, tropas_enemigas=50, oro=50.0,
                                        fortificada_propia=True)
    ordenes = decidir_ordenes_ia(jugador, partida, PARAMS, random.Random(1))
    assert ordenes[0]["tipo"] == "RECLUTAR"
    assert ordenes[0]["id_provincia"] == 1
