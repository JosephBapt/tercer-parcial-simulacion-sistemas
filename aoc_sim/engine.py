"""Motor de simulacion: formulas del modelo matematico y despachador de eventos DES."""

import math

from .events import EventQueue, TipoEvento
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
        log(f"J{jugador.id_jugador} refuerza P{destino_id} con {ejercito.cantidad_fuerza} tropas")
        del partida.ejercitos[ejercito.id_ejercito]
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
        if resultado["rey_derrotado_de"] is not None:
            evaluar_muerte_de_rey(partida, resultado["rey_derrotado_de"], log)
    else:
        if resultado["rey_derrotado_de"] is not None:
            evaluar_muerte_de_rey(partida, resultado["rey_derrotado_de"], log)

    # El ejercito se disuelve al llegar (gana -> se convierte en la guarnicion ya
    # actualizada por resolver_combate; pierde -> queda destruido). Nunca sigue
    # existiendo como unidad movil separada tras resolver un MOVER.
    del partida.ejercitos[ejercito.id_ejercito]


def aplicar_orden(partida, params, jugador, orden, rng, log):
    tipo = orden["tipo"]

    if tipo == "IMPUESTO":
        jugador.nivel_impuesto = max(0.0, orden["nuevo_nivel"])
        log(f"J{jugador.id_jugador} ajusta impuesto a {jugador.nivel_impuesto}%")

    elif tipo == "RECLUTAR":
        provincia = partida.provincias[orden["id_provincia"]]
        costo = orden["cantidad"] * params.costo_reclutamiento_por_tropa
        if (orden["cantidad"] > 0 and provincia.id_propietario == jugador.id_jugador
                and jugador.oro_tesoro >= costo):
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
        if provincia.id_propietario == jugador.id_jugador and provincia.tiene_rey:
            log(f"J{jugador.id_jugador} no puede abandonar P{provincia.id_provincia}: contiene al rey")
        elif provincia.id_propietario == jugador.id_jugador:
            provincia.id_propietario = SIN_DUENO
            jugador.provincias_controladas.remove(provincia.id_provincia)
            log(f"J{jugador.id_jugador} abandona P{provincia.id_provincia}")

    elif tipo == "DESMANTELAR":
        provincia = partida.provincias[orden["id_provincia"]]
        if orden["cantidad"] > 0 and provincia.id_propietario == jugador.id_jugador:
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


def _h_inicio_turno(partida, params, evento, rng, log, contexto):
    jugador = partida.jugadores[evento.entidades["id_jugador"]]
    jugador.puntos_accion = params.puntos_accion_max
    log(f"t={evento.tiempo:.3f} EV_INICIO_TURNO J{jugador.id_jugador}")
    return [(evento.tiempo + 0.001, TipoEvento.PROCESAR_DEMOGRAFIA, evento.entidades, {})]


def _h_procesar_demografia(partida, params, evento, rng, log, contexto):
    jugador = partida.jugadores[evento.entidades["id_jugador"]]
    provincias_jugador = [partida.provincias[i] for i in jugador.provincias_controladas]
    for p in provincias_jugador:
        actualizar_poblacion(p, params)
    en_guerra = any(v == "GUERRA" for v in jugador.relaciones_diplomaticas.values())
    for p in provincias_jugador:
        actualizar_felicidad(p, en_guerra, jugador.nivel_impuesto, params)
    log(f"t={evento.tiempo:.3f} EV_PROCESAR_DEMOGRAFIA J{jugador.id_jugador}")
    return [(evento.tiempo + 0.001, TipoEvento.RECAUDAR_IMPUESTOS, evento.entidades, {})]


def _h_recaudar_impuestos(partida, params, evento, rng, log, contexto):
    jugador = partida.jugadores[evento.entidades["id_jugador"]]
    provincias_jugador = [partida.provincias[i] for i in jugador.provincias_controladas]
    ingreso = sum(calcular_ingreso_impuesto(p, jugador.nivel_impuesto) for p in provincias_jugador)
    jugador.oro_tesoro += ingreso
    contexto["ingreso_impuesto"][jugador.id_jugador] = ingreso
    log(f"t={evento.tiempo:.3f} EV_RECAUDAR_IMPUESTOS J{jugador.id_jugador} +{ingreso:.2f}")
    return [(evento.tiempo + 0.001, TipoEvento.RECAUDAR_IMPUESTO_ANUAL, evento.entidades, {})]


def _h_recaudar_impuesto_anual(partida, params, evento, rng, log, contexto):
    jugador = partida.jugadores[evento.entidades["id_jugador"]]
    provincias_jugador = [partida.provincias[i] for i in jugador.provincias_controladas]
    ingreso = calcular_ingreso_anual(provincias_jugador, partida.turno_actual, params)
    if ingreso:
        jugador.oro_tesoro += ingreso
        log(f"t={evento.tiempo:.3f} EV_RECAUDAR_IMPUESTO_ANUAL J{jugador.id_jugador} +{ingreso:.2f}")
    return [(evento.tiempo + 0.001, TipoEvento.LIQUIDAR_MANTENIMIENTO, evento.entidades, {})]


def _h_liquidar_mantenimiento(partida, params, evento, rng, log, contexto):
    jugador = partida.jugadores[evento.entidades["id_jugador"]]
    provincias_jugador = [partida.provincias[i] for i in jugador.provincias_controladas]
    costo = aplicar_mantenimiento(jugador, provincias_jugador, params)
    log(f"t={evento.tiempo:.3f} EV_LIQUIDAR_MANTENIMIENTO J{jugador.id_jugador} -{costo:.2f}")
    return [(evento.tiempo + 0.001, TipoEvento.FASE_ORDENES, evento.entidades, {})]


def _h_fase_ordenes(partida, params, evento, rng, log, contexto):
    jugador = partida.jugadores[evento.entidades["id_jugador"]]
    if not jugador.provincias_controladas:
        jugador.felicidad_nacional -= 2
        log(f"t={evento.tiempo:.3f} J{jugador.id_jugador} sin territorio, felicidad_nacional-2")
        if jugador.felicidad_nacional <= 0:
            evaluar_muerte_de_rey(partida, jugador.id_jugador, log)
            return [(evento.tiempo + 0.001, TipoEvento.FIN_TURNO, evento.entidades, {})]
    else:
        ordenes = contexto["obtener_ordenes"](jugador, partida, params, rng)
        for orden in ordenes:
            aplicar_orden(partida, params, jugador, orden, rng, log)
            if partida.finalizada:
                return []
    return [(evento.tiempo + 0.001, TipoEvento.GASTO_ADMINISTRACION, evento.entidades, {})]


def _h_gasto_administracion(partida, params, evento, rng, log, contexto):
    jugador = partida.jugadores[evento.entidades["id_jugador"]]
    for id_prov in list(jugador.provincias_controladas):
        p = partida.provincias[id_prov]
        if evaluar_riesgo_revuelta(p, params, rng):
            log(f"t={evento.tiempo:.3f} REVUELTA P{p.id_provincia} se pierde")
            jugador.provincias_controladas.remove(id_prov)

    provincias_jugador = [partida.provincias[i] for i in jugador.provincias_controladas]
    total_provincias = len(partida.provincias)
    total_poblacion = sum(p.poblacion_base for p in partida.provincias.values())
    ingreso_total = contexto["ingreso_impuesto"].get(jugador.id_jugador, 0.0)
    gasto = calcular_gasto_administracion(provincias_jugador, total_provincias, total_poblacion, ingreso_total, params)
    aplicar_gasto_administracion(jugador, provincias_jugador, gasto, params)
    log(f"t={evento.tiempo:.3f} EV_GASTO_ADMINISTRACION J{jugador.id_jugador} -{gasto:.2f}")
    return [(evento.tiempo + 0.001, TipoEvento.EVALUAR_VICTORIA, evento.entidades, {})]


def _h_evaluar_victoria(partida, params, evento, rng, log, contexto):
    partida.evaluar_condicion_victoria()
    return [(evento.tiempo + 0.001, TipoEvento.FIN_TURNO, evento.entidades, {})]


def _h_fin_turno(partida, params, evento, rng, log, contexto):
    log(f"t={evento.tiempo:.3f} EV_FIN_TURNO J{evento.entidades['id_jugador']}")
    contexto["turnos_completados"] += 1
    return []


_DESPACHO = {
    TipoEvento.INICIO_TURNO: _h_inicio_turno,
    TipoEvento.PROCESAR_DEMOGRAFIA: _h_procesar_demografia,
    TipoEvento.RECAUDAR_IMPUESTOS: _h_recaudar_impuestos,
    TipoEvento.RECAUDAR_IMPUESTO_ANUAL: _h_recaudar_impuesto_anual,
    TipoEvento.LIQUIDAR_MANTENIMIENTO: _h_liquidar_mantenimiento,
    TipoEvento.FASE_ORDENES: _h_fase_ordenes,
    TipoEvento.GASTO_ADMINISTRACION: _h_gasto_administracion,
    TipoEvento.EVALUAR_VICTORIA: _h_evaluar_victoria,
    TipoEvento.FIN_TURNO: _h_fin_turno,
}


def ejecutar_partida(partida, params, rng, obtener_ordenes, log, turnos_minimos=5, continuar_callback=None):
    cola = EventQueue()
    contexto = {"obtener_ordenes": obtener_ordenes, "ingreso_impuesto": {}, "turnos_completados": 0}
    orden_jugadores = list(partida.jugadores_activos)
    cola.push(0.0, TipoEvento.INICIO_TURNO, {"id_jugador": orden_jugadores[0]}, {})

    while cola and not partida.finalizada:
        evento = cola.pop()
        handler = _DESPACHO[evento.tipo]
        nuevos = handler(partida, params, evento, rng, log, contexto)
        for (t, tipo, ent, payload) in nuevos:
            cola.push(t, tipo, ent, payload)

        if evento.tipo == TipoEvento.FIN_TURNO and not partida.finalizada:
            id_actual = evento.entidades["id_jugador"]
            orden_jugadores = [j for j in orden_jugadores if j in partida.jugadores_activos]
            if not orden_jugadores:
                break
            if id_actual in orden_jugadores:
                siguiente_idx = (orden_jugadores.index(id_actual) + 1) % len(orden_jugadores)
            else:
                # id_actual fue eliminado durante su propio turno: reinicia desde el primero.
                siguiente_idx = 0
            if siguiente_idx == 0:
                partida.turno_actual += 1
                if contexto["turnos_completados"] >= turnos_minimos * len(orden_jugadores):
                    if continuar_callback is None or not continuar_callback(partida):
                        break
            siguiente_id = orden_jugadores[siguiente_idx]
            cola.push(evento.tiempo + 1.0, TipoEvento.INICIO_TURNO, {"id_jugador": siguiente_id}, {})

    return partida
