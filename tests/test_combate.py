from types import SimpleNamespace
from aoc_sim.models import Ejercito, Jugador, Partida, Provincia, TipoControl, ObjetivoVictoria
from aoc_sim.engine import calcular_desercion, resolver_combate

PARAMS = SimpleNamespace(b_fort=1.0, b_rey_atk=1.0, b_rey_def=0.30, p_barco=0.30, p_conquista=25, p_terr=0.13)


def _ejercito(cantidad_fuerza, rey=False, barco=False):
    return Ejercito(id_ejercito=1, id_propietario=1, cantidad_fuerza=cantidad_fuerza,
                     nodo_posicion_id=1, contiene_rey=rey, desde_barco=barco)


def _provincia(tropas, fort=False, rey=False):
    return Provincia(id_provincia=2, id_propietario=2, poblacion_base=1000.0,
                      nivel_felicidad=80.0, nivel_infraestructura=1,
                      tropas_guarnicion=tropas, nodos_vecinos=[], fortificada=fort, tiene_rey=rey)


def test_ataque_simple_gana_atacante():
    atacante = _ejercito(100)
    defensor = _provincia(50)
    resultado = resolver_combate(atacante, defensor, PARAMS)
    assert resultado["gano_atacante"] is True
    assert defensor.tropas_guarnicion == 50
    assert defensor.id_propietario == 1
    assert defensor.nivel_felicidad == 25


def test_bono_rey_en_ataque():
    atacante = _ejercito(50, rey=True)  # 50 * (1+1.0) = 100
    defensor = _provincia(80)
    resultado = resolver_combate(atacante, defensor, PARAMS)
    assert resultado["gano_atacante"] is True
    assert defensor.tropas_guarnicion == 20


def test_fortificacion_favorece_defensor():
    atacante = _ejercito(80)
    defensor = _provincia(50, fort=True)  # 50 * (1+1.0) = 100
    resultado = resolver_combate(atacante, defensor, PARAMS)
    assert resultado["gano_atacante"] is False
    assert defensor.tropas_guarnicion == 20
    assert defensor.id_propietario == 2


def test_bono_rey_en_defensa():
    atacante = _ejercito(60)
    defensor = _provincia(50, rey=True)  # 50 + 0.30*50 = 65
    resultado = resolver_combate(atacante, defensor, PARAMS)
    assert resultado["gano_atacante"] is False
    assert defensor.tropas_guarnicion == 5


def test_penalizacion_por_desembarco():
    atacante = _ejercito(100, barco=True)  # 100 * (1-0.30) = 70
    defensor = _provincia(50)
    resultado = resolver_combate(atacante, defensor, PARAMS)
    assert resultado["gano_atacante"] is True
    assert defensor.tropas_guarnicion == 20


def test_rey_derrotado_del_atacante_si_pierde_con_rey():
    atacante = _ejercito(50, rey=True)  # 50*2=100
    defensor = _provincia(200, fort=True)  # 200*2=400
    resultado = resolver_combate(atacante, defensor, PARAMS)
    assert resultado["gano_atacante"] is False
    assert resultado["rey_derrotado_de"] == 1


def test_rey_derrotado_del_defensor_si_pierde_con_rey():
    atacante = _ejercito(200)
    defensor = _provincia(50, rey=True)  # 50+15=65
    resultado = resolver_combate(atacante, defensor, PARAMS)
    assert resultado["gano_atacante"] is True
    assert resultado["rey_derrotado_de"] == 2
    assert resultado["id_propietario_anterior"] == 2


def _partida_con_ejercito(id_propietario_provincia, nodo_posicion_id, cantidad_fuerza):
    provincia_propia = Provincia(id_provincia=1, id_propietario=1, poblacion_base=1000.0,
                                  nivel_felicidad=80.0, nivel_infraestructura=1,
                                  tropas_guarnicion=100, nodos_vecinos=[2])
    provincia_ajena = Provincia(id_provincia=2, id_propietario=id_propietario_provincia,
                                 poblacion_base=1000.0, nivel_felicidad=80.0,
                                 nivel_infraestructura=1, tropas_guarnicion=0, nodos_vecinos=[1])
    ejercito = Ejercito(id_ejercito=1, id_propietario=1, cantidad_fuerza=cantidad_fuerza,
                         nodo_posicion_id=nodo_posicion_id)
    jugador = Jugador(id_jugador=1, oro_tesoro=0.0, puntos_accion=0.0, nivel_impuesto=20.0,
                       tipo_control=TipoControl.HUMANO, puesto_clasificacion=1,
                       provincias_controladas=[1])
    partida = Partida(objetivo_victoria=ObjetivoVictoria.ANIQUILACION, turno_limite=50,
                       jugadores={1: jugador}, provincias={1: provincia_propia, 2: provincia_ajena},
                       ejercitos={1: ejercito}, jugadores_activos=[1])
    return partida, jugador, ejercito


def test_desercion_no_afecta_ejercito_en_territorio_propio():
    partida, jugador, ejercito = _partida_con_ejercito(id_propietario_provincia=2, nodo_posicion_id=1,
                                                         cantidad_fuerza=100)
    calcular_desercion(partida, jugador, PARAMS, log=lambda m: None, tiempo=1.0)
    assert ejercito.cantidad_fuerza == 100
    assert ejercito.en_territorio_no_aliado is False
    assert 1 in partida.ejercitos


def test_desercion_reduce_fuerza_en_territorio_no_aliado():
    partida, jugador, ejercito = _partida_con_ejercito(id_propietario_provincia=2, nodo_posicion_id=2,
                                                         cantidad_fuerza=100)
    calcular_desercion(partida, jugador, PARAMS, log=lambda m: None, tiempo=1.0)
    assert ejercito.cantidad_fuerza == 87.0  # 100 * (1 - 0.13)
    assert ejercito.en_territorio_no_aliado is True
    assert 1 in partida.ejercitos


def test_desercion_disuelve_ejercito_si_fuerza_cae_por_debajo_de_uno():
    partida, jugador, ejercito = _partida_con_ejercito(id_propietario_provincia=2, nodo_posicion_id=2,
                                                         cantidad_fuerza=1)
    salidas = []
    calcular_desercion(partida, jugador, PARAMS, log=salidas.append, tiempo=1.0)
    assert 1 not in partida.ejercitos
    assert any("se disuelve" in l for l in salidas)
