"""Árbol de decisión para IA: ataque, consolidación y reclutamiento"""

from .engine import calcular_fuerza_ataque, calcular_fuerza_defensa

UMBRAL_CREAR_EJERCITO = 30
UMBRAL_REFORZAR_EJERCITO = 10


def decidir_ordenes_ia(jugador, partida, params, rng):
    """Determina órdenes del jugador IA prioriza ataques, consolidación y reclutamiento"""
    for id_prov in list(jugador.provincias_controladas):
        provincia = partida.provincias[id_prov]
        ejercito_local = next(
            (e for e in partida.ejercitos.values()
             if e.id_propietario == jugador.id_jugador and e.nodo_posicion_id == id_prov),
            None,
        )
        if ejercito_local is None:
            continue
        for id_vecino in provincia.nodos_vecinos:
            vecino = partida.provincias[id_vecino]
            if vecino.id_propietario == jugador.id_jugador:
                continue
            fuerza_ataque = calcular_fuerza_ataque(ejercito_local, params)
            fuerza_defensa = calcular_fuerza_defensa(vecino, params)
            if fuerza_ataque > params.margen_ia * fuerza_defensa:
                return [{
                    "tipo": "MOVER",
                    "id_ejercito": ejercito_local.id_ejercito,
                    "provincia_destino": id_vecino,
                }]

    if not jugador.provincias_controladas:
        return []

    tiene_ejercito = any(
        e.id_propietario == jugador.id_jugador for e in partida.ejercitos.values())
    if not tiene_ejercito:
        provincia_con_tropas = max(
            (partida.provincias[i] for i in jugador.provincias_controladas),
            key=lambda p: p.tropas_guarnicion)
        if provincia_con_tropas.tropas_guarnicion >= UMBRAL_CREAR_EJERCITO:
            return [{
                "tipo": "CREAR_EJERCITO",
                "id_provincia": provincia_con_tropas.id_provincia,
                "cantidad": provincia_con_tropas.tropas_guarnicion // 2,
            }]

    for ejercito_local in partida.ejercitos.values():
        if ejercito_local.id_propietario != jugador.id_jugador:
            continue
        provincia = partida.provincias[ejercito_local.nodo_posicion_id]
        if provincia.id_propietario != jugador.id_jugador:
            continue
        tiene_vecino_hostil = any(
            partida.provincias[v].id_propietario != jugador.id_jugador
            for v in provincia.nodos_vecinos)
        if tiene_vecino_hostil and provincia.tropas_guarnicion >= UMBRAL_REFORZAR_EJERCITO:
            return [{
                "tipo": "REFORZAR_EJERCITO",
                "id_ejercito": ejercito_local.id_ejercito,
                "cantidad": provincia.tropas_guarnicion // 2,
            }]

    provincia_base = partida.provincias[jugador.provincias_controladas[0]]
    if not provincia_base.fortificada and jugador.oro_tesoro >= params.costo_fortificacion:
        return [{"tipo": "FORTIFICAR", "id_provincia": provincia_base.id_provincia}]

    cantidad = 10
    if jugador.oro_tesoro >= params.costo_reclutamiento_por_tropa * cantidad:
        return [{"tipo": "RECLUTAR", "id_provincia": provincia_base.id_provincia, "cantidad": cantidad}]

    return []
