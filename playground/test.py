"""Test suite for Towers of Hanoi solver."""
import unittest
from main import solve_hanoi


class TestHanoiSolveCore(unittest.TestCase):
    """Core correctness tests."""

    def test_single_disk(self):
        """One disk: A -> C (1 move)."""
        moves = solve_hanoi(1, 'A', 'C', 'B')
        self.assertEqual(len(moves), 1)
        self.assertEqual(moves, [('A', 'C')])

    def test_two_disks(self):
        """Two disks: A->B, A->C, B->C (3 moves)."""
        moves = solve_hanoi(2, 'A', 'C', 'B')
        self.assertEqual(len(moves), 3)
        self.assertEqual(moves, [('A', 'B'), ('A', 'C'), ('B', 'C')])

    def test_three_disks(self):
        """Three disks: 7 moves. First move is A->C (disk 1 to helper)."""
        moves = solve_hanoi(3, 'A', 'C', 'B')
        self.assertEqual(len(moves), 7)
        # First move transfers disk 1 to helper peg (intermediate in this call)
        self.assertEqual(moves[0], ('A', 'C'))
        # Last move for n>=3 lands on target peg
        self.assertEqual(moves[-1][1], 'C')

    def test_zero_disks(self):
        """Zero disks: no moves."""
        moves = solve_hanoi(0, 'A', 'C', 'B')
        self.assertEqual(len(moves), 0)
        self.assertEqual(moves, [])


class TestHanoiSolveOptimal(unittest.TestCase):
    """Test that solutions are optimal (always 2^n - 1 moves)."""

    def test_optimal_moves_n1(self):
        n = 1
        moves = solve_hanoi(n, 'A', 'C', 'B')
        self.assertEqual(len(moves), 2**n - 1)

    def test_optimal_moves_n2(self):
        n = 2
        moves = solve_hanoi(n, 'A', 'C', 'B')
        self.assertEqual(len(moves), 2**n - 1)

    def test_optimal_moves_n3(self):
        n = 3
        moves = solve_hanoi(n, 'A', 'C', 'B')
        self.assertEqual(len(moves), 2**n - 1)

    def test_optimal_moves_n4(self):
        n = 4
        moves = solve_hanoi(n, 'A', 'C', 'B')
        self.assertEqual(len(moves), 2**n - 1)

    def test_optimal_moves_n5(self):
        n = 5
        moves = solve_hanoi(n, 'A', 'C', 'B')
        self.assertEqual(len(moves), 2**n - 1)


class TestHanoiCustomPegs(unittest.TestCase):
    """Test with arbitrary peg names."""

    def test_custom_names(self):
        """Works with any peg names."""
        moves = solve_hanoi(2, 'Left', 'Right', 'Middle')
        self.assertEqual(len(moves), 3)

    def test_four_disks_custom(self):
        """Four disks with custom pegs."""
        moves = solve_hanoi(4, 'X', 'Y', 'Z')
        self.assertEqual(len(moves), 15)

    def test_last_move_tracing(self):
        """Verify last move by tracing algorithm."""
        moves = solve_hanoi(4, 'X', 'Y', 'Z')
        self.assertEqual(len(moves), 15)
        # First move is always source->helper for n>1
        self.assertEqual(moves[0], ('X', 'Z'))
        # Last move lands on target
        self.assertEqual(moves[-1][1], 'Y')


class TestHanoiStructure(unittest.TestCase):
    """Structural properties of the solution."""

    def test_first_move_source(self):
        """First move must be from source."""
        n = 3
        moves = solve_hanoi(n, 'S', 'T', 'H')
        self.assertEqual(moves[0][0], 'S')

    def test_last_move_target(self):
        """Last move must land on target."""
        n = 3
        moves = solve_hanoi(n, 'S', 'T', 'H')
        self.assertEqual(moves[-1][1], 'T')

    def test_move_valid_peg_names(self):
        """All move sources and destinations must be valid peg names."""
        n = 4
        moves = solve_hanoi(n, 'A', 'C', 'B')
        valid_pegs = {'A', 'B', 'C'}
        for from_p, to_p in moves:
            self.assertIn(from_p, valid_pegs)
            self.assertIn(to_p, valid_pegs)


if __name__ == "__main__":
    unittest.main()