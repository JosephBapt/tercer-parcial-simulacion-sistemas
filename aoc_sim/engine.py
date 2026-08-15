"""Motor de simulacion: formulas del modelo matematico y despachador de eventos DES."""

import math

from .models import SIN_DUENO


def calcular_fuerza_ataque(atacante, params):
    fuerza = atacante.cantidad_fuerza
    if atacante.contiene_rey:
        fuerza *= (1 + params.b_rey_atk)
    if atacante.desde_barco:
        fuerza *= (1 - params.p_barco)
    return fuerza


def calcular_fuerza_defensa(defensor, params):
    fuerza = defensor.tropas_guarnicion
    if defensor.fortificada:
        fuerza *= (1 + params.b_fort)
    if defensor.tiene_rey:
        fuerza += params.b_rey_def * defensor.tropas_guarnicion
    return fuerza


def resolver_combate(atacante, defensor, params):
    fuerza_ataque = calcular_fuerza_ataque(atacante, params)
    fuerza_defensa = calcular_fuerza_defensa(defensor, params)
    id_propietario_anterior = defensor.id_propietario
    gano_atacante = fuerza_ataque > fuerza_defensa

    resultado = {
        "fuerza_ataque": fuerza_ataque,
        "fuerza_defensa": fuerza_defensa,
        "gano_atacante": gano_atacante,
        "id_propietario_anterior": id_propietario_anterior,
        "rey_derrotado_de": None,
    }

    if gano_atacante:
        defensor.tropas_guarnicion = int(fuerza_ataque - fuerza_defensa)
        if defensor.tiene_rey:
            resultado["rey_derrotado_de"] = id_propietario_anterior
        defensor.id_propietario = atacante.id_propietario
        defensor.tiene_rey = atacante.contiene_rey
        defensor.nivel_felicidad = params.p_conquista
    else:
        defensor.tropas_guarnicion = int(fuerza_defensa - fuerza_ataque)
        if atacante.contiene_rey:
            resultado["rey_derrotado_de"] = atacante.id_propietario

    return resultado


def calcular_ingreso_impuesto(provincia, nivel_impuesto):
    factor_felicidad = provincia.nivel_felicidad / 100.0
    return provincia.poblacion_base * nivel_impuesto * factor_felicidad * provincia.nivel_infraestructura


def calcular_ingreso_anual(provincias_jugador, turno_actual, params):
    if turno_actual == 0 or turno_actual % params.per_anual != 0:
        return 0.0
    return sum(params.g_anual * p.poblacion_base for p in provincias_jugador)


def calcular_mantenimiento(provincias_jugador, params):
    total = 0.0
    for p in provincias_jugador:
        if p.tropas_guarnicion > 0:
            total += max(params.m_min, params.c_m * p.tropas_guarnicion)
    return total


def aplicar_mantenimiento(jugador, provincias_jugador, params):
    costo = calcular_mantenimiento(provincias_jugador, params)
    if jugador.oro_tesoro >= costo:
        jugador.oro_tesoro -= costo
        return costo

    deficit = costo - jugador.oro_tesoro
    jugador.oro_tesoro = 0.0
    tropas_a_desertar = int(deficit / params.c_m)
    for p in provincias_jugador:
        if tropas_a_desertar <= 0:
            break
        reduccion = min(p.tropas_guarnicion, tropas_a_desertar)
        p.tropas_guarnicion -= reduccion
        tropas_a_desertar -= reduccion
    return costo


def calcular_gasto_administracion(provincias_jugador, total_provincias, total_poblacion, ingreso_total, params):
    x_p = len(provincias_jugador) / total_provincias if total_provincias else 0.0
    poblacion_jugador = sum(p.poblacion_base for p in provincias_jugador)
    x_b = poblacion_jugador / total_poblacion if total_poblacion else 0.0
    x = max((x_p + x_b) / 2, 1e-6)
    factor = x ** 0.5  # correccion de signo respecto a "1 - 1/sqrt(x)", ver nota Task 6 del plan
    gasto = factor * ingreso_total
    return min(gasto, params.cap_adm * ingreso_total)


def aplicar_gasto_administracion(jugador, provincias_jugador, gasto, params):
    if jugador.oro_tesoro >= gasto:
        jugador.oro_tesoro -= gasto
        return
    jugador.oro_tesoro = 0.0
    for p in provincias_jugador:
        p.nivel_felicidad = max(0.0, p.nivel_felicidad - params.p_banca)
        p.tropas_guarnicion = int(p.tropas_guarnicion * params.r_banca)


def actualizar_poblacion(provincia, params):
    if provincia.poblacion_base <= 0:
        provincia.poblacion_base = 0.0
        return
    f_i = provincia.nivel_felicidad / 100.0
    tasa = params.r_base * f_i * (1 + params.gamma * provincia.nivel_infraestructura)
    provincia.poblacion_base *= (1 + tasa)


def actualizar_felicidad(provincia, en_guerra, nivel_impuesto, params):
    delta = 0.0
    if en_guerra:
        delta -= params.p_guerra
    if nivel_impuesto > params.tau_max:
        delta -= params.p_tau
    provincia.nivel_felicidad = min(100.0, max(0.0, provincia.nivel_felicidad + delta))


def evaluar_riesgo_revuelta(provincia, params, rng):
    if provincia.tiene_rey:
        return False
    soldados_minimos = math.ceil(provincia.poblacion_base * params.ratio_min)
    if provincia.tropas_guarnicion >= soldados_minimos:
        return False
    if provincia.nivel_felicidad >= params.f_revuelta:
        return False
    riesgo = (params.f_revuelta - provincia.nivel_felicidad) / params.f_revuelta
    if rng.random() < riesgo:
        provincia.id_propietario = SIN_DUENO
        return True
    return False


def evaluar_muerte_de_rey(partida, id_jugador, log):
    partida.eliminar_jugador(id_jugador)
    log(f"J{id_jugador} pierde: su rey ha muerto")


def _aplicar_movimiento(partida, params, jugador, orden, log):
    ejercito = partida.ejercitos.get(orden["id_ejercito"])
    if ejercito is None or ejercito.id_propietario != jugador.id_jugador:
        return
    origen = partida.provincias[ejercito.nodo_posicion_id]
    destino_id = orden["provincia_destino"]
    if destino_id not in origen.nodos_vecinos:
        log(f"Movimiento invalido: P{destino_id} no es vecino de P{origen.id_provincia}")
        return

    destino = partida.provincias[destino_id]
    if destino.id_propietario == jugador.id_jugador:
        destino.tropas_guarnicion += ejercito.cantidad_fuerza
        ejercito.nodo_posicion_id = destino_id
        log(f"J{jugador.id_jugador} refuerza P{destino_id} con {ejercito.cantidad_fuerza} tropas")
        return

    resultado = resolver_combate(ejercito, destino, params)
    log(f"EV_RESOLVER_ATAQUE E{ejercito.id_ejercito} vs P{destino_id}: "
        f"Fa={resultado['fuerza_ataque']:.1f} Fd={resultado['fuerza_defensa']:.1f} "
        f"gana={'atacante' if resultado['gano_atacante'] else 'defensor'}")

    if resultado["gano_atacante"]:
        anterior_id = resultado["id_propietario_anterior"]
        if anterior_id in partida.jugadores and destino_id in partida.jugadores[anterior_id].provincias_controladas:
            partida.jugadores[anterior_id].provincias_controladas.remove(destino_id)
        jugador.provincias_controladas.append(destino_id)
        ejercito.nodo_posicion_id = destino_id
        if resultado["rey_derrotado_de"] is not None:
            evaluar_muerte_de_rey(partida, resultado["rey_derrotado_de"], log)
    else:
        del partida.ejercitos[ejercito.id_ejercito]
        if resultado["rey_derrotado_de"] is not None:
            evaluar_muerte_de_rey(partida, resultado["rey_derrotado_de"], log)


def aplicar_orden(partida, params, jugador, orden, rng, log):
    tipo = orden["tipo"]

    if tipo == "IMPUESTO":
        jugador.nivel_impuesto = max(0.0, orden["nuevo_nivel"])
        log(f"J{jugador.id_jugador} ajusta impuesto a {jugador.nivel_impuesto}%")

    elif tipo == "RECLUTAR":
        provincia = partida.provincias[orden["id_provincia"]]
        costo = orden["cantidad"] * params.costo_reclutamiento_por_tropa
        if provincia.id_propietario == jugador.id_jugador and jugador.oro_tesoro >= costo:
            jugador.oro_tesoro -= costo
            provincia.tropas_guarnicion += orden["cantidad"]
            log(f"J{jugador.id_jugador} recluta {orden['cantidad']} tropas en P{provincia.id_provincia}")

    elif tipo == "FORTIFICAR":
        provincia = partida.provincias[orden["id_provincia"]]
        if provincia.id_propietario == jugador.id_jugador and jugador.oro_tesoro >= params.costo_fortificacion:
            jugador.oro_tesoro -= params.costo_fortificacion
            provincia.fortificada = True
            log(f"J{jugador.id_jugador} fortifica P{provincia.id_provincia}")

    elif tipo == "DECRETO_FELICIDAD":
        provincia = partida.provincias[orden["id_provincia"]]
        if provincia.id_propietario == jugador.id_jugador and jugador.oro_tesoro >= params.costo_decreto:
            jugador.oro_tesoro -= params.costo_decreto
            provincia.nivel_felicidad = min(100.0, provincia.nivel_felicidad + params.delta_decreto_felicidad)
            log(f"J{jugador.id_jugador} aplica decreto de felicidad en P{provincia.id_provincia}")

    elif tipo == "ABANDONAR":
        provincia = partida.provincias[orden["id_provincia"]]
        if provincia.id_propietario == jugador.id_jugador:
            provincia.id_propietario = SIN_DUENO
            jugador.provincias_controladas.remove(provincia.id_provincia)
            log(f"J{jugador.id_jugador} abandona P{provincia.id_provincia}")

    elif tipo == "DESMANTELAR":
        provincia = partida.provincias[orden["id_provincia"]]
        if provincia.id_propietario == jugador.id_jugador:
            provincia.tropas_guarnicion = max(0, provincia.tropas_guarnicion - orden["cantidad"])
            log(f"J{jugador.id_jugador} desmantela {orden['cantidad']} tropas en P{provincia.id_provincia}")

    elif tipo == "GUERRA":
        jugador.relaciones_diplomaticas[orden["id_objetivo"]] = "GUERRA"
        partida.jugadores[orden["id_objetivo"]].relaciones_diplomaticas[jugador.id_jugador] = "GUERRA"
        log(f"J{jugador.id_jugador} declara guerra a J{orden['id_objetivo']}")

    elif tipo == "MOVER":
        _aplicar_movimiento(partida, params, jugador, orden, log)

    elif tipo == "PASAR":
        pass
