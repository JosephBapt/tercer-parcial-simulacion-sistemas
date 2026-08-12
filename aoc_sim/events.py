import heapq
import itertools
from dataclasses import dataclass, field
from enum import Enum, auto


class TipoEvento(Enum):
    INICIO_TURNO = auto()
    PROCESAR_DEMOGRAFIA = auto()
    RECAUDAR_IMPUESTOS = auto()
    RECAUDAR_IMPUESTO_ANUAL = auto()
    LIQUIDAR_MANTENIMIENTO = auto()
    FASE_ORDENES = auto()
    GASTO_ADMINISTRACION = auto()
    EVALUAR_VICTORIA = auto()
    FIN_TURNO = auto()


@dataclass(order=True)
class EventoDES:
    tiempo: float
    seq: int
    tipo: TipoEvento = field(compare=False)
    entidades: dict = field(compare=False, default_factory=dict)
    payload: dict = field(compare=False, default_factory=dict)


class EventQueue:
    def __init__(self):
        self._heap = []
        self._contador = itertools.count()

    def push(self, tiempo, tipo, entidades=None, payload=None):
        evento = EventoDES(tiempo, next(self._contador), tipo, entidades or {}, payload or {})
        heapq.heappush(self._heap, evento)
        return evento

    def pop(self):
        return heapq.heappop(self._heap)

    def __len__(self):
        return len(self._heap)

    def __bool__(self):
        return len(self._heap) > 0
