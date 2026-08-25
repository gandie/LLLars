# Sudoku Solver (`sudoku.py`)

A 9x9 Sudoku solver built directly on the DPLL solver in [sat.py](sat.md).
The puzzle is translated to a CNF formula and handed to `sat.solve`. No
backtracking search logic is duplicated here — the SAT solver *is* the
search.

## Grid format

A puzzle is an 81-character string, row-major (top-left to bottom-right).

- `.` or `0` — empty cell.
- `1`..`9`  — a given clue.

```
"530070000"   row 0
"600195000"   row 1
...
"000080079"   row 8
```

## SAT encoding

One boolean variable per `(row, col, digit)` triple — `9 * 9 * 9 = 729`
variables. Variable `var(r, c, d)` is true iff cell `(r, c)` holds digit
`d` (with `DIGITS = 1..9`).

Constraints are emitted as CNF clauses:

1. **Every cell holds exactly one digit.**
   - *At least one*: one 9-literal clause `[v(1), ..., v(9)]` per cell.
   - *At most one*: 36 binary clauses `[-v(i), -v(j)]` for each pair.
2. **Each digit appears exactly once in every unit** — the 9 rows, 9
   columns, and 9 boxes (27 units total). Each unit/digit pair gets the same
   at-least-one + at-most-one pattern as (1).
3. **Clues are fixed.** For a given clue the matching variable is asserted
   with a unit clause `[v]` and every other variable in that cell is negated
   with `[-v]`.

The `exactly_one(variables)` helper builds the at-least-one + at-most-one
pair; `build_clauses(grid)` assembles all of it into the CNF list.

## API

### `solve_sudoku(grid)`

Solves the puzzle.

- **Returns** the completed grid as an 81-char string, or `None` if the
  puzzle is unsolvable.
- **Raises** `ValueError` if `grid` is not 81 characters of `.`/`0`/`1`..`9`.
- Clues in the input are preserved in the returned solution.

### `build_clauses(grid)`

Returns the list of CNF clauses encoding the puzzle (useful for
inspection/testing the encoding in isolation).

### `var(row, col, digit)`

Returns the 1-based SAT variable id (1..729) for a row/col/digit triple.

### `render(grid)`

Formats a grid (81-char string) as a human-readable 9-line ASCII block with
3x3 box separators and blank cells shown as spaces. Used by the demo and
easy to print anywhere.

### `if __name__ == "__main__"`

Running `python sudoku.py` solves a built-in 81-cell puzzle, prints both the
puzzle and the solution via `render`, and reports the solve time.

## Web service (`main.py`)

A small FastAPI app that wraps the solver.

- `GET /` — serves the single-page UI from `static/index.html`.
- `POST /solve` — body `{"grid": "<81 chars>"}`. Whitespace inside the grid
  is tolerated. Returns `{"solution": "<81 chars>", "elapsed_ms": <int>}`.
  - `400` for invalid grid input (bad length / characters).
  - `422` when the puzzle has no solution.

Run it:

```bash
pip install fastapi uvicorn
python -m uvicorn main:app --reload
# open http://127.0.0.1:8000
```

## Tests

`test_sat.py` covers the Sudoku side too:

- **round-trip** — the solved grid has every row, column, and box holding
  `1..9` exactly once, and all original clues are preserved.
- **input validation** — a short/invalid grid raises `ValueError`.

Run with `python test_sat.py`.
