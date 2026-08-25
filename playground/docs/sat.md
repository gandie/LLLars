# SAT Solver (`sat.py`)

A small DPLL SAT solver with unit propagation, written in one file with the
Python standard library only.

## CNF format

Formulas are CNF over integer literals:

- `n`  means variable `n` is true.
- `-n` means variable `n` is false.
- A clause is a list of literals (disjunction, OR).
- A formula is a list of clauses (conjunction, AND).

```python
from sat import solve

# (a | b) & (a | ~b) & (~a | b), variables 1..2
solve([[1, 2], [1, -2], [-1, 2]], num_vars=2)
# -> {1: True, 2: True}
```

## API

### `solve(clauses, num_vars)`

Solves a CNF formula.

- **Returns** a complete assignment `dict[int, bool]` over variables
  `1..num_vars`, or `None` if the formula is unsatisfiable.
- Unconstrained variables default to `False` so the result is always
  complete.
- Input clauses are copied; the caller's lists are never mutated.

### `if __name__ == "__main__"`

Running `python sat.py` prints two demo results: a satisfiable formula and
the unsatisfiable `a & ~a`.

## Algorithm

Classic DPLL, three pieces:

1. **Unit propagation** (`_propagate`) — repeatedly reduce all clauses
   against the current assignment:
   - a clause with a true literal is dropped (satisfied),
   - a clause reduced to the empty list means conflict,
   - a unit clause forces its literal into the assignment.

   Returns `(conflicted, clauses, assignment)`.
2. **Variable choice** (`_pick`) — branch on the most-frequent variable in
   the remaining clauses. Ties are broken deterministically (first variable
   seen wins), so results are reproducible.
3. **Search** (`_search`) — propagate to a fixpoint; on conflict backtrack,
   on no remaining clauses return the model, otherwise branch `True` then
   `False`. Each branch works on a copy of the assignment
   (`{**assignment, var: value}`), so a failed branch can never leak partial
   state into the sibling branch.

## Properties

- **Deterministic** — fixed branching order and tie-breaking; the same
  formula always yields the same model.
- **Pure Python state** — lists and dicts only; no external dependencies.
- **Worst case exponential** in the number of variables (complete
  search); unit propagation and frequency-based branching keep practical
  instances fast. The full Sudoku encoding (729 variables, ~12,000 clauses)
  solves in a few milliseconds.

## Tests

`test_sat.py` covers:

- basic satisfiable / unsatisfiable formulas,
- defaulting of unconstrained variables,
- state isolation between sibling branches (a forced assignment from a
  failed branch must not leak).

Run with `python test_sat.py`.
