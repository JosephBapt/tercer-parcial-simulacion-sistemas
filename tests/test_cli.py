import pytest
from types import SimpleNamespace
from aoc_sim.models import Partida, Jugador, Provincia, Ejercito, TipoControl, ObjetivoVictoria
from aoc_sim.cli import menu_ordenes_humano, obtener_ordenes_mixto, SalirDelJuego

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
    entradas = iter(["", "4", "35", "", "15"])  # Enter inicial, 4=Ajustar impuestos, valor, Enter (pausa), 13=Pasar turno
    ordenes = menu_ordenes_humano(j1, partida, PARAMS, rng=None,
                                   entrada=lambda _prompt="": next(entradas), salida=lambda m: None, limpiar=lambda: None)
    assert ordenes == [{"tipo": "IMPUESTO", "nuevo_nivel": 35.0}]


def test_menu_pasar_inmediato_da_lista_vacia():
    partida, j1 = _partida_un_jugador()
    entradas = iter(["", "15"])
    ordenes = menu_ordenes_humano(j1, partida, PARAMS, rng=None,
                                   entrada=lambda _prompt="": next(entradas), salida=lambda m: None, limpiar=lambda: None)
    assert ordenes == []


def test_menu_entrada_no_numerica_no_crashea_y_descarta_orden():
    partida, j1 = _partida_un_jugador()
    entradas = iter(["", "4", "no-es-un-numero", "", "15"])
    ordenes = menu_ordenes_humano(j1, partida, PARAMS, rng=None,
                                   entrada=lambda _prompt="": next(entradas), salida=lambda m: None, limpiar=lambda: None)
    assert ordenes == []


def test_menu_muestra_ejercitos_disponibles_antes_de_pedir_mover():
    partida, j1 = _partida_un_jugador()
    partida.ejercitos[1] = Ejercito(id_ejercito=1, id_propietario=1, cantidad_fuerza=42, nodo_posicion_id=1)
    salidas = []
    entradas = iter(["", "1", "1", "1", "", "15"])
    menu_ordenes_humano(j1, partida, PARAMS, rng=None,
                         entrada=lambda _prompt="": next(entradas), salida=salidas.append, limpiar=lambda: None)
    assert any("E1: 42 tropas" in linea for linea in salidas)


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
    entradas = iter(["", "1", "1", "3", "", "", "15"])  # ultimo "" = cantidad (Enter = mover todas)
    menu_ordenes_humano(j1, partida, PARAMS, rng=None,
                         entrada=lambda _prompt="": next(entradas), salida=salidas.append, limpiar=lambda: None)
    assert any("P2 (propia): 50 tropas" in l for l in salidas)
    assert any("P3 (enemiga de J2, ATACABLE): 30 tropas" in l for l in salidas)


def test_menu_muestra_provincias_y_oro_antes_de_pedir_reclutar():
    partida, j1 = _partida_un_jugador()
    salidas = []
    entradas = iter(["", "5", "1", "5", "", "15"])
    menu_ordenes_humano(j1, partida, PARAMS, rng=None,
                         entrada=lambda _prompt="": next(entradas), salida=salidas.append, limpiar=lambda: None)
    assert any("Tesoro: 500.00 oro" in linea for linea in salidas)
    assert any("P1: 100 tropas" in linea for linea in salidas)


def test_menu_opcion_1_mover_pide_cantidad_y_permite_movimiento_parcial():
    p1 = Provincia(id_provincia=1, id_propietario=1, poblacion_base=1000, nivel_felicidad=80,
                    nivel_infraestructura=1, tropas_guarnicion=100, nodos_vecinos=[2])
    p2 = Provincia(id_provincia=2, id_propietario=0, poblacion_base=500, nivel_felicidad=50,
                    nivel_infraestructura=0, tropas_guarnicion=10, nodos_vecinos=[1])
    j1 = Jugador(id_jugador=1, oro_tesoro=500.0, puntos_accion=10.0, nivel_impuesto=20.0,
                 tipo_control=TipoControl.HUMANO, puesto_clasificacion=1, provincias_controladas=[1])
    partida = Partida(objetivo_victoria=ObjetivoVictoria.ANIQUILACION, turno_limite=50,
                       jugadores={1: j1}, provincias={1: p1, 2: p2},
                       ejercitos={1: Ejercito(id_ejercito=1, id_propietario=1, cantidad_fuerza=60,
                                               nodo_posicion_id=1)},
                       jugadores_activos=[1])
    entradas = iter(["", "1", "1", "2", "25", "", "15"])
    ordenes = menu_ordenes_humano(j1, partida, PARAMS, rng=None,
                                   entrada=lambda _prompt="": next(entradas), salida=lambda m: None,
                                   limpiar=lambda: None)
    assert ordenes == [{"tipo": "MOVER", "id_ejercito": 1, "provincia_destino": 2, "cantidad": 25}]


def test_menu_opcion_1_mover_cantidad_invalida_avisa_y_descarta():
    p1 = Provincia(id_provincia=1, id_propietario=1, poblacion_base=1000, nivel_felicidad=80,
                    nivel_infraestructura=1, tropas_guarnicion=100, nodos_vecinos=[2])
    p2 = Provincia(id_provincia=2, id_propietario=0, poblacion_base=500, nivel_felicidad=50,
                    nivel_infraestructura=0, tropas_guarnicion=10, nodos_vecinos=[1])
    j1 = Jugador(id_jugador=1, oro_tesoro=500.0, puntos_accion=10.0, nivel_impuesto=20.0,
                 tipo_control=TipoControl.HUMANO, puesto_clasificacion=1, provincias_controladas=[1])
    partida = Partida(objetivo_victoria=ObjetivoVictoria.ANIQUILACION, turno_limite=50,
                       jugadores={1: j1}, provincias={1: p1, 2: p2},
                       ejercitos={1: Ejercito(id_ejercito=1, id_propietario=1, cantidad_fuerza=60,
                                               nodo_posicion_id=1)},
                       jugadores_activos=[1])
    salidas = []
    entradas = iter(["", "1", "1", "2", "999", "", "15"])  # el ejercito solo tiene 60 de fuerza
    ordenes = menu_ordenes_humano(j1, partida, PARAMS, rng=None,
                                   entrada=lambda _prompt="": next(entradas), salida=salidas.append,
                                   limpiar=lambda: None)
    assert ordenes == []
    assert any("Cantidad invalida" in l for l in salidas)


def test_menu_opcion_2_encola_reforzar_ejercito():
    partida, j1 = _partida_un_jugador()
    partida.ejercitos[1] = Ejercito(id_ejercito=1, id_propietario=1, cantidad_fuerza=42, nodo_posicion_id=1)
    entradas = iter(["", "2", "1", "20", "", "15"])
    ordenes = menu_ordenes_humano(j1, partida, PARAMS, rng=None,
                                   entrada=lambda _prompt="": next(entradas), salida=lambda m: None,
                                   limpiar=lambda: None)
    assert ordenes == [{"tipo": "REFORZAR_EJERCITO", "id_ejercito": 1, "cantidad": 20}]


def test_menu_opcion_3_encola_dividir_ejercito():
    partida, j1 = _partida_un_jugador()
    partida.ejercitos[1] = Ejercito(id_ejercito=1, id_propietario=1, cantidad_fuerza=60, nodo_posicion_id=1)
    entradas = iter(["", "3", "1", "20", "", "15"])
    ordenes = menu_ordenes_humano(j1, partida, PARAMS, rng=None,
                                   entrada=lambda _prompt="": next(entradas), salida=lambda m: None,
                                   limpiar=lambda: None)
    assert ordenes == [{"tipo": "DIVIDIR_EJERCITO", "id_ejercito": 1, "cantidad": 20}]


def test_menu_opcion_7_encola_invertir_infraestructura():
    partida, j1 = _partida_un_jugador()
    entradas = iter(["", "7", "1", "", "15"])
    ordenes = menu_ordenes_humano(j1, partida, PARAMS, rng=None,
                                   entrada=lambda _prompt="": next(entradas), salida=lambda m: None,
                                   limpiar=lambda: None)
    assert ordenes == [{"tipo": "INVERTIR_INFRAESTRUCTURA", "id_provincia": 1}]


def test_menu_muestra_estado_completo_al_iniciar_y_al_finalizar_turno():
    partida, j1 = _partida_un_jugador()
    salidas = []
    entradas = iter(["", "15"])  # Enter inicial 13=Pasar turno
    menu_ordenes_humano(j1, partida, PARAMS, rng=None,
                         entrada=lambda _prompt="": next(entradas), salida=salidas.append, limpiar=lambda: None)
    assert any("Tu estado al iniciar el turno" in l for l in salidas)
    assert any("Tu estado al finalizar el turno" in l for l in salidas)
    # las provincias deben listarse en ambos momentos
    assert sum(1 for l in salidas if "P1: 100 tropas" in l) >= 2


def test_menu_no_muestra_estado_tras_cada_accion_solo_al_pasar_turno():
    partida, j1 = _partida_un_jugador()
    salidas = []
    valores = iter(["", "4", "35", "", "15"])
    menu_ordenes_humano(j1, partida, PARAMS, rng=None,
                         entrada=lambda _prompt="": next(valores), salida=salidas.append, limpiar=lambda: None)
    assert not any("Estado actual" in l for l in salidas)
    assert any("P1: 100 tropas" in l for l in salidas)


def test_menu_muestra_resumen_del_turno_al_pasar():
    partida, j1 = _partida_un_jugador()
    resumen = ["t=0.002 EV_RECAUDAR_IMPUESTOS J1 +100.00", "t=0.004 EV_LIQUIDAR_MANTENIMIENTO J1 -5.00"]
    salidas = []
    entradas = iter(["", "15"])
    menu_ordenes_humano(j1, partida, PARAMS, rng=None,
                         entrada=lambda _prompt="": next(entradas), salida=salidas.append,
                         limpiar=lambda: None, resumen=resumen)
    assert any("Resumen final de tu turno" in l for l in salidas)
    assert any("Recaudacion de impuestos (J1): +100.00 oro" in l for l in salidas)
    assert any("Mantenimiento de tropas (J1): -5.00 oro" in l for l in salidas)


def test_menu_con_aplicar_ejecuta_la_orden_de_inmediato_y_retorna_lista_vacia():
    partida, j1 = _partida_un_jugador()
    aplicadas = []

    def aplicar_impuesto(orden):
        aplicadas.append(orden)
        if orden["tipo"] == "IMPUESTO":
            j1.nivel_impuesto = orden["nuevo_nivel"]

    entradas = iter(["", "4", "35", "", "15"])  # ajustar impuesto a 35
    ordenes = menu_ordenes_humano(j1, partida, PARAMS, rng=None,
                                   entrada=lambda _prompt="": next(entradas), salida=lambda m: None,
                                   limpiar=lambda: None, aplicar=aplicar_impuesto)
    assert aplicadas == [{"tipo": "IMPUESTO", "nuevo_nivel": 35.0}]
    assert j1.nivel_impuesto == 35.0  # aplicado de inmediato, no solo encolado
    assert ordenes == []  # el llamador ya la aplico, no debe reaplicarse


def test_menu_estado_actual_refleja_la_orden_recien_aplicada():
    partida, j1 = _partida_un_jugador()

    def aplicar_reclutar(orden):
        if orden["tipo"] == "RECLUTAR":
            partida.provincias[1].tropas_guarnicion += orden["cantidad"]
            j1.oro_tesoro -= orden["cantidad"] * PARAMS.costo_reclutamiento_por_tropa

    salidas = []
    entradas = iter(["", "5", "1", "20", "", "15"])
    menu_ordenes_humano(j1, partida, PARAMS, rng=None,
                         entrada=lambda _prompt="": next(entradas), salida=salidas.append,
                         limpiar=lambda: None, aplicar=aplicar_reclutar)
    # el "Estado actual" impreso tras la orden ya debe mostrar 120, no 100
    assert any("P1: 120 tropas" in l for l in salidas)


def test_menu_muestra_ordenes_del_turno_en_vez_de_resumen_viejo():
    partida, j1 = _partida_un_jugador()
    resumen = ["t=0.002 EV_RECAUDAR_IMPUESTOS J1 +100.00"]
    salidas = []
    entradas = iter(["", "4", "35", "", "15"])
    menu_ordenes_humano(j1, partida, PARAMS, rng=None,
                         entrada=lambda _prompt="": next(entradas), salida=salidas.append,
                         limpiar=lambda: None, resumen=resumen)
    assert any("Tus ordenes de este turno" in l for l in salidas)
    assert any("Ajustar impuesto a 35" in l for l in salidas)


def test_menu_opcion_14_muestra_estado_sin_encolar_orden():
    partida, j1 = _partida_un_jugador()
    salidas = []
    entradas = iter(["", "14", "", "15"])
    ordenes = menu_ordenes_humano(j1, partida, PARAMS, rng=None,
                                   entrada=lambda _prompt="": next(entradas), salida=salidas.append,
                                   limpiar=lambda: None)
    assert ordenes == []
    assert any("Impuesto actual: 20%" in l for l in salidas)


def test_menu_opcion_12_encola_crear_ejercito_desde_guarnicion():
    partida, j1 = _partida_un_jugador()
    entradas = iter(["", "12", "1", "40", "", "15"])
    ordenes = menu_ordenes_humano(j1, partida, PARAMS, rng=None,
                                   entrada=lambda _prompt="": next(entradas), salida=lambda m: None,
                                   limpiar=lambda: None)
    assert ordenes == [{"tipo": "CREAR_EJERCITO", "id_provincia": 1, "cantidad": 40}]


def test_menu_crear_ejercito_sin_guarnicion_suficiente_avisa_y_descarta():
    partida, j1 = _partida_un_jugador()
    salidas = []
    entradas = iter(["", "12", "1", "999", "", "15"])  # solo hay 100 tropas
    ordenes = menu_ordenes_humano(j1, partida, PARAMS, rng=None,
                                   entrada=lambda _prompt="": next(entradas), salida=salidas.append,
                                   limpiar=lambda: None)
    assert ordenes == []
    assert any("solo tiene 100 tropas" in l for l in salidas)


def test_menu_mover_con_ejercito_inexistente_avisa_y_descarta():
    partida, j1 = _partida_un_jugador()
    partida.ejercitos[1] = Ejercito(id_ejercito=1, id_propietario=1, cantidad_fuerza=60, nodo_posicion_id=1)
    salidas = []
    entradas = iter(["", "1", "3", "1", "", "15"])  # id_ejercito=3 no existe
    ordenes = menu_ordenes_humano(j1, partida, PARAMS, rng=None,
                                   entrada=lambda _prompt="": next(entradas), salida=salidas.append,
                                   limpiar=lambda: None)
    assert ordenes == []
    assert any("E3 no existe o no es tuyo" in l for l in salidas)


def test_menu_mover_a_provincia_no_vecina_avisa_y_descarta():
    p1 = Provincia(id_provincia=1, id_propietario=1, poblacion_base=1000, nivel_felicidad=80,
                    nivel_infraestructura=1, tropas_guarnicion=100, nodos_vecinos=[2])
    p2 = Provincia(id_provincia=2, id_propietario=0, poblacion_base=500, nivel_felicidad=50,
                    nivel_infraestructura=0, tropas_guarnicion=10, nodos_vecinos=[1])
    p3 = Provincia(id_provincia=3, id_propietario=0, poblacion_base=500, nivel_felicidad=50,
                    nivel_infraestructura=0, tropas_guarnicion=10, nodos_vecinos=[])
    j1 = Jugador(id_jugador=1, oro_tesoro=500.0, puntos_accion=10.0, nivel_impuesto=20.0,
                 tipo_control=TipoControl.HUMANO, puesto_clasificacion=1, provincias_controladas=[1])
    partida = Partida(objetivo_victoria=ObjetivoVictoria.ANIQUILACION, turno_limite=50,
                       jugadores={1: j1}, provincias={1: p1, 2: p2, 3: p3},
                       ejercitos={1: Ejercito(id_ejercito=1, id_propietario=1, cantidad_fuerza=60,
                                               nodo_posicion_id=1)},
                       jugadores_activos=[1])
    salidas = []
    entradas = iter(["", "1", "1", "3", "", "15"])  # destino=3 no es vecino de P1
    ordenes = menu_ordenes_humano(j1, partida, PARAMS, rng=None,
                                   entrada=lambda _prompt="": next(entradas), salida=salidas.append,
                                   limpiar=lambda: None)
    assert ordenes == []
    assert any("no es vecino" in l for l in salidas)


def test_menu_reclutar_sin_oro_suficiente_avisa_y_descarta():
    partida, j1 = _partida_un_jugador()
    j1.oro_tesoro = 5.0
    salidas = []
    entradas = iter(["", "5", "1", "10", "", "15"])  # 10 tropas * 2.0 = 20 oro, solo tiene 5
    ordenes = menu_ordenes_humano(j1, partida, PARAMS, rng=None,
                                   entrada=lambda _prompt="": next(entradas), salida=salidas.append,
                                   limpiar=lambda: None)
    assert ordenes == []
    assert any("Oro insuficiente" in l for l in salidas)


def test_menu_desmantelar_mas_tropas_de_las_que_hay_avisa_y_descarta():
    partida, j1 = _partida_un_jugador()
    salidas = []
    entradas = iter(["", "10", "1", "999", "", "15"])  # solo hay 100 tropas
    ordenes = menu_ordenes_humano(j1, partida, PARAMS, rng=None,
                                   entrada=lambda _prompt="": next(entradas), salida=salidas.append,
                                   limpiar=lambda: None)
    assert ordenes == []
    assert any("solo tiene 100 tropas" in l for l in salidas)


def test_menu_abandonar_provincia_con_rey_avisa_y_descarta():
    partida, j1 = _partida_un_jugador()
    partida.provincias[1].tiene_rey = True
    salidas = []
    entradas = iter(["", "9", "1", "", "15"])
    ordenes = menu_ordenes_humano(j1, partida, PARAMS, rng=None,
                                   entrada=lambda _prompt="": next(entradas), salida=salidas.append,
                                   limpiar=lambda: None)
    assert ordenes == []
    assert any("contiene a tu rey" in l for l in salidas)


def test_menu_guerra_contra_uno_mismo_avisa_y_descarta():
    partida, j1 = _partida_un_jugador()
    salidas = []
    entradas = iter(["", "8", "1", "", "15"])
    ordenes = menu_ordenes_humano(j1, partida, PARAMS, rng=None,
                                   entrada=lambda _prompt="": next(entradas), salida=salidas.append,
                                   limpiar=lambda: None)
    assert ordenes == []
    assert any("no puedes declararte la guerra a ti mismo" in l.lower() for l in salidas)


def test_menu_flechas_navega_y_selecciona_pasar_turno():
    partida, j1 = _partida_un_jugador()
    salidas = []
    # Pasar turno es item de primer nivel, tras las 4 categorias (indice 4)
    teclas = iter(["ABAJO", "ABAJO", "ABAJO", "ABAJO", "ENTER"])
    entradas_texto = iter(["", ""])  # Enter inicial + Enter final de "continuar"
    ordenes = menu_ordenes_humano(j1, partida, PARAMS, rng=None,
                                   entrada=lambda _prompt="": next(entradas_texto), salida=salidas.append,
                                   limpiar=lambda: None, leer_tecla=lambda: next(teclas))
    assert ordenes == []
    assert any("Pasar turno" in l for l in salidas)


def test_menu_flechas_selecciona_ajustar_impuestos():
    partida, j1 = _partida_un_jugador()
    salidas = []
    # categoria Sistema = indice 3; dentro de Sistema, Ajustar impuestos = indice 0 (default, solo ENTER);
    # el indice se reinicia en cada vuelta del menu, asi que la 2da vez hay que re-entrar a Sistema
    # y bajar hasta Pasar turno (indice 3)
    teclas = iter(["ABAJO", "ABAJO", "ABAJO", "ENTER", "ENTER"]
                  + ["ABAJO", "ABAJO", "ABAJO", "ABAJO", "ENTER"])
    entradas_texto = iter(["", "35", ""])  # Enter inicial, nuevo nivel, Enter tras la orden
    ordenes = menu_ordenes_humano(j1, partida, PARAMS, rng=None,
                                   entrada=lambda _prompt="": next(entradas_texto), salida=salidas.append,
                                   limpiar=lambda: None, leer_tecla=lambda: next(teclas))
    assert ordenes == [{"tipo": "IMPUESTO", "nuevo_nivel": 35.0}]


def test_menu_flechas_mover_selecciona_ejercito_y_destino():
    p1 = Provincia(id_provincia=1, id_propietario=1, poblacion_base=1000, nivel_felicidad=80,
                    nivel_infraestructura=1, tropas_guarnicion=100, nodos_vecinos=[2, 3])
    p2 = Provincia(id_provincia=2, id_propietario=0, poblacion_base=500, nivel_felicidad=50,
                    nivel_infraestructura=0, tropas_guarnicion=10, nodos_vecinos=[1])
    p3 = Provincia(id_provincia=3, id_propietario=0, poblacion_base=500, nivel_felicidad=50,
                    nivel_infraestructura=0, tropas_guarnicion=10, nodos_vecinos=[1])
    j1 = Jugador(id_jugador=1, oro_tesoro=500.0, puntos_accion=10.0, nivel_impuesto=20.0,
                 tipo_control=TipoControl.HUMANO, puesto_clasificacion=1, provincias_controladas=[1])
    partida = Partida(objetivo_victoria=ObjetivoVictoria.ANIQUILACION, turno_limite=50,
                       jugadores={1: j1}, provincias={1: p1, 2: p2, 3: p3},
                       ejercitos={1: Ejercito(id_ejercito=1, id_propietario=1, cantidad_fuerza=60,
                                               nodo_posicion_id=1)},
                       jugadores_activos=[1])
    salidas = []
    # categoria Ejercitos = indice0 (default); dentro, Mover = indice0 (default);
    # ejercito: 1 solo item (ENTER); destino: 1 ABAJO -> P3 (ENTER); cantidad: Enter = mover todas;
    # menu de nuevo: Sistema(3 ABAJO) -> Pasar turno(3 ABAJO)
    teclas = iter(["ENTER"] + ["ENTER"] + ["ENTER"] + ["ABAJO", "ENTER"]
                  + ["ABAJO", "ABAJO", "ABAJO", "ABAJO", "ENTER"])
    entradas_texto = iter(["", "", ""])  # Enter inicial, cantidad (Enter=todas), Enter tras la orden
    ordenes = menu_ordenes_humano(j1, partida, PARAMS, rng=None,
                                   entrada=lambda _prompt="": next(entradas_texto), salida=salidas.append,
                                   limpiar=lambda: None, leer_tecla=lambda: next(teclas))
    assert ordenes == [{"tipo": "MOVER", "id_ejercito": 1, "provincia_destino": 3}]


def test_menu_flechas_mover_con_cantidad_parcial():
    p1 = Provincia(id_provincia=1, id_propietario=1, poblacion_base=1000, nivel_felicidad=80,
                    nivel_infraestructura=1, tropas_guarnicion=100, nodos_vecinos=[2])
    p2 = Provincia(id_provincia=2, id_propietario=0, poblacion_base=500, nivel_felicidad=50,
                    nivel_infraestructura=0, tropas_guarnicion=10, nodos_vecinos=[1])
    j1 = Jugador(id_jugador=1, oro_tesoro=500.0, puntos_accion=10.0, nivel_impuesto=20.0,
                 tipo_control=TipoControl.HUMANO, puesto_clasificacion=1, provincias_controladas=[1])
    partida = Partida(objetivo_victoria=ObjetivoVictoria.ANIQUILACION, turno_limite=50,
                       jugadores={1: j1}, provincias={1: p1, 2: p2},
                       ejercitos={1: Ejercito(id_ejercito=1, id_propietario=1, cantidad_fuerza=60,
                                               nodo_posicion_id=1)},
                       jugadores_activos=[1])
    salidas = []
    # Ejercitos(ENTER) -> Mover(ENTER) -> ejercito unico(ENTER) -> destino unico P2(ENTER)
    teclas = iter(["ENTER", "ENTER", "ENTER", "ENTER"]
                  + ["ABAJO", "ABAJO", "ABAJO", "ABAJO", "ENTER"])
    entradas_texto = iter(["", "25", ""])  # Enter inicial, cantidad parcial, Enter tras la orden
    ordenes = menu_ordenes_humano(j1, partida, PARAMS, rng=None,
                                   entrada=lambda _prompt="": next(entradas_texto), salida=salidas.append,
                                   limpiar=lambda: None, leer_tecla=lambda: next(teclas))
    assert ordenes == [{"tipo": "MOVER", "id_ejercito": 1, "provincia_destino": 2, "cantidad": 25}]


def test_menu_flechas_fortificar_excluye_provincias_ya_fortificadas():
    p1 = Provincia(id_provincia=1, id_propietario=1, poblacion_base=1000, nivel_felicidad=80,
                    nivel_infraestructura=1, tropas_guarnicion=100, nodos_vecinos=[], fortificada=False)
    p2 = Provincia(id_provincia=2, id_propietario=1, poblacion_base=1000, nivel_felicidad=80,
                    nivel_infraestructura=1, tropas_guarnicion=100, nodos_vecinos=[], fortificada=True)
    j1 = Jugador(id_jugador=1, oro_tesoro=500.0, puntos_accion=10.0, nivel_impuesto=20.0,
                 tipo_control=TipoControl.HUMANO, puesto_clasificacion=1, provincias_controladas=[1, 2])
    partida = Partida(objetivo_victoria=ObjetivoVictoria.ANIQUILACION, turno_limite=50,
                       jugadores={1: j1}, provincias={1: p1, 2: p2}, ejercitos={}, jugadores_activos=[1])
    salidas = []
    # categoria Provincias = indice1; dentro, Fortificar = indice1; provincias solo tiene P1 (ENTER);
    # menu de nuevo: Sistema(3 ABAJO) -> Pasar turno(3 ABAJO)
    teclas = iter(["ABAJO", "ENTER", "ABAJO", "ENTER"] + ["ENTER"]
                  + ["ABAJO", "ABAJO", "ABAJO", "ABAJO", "ENTER"])
    entradas_texto = iter(["", ""])
    ordenes = menu_ordenes_humano(j1, partida, PARAMS, rng=None,
                                   entrada=lambda _prompt="": next(entradas_texto), salida=salidas.append,
                                   limpiar=lambda: None, leer_tecla=lambda: next(teclas))
    assert ordenes == [{"tipo": "FORTIFICAR", "id_provincia": 1}]


def test_menu_flechas_abandonar_excluye_provincia_del_rey():
    p1 = Provincia(id_provincia=1, id_propietario=1, poblacion_base=1000, nivel_felicidad=80,
                    nivel_infraestructura=1, tropas_guarnicion=100, nodos_vecinos=[], tiene_rey=True)
    p2 = Provincia(id_provincia=2, id_propietario=1, poblacion_base=1000, nivel_felicidad=80,
                    nivel_infraestructura=1, tropas_guarnicion=100, nodos_vecinos=[], tiene_rey=False)
    j1 = Jugador(id_jugador=1, oro_tesoro=500.0, puntos_accion=10.0, nivel_impuesto=20.0,
                 tipo_control=TipoControl.HUMANO, puesto_clasificacion=1, provincias_controladas=[1, 2])
    partida = Partida(objetivo_victoria=ObjetivoVictoria.ANIQUILACION, turno_limite=50,
                       jugadores={1: j1}, provincias={1: p1, 2: p2}, ejercitos={}, jugadores_activos=[1])
    salidas = []
    # categoria Provincias = indice1; dentro, Abandonar = indice3; provincias solo tiene P2 (ENTER);
    # menu de nuevo: Sistema(3 ABAJO) -> Pasar turno(3 ABAJO)
    teclas = iter(["ABAJO", "ENTER", "ABAJO", "ABAJO", "ABAJO", "ENTER"] + ["ENTER"]
                  + ["ABAJO", "ABAJO", "ABAJO", "ABAJO", "ENTER"])
    entradas_texto = iter(["", ""])
    ordenes = menu_ordenes_humano(j1, partida, PARAMS, rng=None,
                                   entrada=lambda _prompt="": next(entradas_texto), salida=salidas.append,
                                   limpiar=lambda: None, leer_tecla=lambda: next(teclas))
    assert ordenes == [{"tipo": "ABANDONAR", "id_provincia": 2}]


def test_menu_flechas_guerra_selecciona_jugador_sin_escribir_id():
    p1 = Provincia(id_provincia=1, id_propietario=1, poblacion_base=1000, nivel_felicidad=80,
                    nivel_infraestructura=1, tropas_guarnicion=100, nodos_vecinos=[])
    j1 = Jugador(id_jugador=1, oro_tesoro=500.0, puntos_accion=10.0, nivel_impuesto=20.0,
                 tipo_control=TipoControl.HUMANO, puesto_clasificacion=1, provincias_controladas=[1])
    j2 = Jugador(id_jugador=2, oro_tesoro=500.0, puntos_accion=10.0, nivel_impuesto=20.0,
                 tipo_control=TipoControl.IA, puesto_clasificacion=2, provincias_controladas=[])
    partida = Partida(objetivo_victoria=ObjetivoVictoria.ANIQUILACION, turno_limite=50,
                       jugadores={1: j1, 2: j2}, provincias={1: p1}, ejercitos={}, jugadores_activos=[1, 2])
    salidas = []
    # categoria Diplomacia = indice2; dentro, Declarar guerra = indice0 (default, solo ENTER);
    # lista de jugadores solo tiene J2 (ENTER); menu de nuevo: Sistema(3 ABAJO) -> Pasar turno(3 ABAJO)
    teclas = iter(["ABAJO", "ABAJO", "ENTER", "ENTER"] + ["ENTER"]
                  + ["ABAJO", "ABAJO", "ABAJO", "ABAJO", "ENTER"])
    entradas_texto = iter(["", ""])
    ordenes = menu_ordenes_humano(j1, partida, PARAMS, rng=None,
                                   entrada=lambda _prompt="": next(entradas_texto), salida=salidas.append,
                                   limpiar=lambda: None, leer_tecla=lambda: next(teclas))
    assert ordenes == [{"tipo": "GUERRA", "id_objetivo": 2}]


def test_menu_deshacer_sin_ordenes_avisa_y_no_falla():
    partida, j1 = _partida_un_jugador()
    salidas = []
    entradas = iter(["", "13", "", "15"])
    ordenes = menu_ordenes_humano(j1, partida, PARAMS, rng=None,
                                   entrada=lambda _prompt="": next(entradas), salida=salidas.append,
                                   limpiar=lambda: None)
    assert ordenes == []
    assert any("No tienes ordenes para deshacer" in l for l in salidas)


def test_menu_deshacer_numerico_quita_la_orden_encolada():
    partida, j1 = _partida_un_jugador()
    salidas = []
    # 4=Ajustar impuestos a 35, 13=Deshacer la orden #1, 15=Pasar turno
    entradas = iter(["", "4", "35", "", "13", "1", "", "15"])
    ordenes = menu_ordenes_humano(j1, partida, PARAMS, rng=None,
                                   entrada=lambda _prompt="": next(entradas), salida=salidas.append,
                                   limpiar=lambda: None)
    assert ordenes == []
    assert any("Orden deshecha: Ajustar impuesto a 35%" in l for l in salidas)


def test_menu_flechas_deshacer_quita_la_orden_seleccionada():
    partida, j1 = _partida_un_jugador()
    salidas = []
    # categoria Sistema = indice3; dentro: Ajustar impuestos = indice0 (ENTER);
    # 2da vuelta: Sistema de nuevo, Deshacer = indice1; lista de ordenes: 1 sola (ENTER);
    # 3ra vuelta: Sistema de nuevo, Pasar turno = indice3
    teclas = iter(["ABAJO", "ABAJO", "ABAJO", "ENTER", "ENTER"]
                  + ["ABAJO", "ABAJO", "ABAJO", "ENTER", "ABAJO", "ENTER"]
                  + ["ENTER"]
                  + ["ABAJO", "ABAJO", "ABAJO", "ABAJO", "ENTER"])
    entradas_texto = iter(["", "35", "", ""])  # Enter inicial, valor, Enter tras ajustar, Enter tras deshacer
    ordenes = menu_ordenes_humano(j1, partida, PARAMS, rng=None,
                                   entrada=lambda _prompt="": next(entradas_texto), salida=salidas.append,
                                   limpiar=lambda: None, leer_tecla=lambda: next(teclas))
    assert ordenes == []
    assert any("Orden deshecha: Ajustar impuesto a 35%" in l for l in salidas)


def test_menu_loguea_seleccion_de_opcion_y_orden_encolada_antes_de_pasar_turno():
    partida, j1 = _partida_un_jugador()
    logs = []
    entradas = iter(["", "4", "35", "", "15"])
    menu_ordenes_humano(j1, partida, PARAMS, rng=None,
                         entrada=lambda _prompt="": next(entradas), salida=lambda m: None,
                         limpiar=lambda: None, log=logs.append)
    assert any("elige: Ajustar impuestos" in l for l in logs)
    assert any("encola orden" in l and "Ajustar impuesto a 35%" in l for l in logs)
    assert any("elige: Pasar turno" in l for l in logs)


def test_menu_salir_del_juego_confirmado_lanza_excepcion():
    partida, j1 = _partida_un_jugador()
    entradas = iter(["", "0", "s"])
    with pytest.raises(SalirDelJuego):
        menu_ordenes_humano(j1, partida, PARAMS, rng=None,
                             entrada=lambda _prompt="": next(entradas), salida=lambda m: None,
                             limpiar=lambda: None)


def test_menu_salir_del_juego_cancelado_sigue_en_el_turno():
    partida, j1 = _partida_un_jugador()
    salidas = []
    entradas = iter(["", "0", "n", "15"])
    ordenes = menu_ordenes_humano(j1, partida, PARAMS, rng=None,
                                   entrada=lambda _prompt="": next(entradas), salida=salidas.append,
                                   limpiar=lambda: None)
    assert ordenes == []
    assert any("Cancelado" in l for l in salidas)


def test_menu_flechas_salir_del_juego_confirmado_lanza_excepcion():
    partida, j1 = _partida_un_jugador()
    # Sistema=3 categorias, Pasar turno=indice4, Salir=indice5 (5 ABAJO desde indice0)
    teclas = iter(["ABAJO", "ABAJO", "ABAJO", "ABAJO", "ABAJO", "ENTER"])
    entradas_texto = iter(["", "s"])
    with pytest.raises(SalirDelJuego):
        menu_ordenes_humano(j1, partida, PARAMS, rng=None,
                             entrada=lambda _prompt="": next(entradas_texto), salida=lambda m: None,
                             limpiar=lambda: None, leer_tecla=lambda: next(teclas))


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
