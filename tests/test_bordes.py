from types import SimpleNamespace
from aoc_sim.models import Provincia, Jugador, TipoControl, SIN_DUENO
from aoc_sim.engine import (
    actualizar_felicidad, aplicar_gasto_administracion, calcular_gasto_administracion,
    aplicar_mantenimiento, actualizar_poblacion,
)

PARAMS = SimpleNamespace(
    r_base=0.01, gamma=0.05, p_guerra=1, p_tau=2, tau_max=100,
    cap_adm=0.69, p_banca=15, r_banca=0.85, c_m=0.05, m_min=1.0,
)


def _provincia(**kwargs):
    base = dict(id_provincia=1, id_propietario=1, poblacion_base=1000.0, nivel_felicidad=80.0,
                nivel_infraestructura=1, tropas_guarnicion=100, nodos_vecinos=[])
    base.update(kwargs)
    return Provincia(**base)


def test_impuesto_al_maximo_penaliza_felicidad_cada_turno():
    p = _provincia(nivel_felicidad=80.0)
    for _ in range(3):
        actualizar_felicidad(p, en_guerra=False, nivel_impuesto=200.0, params=PARAMS)
    assert p.nivel_felicidad == 74.0  # -2 por turno, 3 turnos


def test_felicidad_en_cero_no_baja_de_cero():
    p = _provincia(nivel_felicidad=1.0)
    actualizar_felicidad(p, en_guerra=True, nivel_impuesto=200.0, params=PARAMS)
    assert p.nivel_felicidad == 0.0


def test_bancarrota_administrativa_total_aplica_fallback_global():
    jugador = Jugador(id_jugador=1, oro_tesoro=0.0, puntos_accion=0.0, nivel_impuesto=20.0,
                       tipo_control=TipoControl.HUMANO, puesto_clasificacion=1)
    provincias = [_provincia(nivel_felicidad=40.0, tropas_guarnicion=100)]
    gasto = calcular_gasto_administracion(provincias, total_provincias=1, total_poblacion=1000.0,
                                           ingreso_total=1000.0, params=PARAMS)
    aplicar_gasto_administracion(jugador, provincias, gasto, PARAMS)
    assert jugador.oro_tesoro == 0.0
    assert provincias[0].nivel_felicidad == 25.0  # max(0, 40-15)
    assert provincias[0].tropas_guarnicion == 85  # int(100*0.85)


def test_provincia_con_poblacion_cero_no_crece_ni_paga_impuesto():
    p = _provincia(poblacion_base=0.0)
    actualizar_poblacion(p, PARAMS)
    assert p.poblacion_base == 0.0


def test_cero_provincias_totales_no_divide_por_cero():
    gasto = calcular_gasto_administracion([], total_provincias=0, total_poblacion=0.0,
                                           ingreso_total=100.0, params=PARAMS)
    assert gasto >= 0.0


def test_mantenimiento_con_multiples_provincias_deserta_en_orden():
    jugador = Jugador(id_jugador=1, oro_tesoro=0.0, puntos_accion=0.0, nivel_impuesto=20.0,
                       tipo_control=TipoControl.HUMANO, puesto_clasificacion=1)
    p1 = _provincia(id_provincia=1, tropas_guarnicion=50)
    p2 = _provincia(id_provincia=2, tropas_guarnicion=50)
    # costo = max(1,50*0.05)*2 = 5.0, deficit=5.0, tropas_a_desertar=int(5/0.05)=100
    aplicar_mantenimiento(jugador, [p1, p2], PARAMS)
    assert p1.tropas_guarnicion == 0
    assert p2.tropas_guarnicion == 0


def test_tropas_nunca_negativas_tras_desercion_total():
    jugador = Jugador(id_jugador=1, oro_tesoro=0.0, puntos_accion=0.0, nivel_impuesto=20.0,
                       tipo_control=TipoControl.HUMANO, puesto_clasificacion=1)
    p1 = _provincia(id_provincia=1, tropas_guarnicion=10)
    aplicar_mantenimiento(jugador, [p1], PARAMS)
    assert p1.tropas_guarnicion >= 0
