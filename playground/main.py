"""FastAPI app exposing the sudoku SAT solver.

Run:  python -m uvicorn main:app --reload
API:  POST /solve  {"grid": "53.070000..."} -> {"solution": "534678912...", "elapsed_ms": 3}
      400 invalid input, 422 no solution.
"""

import time
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

import sudoku

STATIC = Path(__file__).with_name("static")

app = FastAPI(title="Sudoku SAT Solver")


class Puzzle(BaseModel):
    grid: str
    """81 chars, row-major; blanks as '.' or '0'."""


class Solved(BaseModel):
    solution: str
    elapsed_ms: int


@app.post("/solve", response_model=Solved)
def solve_puzzle(puzzle: Puzzle):
    grid = "".join(puzzle.grid.split())  # tolerate spaces/newlines
    try:
        t0 = time.perf_counter()
        solution = sudoku.solve_sudoku(grid)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    if solution is None:
        raise HTTPException(422, "puzzle has no solution")
    return Solved(solution=solution, elapsed_ms=int(round((time.perf_counter() - t0) * 1000)))


@app.get("/", response_class=HTMLResponse)
def index():
    return (STATIC / "index.html").read_text()
