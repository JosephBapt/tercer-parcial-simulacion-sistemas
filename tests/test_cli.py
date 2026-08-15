from types import SimpleNamespace
from aoc_sim.models import Partida, Jugador, Provincia, Ejercito, TipoControl, ObjetivoVictoria
from aoc_sim.cli import menu_ordenes_humano, obtener_ordenes_mixto

PARAMS = SimpleNamespace(margen_ia=1.2, b_fort=1.0, b_rey_atk=1.0, b_rey_def=0.30, p_barco=0.30,
                          costo_fortificacion=100.0, costo_reclutamiento_por_tropa=2.0)


def _partida_un_jugador():
    p1 = Provincia(id_provincia=1, id_propietario=1, poblacion_base=1000, nivel_felicidad=80,
                    nivel_infraestructura=1, tropas_guarnicion=100, nodos_vecinos=[])
    j1 = Jugador(id_jugador=1, oro_tesoro=500.0, puntos_accion=10.0, nivel_impuesto=20.0,
                 tipo_control=TipoControl.HUMANO, puesto_clasificacion=1, provincias_controladas=[1])
    return Partida(objetivo_victoria=ObjetivoVictoria.ANIQUILACION, turno_limite=50,
                    jugadores={1: j1}, provincias={1: p1}, ejercitos={}, jugadores_activos=[1]), j1


def test_menu_recolecta_ordenes_hasta_pasar():
    partida, j1 = _partida_un_jugador()
    entradas = iter(["2", "35", "9"])  # 2=Ajustar impuestos, luego valor, 9=Pasar turno
    ordenes = menu_ordenes_humano(j1, partida, PARAMS, rng=None,
                                   entrada=lambda _prompt="": next(entradas), salida=lambda m: None)
    assert ordenes == [{"tipo": "IMPUESTO", "nuevo_nivel": 35.0}]


def test_menu_pasar_inmediato_da_lista_vacia():
    partida, j1 = _partida_un_jugador()
    entradas = iter(["9"])
    ordenes = menu_ordenes_humano(j1, partida, PARAMS, rng=None,
                                   entrada=lambda _prompt="": next(entradas), salida=lambda m: None)
    assert ordenes == []


def test_menu_entrada_no_numerica_no_crashea_y_descarta_orden():
    partida, j1 = _partida_un_jugador()
    entradas = iter(["2", "no-es-un-numero", "9"])
    ordenes = menu_ordenes_humano(j1, partida, PARAMS, rng=None,
                                   entrada=lambda _prompt="": next(entradas), salida=lambda m: None)
    assert ordenes == []


def test_obtener_ordenes_mixto_despacha_a_ia():
    p1 = Provincia(id_provincia=1, id_propietario=1, poblacion_base=1000, nivel_felicidad=80,
                    nivel_infraestructura=1, tropas_guarnicion=100, nodos_vecinos=[])
    j_ia = Jugador(id_jugador=1, oro_tesoro=500.0, puntos_accion=10.0, nivel_impuesto=20.0,
                   tipo_control=TipoControl.IA, puesto_clasificacion=1, provincias_controladas=[1])
    partida = Partida(objetivo_victoria=ObjetivoVictoria.ANIQUILACION, turno_limite=50,
                       jugadores={1: j_ia}, provincias={1: p1}, ejercitos={}, jugadores_activos=[1])
    import random
    ordenes = obtener_ordenes_mixto(j_ia, partida, PARAMS, random.Random(1))
    assert isinstance(ordenes, list)
