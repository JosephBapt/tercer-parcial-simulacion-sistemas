import random
from types import SimpleNamespace
from aoc_sim.models import Provincia, SIN_DUENO
from aoc_sim.engine import evaluar_riesgo_revuelta

PARAMS = SimpleNamespace(f_revuelta=50, ratio_min=1 / 2500)


def _provincia(poblacion, felicidad, tropas, tiene_rey=False):
    return Provincia(id_provincia=1, id_propietario=1, poblacion_base=poblacion,
                      nivel_felicidad=felicidad, nivel_infraestructura=1,
                      tropas_guarnicion=tropas, nodos_vecinos=[], tiene_rey=tiene_rey)


def test_sin_riesgo_si_guarnicion_cubre_minimo():
    # soldados_minimos = ceil(5000/2500) = 2
    p = _provincia(poblacion=5000, felicidad=10.0, tropas=2)
    perdida = evaluar_riesgo_revuelta(p, PARAMS, rng=random.Random(1))
    assert perdida is False
    assert p.id_propietario == 1


def test_sin_riesgo_si_tiene_rey_pese_a_felicidad_baja():
    p = _provincia(poblacion=5000, felicidad=1.0, tropas=0, tiene_rey=True)
    perdida = evaluar_riesgo_revuelta(p, PARAMS, rng=random.Random(1))
    assert perdida is False


def test_sin_riesgo_si_felicidad_igual_al_umbral():
    p = _provincia(poblacion=5000, felicidad=50.0, tropas=0)
    perdida = evaluar_riesgo_revuelta(p, PARAMS, rng=random.Random(1))
    assert perdida is False


def test_riesgo_maximo_en_felicidad_cero_siempre_se_pierde():
    p = _provincia(poblacion=5000, felicidad=0.0, tropas=0)
    # R_i = (50-0)/50 = 1.0 -> siempre U(0,1) < 1.0
    perdida = evaluar_riesgo_revuelta(p, PARAMS, rng=random.Random(123))
    assert perdida is True
    assert p.id_propietario == SIN_DUENO


def test_reproducibilidad_con_misma_semilla():
    p1 = _provincia(poblacion=5000, felicidad=30.0, tropas=0)
    p2 = _provincia(poblacion=5000, felicidad=30.0, tropas=0)
    r1 = evaluar_riesgo_revuelta(p1, PARAMS, rng=random.Random(99))
    r2 = evaluar_riesgo_revuelta(p2, PARAMS, rng=random.Random(99))
    assert r1 == r2
