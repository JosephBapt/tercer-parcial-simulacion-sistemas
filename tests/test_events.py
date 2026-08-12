from aoc_sim.events import EventQueue, TipoEvento


def test_pop_respeta_orden_por_tiempo_no_por_insercion():
    cola = EventQueue()
    cola.push(5.0, TipoEvento.FIN_TURNO)
    cola.push(1.0, TipoEvento.INICIO_TURNO)
    cola.push(3.0, TipoEvento.PROCESAR_DEMOGRAFIA)

    primero = cola.pop()
    segundo = cola.pop()
    tercero = cola.pop()

    assert [primero.tiempo, segundo.tiempo, tercero.tiempo] == [1.0, 3.0, 5.0]
    assert primero.tipo == TipoEvento.INICIO_TURNO


def test_empate_de_tiempo_respeta_orden_de_insercion():
    cola = EventQueue()
    cola.push(1.0, TipoEvento.INICIO_TURNO, entidades={"id_jugador": 1})
    cola.push(1.0, TipoEvento.INICIO_TURNO, entidades={"id_jugador": 2})

    primero = cola.pop()
    segundo = cola.pop()

    assert primero.entidades["id_jugador"] == 1
    assert segundo.entidades["id_jugador"] == 2


def test_len_y_bool():
    cola = EventQueue()
    assert len(cola) == 0
    assert bool(cola) is False
    cola.push(0.0, TipoEvento.INICIO_TURNO)
    assert len(cola) == 1
    assert bool(cola) is True
