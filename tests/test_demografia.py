from types import SimpleNamespace
from aoc_sim.models import Provincia
from aoc_sim.engine import actualizar_poblacion, actualizar_felicidad

PARAMS = SimpleNamespace(r_base=0.01, gamma=0.05, p_guerra=1, p_tau=2, tau_max=100)


def _provincia(poblacion, felicidad=80.0, infraestructura=1):
    return Provincia(id_provincia=1, id_propietario=1, poblacion_base=poblacion,
                      nivel_felicidad=felicidad, nivel_infraestructura=infraestructura,
                      tropas_guarnicion=0, nodos_vecinos=[])


def test_poblacion_crece_segun_formula():
    p = _provincia(poblacion=1000.0, felicidad=100.0, infraestructura=2)
    actualizar_poblacion(p, PARAMS)
    # 1000 * (1 + 0.01*1.0*(1+0.05*2)) = 1000 * 1.011 = 1011.0
    assert round(p.poblacion_base, 4) == 1011.0


def test_poblacion_cero_permanece_cero():
    p = _provincia(poblacion=0.0)
    actualizar_poblacion(p, PARAMS)
    assert p.poblacion_base == 0.0


def test_felicidad_baja_por_guerra():
    p = _provincia(poblacion=1000.0, felicidad=80.0)
    actualizar_felicidad(p, en_guerra=True, nivel_impuesto=20.0, params=PARAMS)
    assert p.nivel_felicidad == 79.0


def test_felicidad_baja_por_impuesto_excesivo():
    p = _provincia(poblacion=1000.0, felicidad=80.0)
    actualizar_felicidad(p, en_guerra=False, nivel_impuesto=150.0, params=PARAMS)
    assert p.nivel_felicidad == 78.0


def test_felicidad_clamp_superior_100():
    p = _provincia(poblacion=1000.0, felicidad=100.0)
    actualizar_felicidad(p, en_guerra=False, nivel_impuesto=20.0, params=PARAMS)
    assert p.nivel_felicidad == 100.0


def test_felicidad_clamp_inferior_0():
    p = _provincia(poblacion=1000.0, felicidad=0.5)
    actualizar_felicidad(p, en_guerra=True, nivel_impuesto=150.0, params=PARAMS)
    assert p.nivel_felicidad == 0.0
