"""Interfaz interactiva de CLI menús, estado y entrada del jugador"""

import re
import sys

from rich.console import Console

from .models import TipoControl, SIN_DUENO
from .ai import decidir_ordenes_ia

_console = Console()


class SalirDelJuego(Exception):
    """Se lanza cuando el jugador humano confirma que quiere abandonar la partida"""

_PATRONES_ERROR = (
    "orden descartada", "invalida", "invalido", "insuficiente", "no existe",
    "no es tuya", "no puedes", "no tienes", "no esta", "no quedan",
)
_PATRONES_EXITO = ("orden deshecha", "encola orden")

_ETIQUETAS_EVENTO = {
    "EV_INICIO_TURNO": "Inicio de turno",
    "EV_FIN_TURNO": "Fin de turno",
    "EV_PROCESAR_DEMOGRAFIA": "Crecimiento poblacional",
    "EV_RECAUDAR_IMPUESTOS": "Recaudacion de impuestos",
    "EV_RECAUDAR_COMERCIO": "Ingresos por comercio",
    "EV_RECAUDAR_IMPUESTO_ANUAL": "Impuesto anual",
    "EV_LIQUIDAR_MANTENIMIENTO": "Mantenimiento de tropas",
    "EV_GASTO_ADMINISTRACION": "Gasto de administracion",
    "EV_RESOLVER_ATAQUE": "Combate",
}

_PATRON_EVENTO = re.compile(r"^(?:t=[\d.]+\s+)?(EV_[A-Z_]+)\s*(.*)$")
_PATRON_JUGADOR_MONTO = re.compile(r"^J(\d+)\s*(?:([+-])([\d.]+))?$")
_PATRON_ATAQUE = re.compile(
    r"^E(\d+) vs P(\d+): Fa=([\d.]+) Fd=([\d.]+) gana=(\w+)$")


def _formatear_evento(mensaje):
    coincidencia = _PATRON_EVENTO.match(mensaje)
    if not coincidencia:
        return mensaje
    codigo, resto = coincidencia.groups()
    etiqueta = _ETIQUETAS_EVENTO.get(codigo)
    if etiqueta is None:
        return mensaje

    if codigo == "EV_RESOLVER_ATAQUE":
        m = _PATRON_ATAQUE.match(resto)
        if m:
            id_ejercito, id_provincia, fa, fd, gana = m.groups()
            ganador = "el atacante" if gana == "atacante" else "el defensor"
            return (f"{etiqueta}: E{id_ejercito} ataca P{id_provincia} "
                     f"(fuerza {fa} vs {fd}) -> gana {ganador}")
        return f"{etiqueta}: {resto}"

    m = _PATRON_JUGADOR_MONTO.match(resto)
    if m:
        id_jugador, signo, monto = m.groups()
        if monto is not None:
            return f"{etiqueta} (J{id_jugador}): {signo}{monto} oro"
        return f"{etiqueta} (J{id_jugador})"
    return f"{etiqueta}: {resto}" if resto else etiqueta


def _clasificar_estilo(mensaje):
    texto = mensaje.lower()
    inicio = mensaje.lstrip()
    if inicio.startswith("==="):
        return "bold cyan"
    if inicio.startswith("---"):
        return "bold magenta"
    if "< volver" in texto:
        return "bold yellow" if inicio.startswith("> ") else "grey58"
    if inicio.startswith("> "):
        return "bold yellow"
    if "[atacable]" in texto:
        return "yellow"
    if any(p in texto for p in _PATRONES_ERROR):
        return "bold red"
    if any(p in texto for p in _PATRONES_EXITO):
        return "bold green"
    if "partida finalizada" in texto:
        return "bold green"
    if ": +" in mensaje:
        return "green"
    if ": -" in mensaje:
        return "red"
    return None


def imprimir_rich(mensaje):
    """Imprime mensaje con estilo según su contenido"""
    _console.print(mensaje, style=_clasificar_estilo(mensaje), markup=False, highlight=False)

MENU = """
--- Ordenes de J{id_jugador} (turno {turno}) ---
1. Mover/atacar ejercito
2. Reforzar ejercito con guarnicion
3. Dividir ejercito
4. Ajustar impuestos
5. Reclutar tropas
6. Fortificar provincia
7. Invertir en infraestructura
8. Declarar guerra
9. Abandonar provincia
10. Desmantelar tropas
11. Aplicar decreto de felicidad
12. Crear ejercito desde guarnicion
13. Deshacer una orden
14. Ver mi estado

15. Pasar turno
0. Salir del juego
"""

OPCIONES_MENU = [
    ("1", "Mover/atacar ejercito"),
    ("2", "Reforzar ejercito con guarnicion"),
    ("3", "Dividir ejercito"),
    ("4", "Ajustar impuestos"),
    ("5", "Reclutar tropas"),
    ("6", "Fortificar provincia"),
    ("7", "Invertir en infraestructura"),
    ("8", "Declarar guerra"),
    ("9", "Abandonar provincia"),
    ("10", "Desmantelar tropas"),
    ("11", "Aplicar decreto de felicidad"),
    ("12", "Crear ejercito desde guarnicion"),
    ("13", "Deshacer una orden"),
    ("14", "Ver mi estado"),
    ("15", "Pasar turno"),
    ("0", "Salir del juego"),
]

_TEXTO_POR_OPCION = dict(OPCIONES_MENU)

CATEGORIAS_MENU = [
    ("Ejercitos", ["1", "2", "3", "12"]),
    ("Provincias", ["5", "6", "7", "9", "10", "11"]),
    ("Diplomacia", ["8"]),
    ("Sistema", ["4", "13", "14"]),
]

OPCION_PASAR_TURNO = ("15", "Pasar turno")
OPCION_SALIR_DEL_JUEGO = ("0", "Salir del juego")

_DESCRIPCIONES_ORDEN = {
    "MOVER": lambda o: (
        f"Mover/atacar ejercito E{o['id_ejercito']} ({o['cantidad']} tropas) -> P{o['provincia_destino']}"
        if o.get("cantidad") is not None
        else f"Mover/atacar ejercito E{o['id_ejercito']} -> P{o['provincia_destino']}"
    ),
    "REFORZAR_EJERCITO": lambda o: f"Reforzar ejercito E{o['id_ejercito']} con {o['cantidad']} tropas",
    "DIVIDIR_EJERCITO": lambda o: f"Dividir ejercito E{o['id_ejercito']} ({o['cantidad']} tropas al nuevo)",
    "CREAR_EJERCITO": lambda o: f"Crear ejercito con {o['cantidad']} tropas desde la guarnicion de P{o['id_provincia']}",
    "IMPUESTO": lambda o: f"Ajustar impuesto a {o['nuevo_nivel']:.0f}%",
    "RECLUTAR": lambda o: f"Reclutar {o['cantidad']} tropas en P{o['id_provincia']}",
    "FORTIFICAR": lambda o: f"Fortificar P{o['id_provincia']}",
    "INVERTIR_INFRAESTRUCTURA": lambda o: f"Invertir en infraestructura de P{o['id_provincia']}",
    "GUERRA": lambda o: f"Declarar guerra a J{o['id_objetivo']}",
    "ABANDONAR": lambda o: f"Abandonar P{o['id_provincia']}",
    "DESMANTELAR": lambda o: f"Desmantelar {o['cantidad']} tropas en P{o['id_provincia']}",
    "DECRETO_FELICIDAD": lambda o: f"Aplicar decreto de felicidad en P{o['id_provincia']}",
}


def _describir_orden(orden):
    descriptor = _DESCRIPCIONES_ORDEN.get(orden["tipo"])
    return descriptor(orden) if descriptor else str(orden)


def _mostrar_ordenes_actuales(ordenes, salida, titulo="Tus ordenes de este turno"):
    salida(f"=== {titulo} ===")
    if not ordenes:
        salida("  (aun no has dado ninguna orden)")
    else:
        for i, orden in enumerate(ordenes, start=1):
            salida(f"  {i}. {_describir_orden(orden)}")
    salida("")


def _formatear_provincia(p):
    marcas = []
    if p.tiene_rey:
        marcas.append("REY")
    if p.fortificada:
        marcas.append("fortificada")
    etiqueta = f" [{', '.join(marcas)}]" if marcas else ""
    return (f"P{p.id_provincia}: {p.tropas_guarnicion} tropas | felicidad {p.nivel_felicidad:.0f}% "
            f"| infraestructura nivel {p.nivel_infraestructura}{etiqueta}")


def _formatear_ejercito(e):
    return f"E{e.id_ejercito}: {e.cantidad_fuerza} tropas (en P{e.nodo_posicion_id})"


def _listar_provincias_propias(jugador, partida, salida, encabezado="Tus provincias"):
    salida(f"Tesoro: {jugador.oro_tesoro:.2f} oro")
    salida(f"{encabezado}:")
    if not jugador.provincias_controladas:
        salida("  (no controlas ninguna provincia)")
        return
    for id_prov in jugador.provincias_controladas:
        p = partida.provincias[id_prov]
        salida(f"  {_formatear_provincia(p)}")


def _describir_vecino(jugador, partida, id_vecino):
    v = partida.provincias[id_vecino]
    if v.id_propietario == jugador.id_jugador:
        return f"P{id_vecino} (propia): {v.tropas_guarnicion} tropas"
    if v.id_propietario == SIN_DUENO:
        return f"P{id_vecino} (sin dueño, ATACABLE): {v.tropas_guarnicion} tropas"
    fort = ", fortificada" if v.fortificada else ""
    return (f"P{id_vecino} (enemiga de J{v.id_propietario}{fort}, ATACABLE): "
            f"{v.tropas_guarnicion} tropas")


def _listar_ejercitos_propios(jugador, partida, salida, mostrar_vecinos=False):
    ejercitos = [e for e in partida.ejercitos.values() if e.id_propietario == jugador.id_jugador]
    salida("Tus ejercitos:")
    if not ejercitos:
        salida("  (no tienes ejercitos disponibles para mover)")
        return
    for e in ejercitos:
        origen = partida.provincias[e.nodo_posicion_id]
        salida(f"  {_formatear_ejercito(e)}")
        if not mostrar_vecinos:
            continue
        if not origen.nodos_vecinos:
            salida("    vecinos: ninguno")
        else:
            salida("    vecinos:")
            for id_vecino in origen.nodos_vecinos:
                salida(f"      -> {_describir_vecino(jugador, partida, id_vecino)}")


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


def _limpiar_pantalla_real():
    print("\033[H\033[J", end="")


def _mostrar_resumen_turno(resumen, salida, titulo="Lo que paso este turno"):
    if not resumen:
        return
    salida(f"=== {titulo} ===")
    for linea in resumen:
        salida(_formatear_evento(linea))
    salida("")


def _mostrar_estado_completo(jugador, partida, salida, titulo="Tu estado actual"):
    salida(f"=== {titulo} ===")
    salida(f"Impuesto actual: {jugador.nivel_impuesto:.0f}%")
    salida(f"Puntos de accion: {jugador.puntos_accion:.1f}")
    _listar_provincias_propias(jugador, partida, salida)
    _listar_ejercitos_propios(jugador, partida, salida)
    salida("")


def _obtener_ejercito_propio(jugador, partida, id_ejercito, salida):
    ejercito = partida.ejercitos.get(id_ejercito)
    if ejercito is None or ejercito.id_propietario != jugador.id_jugador:
        salida(f"Ejercito E{id_ejercito} no existe o no es tuyo. Orden descartada.")
        return None
    return ejercito


def _obtener_provincia_propia(jugador, partida, id_provincia, salida):
    provincia = partida.provincias.get(id_provincia)
    if provincia is None:
        salida(f"Provincia P{id_provincia} no existe. Orden descartada.")
        return None
    if provincia.id_propietario != jugador.id_jugador:
        salida(f"Provincia P{id_provincia} no es tuya. Orden descartada.")
        return None
    return provincia


def _cantidad_valida(cantidad, salida, minimo=1):
    if cantidad < minimo:
        salida(f"Cantidad invalida (debe ser >= {minimo}). Orden descartada.")
        return False
    return True


def _oro_suficiente(jugador, costo, salida):
    if jugador.oro_tesoro < costo:
        salida(f"Oro insuficiente: necesitas {costo:.2f}, tienes {jugador.oro_tesoro:.2f}. Orden descartada.")
        return False
    return True


def _leer_tecla_real():
    import termios
    import tty

    fd = sys.stdin.fileno()
    config_previa = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        caracter = sys.stdin.read(1)
        if caracter == "\x1b":
            resto = sys.stdin.read(2)
            if resto == "[A":
                return "ARRIBA"
            if resto == "[B":
                return "ABAJO"
            return "OTRA"
        if caracter in ("\r", "\n"):
            return "ENTER"
        if caracter == "\x03":
            raise KeyboardInterrupt
        return "OTRA"
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, config_previa)


def _seleccionar_opcion_flechas(jugador, partida, ordenes, salida, limpiar, leer_tecla):
    indice_pasar_turno = len(CATEGORIAS_MENU)
    indice_salir = indice_pasar_turno + 1
    total_items = indice_salir + 1
    indice_categoria = 0
    while True:
        limpiar()
        _mostrar_ordenes_actuales(ordenes, salida)
        salida(f"--- Ordenes de J{jugador.id_jugador} (turno {partida.turno_actual}) ---")
        salida("(Flechas arriba/abajo para moverte, Enter para elegir)")
        for i, (nombre_categoria, _numeros) in enumerate(CATEGORIAS_MENU):
            cursor = "> " if i == indice_categoria else "  "
            salida(f"{cursor}{nombre_categoria}")
        salida("")
        cursor_pasar_turno = "> " if indice_categoria == indice_pasar_turno else "  "
        salida(f"{cursor_pasar_turno}{OPCION_PASAR_TURNO[1]}")
        cursor_salir = "> " if indice_categoria == indice_salir else "  "
        salida(f"{cursor_salir}{OPCION_SALIR_DEL_JUEGO[1]}")
        tecla = leer_tecla()
        if tecla == "ARRIBA":
            indice_categoria = (indice_categoria - 1) % total_items
        elif tecla == "ABAJO":
            indice_categoria = (indice_categoria + 1) % total_items
        elif tecla == "ENTER":
            if indice_categoria == indice_pasar_turno:
                return OPCION_PASAR_TURNO[0]
            if indice_categoria == indice_salir:
                return OPCION_SALIR_DEL_JUEGO[0]
            nombre_categoria, numeros = CATEGORIAS_MENU[indice_categoria]
            items = [(n, _TEXTO_POR_OPCION[n]) for n in numeros] + [("VOLVER", "< Volver")]
            numero, _texto = _seleccionar_de_lista(
                items, lambda t: t[1], salida, limpiar, leer_tecla, titulo=f"--- {nombre_categoria} ---")
            if numero != "VOLVER":
                return numero


def _seleccionar_de_lista(items, formatear, salida, limpiar, leer_tecla, titulo):
    indice = 0
    while True:
        limpiar()
        salida(titulo)
        salida("(Flechas arriba/abajo para moverte, Enter para elegir)")
        for i, item in enumerate(items):
            cursor = "> " if i == indice else "  "
            salida(f"{cursor}{formatear(item)}")
        tecla = leer_tecla()
        if tecla == "ARRIBA":
            indice = (indice - 1) % len(items)
        elif tecla == "ABAJO":
            indice = (indice + 1) % len(items)
        elif tecla == "ENTER":
            return items[indice]


def _elegir_ejercito_propio(jugador, partida, salida, limpiar, leer_tecla, titulo,
                             mensaje_vacio="No tienes ejercitos disponibles."):
    ejercitos = [e for e in partida.ejercitos.values() if e.id_propietario == jugador.id_jugador]
    if not ejercitos:
        salida(mensaje_vacio)
        return None
    return _seleccionar_de_lista(
        ejercitos, _formatear_ejercito,
        salida, limpiar, leer_tecla, titulo)


def _elegir_provincia_propia(jugador, partida, salida, limpiar, leer_tecla, titulo, filtro=None,
                              mensaje_vacio="No tienes provincias disponibles para esta accion."):
    provincias = [partida.provincias[i] for i in jugador.provincias_controladas]
    if filtro is not None:
        provincias = [p for p in provincias if filtro(p)]
    if not provincias:
        salida(mensaje_vacio)
        return None
    return _seleccionar_de_lista(provincias, _formatear_provincia, salida, limpiar, leer_tecla, titulo)


def _elegir_jugador_objetivo(jugador, partida, salida, limpiar, leer_tecla, titulo):
    otros = [partida.jugadores[i] for i in partida.jugadores_activos if i != jugador.id_jugador]
    if not otros:
        salida("No quedan otros jugadores.")
        return None
    seleccionado = _seleccionar_de_lista(
        otros,
        lambda j: f"J{j.id_jugador} ({j.tipo_control.value}): "
                  f"relacion={jugador.relaciones_diplomaticas.get(j.id_jugador, 'Neutral')}",
        salida, limpiar, leer_tecla, titulo)
    return seleccionado.id_jugador


def menu_ordenes_humano(jugador, partida, params, rng, entrada=input, salida=imprimir_rich, limpiar=None,
                         resumen=None, aplicar=None, leer_tecla=None, log=None):
    """Menú interactivo para que el jugador seleccione órdenes"""
    if limpiar is None:
        limpiar = _limpiar_pantalla_real
    if resumen is None:
        resumen = []

    usar_flechas = entrada is input and leer_tecla is None and sys.stdin.isatty()
    if usar_flechas:
        leer_tecla = _leer_tecla_real
    elif leer_tecla is not None:
        usar_flechas = True

    limpiar()
    _mostrar_resumen_turno(resumen, salida)
    _mostrar_estado_completo(jugador, partida, salida, titulo="Tu estado al iniciar el turno")
    entrada("Presiona Enter para ver el menu de ordenes...")

    ordenes = []

    def _encolar(orden):
        ordenes.append(orden)
        if log is not None:
            log(f"J{jugador.id_jugador} encola orden (turno {partida.turno_actual}): {_describir_orden(orden)}")

    while True:
        if usar_flechas:
            opcion = _seleccionar_opcion_flechas(jugador, partida, ordenes, salida, limpiar, leer_tecla)
        else:
            limpiar()
            _mostrar_ordenes_actuales(ordenes, salida)
            salida(MENU.format(id_jugador=jugador.id_jugador, turno=partida.turno_actual))
            opcion = entrada("Elige una opcion: ").strip()
            if opcion == "":
                opcion = "15"

        if opcion == "15":
            if log is not None:
                log(f"J{jugador.id_jugador} elige: Pasar turno")
            break

        if opcion == "0":
            confirmacion = entrada("Seguro que quieres salir del juego? (s/n): ").strip().lower()
            if confirmacion == "s":
                if log is not None:
                    log(f"J{jugador.id_jugador} elige: Salir del juego")
                raise SalirDelJuego()
            salida("Cancelado, seguimos en el turno.")
            continue

        if log is not None:
            texto_opcion = next((t for n, t in OPCIONES_MENU if n == opcion), opcion)
            log(f"J{jugador.id_jugador} elige: {texto_opcion}")

        cantidad_ordenes_antes = len(ordenes)
        try:
            if opcion == "1":
                if usar_flechas:
                    ejercito = _elegir_ejercito_propio(
                        jugador, partida, salida, limpiar, leer_tecla,
                        titulo="Elige el ejercito a mover/atacar:",
                        mensaje_vacio="No tienes ejercitos disponibles para mover.")
                else:
                    _listar_ejercitos_propios(jugador, partida, salida, mostrar_vecinos=True)
                    id_ejercito = int(entrada("ID de ejercito propio: "))
                    ejercito = _obtener_ejercito_propio(jugador, partida, id_ejercito, salida)
                if ejercito is not None:
                    origen = partida.provincias[ejercito.nodo_posicion_id]
                    if not origen.nodos_vecinos:
                        salida(f"P{origen.id_provincia} no tiene provincias vecinas. Orden descartada.")
                    else:
                        if usar_flechas:
                            destino = _seleccionar_de_lista(
                                origen.nodos_vecinos,
                                lambda v: _describir_vecino(jugador, partida, v),
                                salida, limpiar, leer_tecla,
                                titulo=f"Elige destino desde P{origen.id_provincia}:")
                        else:
                            destino = int(entrada("ID de provincia destino: "))
                            if destino not in origen.nodos_vecinos:
                                salida(f"P{destino} no es vecino de P{origen.id_provincia}. Orden descartada.")
                                destino = None
                        if destino is not None:
                            texto_cantidad = entrada(
                                f"Cantidad de tropas a mover (Enter = mover las {ejercito.cantidad_fuerza} "
                                f"disponibles): ").strip()
                            if texto_cantidad == "":
                                _encolar({"tipo": "MOVER", "id_ejercito": ejercito.id_ejercito,
                                          "provincia_destino": destino})
                            else:
                                cantidad = int(texto_cantidad)
                                if not (0 < cantidad <= ejercito.cantidad_fuerza):
                                    salida(f"Cantidad invalida (debe ser entre 1 y {ejercito.cantidad_fuerza}). "
                                           f"Orden descartada.")
                                else:
                                    _encolar({"tipo": "MOVER", "id_ejercito": ejercito.id_ejercito,
                                              "provincia_destino": destino, "cantidad": cantidad})
            elif opcion == "2":
                if usar_flechas:
                    ejercito = _elegir_ejercito_propio(
                        jugador, partida, salida, limpiar, leer_tecla,
                        titulo="Elige el ejercito a reforzar:")
                else:
                    _listar_ejercitos_propios(jugador, partida, salida)
                    _listar_provincias_propias(jugador, partida, salida)
                    id_ejercito = int(entrada("ID de ejercito propio a reforzar: "))
                    ejercito = _obtener_ejercito_propio(jugador, partida, id_ejercito, salida)
                if ejercito is not None:
                    provincia = partida.provincias[ejercito.nodo_posicion_id]
                    salida(f"Guarnicion disponible en P{provincia.id_provincia}: {provincia.tropas_guarnicion}")
                    cantidad = int(entrada("Cantidad de tropas a fusionar desde la guarnicion: "))
                    if _cantidad_valida(cantidad, salida):
                        if cantidad > provincia.tropas_guarnicion:
                            salida(f"P{provincia.id_provincia} solo tiene {provincia.tropas_guarnicion} tropas "
                                   f"en guarnicion. Orden descartada.")
                        else:
                            _encolar({"tipo": "REFORZAR_EJERCITO", "id_ejercito": ejercito.id_ejercito,
                                             "cantidad": cantidad})
            elif opcion == "3":
                if usar_flechas:
                    ejercito = _elegir_ejercito_propio(
                        jugador, partida, salida, limpiar, leer_tecla,
                        titulo="Elige el ejercito a dividir:")
                else:
                    _listar_ejercitos_propios(jugador, partida, salida)
                    id_ejercito = int(entrada("ID de ejercito propio a dividir: "))
                    ejercito = _obtener_ejercito_propio(jugador, partida, id_ejercito, salida)
                if ejercito is not None:
                    cantidad = int(entrada("Cantidad de tropas para el nuevo ejercito: "))
                    if not (0 < cantidad < ejercito.cantidad_fuerza):
                        salida(f"Cantidad invalida para dividir E{ejercito.id_ejercito} (debe ser entre 1 y "
                               f"{ejercito.cantidad_fuerza - 1}). Orden descartada.")
                    else:
                        _encolar({"tipo": "DIVIDIR_EJERCITO", "id_ejercito": ejercito.id_ejercito,
                                         "cantidad": cantidad})
            elif opcion == "4":
                salida(f"Nivel de impuesto actual: {jugador.nivel_impuesto:.0f}%")
                nuevo_nivel = float(entrada("Nuevo nivel de impuesto (%): "))
                if nuevo_nivel < 0:
                    salida("Nivel de impuesto no puede ser negativo. Orden descartada.")
                else:
                    _encolar({"tipo": "IMPUESTO", "nuevo_nivel": nuevo_nivel})
            elif opcion == "5":
                salida(f"Costo por tropa: {params.costo_reclutamiento_por_tropa:.2f} oro")
                if usar_flechas:
                    provincia = _elegir_provincia_propia(
                        jugador, partida, salida, limpiar, leer_tecla,
                        titulo="Elige la provincia donde reclutar:")
                else:
                    _listar_provincias_propias(jugador, partida, salida)
                    id_prov = int(entrada("ID de provincia propia: "))
                    provincia = _obtener_provincia_propia(jugador, partida, id_prov, salida)
                if provincia is not None:
                    cantidad = int(entrada("Cantidad de tropas a reclutar: "))
                    if _cantidad_valida(cantidad, salida):
                        costo = cantidad * params.costo_reclutamiento_por_tropa
                        if _oro_suficiente(jugador, costo, salida):
                            _encolar({"tipo": "RECLUTAR", "id_provincia": provincia.id_provincia,
                                             "cantidad": cantidad})
            elif opcion == "6":
                salida(f"Costo de fortificacion: {params.costo_fortificacion:.2f} oro")
                if usar_flechas:
                    provincia = _elegir_provincia_propia(
                        jugador, partida, salida, limpiar, leer_tecla,
                        titulo="Elige la provincia a fortificar:",
                        filtro=lambda p: not p.fortificada,
                        mensaje_vacio="Todas tus provincias ya estan fortificadas.")
                    if provincia is not None and _oro_suficiente(jugador, params.costo_fortificacion, salida):
                        _encolar({"tipo": "FORTIFICAR", "id_provincia": provincia.id_provincia})
                else:
                    _listar_provincias_propias(jugador, partida, salida)
                    id_prov = int(entrada("ID de provincia propia a fortificar: "))
                    provincia = _obtener_provincia_propia(jugador, partida, id_prov, salida)
                    if provincia is not None:
                        if provincia.fortificada:
                            salida(f"P{id_prov} ya esta fortificada. Orden descartada.")
                        elif _oro_suficiente(jugador, params.costo_fortificacion, salida):
                            _encolar({"tipo": "FORTIFICAR", "id_provincia": id_prov})
            elif opcion == "7":
                salida(f"Costo de infraestructura: {params.costo_infraestructura:.2f} oro "
                       f"(+1 nivel, sube impuestos y crecimiento poblacional)")
                if usar_flechas:
                    provincia = _elegir_provincia_propia(
                        jugador, partida, salida, limpiar, leer_tecla,
                        titulo="Elige la provincia para invertir en infraestructura:")
                else:
                    _listar_provincias_propias(jugador, partida, salida)
                    id_prov = int(entrada("ID de provincia propia: "))
                    provincia = _obtener_provincia_propia(jugador, partida, id_prov, salida)
                if provincia is not None and _oro_suficiente(jugador, params.costo_infraestructura, salida):
                    _encolar({"tipo": "INVERTIR_INFRAESTRUCTURA", "id_provincia": provincia.id_provincia})
            elif opcion == "8":
                if usar_flechas:
                    id_objetivo = _elegir_jugador_objetivo(
                        jugador, partida, salida, limpiar, leer_tecla,
                        titulo="Elige el jugador a quien declarar la guerra:")
                    if id_objetivo is not None:
                        if jugador.relaciones_diplomaticas.get(id_objetivo) == "GUERRA":
                            salida(f"Ya estas en guerra con J{id_objetivo}. Orden descartada.")
                        else:
                            _encolar({"tipo": "GUERRA", "id_objetivo": id_objetivo})
                else:
                    _listar_otros_jugadores(jugador, partida, salida)
                    id_objetivo = int(entrada("ID de jugador objetivo: "))
                    if id_objetivo == jugador.id_jugador:
                        salida("No puedes declararte la guerra a ti mismo. Orden descartada.")
                    elif id_objetivo not in partida.jugadores or id_objetivo not in partida.jugadores_activos:
                        salida(f"J{id_objetivo} no existe o no esta activo. Orden descartada.")
                    elif jugador.relaciones_diplomaticas.get(id_objetivo) == "GUERRA":
                        salida(f"Ya estas en guerra con J{id_objetivo}. Orden descartada.")
                    else:
                        _encolar({"tipo": "GUERRA", "id_objetivo": id_objetivo})
            elif opcion == "9":
                salida("(No puedes abandonar la provincia donde esta tu rey)")
                if usar_flechas:
                    provincia = _elegir_provincia_propia(
                        jugador, partida, salida, limpiar, leer_tecla,
                        titulo="Elige la provincia a abandonar:",
                        filtro=lambda p: not p.tiene_rey,
                        mensaje_vacio="No tienes provincias que puedas abandonar.")
                    if provincia is not None:
                        _encolar({"tipo": "ABANDONAR", "id_provincia": provincia.id_provincia})
                else:
                    _listar_provincias_propias(jugador, partida, salida)
                    id_prov = int(entrada("ID de provincia propia a abandonar: "))
                    provincia = _obtener_provincia_propia(jugador, partida, id_prov, salida)
                    if provincia is not None:
                        if provincia.tiene_rey:
                            salida(f"No puedes abandonar P{id_prov}: contiene a tu rey. Orden descartada.")
                        else:
                            _encolar({"tipo": "ABANDONAR", "id_provincia": id_prov})
            elif opcion == "10":
                if usar_flechas:
                    provincia = _elegir_provincia_propia(
                        jugador, partida, salida, limpiar, leer_tecla,
                        titulo="Elige la provincia donde desmantelar tropas:")
                else:
                    _listar_provincias_propias(jugador, partida, salida)
                    id_prov = int(entrada("ID de provincia propia: "))
                    provincia = _obtener_provincia_propia(jugador, partida, id_prov, salida)
                if provincia is not None:
                    cantidad = int(entrada("Cantidad de tropas a desmantelar: "))
                    if _cantidad_valida(cantidad, salida):
                        if cantidad > provincia.tropas_guarnicion:
                            salida(f"P{provincia.id_provincia} solo tiene {provincia.tropas_guarnicion} tropas "
                                   f"en guarnicion. Orden descartada.")
                        else:
                            _encolar({"tipo": "DESMANTELAR", "id_provincia": provincia.id_provincia,
                                             "cantidad": cantidad})
            elif opcion == "11":
                salida(f"Costo del decreto: {params.costo_decreto:.2f} oro "
                       f"(+{params.delta_decreto_felicidad:.0f}% felicidad)")
                if usar_flechas:
                    provincia = _elegir_provincia_propia(
                        jugador, partida, salida, limpiar, leer_tecla,
                        titulo="Elige la provincia para el decreto de felicidad:")
                else:
                    _listar_provincias_propias(jugador, partida, salida)
                    id_prov = int(entrada("ID de provincia propia: "))
                    provincia = _obtener_provincia_propia(jugador, partida, id_prov, salida)
                if provincia is not None and _oro_suficiente(jugador, params.costo_decreto, salida):
                    _encolar({"tipo": "DECRETO_FELICIDAD", "id_provincia": provincia.id_provincia})
            elif opcion == "12":
                if usar_flechas:
                    provincia = _elegir_provincia_propia(
                        jugador, partida, salida, limpiar, leer_tecla,
                        titulo="Elige la provincia desde donde crear el ejercito:")
                else:
                    _listar_provincias_propias(jugador, partida, salida)
                    id_prov = int(entrada("ID de provincia propia: "))
                    provincia = _obtener_provincia_propia(jugador, partida, id_prov, salida)
                if provincia is not None:
                    cantidad = int(entrada("Cantidad de tropas para el nuevo ejercito: "))
                    if _cantidad_valida(cantidad, salida):
                        if cantidad > provincia.tropas_guarnicion:
                            salida(f"P{provincia.id_provincia} solo tiene {provincia.tropas_guarnicion} tropas "
                                   f"en guarnicion. Orden descartada.")
                        else:
                            _encolar({"tipo": "CREAR_EJERCITO", "id_provincia": provincia.id_provincia,
                                             "cantidad": cantidad})
            elif opcion == "13":
                if not ordenes:
                    salida("No tienes ordenes para deshacer.")
                elif usar_flechas:
                    indice_a_deshacer = _seleccionar_de_lista(
                        list(range(len(ordenes))), lambda i: _describir_orden(ordenes[i]),
                        salida, limpiar, leer_tecla, titulo="Elige la orden a deshacer:")
                    orden_removida = ordenes.pop(indice_a_deshacer)
                    salida(f"Orden deshecha: {_describir_orden(orden_removida)}")
                    if log is not None:
                        log(f"J{jugador.id_jugador} deshace orden (turno {partida.turno_actual}): "
                            f"{_describir_orden(orden_removida)}")
                else:
                    _mostrar_ordenes_actuales(ordenes, salida)
                    numero = int(entrada("Numero de orden a deshacer: "))
                    if 1 <= numero <= len(ordenes):
                        orden_removida = ordenes.pop(numero - 1)
                        salida(f"Orden deshecha: {_describir_orden(orden_removida)}")
                        if log is not None:
                            log(f"J{jugador.id_jugador} deshace orden (turno {partida.turno_actual}): "
                                f"{_describir_orden(orden_removida)}")
                    else:
                        salida("Numero de orden invalido.")
            elif opcion == "14":
                _mostrar_estado_completo(jugador, partida, salida, titulo="Tu estado actual")
            else:
                salida("Opcion invalida.")
        except ValueError:
            salida("Entrada invalida: se esperaba un numero. Orden descartada.")

        if aplicar is not None and len(ordenes) > cantidad_ordenes_antes:
            aplicar(ordenes[-1])

        salida("")

        if partida.finalizada:
            salida("La partida ha finalizado con esa orden.")
            break

        entrada("Presiona Enter para continuar...")

    limpiar()
    _mostrar_resumen_turno(resumen, salida, titulo="Resumen final de tu turno")
    _mostrar_estado_completo(jugador, partida, salida, titulo="Tu estado al finalizar el turno")
    return [] if aplicar is not None else ordenes


def obtener_ordenes_mixto(jugador, partida, params, rng):
    """Retorna órdenes del menú interactivo o IA según tipo de control"""
    if jugador.tipo_control == TipoControl.HUMANO:
        return menu_ordenes_humano(jugador, partida, params, rng)
    return decidir_ordenes_ia(jugador, partida, params, rng)
