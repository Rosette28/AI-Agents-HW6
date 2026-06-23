"""Generates valid, distinct starting positions for Cop and Thief."""

import random


def random_start_positions(grid_size: tuple[int, int]) -> tuple[tuple, tuple]:
    """Pick two distinct random cells on a grid_size = (rows, cols) board.

    Raises if the grid has fewer than 2 cells (cannot seat both agents).
    """
    rows, cols = grid_size
    cells = [(r, c) for r in range(rows) for c in range(cols)]
    if len(cells) < 2:
        raise ValueError("Grid must have at least 2 cells for Cop and Thief")
    cop_pos, thief_pos = random.sample(cells, 2)
    return cop_pos, thief_pos
