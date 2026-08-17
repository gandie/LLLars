"""Sudoku solver on top of the sat.DPLL solver.

Encoding: one boolean variable per (row, col, digit) triple, true meaning
that cell holds that digit.  Constraints:

  * every cell holds exactly one digit
  * each digit occurs exactly once in every row, column and 3x3 box
  * given clues are fixed by unit clauses
"""

import time

from sat import solve

DIGITS = list(range(1, 10))
NUM_VARS = 9 * 9 * 9


def var(row, col, digit):
    """SAT variable id (1..729) for a row/col/digit triple."""
    return (row * 9 + col) * 9 + digit


def build_clauses(grid):
    """Encode sudoku rules as CNF; ``grid`` is 81 chars of '.'/'0' and '1'..'9'."""
    clauses = []

    def exactly_one(variables):
        clauses.append(variables)  # ATLEAST1
        clauses.extend([          # ATMOST1 (one unit clause per negative lit)
            [-variables[i], -variables[j]]
            for i in range(9) for j in range(i + 1, 9)
        ])

    for r in range(9):
        for c in range(9):
            cell_vars = [var(r, c, d) for d in DIGITS]
            clue = grid[r * 9 + c]
            if clue in ".0":
                exactly_one(cell_vars)
            else:
                fixed = cell_vars[int(clue) - 1]
                clauses.append([fixed])                          # clue is true
                clauses.extend([[-v] for v in cell_vars if v != fixed])  # others false

    groups = (
        [[(r, c) for c in range(9)] for r in range(9)]          # rows
        + [[(r, c) for r in range(9)] for c in range(9)]        # columns
        + [[(r, c) for r in range(br, br + 3) for c in range(bc, bc + 3)]
           for br in (0, 3, 6) for bc in (0, 3, 6)]             # 3x3 boxes
    )
    for group in groups:
        for digit in DIGITS:
            exactly_one([var(r, c, digit) for r, c in group])

    return clauses


def solve_sudoku(grid):
    """Return the completed grid as an 81-char string, or None if unsolvable."""
    if len(grid) != 81 or not all(ch in ".0123456789" for ch in grid):
        raise ValueError("grid must be 81 chars of '.'/'0' or '1'..'9'")
    assignment = solve(build_clauses(grid), NUM_VARS)
    if assignment is None:
        return None
    return "".join(
        str(next(d for d in DIGITS if assignment[var(r, c, d)]))
        for r in range(9) for c in range(9)
    )


def render(grid):
    lines = []
    for r in range(9):
        if r and r % 3 == 0:
            lines.append("------+-------+------")
        cells = [grid[r * 9 + c] if grid[r * 9 + c] not in ".0" else " " for c in range(9)]
        lines.append(" ".join(cells[:3]) + "  |  " + " ".join(cells[3:6]) + "  |  " + " ".join(cells[6:9]))
    return "\n".join(lines)


if __name__ == "__main__":
    puzzle = (
        "530070000600195000098000060"
        "800060003400803001700020006"
        "060000280000419005000080079"
    )
    t0 = time.perf_counter()
    solution = solve_sudoku(puzzle)
    elapsed = time.perf_counter() - t0

    print("Puzzle")
    print(render(puzzle))
    print()
    if solution is None:
        print("No solution.")
    else:
        print("Solution")
        print(render(solution))
        print(f"\nsolved in {elapsed:.2f}s")
