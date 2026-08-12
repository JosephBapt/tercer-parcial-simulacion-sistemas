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
