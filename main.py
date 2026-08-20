"""Punto de entrada principal"""

import argparse
import os
import random
from datetime import datetime

from aoc_sim.scenario import cargar_parametros, cargar_escenario
from aoc_sim.engine import ejecutar_partida
from aoc_sim.models import TipoControl
from aoc_sim.ai import decidir_ordenes_ia
from aoc_sim.cli import menu_ordenes_humano, imprimir_rich, SalirDelJuego


def _resumen_estado(partida):
    lineas = [f"\n=== Resumen turno {partida.turno_actual} ==="]
    for id_jugador in partida.jugadores_activos:
        j = partida.jugadores[id_jugador]
        provincias = [partida.provincias[i] for i in j.provincias_controladas]
        tropas = sum(p.tropas_guarnicion for p in provincias)
        felicidad_prom = sum(p.nivel_felicidad for p in provincias) / len(provincias) if provincias else 0.0
        lineas.append(
            f"J{id_jugador} ({j.tipo_control.value}): oro={j.oro_tesoro:.2f} "
            f"provincias={len(provincias)} tropas={tropas} felicidad_prom={felicidad_prom:.1f}"
        )
    return "\n".join(lineas)


def main():
    """Inicia la ejecucion de la simulación"""
    parser = argparse.ArgumentParser(description="Simulador Age of Conquest")
    parser.add_argument("--scenario", default="data/scenario.json")
    parser.add_argument("--params", default="data/params.json")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--turnos-min", type=int, default=5)
    parser.add_argument("--log-file", default="logs/partida.log",
                         help="Archivo donde se acumula el log de eventos de cada partida")
    args = parser.parse_args()

    partida = cargar_escenario(args.scenario)
    params = cargar_parametros(args.params)
    rng = random.Random(args.seed)

    directorio_log = os.path.dirname(args.log_file)
    if directorio_log:
        os.makedirs(directorio_log, exist_ok=True)
    archivo_log = open(args.log_file, "a", encoding="utf-8")
    archivo_log.write(f"\n===== Nueva partida {datetime.now().isoformat(timespec='seconds')} "
                       f"(seed={args.seed}, scenario={args.scenario}) =====\n")
    archivo_log.flush()

    def continuar(partida_actual):
        imprimir_rich(_resumen_estado(partida_actual))
        respuesta = input("Continuar otro turno? (s/n): ").strip().lower()
        return respuesta == "s"

    resumen_turno_actual = []

    def log_y_registrar(mensaje):
        if "EV_INICIO_TURNO" in mensaje:
            resumen_turno_actual.clear()
        imprimir_rich(mensaje)
        resumen_turno_actual.append(mensaje)
        archivo_log.write(mensaje + "\n")
        archivo_log.flush()

    def obtener_ordenes(jugador, partida_actual, params_actuales, rng_actual):
        if jugador.tipo_control == TipoControl.HUMANO:
            return menu_ordenes_humano(jugador, partida_actual, params_actuales, rng_actual,
                                        resumen=resumen_turno_actual, log=log_y_registrar)
        return decidir_ordenes_ia(jugador, partida_actual, params_actuales, rng_actual)

    try:
        try:
            ejecutar_partida(
                partida, params, rng, obtener_ordenes=obtener_ordenes,
                log=log_y_registrar, turnos_minimos=args.turnos_min, continuar_callback=continuar,
            )
        except SalirDelJuego:
            mensaje_salida = "\nPartida abandonada por el jugador."
            imprimir_rich(mensaje_salida)
            archivo_log.write(mensaje_salida + "\n")
            archivo_log.flush()
            return

        resumen_final = _resumen_estado(partida)
        imprimir_rich(resumen_final)
        archivo_log.write(resumen_final + "\n")
        if partida.finalizada:
            if partida.ganador is not None:
                mensaje_final = f"\nPartida finalizada. Gana J{partida.ganador}."
            else:
                mensaje_final = "\nPartida finalizada. Empate."
            imprimir_rich(mensaje_final)
            archivo_log.write(mensaje_final + "\n")
        archivo_log.flush()
    finally:
        archivo_log.close()


if __name__ == "__main__":
    main()
