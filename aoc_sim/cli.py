from .models import TipoControl
from .ai import decidir_ordenes_ia

MENU = """
--- Ordenes de J{id_jugador} (turno {turno}) ---
1. Mover/atacar ejercito
2. Ajustar impuestos
3. Reclutar tropas
4. Fortificar provincia
5. Declarar guerra
6. Abandonar provincia
7. Desmantelar tropas
8. Aplicar decreto de felicidad
9. Pasar turno
"""


def menu_ordenes_humano(jugador, partida, params, rng, entrada=input, salida=print):
    ordenes = []
    while True:
        salida(MENU.format(id_jugador=jugador.id_jugador, turno=partida.turno_actual))
        opcion = entrada("Elige una opcion: ").strip()

        if opcion == "9" or opcion == "":
            break

        try:
            if opcion == "1":
                id_ejercito = int(entrada("ID de ejercito propio: "))
                destino = int(entrada("ID de provincia destino: "))
                ordenes.append({"tipo": "MOVER", "id_ejercito": id_ejercito, "provincia_destino": destino})
            elif opcion == "2":
                nuevo_nivel = float(entrada("Nuevo nivel de impuesto (%): "))
                ordenes.append({"tipo": "IMPUESTO", "nuevo_nivel": nuevo_nivel})
            elif opcion == "3":
                id_prov = int(entrada("ID de provincia propia: "))
                cantidad = int(entrada("Cantidad de tropas a reclutar: "))
                ordenes.append({"tipo": "RECLUTAR", "id_provincia": id_prov, "cantidad": cantidad})
            elif opcion == "4":
                id_prov = int(entrada("ID de provincia propia a fortificar: "))
                ordenes.append({"tipo": "FORTIFICAR", "id_provincia": id_prov})
            elif opcion == "5":
                id_objetivo = int(entrada("ID de jugador objetivo: "))
                ordenes.append({"tipo": "GUERRA", "id_objetivo": id_objetivo})
            elif opcion == "6":
                id_prov = int(entrada("ID de provincia propia a abandonar: "))
                ordenes.append({"tipo": "ABANDONAR", "id_provincia": id_prov})
            elif opcion == "7":
                id_prov = int(entrada("ID de provincia propia: "))
                cantidad = int(entrada("Cantidad de tropas a desmantelar: "))
                ordenes.append({"tipo": "DESMANTELAR", "id_provincia": id_prov, "cantidad": cantidad})
            elif opcion == "8":
                id_prov = int(entrada("ID de provincia propia: "))
                ordenes.append({"tipo": "DECRETO_FELICIDAD", "id_provincia": id_prov})
            else:
                salida("Opcion invalida.")
        except ValueError:
            salida("Entrada invalida: se esperaba un numero. Orden descartada.")
    return ordenes


def obtener_ordenes_mixto(jugador, partida, params, rng):
    if jugador.tipo_control == TipoControl.HUMANO:
        return menu_ordenes_humano(jugador, partida, params, rng)
    return decidir_ordenes_ia(jugador, partida, params, rng)
