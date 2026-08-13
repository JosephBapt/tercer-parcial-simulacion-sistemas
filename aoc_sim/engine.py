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
