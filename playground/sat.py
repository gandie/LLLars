"""A small DPLL SAT solver with unit propagation.

Interface
---------
CNF over integer literals: ``n`` := variable ``n`` is true,
``-n`` := variable ``n`` is false.  A clause is a list of literals
(disjunction); a formula is a list of clauses (conjunction).

    from sat import solve
    a = solve([[1, 2], [1, -2], [-1, 2]], num_vars=2)
    # -> {1: True, 2: True}   or None if unsatisfiable

Search is classic DPLL: at each node, close under unit propagation, then
branch on the most-frequent variable of the remaining clauses.  State is
plain Python (lists + dict) -- the whole solver fits in one file.
"""

from __future__ import annotations


def _propagate(clauses, assignment):
    """Reduce ``clauses`` under ``assignment`` and force all unit literals.

    Returns ``(conflicted, clauses, assignment)`` where ``conflicted`` is
    True when the remaining constraints are contradictory.
    """

    def reduce(clause):
        for lit in clause:
            if assignment.get(abs(lit)) is (lit > 0):
                return None  # satisfied; drop
        return [lit for lit in clause if assignment.get(abs(lit)) is None]

    changed = True
    while changed:
        changed = False
        kept = []
        for clause in clauses:
            rest = reduce(clause)
            if rest is None:
                continue
            if not rest:
                return True, [], assignment  # empty clause -> contradictory
            if len(rest) == 1:
                var, value = abs(rest[0]), rest[0] > 0
                if assignment.get(var) is not value:
                    assignment[var] = value
                    changed = True
            else:
                kept.append(rest)
        clauses = kept
    return False, clauses, assignment


def _pick(clauses):
    """Most-frequent variable in ``clauses`` (deterministic on ties)."""
    counts = {}
    for clause in clauses:
        for lit in clause:
            var = abs(lit)
            counts[var] = counts.get(var, 0) + 1
    return max(counts, key=counts.__getitem__)


def _search(clauses, assignment):
    conflicted, clauses, assignment = _propagate(clauses, assignment)
    if conflicted:
        return None
    if not clauses:
        return dict(assignment)
    var = _pick(clauses)
    for value in (True, False):
        assignment[var] = value
        result = _search(clauses, assignment)
        if result is not None:
            return result
    del assignment[var]
    return None


def solve(clauses, num_vars):
    """Solve a CNF formula.

    Returns a complete assignment of variables ``1..num_vars`` as a
    ``dict[int, bool]``, or ``None`` if the formula is unsatisfiable.
    """
    result = _search([list(clause) for clause in clauses], {})
    if result is None:
        return None
    return {var: result.get(var, False) for var in range(1, num_vars + 1)}


if __name__ == "__main__":
    # (a | b) & (a | ~b) & (~a | b)
    print("sat:   ", solve([[1, 2], [1, -2], [-1, 2]], 2))
    # a & ~a
    print("unsat: ", solve([[1], [-1]], 1))
