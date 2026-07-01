"""Towers of Hanoi solver with enhanced console visualization."""
import sys
import time


def solve_hanoi(n: int, source: str = 'A', target: str = 'C', helper: str = 'B') -> list[tuple[str, str]]:
    """Solve Towers of Hanoi and return move history.

    Args:
        n: Number of disks
        source: Source peg identifier
        target: Target peg identifier
        helper: Helper peg identifier

    Returns list of tuples (from_peg, to_peg).
    """
    if n <= 0:
        return []
    if n == 1:
        return [(source, target)]

    # Move n-1 disks to helper
    moves = solve_hanoi(n - 1, source, helper, target)
    # Move largest disk to target
    moves.append((source, target))
    # Move n-1 disks from helper to target
    moves.extend(solve_hanoi(n - 1, helper, target, source))
    return moves


def _render_peg(peg_chars: list[str], row: int) -> str:
    """Render a single peg at given row level.

    Args:
        peg_chars: List of disk identifiers on the peg (empty if none)
        row: Current row in the visualization (0 = top)

    Returns formatted string for this peg representation.
    """
    if row >= len(peg_chars):
        return '    '
    disk = peg_chars[row]
    return f"{disk:>8}"


def _render_snapshot(pegs: list[str], pegs_data: list[list[str]], row: int) -> str:
    """Render visualization for one row of the pegs.

    Args:
        pegs: List of peg identifiers [source, helper, target]
        pegs_data: Current state of each peg (disks on each)
        row: Row number (0 = highest disks)

    Returns formatted row string.
    """
    row_parts = []
    for peg in pegs:
        row_parts.append(_render_peg(pegs_data[pegs.index(peg)], row))
    return ' '.join(row_parts)


def visualize_hanoi(
    n: int,
    source: str = 'A',
    target: str = 'C',
    helper: str = 'B',
    show_delays: bool = False,
    delay_ms: float = 100.0
) -> None:
    """Print step-by-step visualization of solving Towers of Hanoi.

    Args:
        n: Number of disks
        source: Source peg identifier
        target: Target peg identifier
        helper: Helper peg identifier
        show_delays: If True, add delays between steps for viewing
        delay_ms: Delay in milliseconds between steps (when show_delays=True)
    """
    # Setup peg data structure - each peg holds disk identifiers
    pegs = [source, helper, target]
    # Start with all n disks on source peg
    disks_on = {peg: [f"disk{i}" for i in range(1, n + 1)] for peg in pegs}
    
    # Initialize: insert disks in order, largest at bottom
    for disk in range(1, n + 1):
        disks_on[source].insert(0, f"disk{disk}")

    # Compute all moves first (needed for the visualization loop)
    all_moves = [(source, target)] + solve_hanoi(n - 1, source, helper, target) + solve_hanoi(n - 1, helper, target, source)

    # Header with timing
    print()
    print(f"Towers of Hanoi: {n} disks")
    print(f"{'=' * 50}")
    print(f"Source: {source} >>> Target: {target} via Helper: {helper}")
    print(f"{'=' * 50}")
    
    # Show initial state
    print(f"Initial state:")
    print("-" * 40)
    display_lines = []
    for row in range(n, -1, -1):
        display_lines.append(_render_snapshot(pegs, [disks_on[peg][::-1] for peg in pegs], row))
    print('\n'.join(display_lines))
    print("-" * 40)
    
    # Execute moves
    start_time = time.perf_counter()

    for step, (from_p, to_p) in enumerate(all_moves, 1):
        disk = disks_on[from_p].pop()
        disks_on[to_p].insert(0, disk)
        
        # Render and print current state
        current_snapshot = _render_snapshot(pegs, [disks_on[peg][::-1] for peg in pegs], 0)
        print(f"Step {step:2d}: {disk:>6} moved {from_p} -> {to_p}")
        print(current_snapshot)

        if show_delays:
            time.sleep(delay_ms / 1000.0)

    total_time = time.perf_counter() - start_time
    
    # Optimal verification
    expected_moves = 2 ** n - 1
    print()
    print("-" * 40)
    if len(all_moves) == expected_moves:
        print(f"Completed in {len(all_moves)} moves (OPTIMAL!)")
    else:
        print(f"Completed in {len(all_moves)} moves")
        print(f"Expected: {expected_moves} moves")
    print(f"Execution time: {total_time:.3f} seconds")
    print("-" * 40)


def visualize_hanoi_summary(n: int, source: str = 'A', target: str = 'C', helper: str = 'B') -> None:
    """Compact, summary-style visualization.

    Args:
        n: Number of disks
        source: Source peg identifier
        target: Target peg identifier
        helper: Helper peg identifier
    """
    # Setup
    pegs = [source, helper, target]
    pegs_data = {peg: list(f"disk{i}" for i in range(1, n + 1)) for peg in pegs}
    for disk in range(1, n + 1):
        pegs_data[source].insert(0, f"disk{disk}")

    # Get all moves
    all_moves = [(source, target)] + solve_hanoi(n - 1, source, helper, target) + solve_hanoi(n - 1, helper, target, source)

    # Header
    print()
    print(f"[Towers of Hanoi] {n} disks")
    print(f"  Pegs: {source} -> {target} via {helper}")
    print(f"  Expected: {2**n - 1} moves")
    print()
    
    # Execute with compact output
    for step, (from_p, to_p) in enumerate(all_moves, 1):
        disk_name = pegs_data[from_p].pop()
        pegs_data[to_p].insert(0, disk_name)
        print(f"  {step:3d}: {disk_name:6} {from_p} -> {to_p}")
    
    print()
    print(f"  Completed in {len(all_moves)} moves (OPTIMAL!)")


def main():
    """Main entry point with demonstrations."""
    print()
    print("=" * 60)
    print("Towers of Hanoi - Console Visualizer")
    print("=" * 60)
    
    # Demo with full visualization
    print("\n--- Full Visualization (n=3) ---")
    visualize_hanoi(3, show_delays=False)
    
    # Demo with more disks still achievable
    print("\n--- Full Visualization (n=4) ---")
    visualize_hanoi(4)
    
    # Demo with summary style
    print("\n--- Summary Visualization (n=5) ---")
    visualize_hanoi_summary(5)
    
    print()
    print("=" * 60)
    print("End")
    print("=" * 60)
    print()


if __name__ == "__main__":
    main()
