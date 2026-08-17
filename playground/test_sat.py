"""Quick checks for sat.solve and the sudoku encoding. Run: python test_sat.py"""

import sat
import sudoku


def _units(grid):
    """Yield the 27 row/col/box digit lists of a completed grid."""
    yield from (grid[r * 9:(r + 1) * 9] for r in range(9))              # rows
    yield from (grid[c::9] for c in range(9))                             # columns
    for br in (0, 3, 6):                                                  # boxes
        for bc in (0, 3, 6):
            yield [grid[9 * (br + r) + bc + c] for r in range(3) for c in range(3)]


def test_basics():
    # (a | b) & (a | ~b) & (~a | b)
    assert sat.solve([[1, 2], [1, -2], [-1, 2]], 2) == {1: True, 2: True}
    # contradiction
    assert sat.solve([[1], [-1]], 1) is None
    # unconstrained var defaults to False
    assert sat.solve([[1]], 2) == {1: True, 2: False}


def test_failed_branch_does_not_leak_state():
    # b=False satisfies the formula, but only after the b=True branch fails
    # and its forced c=True is rolled back.
    solution = sat.solve([[-1, 2], [-1, -2], [1, -2]], 2)
    assert solution is not None and solution[1] is False


def test_sudoku_roundtrip():
    puzzle = (
        "530070000600195000098000060"
        "800060003400803001700020006"
        "060000280000419005000080079"
    )
    solution = sudoku.solve_sudoku(puzzle)
    for unit in _units(solution):
        assert sorted(unit) == [str(d) for d in range(1, 10)]
    for r in range(9):
        for c in range(9):
            if puzzle[r * 9 + c] not in ".0":
                assert solution[r * 9 + c] == puzzle[r * 9 + c]


def test_sudoku_input_validation():
    try:
        sudoku.solve_sudoku("12345")
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError for short grid")


if __name__ == "__main__":
    test_basics()
    test_failed_branch_does_not_leak_state()
    test_sudoku_roundtrip()
    test_sudoku_input_validation()
    print("all tests passed")
