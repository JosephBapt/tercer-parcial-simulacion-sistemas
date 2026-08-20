# Simulador Age of Conquest

Motor de simulación de eventos discretos (back-end) del caso de estudio Age of Conquest, para la evaluación "Implementación del Modelo Operacional y Defensa del Proyecto".

## Requisitos
- Python 3.11+
- `pip install pytest`

## Ejecutar
    python3 main.py --scenario data/scenario.json --params data/params.json --seed 42

## Tests
    pytest tests/ -v

## Extra: ejecutar con uv (sin instalar nada globalmente)
Si tienes [uv](https://docs.astral.sh/uv/) instalado, no hace falta crear un venv ni instalar pytest a mano (el proyecto ya trae `pyproject.toml`/`uv.lock`):

    uv run python3 main.py --seed 42
    uv run pytest tests/ -v

## Escenarios
Además de `data/scenario.json` (por defecto), hay 3 escenarios listos para distinta dificultad:

    uv run python3 main.py --scenario data/scenario_facil.json --params data/params.json --seed 42
    uv run python3 main.py --scenario data/scenario_medio.json --params data/params.json --seed 42
    uv run python3 main.py --scenario data/scenario_dificil.json --params data/params.json --seed 42
