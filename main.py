import argparse
import random

from aoc_sim.scenario import cargar_parametros, cargar_escenario
from aoc_sim.engine import ejecutar_partida, aplicar_orden
from aoc_sim.models import TipoControl
from aoc_sim.ai import decidir_ordenes_ia
from aoc_sim.cli import menu_ordenes_humano


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
    parser = argparse.ArgumentParser(description="Simulador Age of Conquest")
    parser.add_argument("--scenario", default="data/scenario.json")
    parser.add_argument("--params", default="data/params.json")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--turnos-min", type=int, default=5)
    args = parser.parse_args()

    partida = cargar_escenario(args.scenario)
    params = cargar_parametros(args.params)
    rng = random.Random(args.seed)

    def continuar(partida_actual):
        print(_resumen_estado(partida_actual))
        respuesta = input("Continuar otro turno? (s/n): ").strip().lower()
        return respuesta == "s"

    resumen_turno_actual = []

    def log_y_registrar(mensaje):
        if "EV_INICIO_TURNO" in mensaje:
            resumen_turno_actual.clear()
        print(mensaje)
        resumen_turno_actual.append(mensaje)

    def obtener_ordenes(jugador, partida_actual, params_actuales, rng_actual):
        if jugador.tipo_control == TipoControl.HUMANO:
            def aplicar_inline(orden):
                aplicar_orden(partida_actual, params_actuales, jugador, orden, rng_actual, log_y_registrar)

            return menu_ordenes_humano(jugador, partida_actual, params_actuales, rng_actual,
                                        resumen=resumen_turno_actual, aplicar=aplicar_inline)
        return decidir_ordenes_ia(jugador, partida_actual, params_actuales, rng_actual)

    ejecutar_partida(
        partida, params, rng, obtener_ordenes=obtener_ordenes,
        log=log_y_registrar, turnos_minimos=args.turnos_min, continuar_callback=continuar,
    )

    print(_resumen_estado(partida))
    if partida.finalizada:
        if partida.ganador is not None:
            print(f"\nPartida finalizada. Gana J{partida.ganador}.")
        else:
            print("\nPartida finalizada. Empate.")


if __name__ == "__main__":
    main()
