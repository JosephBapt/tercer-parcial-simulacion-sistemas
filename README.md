# Simulador Age of Conquest

Motor de simulación de eventos discretos (back-end) del caso de estudio Age of Conquest, para la evaluación "Implementación del Modelo Operacional y Defensa del Proyecto".

## Requisitos
- Python 3.11+
- `pip install pytest`

## Ejecutar
    python3 main.py --scenario data/scenario.json --params data/params.json --seed 42

## Tests
    pytest tests/ -v

## Estructura
- `aoc_sim/models.py` — entidades del Modelo Conceptual (Partida, Jugador, Provincia, Ejercito).
- `aoc_sim/events.py` — cola de eventos (`EventQueue`) y tipos de evento.
- `aoc_sim/engine.py` — fórmulas del modelo matemático y motor DES (dispatch table).
- `aoc_sim/ai.py` — árbol de decisión de la IA.
- `aoc_sim/scenario.py` — carga y validación de `data/scenario.json` y `data/params.json`.
- `aoc_sim/cli.py` — menú de órdenes del jugador humano.
- `data/` — escenario inicial y parámetros del modelo (editables sin tocar código).
