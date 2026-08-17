from .models import TipoControl, SIN_DUENO
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


def _listar_provincias_propias(jugador, partida, salida, encabezado="Tus provincias"):
    salida(f"{encabezado} (oro disponible: {jugador.oro_tesoro:.2f}):")
    if not jugador.provincias_controladas:
        salida("  (no controlas ninguna provincia)")
        return
    for id_prov in jugador.provincias_controladas:
        p = partida.provincias[id_prov]
        marcas = []
        if p.tiene_rey:
            marcas.append("REY")
        if p.fortificada:
            marcas.append("fortificada")
        etiqueta = f" [{', '.join(marcas)}]" if marcas else ""
        salida(f"  P{p.id_provincia}: tropas={p.tropas_guarnicion} felicidad={p.nivel_felicidad:.0f}%{etiqueta}")


def _describir_vecino(jugador, partida, id_vecino):
    v = partida.provincias[id_vecino]
    if v.id_propietario == jugador.id_jugador:
        return f"P{id_vecino} (propia, tropas={v.tropas_guarnicion})"
    if v.id_propietario == SIN_DUENO:
        return f"P{id_vecino} (sin dueño, tropas={v.tropas_guarnicion}) [ATACABLE]"
    fort = " fortificada" if v.fortificada else ""
    return (f"P{id_vecino} (enemiga de J{v.id_propietario}, "
            f"tropas={v.tropas_guarnicion}{fort}) [ATACABLE]")


def _listar_ejercitos_propios(jugador, partida, salida):
    ejercitos = [e for e in partida.ejercitos.values() if e.id_propietario == jugador.id_jugador]
    salida("Tus ejercitos:")
    if not ejercitos:
        salida("  (no tienes ejercitos disponibles para mover)")
        return
    for e in ejercitos:
        origen = partida.provincias[e.nodo_posicion_id]
        if origen.nodos_vecinos:
            vecinos = ", ".join(_describir_vecino(jugador, partida, v) for v in origen.nodos_vecinos)
        else:
            vecinos = "ninguno"
        salida(f"  E{e.id_ejercito}: fuerza={e.cantidad_fuerza} en P{origen.id_provincia}")
        salida(f"    vecinos: {vecinos}")


def _listar_otros_jugadores(jugador, partida, salida):
    salida("Otros jugadores activos:")
    otros = [j for j in partida.jugadores_activos if j != jugador.id_jugador]
    if not otros:
        salida("  (no quedan otros jugadores)")
        return
    for id_otro in otros:
        otro = partida.jugadores[id_otro]
        relacion = jugador.relaciones_diplomaticas.get(id_otro, "Neutral")
        salida(f"  J{id_otro} ({otro.tipo_control.value}): relacion={relacion}")


def menu_ordenes_humano(jugador, partida, params, rng, entrada=input, salida=print):
    ordenes = []
    while True:
        salida(MENU.format(id_jugador=jugador.id_jugador, turno=partida.turno_actual))
        opcion = entrada("Elige una opcion: ").strip()

        if opcion == "9" or opcion == "":
            break

        try:
            if opcion == "1":
                _listar_ejercitos_propios(jugador, partida, salida)
                id_ejercito = int(entrada("ID de ejercito propio: "))
                destino = int(entrada("ID de provincia destino: "))
                ordenes.append({"tipo": "MOVER", "id_ejercito": id_ejercito, "provincia_destino": destino})
            elif opcion == "2":
                salida(f"Nivel de impuesto actual: {jugador.nivel_impuesto:.0f}%")
                nuevo_nivel = float(entrada("Nuevo nivel de impuesto (%): "))
                ordenes.append({"tipo": "IMPUESTO", "nuevo_nivel": nuevo_nivel})
            elif opcion == "3":
                _listar_provincias_propias(jugador, partida, salida)
                salida(f"Costo por tropa: {params.costo_reclutamiento_por_tropa:.2f} oro")
                id_prov = int(entrada("ID de provincia propia: "))
                cantidad = int(entrada("Cantidad de tropas a reclutar: "))
                ordenes.append({"tipo": "RECLUTAR", "id_provincia": id_prov, "cantidad": cantidad})
            elif opcion == "4":
                _listar_provincias_propias(jugador, partida, salida)
                salida(f"Costo de fortificacion: {params.costo_fortificacion:.2f} oro")
                id_prov = int(entrada("ID de provincia propia a fortificar: "))
                ordenes.append({"tipo": "FORTIFICAR", "id_provincia": id_prov})
            elif opcion == "5":
                _listar_otros_jugadores(jugador, partida, salida)
                id_objetivo = int(entrada("ID de jugador objetivo: "))
                ordenes.append({"tipo": "GUERRA", "id_objetivo": id_objetivo})
            elif opcion == "6":
                _listar_provincias_propias(jugador, partida, salida)
                salida("(No puedes abandonar la provincia donde esta tu rey)")
                id_prov = int(entrada("ID de provincia propia a abandonar: "))
                ordenes.append({"tipo": "ABANDONAR", "id_provincia": id_prov})
            elif opcion == "7":
                _listar_provincias_propias(jugador, partida, salida)
                id_prov = int(entrada("ID de provincia propia: "))
                cantidad = int(entrada("Cantidad de tropas a desmantelar: "))
                ordenes.append({"tipo": "DESMANTELAR", "id_provincia": id_prov, "cantidad": cantidad})
            elif opcion == "8":
                _listar_provincias_propias(jugador, partida, salida)
                salida(f"Costo del decreto: {params.costo_decreto:.2f} oro "
                       f"(+{params.delta_decreto_felicidad:.0f}% felicidad)")
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
