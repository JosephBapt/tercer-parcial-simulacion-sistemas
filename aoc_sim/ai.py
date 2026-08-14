from .engine import calcular_fuerza_ataque, calcular_fuerza_defensa


def decidir_ordenes_ia(jugador, partida, params, rng):
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

    provincia_base = partida.provincias[jugador.provincias_controladas[0]]
    if not provincia_base.fortificada and jugador.oro_tesoro >= params.costo_fortificacion:
        return [{"tipo": "FORTIFICAR", "id_provincia": provincia_base.id_provincia}]

    cantidad = 10
    if jugador.oro_tesoro >= params.costo_reclutamiento_por_tropa * cantidad:
        return [{"tipo": "RECLUTAR", "id_provincia": provincia_base.id_provincia, "cantidad": cantidad}]

    return []
