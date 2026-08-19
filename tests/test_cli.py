from types import SimpleNamespace
from aoc_sim.models import Partida, Jugador, Provincia, Ejercito, TipoControl, ObjetivoVictoria
from aoc_sim.cli import menu_ordenes_humano, obtener_ordenes_mixto

PARAMS = SimpleNamespace(margen_ia=1.2, b_fort=1.0, b_rey_atk=1.0, b_rey_def=0.30, p_barco=0.30,
                          costo_fortificacion=100.0, costo_reclutamiento_por_tropa=2.0,
                          costo_decreto=50.0, delta_decreto_felicidad=10.0,
                          costo_infraestructura=200.0)


def _partida_un_jugador():
    p1 = Provincia(id_provincia=1, id_propietario=1, poblacion_base=1000, nivel_felicidad=80,
                    nivel_infraestructura=1, tropas_guarnicion=100, nodos_vecinos=[])
    j1 = Jugador(id_jugador=1, oro_tesoro=500.0, puntos_accion=10.0, nivel_impuesto=20.0,
                 tipo_control=TipoControl.HUMANO, puesto_clasificacion=1, provincias_controladas=[1])
    return Partida(objetivo_victoria=ObjetivoVictoria.ANIQUILACION, turno_limite=50,
                    jugadores={1: j1}, provincias={1: p1}, ejercitos={}, jugadores_activos=[1]), j1


def test_menu_recolecta_ordenes_hasta_pasar():
    partida, j1 = _partida_un_jugador()
    entradas = iter(["", "4", "35", "", "12"])  # Enter inicial, 4=Ajustar impuestos, valor, Enter (pausa), 12=Pasar turno
    ordenes = menu_ordenes_humano(j1, partida, PARAMS, rng=None,
                                   entrada=lambda _prompt="": next(entradas), salida=lambda m: None, limpiar=lambda: None)
    assert ordenes == [{"tipo": "IMPUESTO", "nuevo_nivel": 35.0}]


def test_menu_pasar_inmediato_da_lista_vacia():
    partida, j1 = _partida_un_jugador()
    entradas = iter(["", "12"])
    ordenes = menu_ordenes_humano(j1, partida, PARAMS, rng=None,
                                   entrada=lambda _prompt="": next(entradas), salida=lambda m: None, limpiar=lambda: None)
    assert ordenes == []


def test_menu_entrada_no_numerica_no_crashea_y_descarta_orden():
    partida, j1 = _partida_un_jugador()
    entradas = iter(["", "4", "no-es-un-numero", "", "12"])
    ordenes = menu_ordenes_humano(j1, partida, PARAMS, rng=None,
                                   entrada=lambda _prompt="": next(entradas), salida=lambda m: None, limpiar=lambda: None)
    assert ordenes == []


def test_menu_muestra_ejercitos_disponibles_antes_de_pedir_mover():
    partida, j1 = _partida_un_jugador()
    partida.ejercitos[1] = Ejercito(id_ejercito=1, id_propietario=1, cantidad_fuerza=42, nodo_posicion_id=1)
    salidas = []
    entradas = iter(["", "1", "1", "1", "", "12"])
    menu_ordenes_humano(j1, partida, PARAMS, rng=None,
                         entrada=lambda _prompt="": next(entradas), salida=salidas.append, limpiar=lambda: None)
    assert any("E1: fuerza=42" in linea for linea in salidas)


def test_menu_marca_vecinos_atacables_y_propios():
    p1 = Provincia(id_provincia=1, id_propietario=1, poblacion_base=1000, nivel_felicidad=80,
                    nivel_infraestructura=1, tropas_guarnicion=100, nodos_vecinos=[2, 3])
    p2 = Provincia(id_provincia=2, id_propietario=1, poblacion_base=1000, nivel_felicidad=80,
                    nivel_infraestructura=1, tropas_guarnicion=50, nodos_vecinos=[1])
    p3 = Provincia(id_provincia=3, id_propietario=2, poblacion_base=1000, nivel_felicidad=80,
                    nivel_infraestructura=1, tropas_guarnicion=30, nodos_vecinos=[1])
    j1 = Jugador(id_jugador=1, oro_tesoro=500.0, puntos_accion=10.0, nivel_impuesto=20.0,
                 tipo_control=TipoControl.HUMANO, puesto_clasificacion=1, provincias_controladas=[1, 2])
    j2 = Jugador(id_jugador=2, oro_tesoro=500.0, puntos_accion=10.0, nivel_impuesto=20.0,
                 tipo_control=TipoControl.IA, puesto_clasificacion=2, provincias_controladas=[3])
    partida = Partida(objetivo_victoria=ObjetivoVictoria.ANIQUILACION, turno_limite=50,
                       jugadores={1: j1, 2: j2}, provincias={1: p1, 2: p2, 3: p3},
                       ejercitos={1: Ejercito(id_ejercito=1, id_propietario=1, cantidad_fuerza=60,
                                               nodo_posicion_id=1)},
                       jugadores_activos=[1, 2])
    salidas = []
    entradas = iter(["", "1", "1", "3", "", "12"])
    menu_ordenes_humano(j1, partida, PARAMS, rng=None,
                         entrada=lambda _prompt="": next(entradas), salida=salidas.append, limpiar=lambda: None)
    linea_vecinos = next(l for l in salidas if "vecinos:" in l)
    assert "P2 (propia, tropas=50)" in linea_vecinos
    assert "P3 (enemiga de J2, tropas=30) [ATACABLE]" in linea_vecinos


def test_menu_muestra_provincias_y_oro_antes_de_pedir_reclutar():
    partida, j1 = _partida_un_jugador()
    salidas = []
    entradas = iter(["", "5", "1", "5", "", "12"])
    menu_ordenes_humano(j1, partida, PARAMS, rng=None,
                         entrada=lambda _prompt="": next(entradas), salida=salidas.append, limpiar=lambda: None)
    assert any("oro disponible: 500.00" in linea for linea in salidas)
    assert any("P1: tropas=100" in linea for linea in salidas)


def test_menu_opcion_2_encola_reforzar_ejercito():
    partida, j1 = _partida_un_jugador()
    partida.ejercitos[1] = Ejercito(id_ejercito=1, id_propietario=1, cantidad_fuerza=42, nodo_posicion_id=1)
    entradas = iter(["", "2", "1", "20", "", "12"])
    ordenes = menu_ordenes_humano(j1, partida, PARAMS, rng=None,
                                   entrada=lambda _prompt="": next(entradas), salida=lambda m: None,
                                   limpiar=lambda: None)
    assert ordenes == [{"tipo": "REFORZAR_EJERCITO", "id_ejercito": 1, "cantidad": 20}]


def test_menu_opcion_3_encola_dividir_ejercito():
    partida, j1 = _partida_un_jugador()
    partida.ejercitos[1] = Ejercito(id_ejercito=1, id_propietario=1, cantidad_fuerza=60, nodo_posicion_id=1)
    entradas = iter(["", "3", "1", "20", "", "12"])
    ordenes = menu_ordenes_humano(j1, partida, PARAMS, rng=None,
                                   entrada=lambda _prompt="": next(entradas), salida=lambda m: None,
                                   limpiar=lambda: None)
    assert ordenes == [{"tipo": "DIVIDIR_EJERCITO", "id_ejercito": 1, "cantidad": 20}]


def test_menu_opcion_7_encola_invertir_infraestructura():
    partida, j1 = _partida_un_jugador()
    entradas = iter(["", "7", "1", "", "12"])
    ordenes = menu_ordenes_humano(j1, partida, PARAMS, rng=None,
                                   entrada=lambda _prompt="": next(entradas), salida=lambda m: None,
                                   limpiar=lambda: None)
    assert ordenes == [{"tipo": "INVERTIR_INFRAESTRUCTURA", "id_provincia": 1}]


def test_menu_muestra_estado_completo_al_iniciar_y_al_finalizar_turno():
    partida, j1 = _partida_un_jugador()
    salidas = []
    entradas = iter(["", "12"])  # Enter inicial (ve estado), 12=Pasar turno
    menu_ordenes_humano(j1, partida, PARAMS, rng=None,
                         entrada=lambda _prompt="": next(entradas), salida=salidas.append, limpiar=lambda: None)
    assert any("Tu estado al iniciar el turno" in l for l in salidas)
    assert any("Tu estado al finalizar el turno" in l for l in salidas)
    # las provincias deben listarse en ambos momentos
    assert sum(1 for l in salidas if "P1: tropas=100" in l) >= 2


def test_menu_muestra_estado_y_pausa_tras_cada_accion():
    partida, j1 = _partida_un_jugador()
    salidas = []
    valores = iter(["", "4", "35", "", "12"])
    menu_ordenes_humano(j1, partida, PARAMS, rng=None,
                         entrada=lambda _prompt="": next(valores), salida=salidas.append, limpiar=lambda: None)
    assert any("Estado actual" in l for l in salidas)
    assert any("P1: tropas=100" in l for l in salidas)


def test_menu_muestra_resumen_del_turno_al_pasar():
    partida, j1 = _partida_un_jugador()
    resumen = ["t=0.002 EV_RECAUDAR_IMPUESTOS J1 +100.00", "t=0.004 EV_LIQUIDAR_MANTENIMIENTO J1 -5.00"]
    salidas = []
    entradas = iter(["", "12"])
    menu_ordenes_humano(j1, partida, PARAMS, rng=None,
                         entrada=lambda _prompt="": next(entradas), salida=salidas.append,
                         limpiar=lambda: None, resumen=resumen)
    assert any("Resumen final de tu turno" in l for l in salidas)
    assert any("EV_RECAUDAR_IMPUESTOS J1 +100.00" in l for l in salidas)
    assert any("EV_LIQUIDAR_MANTENIMIENTO J1 -5.00" in l for l in salidas)


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
