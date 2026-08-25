# Playground: SAT & Sudoku Solver

A self-contained SAT solver and a Sudoku solver built directly on top of it.
No dependencies for the core solvers; the optional web service uses FastAPI.

## Layout

| File               | Purpose                                             |
| ------------------ | --------------------------------------------------- |
| `sat.py`           | DPLL SAT solver with unit propagation (stdlib only) |
| `sudoku.py`        | Sudoku solver encoded as a CNF formula via `sat`    |
| `main.py`          | FastAPI service exposing the Sudoku solver          |
| `static/index.html`| Single-page web UI for the service                  |
| `test_sat.py`      | Tests for the SAT solver and the Sudoku encoding    |

## Documentation

- [docs/sat.md](docs/sat.md) — SAT solver: CNF format, DPLL algorithm, usage.
- [docs/sudoku.md](docs/sudoku.md) — Sudoku solver: CNF encoding, API, web service.

## Quickstart

Solve a small formula:

```bash
python sat.py
```

Solve a Sudoku puzzle (built-in example):

```bash
python sudoku.py
```

Run the tests:

```bash
python test_sat.py
```

Serve the Sudoku web UI (requires `pip install fastapi uvicorn`):

```bash
python -m uvicorn main:app --reload
# open http://127.0.0.1:8000
```
