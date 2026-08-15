from types import SimpleNamespace
from aoc_sim.models import Partida, Jugador, Provincia, Ejercito, TipoControl, ObjetivoVictoria, SIN_DUENO
from aoc_sim.engine import aplicar_orden

PARAMS = SimpleNamespace(
    b_fort=1.0, b_rey_atk=1.0, b_rey_def=0.30, p_barco=0.30, p_conquista=25,
    costo_reclutamiento_por_tropa=2.0, costo_fortificacion=100.0,
    costo_decreto=50.0, delta_decreto_felicidad=10.0,
)


def _partida_dos_jugadores():
    p1 = Provincia(id_provincia=1, id_propietario=1, poblacion_base=1000, nivel_felicidad=80,
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


def test_orden_mover_a_provincia_enemiga_resuelve_combate_y_transfiere():
    partida, j1 = _partida_dos_jugadores()
    aplicar_orden(partida, PARAMS, j1, {"tipo": "MOVER", "id_ejercito": 1, "provincia_destino": 2}, None, log=lambda m: None)
    assert partida.provincias[2].id_propietario == 1
    assert 2 in j1.provincias_controladas
    assert 2 not in partida.jugadores[2].provincias_controladas


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
    aplicar_orden(partida, PARAMS, j1, {"tipo": "ABANDONAR", "id_provincia": 1}, None, log=lambda m: None)
    assert partida.provincias[1].id_propietario == SIN_DUENO
    assert 1 not in j1.provincias_controladas


def test_orden_desmantelar():
    partida, j1 = _partida_dos_jugadores()
    aplicar_orden(partida, PARAMS, j1, {"tipo": "DESMANTELAR", "id_provincia": 1, "cantidad": 30}, None, log=lambda m: None)
    assert partida.provincias[1].tropas_guarnicion == 70


def test_orden_guerra_marca_relacion_bidireccional():
    partida, j1 = _partida_dos_jugadores()
    aplicar_orden(partida, PARAMS, j1, {"tipo": "GUERRA", "id_objetivo": 2}, None, log=lambda m: None)
    assert j1.relaciones_diplomaticas[2] == "GUERRA"
    assert partida.jugadores[2].relaciones_diplomaticas[1] == "GUERRA"


def test_orden_decreto_felicidad():
    partida, j1 = _partida_dos_jugadores()
    aplicar_orden(partida, PARAMS, j1, {"tipo": "DECRETO_FELICIDAD", "id_provincia": 1}, None, log=lambda m: None)
    assert partida.provincias[1].nivel_felicidad == 90.0
    assert j1.oro_tesoro == 450.0


def test_orden_pasar_no_hace_nada():
    partida, j1 = _partida_dos_jugadores()
    oro_antes = j1.oro_tesoro
    aplicar_orden(partida, PARAMS, j1, {"tipo": "PASAR"}, None, log=lambda m: None)
    assert j1.oro_tesoro == oro_antes
