import json
from dataclasses import dataclass

from .models import Partida, Jugador, Provincia, Ejercito, TipoControl, ObjetivoVictoria


@dataclass
class Parametros:
    c_m: float
    m_min: float
    b_fort: float
    b_rey_atk: float
    b_rey_def: float
    p_barco: float
    p_terr: float
    p_conquista: float
    tau_max: float
    p_tau: float
    p_guerra: float
    f_revuelta: float
    ratio_min: float
    g_anual: float
    per_anual: int
    cap_adm: float
    p_banca: float
    r_banca: float
    r_base: float
    gamma: float
    margen_ia: float
    puntos_accion_max: float
    costo_reclutamiento_por_tropa: float
    costo_fortificacion: float
    costo_decreto: float
    delta_decreto_felicidad: float
    costo_infraestructura: float
    comercio_por_poblacion: float


def cargar_parametros(path: str) -> Parametros:
    with open(path, encoding="utf-8") as f:
        datos = json.load(f)
    return Parametros(**datos)


def cargar_escenario(path: str) -> Partida:
    with open(path, encoding="utf-8") as f:
        datos = json.load(f)

    provincias = {}
    for p in datos["provincias"]:
        provincias[p["id_provincia"]] = Provincia(
            id_provincia=p["id_provincia"],
            id_propietario=p["id_propietario"],
            poblacion_base=p["poblacion_base"],
            nivel_felicidad=p["nivel_felicidad"],
            nivel_infraestructura=p["nivel_infraestructura"],
            tropas_guarnicion=p["tropas_guarnicion"],
            nodos_vecinos=list(p["nodos_vecinos"]),
            fortificada=p.get("fortificada", False),
            tiene_rey=p.get("tiene_rey", False),
        )

    ids_provincias = set(provincias)
    for p in provincias.values():
        for vecino in p.nodos_vecinos:
            if vecino not in ids_provincias:
                raise ValueError(f"Provincia {p.id_provincia} referencia vecino inexistente {vecino}")

    jugadores = {}
    for j in datos["jugadores"]:
        jugadores[j["id_jugador"]] = Jugador(
            id_jugador=j["id_jugador"],
            oro_tesoro=j["oro_tesoro"],
            puntos_accion=j["puntos_accion"],
            nivel_impuesto=j["nivel_impuesto"],
            tipo_control=TipoControl(j["tipo_control"]),
            puesto_clasificacion=j["puesto_clasificacion"],
        )

    for p in provincias.values():
        if p.id_propietario == 0:
            continue
        if p.id_propietario not in jugadores:
            raise ValueError(f"Provincia {p.id_provincia} tiene dueño inexistente {p.id_propietario}")
        jugadores[p.id_propietario].provincias_controladas.append(p.id_provincia)

    ejercitos = {}
    for e in datos.get("ejercitos", []):
        ejercitos[e["id_ejercito"]] = Ejercito(
            id_ejercito=e["id_ejercito"],
            id_propietario=e["id_propietario"],
            cantidad_fuerza=e["cantidad_fuerza"],
            nodo_posicion_id=e["nodo_posicion_id"],
            contiene_rey=e.get("contiene_rey", False),
        )

    return Partida(
        objetivo_victoria=ObjetivoVictoria(datos["objetivo_victoria"]),
        turno_limite=datos["turno_limite"],
        jugadores=jugadores,
        provincias=provincias,
        ejercitos=ejercitos,
        jugadores_activos=list(jugadores.keys()),
    )
