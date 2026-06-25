"""Generates valid, distinct starting positions for Cop and Thief."""

import random


def random_start_positions(grid_size: tuple[int, int], rng: random.Random | None = None) -> tuple[tuple, tuple]:
    """Pick two distinct random cells on a grid_size = (rows, cols) board.

    Raises if the grid has fewer than 2 cells (cannot seat both agents).

    `rng`, if given, is used instead of the module-level `random` — lets
    two independent processes (Phase 7 bonus: each group runs its own
    process driving its own agent) compute the *same* starting positions
    without any network coordination, by both constructing
    `random.Random(shared_seed)` from a seed they agreed on ahead of time
    (see `src.agents.bonus_peer`).
    """
    rows, cols = grid_size
    cells = [(r, c) for r in range(rows) for c in range(cols)]
    if len(cells) < 2:
        raise ValueError("Grid must have at least 2 cells for Cop and Thief")
    picker = rng or random
    cop_pos, thief_pos = picker.sample(cells, 2)
    return cop_pos, thief_pos
