from types import SimpleNamespace
from aoc_sim.models import Provincia, Jugador, TipoControl
from aoc_sim.engine import (
    calcular_ingreso_impuesto, calcular_ingreso_anual,
    calcular_mantenimiento, aplicar_mantenimiento,
)

PARAMS = SimpleNamespace(c_m=0.05, m_min=1.0, g_anual=0.05, per_anual=12)


def _provincia(id_provincia, poblacion, felicidad, infraestructura, tropas):
    return Provincia(id_provincia=id_provincia, id_propietario=1, poblacion_base=poblacion,
                      nivel_felicidad=felicidad, nivel_infraestructura=infraestructura,
                      tropas_guarnicion=tropas, nodos_vecinos=[])


def _jugador(oro):
    return Jugador(id_jugador=1, oro_tesoro=oro, puntos_accion=10.0, nivel_impuesto=20.0,
                    tipo_control=TipoControl.HUMANO, puesto_clasificacion=1)


def test_ingreso_impuesto_formula_exacta():
    p = _provincia(1, poblacion=1000, felicidad=50, infraestructura=2, tropas=0)
    # 1000 * 20 * 0.5 * 2 = 20000
    assert calcular_ingreso_impuesto(p, nivel_impuesto=20) == 20000.0


def test_ingreso_anual_excluido_en_turno_cero():
    provincias = [_provincia(1, 1000, 80, 1, 0)]
    assert calcular_ingreso_anual(provincias, turno_actual=0, params=PARAMS) == 0.0


def test_ingreso_anual_se_dispara_en_multiplo_de_12():
    provincias = [_provincia(1, 1000, 80, 1, 0), _provincia(2, 2000, 80, 1, 0)]
    # 0.05*1000 + 0.05*2000 = 150
    assert calcular_ingreso_anual(provincias, turno_actual=12, params=PARAMS) == 150.0


def test_ingreso_anual_cero_fuera_de_multiplo():
    provincias = [_provincia(1, 1000, 80, 1, 0)]
    assert calcular_ingreso_anual(provincias, turno_actual=13, params=PARAMS) == 0.0


def test_mantenimiento_usa_minimo_por_provincia():
    # 10 tropas * 0.05 = 0.5, pero m_min=1.0 domina
    provincias = [_provincia(1, 1000, 80, 1, 10)]
    assert calcular_mantenimiento(provincias, PARAMS) == 1.0


def test_mantenimiento_provincia_sin_tropas_no_cuenta():
    provincias = [_provincia(1, 1000, 80, 1, 0)]
    assert calcular_mantenimiento(provincias, PARAMS) == 0.0


def test_aplicar_mantenimiento_solvente_descuenta_oro():
    jugador = _jugador(oro=100.0)
    provincias = [_provincia(1, 1000, 80, 1, 200)]  # 200*0.05=10
    costo = aplicar_mantenimiento(jugador, provincias, PARAMS)
    assert costo == 10.0
    assert jugador.oro_tesoro == 90.0
    assert provincias[0].tropas_guarnicion == 200


def test_aplicar_mantenimiento_insolvente_deserta_tropas():
    jugador = _jugador(oro=5.0)
    provincias = [_provincia(1, 1000, 80, 1, 200)]  # costo=10, deficit=5
    costo = aplicar_mantenimiento(jugador, provincias, PARAMS)
    assert costo == 10.0
    assert jugador.oro_tesoro == 0.0
    # deficit=5, tropas_a_desertar = int(5/0.05) = 100
    assert provincias[0].tropas_guarnicion == 100


def test_aplicar_mantenimiento_oro_exacto_no_deserta():
    jugador = _jugador(oro=10.0)
    provincias = [_provincia(1, 1000, 80, 1, 200)]
    aplicar_mantenimiento(jugador, provincias, PARAMS)
    assert jugador.oro_tesoro == 0.0
    assert provincias[0].tropas_guarnicion == 200


from aoc_sim.engine import calcular_gasto_administracion, aplicar_gasto_administracion

PARAMS_ADM = SimpleNamespace(cap_adm=0.69, p_banca=15, r_banca=0.85)


def test_gasto_administracion_x_maximo_topa_en_cap_adm():
    provincias = [_provincia(1, 1000, 80, 1, 0)]
    # x_p=1, x_b=1 -> x=1 -> factor=sqrt(1)=1 -> gasto=min(1*1000, 0.69*1000)=690
    gasto = calcular_gasto_administracion(provincias, total_provincias=1, total_poblacion=1000,
                                           ingreso_total=1000.0, params=PARAMS_ADM)
    assert gasto == 690.0


def test_gasto_administracion_x_pequeno_da_gasto_bajo():
    provincias = [_provincia(1, 100, 80, 1, 0)]
    # x_p=1/100=0.01, x_b=100/100000=0.001 -> x=0.0055 -> factor=sqrt(0.0055)=~0.0742
    gasto = calcular_gasto_administracion(provincias, total_provincias=100, total_poblacion=100000,
                                           ingreso_total=1000.0, params=PARAMS_ADM)
    assert 70.0 < gasto < 80.0


def test_gasto_administracion_guarda_epsilon_sin_division_por_cero():
    provincias = []
    gasto = calcular_gasto_administracion(provincias, total_provincias=1, total_poblacion=1000,
                                           ingreso_total=1000.0, params=PARAMS_ADM)
    assert gasto >= 0.0


def test_aplicar_gasto_administracion_solvente():
    jugador = _jugador(oro=1000.0)
    provincias = [_provincia(1, 1000, 80, 1, 100)]
    aplicar_gasto_administracion(jugador, provincias, gasto=300.0, params=PARAMS_ADM)
    assert jugador.oro_tesoro == 700.0
    assert provincias[0].nivel_felicidad == 80  # sin penalizacion


def test_aplicar_gasto_administracion_bancarrota_fallback_global():
    jugador = _jugador(oro=50.0)
    provincias = [_provincia(1, 1000, 80, 1, 100)]
    aplicar_gasto_administracion(jugador, provincias, gasto=300.0, params=PARAMS_ADM)
    assert jugador.oro_tesoro == 0.0
    assert provincias[0].nivel_felicidad == 65  # 80-15
    assert provincias[0].tropas_guarnicion == 85  # int(100*0.85)
