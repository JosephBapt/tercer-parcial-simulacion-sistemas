from types import SimpleNamespace
from aoc_sim.models import Partida, Jugador, Provincia, Ejercito, TipoControl, ObjetivoVictoria, SIN_DUENO
from aoc_sim.engine import aplicar_orden

PARAMS = SimpleNamespace(
    b_fort=1.0, b_rey_atk=1.0, b_rey_def=0.30, p_barco=0.30, p_conquista=25,
    costo_reclutamiento_por_tropa=2.0, costo_fortificacion=100.0,
    costo_decreto=50.0, delta_decreto_felicidad=10.0, costo_infraestructura=200.0,
)


def _partida_dos_jugadores():
    p1 = Provincia(id_provincia=1, id_propietario=1, poblacion_base=10000, nivel_felicidad=80,
                    nivel_infraestructura=1, tropas_guarnicion=100, nodos_vecinos=[2], tiene_rey=True)
    p2 = Provincia(id_provincia=2, id_propietario=2, poblacion_base=1000, nivel_felicidad=80,
                    nivel_infraestructura=1, tropas_guarnicion=20, nodos_vecinos=[1])
    j1 = Jugador(id_jugador=1, oro_tesoro=500.0, puntos_accion=10.0, nivel_impuesto=20.0,
                 tipo_control=TipoControl.HUMANO, puesto_clasificacion=1, provincias_controladas=[1])
    j2 = Jugador(id_jugador=2, oro_tesoro=500.0, puntos_accion=10.0, nivel_impuesto=20.0,
                 tipo_control=TipoControl.IA, puesto_clasificacion=2, provincias_controladas=[2])
    ej1 = Ejercito(id_ejercito=1, id_propietario=1, cantidad_fuerza=60, nodo_posicion_id=1)
    partida = Partida(
        objetivo_victoria=ObjetivoVictoria.ANIQUILACION, turno_limite=50,
        jugadores={1: j1, 2: j2}, provincias={1: p1, 2: p2}, ejercitos={1: ej1},
        jugadores_activos=[1, 2],
    )
    return partida, j1


def test_orden_impuesto_ajusta_nivel():
    partida, j1 = _partida_dos_jugadores()
    aplicar_orden(partida, PARAMS, j1, {"tipo": "IMPUESTO", "nuevo_nivel": 55.0}, None, log=lambda m: None)
    assert j1.nivel_impuesto == 55.0


def test_orden_reclutar_descuenta_oro_y_suma_tropas():
    partida, j1 = _partida_dos_jugadores()
    aplicar_orden(partida, PARAMS, j1, {"tipo": "RECLUTAR", "id_provincia": 1, "cantidad": 20}, None, log=lambda m: None)
    assert j1.oro_tesoro == 460.0
    assert partida.provincias[1].tropas_guarnicion == 120
    assert partida.provincias[1].poblacion_base == 8000  # 10000 - 20*100


def test_orden_reclutar_sin_poblacion_suficiente_no_hace_nada():
    partida, j1 = _partida_dos_jugadores()
    partida.provincias[1].poblacion_base = 500  # alcanza para 5 tropas, no para 20
    aplicar_orden(partida, PARAMS, j1, {"tipo": "RECLUTAR", "id_provincia": 1, "cantidad": 20}, None, log=lambda m: None)
    assert j1.oro_tesoro == 500.0
    assert partida.provincias[1].tropas_guarnicion == 100
    assert partida.provincias[1].poblacion_base == 500


def test_orden_reclutar_cantidad_negativa_no_hace_nada():
    partida, j1 = _partida_dos_jugadores()
    oro_antes = j1.oro_tesoro
    aplicar_orden(partida, PARAMS, j1, {"tipo": "RECLUTAR", "id_provincia": 1, "cantidad": -100}, None, log=lambda m: None)
    assert j1.oro_tesoro == oro_antes
    assert partida.provincias[1].tropas_guarnicion == 100


def test_orden_desmantelar_cantidad_negativa_no_hace_nada():
    partida, j1 = _partida_dos_jugadores()
    aplicar_orden(partida, PARAMS, j1, {"tipo": "DESMANTELAR", "id_provincia": 1, "cantidad": -30}, None, log=lambda m: None)
    assert partida.provincias[1].tropas_guarnicion == 100


def test_orden_reclutar_sin_oro_suficiente_no_hace_nada():
    partida, j1 = _partida_dos_jugadores()
    j1.oro_tesoro = 5.0
    aplicar_orden(partida, PARAMS, j1, {"tipo": "RECLUTAR", "id_provincia": 1, "cantidad": 20}, None, log=lambda m: None)
    assert j1.oro_tesoro == 5.0
    assert partida.provincias[1].tropas_guarnicion == 100


def test_orden_fortificar():
    partida, j1 = _partida_dos_jugadores()
    aplicar_orden(partida, PARAMS, j1, {"tipo": "FORTIFICAR", "id_provincia": 1}, None, log=lambda m: None)
    assert partida.provincias[1].fortificada is True
    assert j1.oro_tesoro == 400.0


def test_orden_mover_a_provincia_propia_refuerza():
    partida, j1 = _partida_dos_jugadores()
    partida.provincias[2].id_propietario = 1
    j1.provincias_controladas.append(2)
    aplicar_orden(partida, PARAMS, j1, {"tipo": "MOVER", "id_ejercito": 1, "provincia_destino": 2}, None, log=lambda m: None)
    assert partida.provincias[2].tropas_guarnicion == 80  # 20+60
    assert 1 not in partida.ejercitos  # se absorbe en la guarnicion, no queda duplicado


def test_orden_mover_a_provincia_enemiga_resuelve_combate_y_transfiere():
    partida, j1 = _partida_dos_jugadores()
    aplicar_orden(partida, PARAMS, j1, {"tipo": "MOVER", "id_ejercito": 1, "provincia_destino": 2}, None, log=lambda m: None)
    assert partida.provincias[2].id_propietario == 1
    assert 2 in j1.provincias_controladas
    assert 2 not in partida.jugadores[2].provincias_controladas
    assert 1 not in partida.ejercitos  # se absorbe como guarnicion, no queda como unidad movil


def test_orden_mover_cantidad_parcial_refuerza_y_deja_remanente_en_origen():
    partida, j1 = _partida_dos_jugadores()
    partida.provincias[2].id_propietario = 1
    j1.provincias_controladas.append(2)
    aplicar_orden(partida, PARAMS, j1,
                   {"tipo": "MOVER", "id_ejercito": 1, "provincia_destino": 2, "cantidad": 25},
                   None, log=lambda m: None)
    assert partida.provincias[2].tropas_guarnicion == 45  # 20+25
    assert 1 in partida.ejercitos  # el ejercito original sigue existiendo con el resto
    assert partida.ejercitos[1].cantidad_fuerza == 35  # 60-25
    assert partida.ejercitos[1].nodo_posicion_id == 1


def test_orden_mover_cantidad_parcial_ataca_con_solo_esa_fuerza():
    partida, j1 = _partida_dos_jugadores()
    aplicar_orden(partida, PARAMS, j1,
                   {"tipo": "MOVER", "id_ejercito": 1, "provincia_destino": 2, "cantidad": 25},
                   None, log=lambda m: None)
    # Fa=25 < Fd=20*1(sin bono) -> en realidad Fa=25 > Fd=20, gana atacante igual con solo 25 de fuerza
    assert partida.provincias[2].id_propietario == 1
    assert 1 in partida.ejercitos  # el ejercito original conserva el resto en P1
    assert partida.ejercitos[1].cantidad_fuerza == 35  # 60-25
    assert partida.ejercitos[1].nodo_posicion_id == 1


def test_orden_mover_cantidad_mayor_o_igual_a_la_fuerza_mueve_todo():
    partida, j1 = _partida_dos_jugadores()
    partida.provincias[2].id_propietario = 1
    j1.provincias_controladas.append(2)
    aplicar_orden(partida, PARAMS, j1,
                   {"tipo": "MOVER", "id_ejercito": 1, "provincia_destino": 2, "cantidad": 999},
                   None, log=lambda m: None)
    assert partida.provincias[2].tropas_guarnicion == 80  # 20+60, se movio todo
    assert 1 not in partida.ejercitos


def test_orden_mover_a_no_vecino_no_hace_nada():
    partida, j1 = _partida_dos_jugadores()
    partida.provincias[1].nodos_vecinos = []
    aplicar_orden(partida, PARAMS, j1, {"tipo": "MOVER", "id_ejercito": 1, "provincia_destino": 2}, None, log=lambda m: None)
    assert partida.provincias[2].id_propietario == 2


def test_orden_mover_perdiendo_elimina_ejercito():
    partida, j1 = _partida_dos_jugadores()
    partida.provincias[2].tropas_guarnicion = 500
    aplicar_orden(partida, PARAMS, j1, {"tipo": "MOVER", "id_ejercito": 1, "provincia_destino": 2}, None, log=lambda m: None)
    assert 1 not in partida.ejercitos


def test_orden_mover_venciendo_rey_defensor_elimina_jugador():
    partida, j1 = _partida_dos_jugadores()
    partida.provincias[2].tiene_rey = True
    partida.provincias[2].tropas_guarnicion = 10
    aplicar_orden(partida, PARAMS, j1, {"tipo": "MOVER", "id_ejercito": 1, "provincia_destino": 2}, None, log=lambda m: None)
    assert 2 not in partida.jugadores_activos
    assert partida.jugadores[2].rey_vivo is False


def test_orden_abandonar():
    partida, j1 = _partida_dos_jugadores()
    partida.provincias[1].tiene_rey = False
    aplicar_orden(partida, PARAMS, j1, {"tipo": "ABANDONAR", "id_provincia": 1}, None, log=lambda m: None)
    assert partida.provincias[1].id_propietario == SIN_DUENO
    assert 1 not in j1.provincias_controladas


def test_orden_abandonar_provincia_con_rey_es_rechazada():
    partida, j1 = _partida_dos_jugadores()
    aplicar_orden(partida, PARAMS, j1, {"tipo": "ABANDONAR", "id_provincia": 1}, None, log=lambda m: None)
    assert partida.provincias[1].id_propietario == 1
    assert 1 in j1.provincias_controladas


def test_orden_desmantelar():
    partida, j1 = _partida_dos_jugadores()
    aplicar_orden(partida, PARAMS, j1, {"tipo": "DESMANTELAR", "id_provincia": 1, "cantidad": 30}, None, log=lambda m: None)
    assert partida.provincias[1].tropas_guarnicion == 70


def test_orden_guerra_marca_relacion_bidireccional():
    partida, j1 = _partida_dos_jugadores()
    aplicar_orden(partida, PARAMS, j1, {"tipo": "GUERRA", "id_objetivo": 2}, None, log=lambda m: None)
    assert j1.relaciones_diplomaticas[2] == "GUERRA"
    assert partida.jugadores[2].relaciones_diplomaticas[1] == "GUERRA"


def test_orden_guerra_aplica_golpe_inmediato_de_felicidad():
    partida, j1 = _partida_dos_jugadores()
    partida.provincias[1].nivel_felicidad = 80.0
    aplicar_orden(partida, PARAMS, j1, {"tipo": "GUERRA", "id_objetivo": 2}, None, log=lambda m: None)
    assert partida.provincias[1].nivel_felicidad == 64.0  # 80 - 16


def test_orden_guerra_golpe_de_felicidad_no_baja_de_cero():
    partida, j1 = _partida_dos_jugadores()
    partida.provincias[1].nivel_felicidad = 10.0
    aplicar_orden(partida, PARAMS, j1, {"tipo": "GUERRA", "id_objetivo": 2}, None, log=lambda m: None)
    assert partida.provincias[1].nivel_felicidad == 0.0


def test_orden_consume_puntos_de_accion():
    partida, j1 = _partida_dos_jugadores()
    j1.puntos_accion = 10.0
    aplicar_orden(partida, PARAMS, j1, {"tipo": "FORTIFICAR", "id_provincia": 1}, None, log=lambda m: None)
    assert j1.puntos_accion == 9.5  # 10 - 0.5
    assert partida.provincias[1].fortificada is True


def test_orden_sin_puntos_de_accion_suficientes_se_descarta():
    partida, j1 = _partida_dos_jugadores()
    j1.puntos_accion = 0.0
    aplicar_orden(partida, PARAMS, j1, {"tipo": "FORTIFICAR", "id_provincia": 1}, None, log=lambda m: None)
    assert j1.puntos_accion == 0.0
    assert partida.provincias[1].fortificada is False
    assert j1.oro_tesoro == 500.0  # tampoco se cobro el oro


def test_orden_guerra_id_objetivo_inexistente_no_crashea():
    partida, j1 = _partida_dos_jugadores()
    aplicar_orden(partida, PARAMS, j1, {"tipo": "GUERRA", "id_objetivo": 999}, None, log=lambda m: None)
    assert 999 not in j1.relaciones_diplomaticas


def test_orden_guerra_a_si_mismo_no_hace_nada():
    partida, j1 = _partida_dos_jugadores()
    aplicar_orden(partida, PARAMS, j1, {"tipo": "GUERRA", "id_objetivo": 1}, None, log=lambda m: None)
    assert 1 not in j1.relaciones_diplomaticas


def test_orden_reclutar_id_provincia_inexistente_no_crashea():
    partida, j1 = _partida_dos_jugadores()
    aplicar_orden(partida, PARAMS, j1, {"tipo": "RECLUTAR", "id_provincia": 999, "cantidad": 10},
                  None, log=lambda m: None)
    assert j1.oro_tesoro == 500.0


def test_orden_fortificar_id_provincia_inexistente_no_crashea():
    partida, j1 = _partida_dos_jugadores()
    aplicar_orden(partida, PARAMS, j1, {"tipo": "FORTIFICAR", "id_provincia": 999}, None, log=lambda m: None)
    assert j1.oro_tesoro == 500.0


def test_orden_decreto_id_provincia_inexistente_no_crashea():
    partida, j1 = _partida_dos_jugadores()
    aplicar_orden(partida, PARAMS, j1, {"tipo": "DECRETO_FELICIDAD", "id_provincia": 999}, None, log=lambda m: None)
    assert j1.oro_tesoro == 500.0


def test_orden_abandonar_id_provincia_inexistente_no_crashea():
    partida, j1 = _partida_dos_jugadores()
    aplicar_orden(partida, PARAMS, j1, {"tipo": "ABANDONAR", "id_provincia": 999}, None, log=lambda m: None)
    assert 999 not in j1.provincias_controladas


def test_orden_desmantelar_id_provincia_inexistente_no_crashea():
    partida, j1 = _partida_dos_jugadores()
    aplicar_orden(partida, PARAMS, j1, {"tipo": "DESMANTELAR", "id_provincia": 999, "cantidad": 10},
                  None, log=lambda m: None)
    assert partida.provincias[1].tropas_guarnicion == 100


def test_orden_reclutar_provincia_ajena_no_hace_nada():
    partida, j1 = _partida_dos_jugadores()
    aplicar_orden(partida, PARAMS, j1, {"tipo": "RECLUTAR", "id_provincia": 2, "cantidad": 10},
                  None, log=lambda m: None)
    assert j1.oro_tesoro == 500.0
    assert partida.provincias[2].tropas_guarnicion == 20


def test_orden_decreto_felicidad():
    partida, j1 = _partida_dos_jugadores()
    aplicar_orden(partida, PARAMS, j1, {"tipo": "DECRETO_FELICIDAD", "id_provincia": 1}, None, log=lambda m: None)
    assert partida.provincias[1].nivel_felicidad == 90.0
    assert j1.oro_tesoro == 450.0


def test_orden_reforzar_ejercito_mueve_tropas_de_guarnicion_a_fuerza():
    partida, j1 = _partida_dos_jugadores()
    aplicar_orden(partida, PARAMS, j1, {"tipo": "REFORZAR_EJERCITO", "id_ejercito": 1, "cantidad": 30},
                  None, log=lambda m: None)
    assert partida.ejercitos[1].cantidad_fuerza == 90  # 60+30
    assert partida.provincias[1].tropas_guarnicion == 70  # 100-30


def test_orden_reforzar_ejercito_sin_guarnicion_suficiente_no_hace_nada():
    partida, j1 = _partida_dos_jugadores()
    aplicar_orden(partida, PARAMS, j1, {"tipo": "REFORZAR_EJERCITO", "id_ejercito": 1, "cantidad": 500},
                  None, log=lambda m: None)
    assert partida.ejercitos[1].cantidad_fuerza == 60
    assert partida.provincias[1].tropas_guarnicion == 100


def test_orden_reforzar_ejercito_cantidad_negativa_no_hace_nada():
    partida, j1 = _partida_dos_jugadores()
    aplicar_orden(partida, PARAMS, j1, {"tipo": "REFORZAR_EJERCITO", "id_ejercito": 1, "cantidad": -10},
                  None, log=lambda m: None)
    assert partida.ejercitos[1].cantidad_fuerza == 60
    assert partida.provincias[1].tropas_guarnicion == 100


def test_orden_reforzar_ejercito_en_provincia_ajena_no_hace_nada():
    partida, j1 = _partida_dos_jugadores()
    partida.ejercitos[1].nodo_posicion_id = 2  # quedo parado en territorio de J2
    aplicar_orden(partida, PARAMS, j1, {"tipo": "REFORZAR_EJERCITO", "id_ejercito": 1, "cantidad": 5},
                  None, log=lambda m: None)
    assert partida.ejercitos[1].cantidad_fuerza == 60
    assert partida.provincias[2].tropas_guarnicion == 20


def test_orden_reforzar_ejercito_ajeno_no_hace_nada():
    partida, j1 = _partida_dos_jugadores()
    partida.ejercitos[2] = Ejercito(id_ejercito=2, id_propietario=2, cantidad_fuerza=10, nodo_posicion_id=2)
    aplicar_orden(partida, PARAMS, j1, {"tipo": "REFORZAR_EJERCITO", "id_ejercito": 2, "cantidad": 5},
                  None, log=lambda m: None)
    assert partida.ejercitos[2].cantidad_fuerza == 10
    assert partida.provincias[2].tropas_guarnicion == 20


def test_orden_invertir_infraestructura_sube_nivel_y_cobra():
    partida, j1 = _partida_dos_jugadores()
    aplicar_orden(partida, PARAMS, j1, {"tipo": "INVERTIR_INFRAESTRUCTURA", "id_provincia": 1},
                  None, log=lambda m: None)
    assert partida.provincias[1].nivel_infraestructura == 2
    assert j1.oro_tesoro == 300.0


def test_orden_invertir_infraestructura_sin_oro_no_hace_nada():
    partida, j1 = _partida_dos_jugadores()
    j1.oro_tesoro = 50.0
    aplicar_orden(partida, PARAMS, j1, {"tipo": "INVERTIR_INFRAESTRUCTURA", "id_provincia": 1},
                  None, log=lambda m: None)
    assert partida.provincias[1].nivel_infraestructura == 1
    assert j1.oro_tesoro == 50.0


def test_orden_dividir_ejercito_crea_nuevo_ejercito():
    partida, j1 = _partida_dos_jugadores()
    aplicar_orden(partida, PARAMS, j1, {"tipo": "DIVIDIR_EJERCITO", "id_ejercito": 1, "cantidad": 20},
                  None, log=lambda m: None)
    assert partida.ejercitos[1].cantidad_fuerza == 40
    nuevo = next(e for e in partida.ejercitos.values() if e.id_ejercito != 1)
    assert nuevo.cantidad_fuerza == 20
    assert nuevo.nodo_posicion_id == 1
    assert nuevo.id_propietario == 1


def test_orden_dividir_ejercito_cantidad_igual_a_fuerza_total_no_hace_nada():
    partida, j1 = _partida_dos_jugadores()
    aplicar_orden(partida, PARAMS, j1, {"tipo": "DIVIDIR_EJERCITO", "id_ejercito": 1, "cantidad": 60},
                  None, log=lambda m: None)
    assert len(partida.ejercitos) == 1
    assert partida.ejercitos[1].cantidad_fuerza == 60


def test_orden_dividir_ejercito_ajeno_no_hace_nada():
    partida, j1 = _partida_dos_jugadores()
    partida.ejercitos[2] = Ejercito(id_ejercito=2, id_propietario=2, cantidad_fuerza=10, nodo_posicion_id=2)
    aplicar_orden(partida, PARAMS, j1, {"tipo": "DIVIDIR_EJERCITO", "id_ejercito": 2, "cantidad": 5},
                  None, log=lambda m: None)
    assert len(partida.ejercitos) == 2
    assert partida.ejercitos[2].cantidad_fuerza == 10


def test_orden_pasar_no_hace_nada():
    partida, j1 = _partida_dos_jugadores()
    oro_antes = j1.oro_tesoro
    aplicar_orden(partida, PARAMS, j1, {"tipo": "PASAR"}, None, log=lambda m: None)
    assert j1.oro_tesoro == oro_antes
