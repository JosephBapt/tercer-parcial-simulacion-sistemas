from types import SimpleNamespace
from aoc_sim.models import Ejercito, Provincia
from aoc_sim.engine import resolver_combate

PARAMS = SimpleNamespace(b_fort=1.0, b_rey_atk=1.0, b_rey_def=0.30, p_barco=0.30, p_conquista=25)


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
