from dataclasses import dataclass, field
from enum import Enum

SIN_DUENO = 0


class TipoControl(Enum):
    HUMANO = "HUMANO"
    IA = "IA"


class ObjetivoVictoria(Enum):
    ANIQUILACION = "ANIQUILACION"


@dataclass
class Provincia:
    id_provincia: int
    id_propietario: int
    poblacion_base: float
    nivel_felicidad: float
    nivel_infraestructura: int
    tropas_guarnicion: int
    nodos_vecinos: list
    fortificada: bool = False
    tiene_rey: bool = False
    esta_en_guerra: bool = False


@dataclass
class Ejercito:
    id_ejercito: int
    id_propietario: int
    cantidad_fuerza: float
    nodo_posicion_id: int
    contiene_rey: bool = False
    en_territorio_no_aliado: bool = False
    desde_barco: bool = False


@dataclass
class Jugador:
    id_jugador: int
    oro_tesoro: float
    puntos_accion: float
    nivel_impuesto: float
    tipo_control: TipoControl
    puesto_clasificacion: int
    provincias_controladas: list = field(default_factory=list)
    relaciones_diplomaticas: dict = field(default_factory=dict)
    rey_vivo: bool = True
    felicidad_nacional: float = 100.0


@dataclass
class Partida:
    objetivo_victoria: ObjetivoVictoria
    turno_limite: int
    jugadores: dict
    provincias: dict
    ejercitos: dict
    jugadores_activos: list = field(default_factory=list)
    turno_actual: int = 0
    finalizada: bool = False
    ganador: int = None

    def eliminar_jugador(self, id_jugador: int) -> None:
        if id_jugador in self.jugadores_activos:
            self.jugadores_activos.remove(id_jugador)
        self.jugadores[id_jugador].rey_vivo = False
        self.evaluar_condicion_victoria()

    def evaluar_condicion_victoria(self) -> None:
        if len(self.jugadores_activos) <= 1:
            self.finalizada = True
            self.ganador = self.jugadores_activos[0] if self.jugadores_activos else None
            return
        if self.turno_actual >= self.turno_limite:
            self.finalizada = True
            conteo = {
                jid: sum(1 for p in self.provincias.values() if p.id_propietario == jid)
                for jid in self.jugadores_activos
            }
            maximo = max(conteo.values())
            ganadores = [jid for jid, c in conteo.items() if c == maximo]
            self.ganador = ganadores[0] if len(ganadores) == 1 else None
