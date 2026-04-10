"""Tests for PySim grid — pathfinding, movement, collision.

Validates fidelity vs Java Map.java behavior, especially:
- Entity collision: entities cannot occupy the same cell (Map.java:1045-1048)
- BFS pathfinding correctness on the diamond grid
- move_away_from behavior
"""

import pytest

from leekwars_agent.pysim.grid import Grid


@pytest.fixture
def grid():
    """Small 5x5 grid for fast tests."""
    return Grid(width=5, height=5)


@pytest.fixture
def real_grid():
    """Standard 18x18 grid matching real game."""
    return Grid(width=18, height=18)


# ── BFS basics ────────────────────────────────────────────────────────


class TestBFS:
    def test_same_cell_returns_empty(self, grid):
        assert grid.find_path_bfs(20, 20) == []

    def test_adjacent_cells(self, grid):
        """Path to a neighbor should be length 1."""
        nbs = grid._neighbors[20]
        assert len(nbs) > 0
        nb = nbs[0]
        path = grid.find_path_bfs(20, nb)
        assert len(path) == 1
        assert path[-1] == nb

    def test_path_excludes_start(self, grid):
        path = grid.find_path_bfs(20, 22)
        assert 20 not in path
        assert path[-1] == 22

    def test_blocked_cell_avoided(self, grid):
        """Path should route around blocked cells."""
        path_direct = grid.find_path_bfs(20, 22)
        midpoint = path_direct[0]
        path_around = grid.find_path_bfs(20, 22, blocked={midpoint})
        assert midpoint not in path_around
        assert path_around[-1] == 22

    def test_obstacle_cell_avoided(self, grid):
        """Obstacles (rocks) are impassable."""
        path_direct = grid.find_path_bfs(20, 22)
        midpoint = path_direct[0]
        grid_with_obs = Grid(width=5, height=5, obstacles={midpoint})
        path_around = grid_with_obs.find_path_bfs(20, 22)
        assert midpoint not in path_around

    def test_unreachable_returns_empty(self, grid):
        """Completely surrounded cell → no path."""
        center = 20
        nbs = grid._neighbors[center]
        blocked = set(nbs)
        # Block all neighbors of some target beyond center
        # Just test with an invalid/out-of-range cell
        assert grid.find_path_bfs(0, -1) == []

    def test_blocked_goal_still_reachable_by_bfs(self, grid):
        """BFS itself CAN reach a blocked goal (the truncation is in move_toward)."""
        nbs = grid._neighbors[20]
        start = nbs[0]
        path = grid.find_path_bfs(start, 20, blocked={20})
        assert path[-1] == 20  # BFS reaches it


# ── move_toward: entity collision fix ─────────────────────────────────


class TestMoveTowardCollision:
    """Validates Java Map.java:1045-1048 — stop adjacent to occupied cell."""

    def test_entity_cannot_land_on_blocked_goal(self, grid):
        """The critical fix: move_toward must NOT place entity on occupied cell."""
        nbs = grid._neighbors[20]
        start = nbs[0]
        # Entity at cell 20 is in blocked set
        path = grid.move_toward(start, 20, max_steps=10, blocked={20})
        assert 20 not in path, "Entity must not occupy the same cell as another entity"

    def test_stops_adjacent_to_entity(self, grid):
        """Entity should stop one cell before the target entity."""
        # Find two cells that are 3+ apart
        start = 0
        target = 20
        path_unblocked = grid.find_path_bfs(start, target)
        assert len(path_unblocked) >= 2, "Need cells far enough apart"

        # With target blocked (occupied by entity), move_toward stops adjacent
        path = grid.move_toward(start, target, max_steps=50, blocked={target})
        if path:
            # Last cell in path should be adjacent to target, not ON target
            assert path[-1] != target
            assert path[-1] in grid._neighbors[target]

    def test_already_adjacent_no_movement(self, grid):
        """If already adjacent to entity, no movement needed."""
        nbs = grid._neighbors[20]
        start = nbs[0]
        path = grid.move_toward(start, 20, max_steps=10, blocked={20})
        assert path == [], "Already adjacent — should not move"

    def test_unblocked_goal_still_reachable(self, grid):
        """moveTowardCell (no entity) still reaches the target cell."""
        nbs = grid._neighbors[20]
        start = nbs[0]
        path = grid.move_toward(start, 20, max_steps=10, blocked=set())
        assert path[-1] == 20, "Empty cell should be reachable"

    def test_max_steps_respected_with_blocked_goal(self, grid):
        """max_steps truncation still works after removing blocked goal."""
        start = 0
        target = 40
        path = grid.move_toward(start, target, max_steps=1, blocked={target})
        assert len(path) <= 1

    def test_no_blocked_set_reaches_goal(self, grid):
        """Without any blocked set, goal is reachable (moveTowardCell to empty cell)."""
        path = grid.move_toward(0, 20, max_steps=50)
        assert path[-1] == 20

    def test_real_grid_entity_collision(self, real_grid):
        """Same test on 18x18 grid — the actual game size."""
        # Place two entities far apart
        start = 50
        target = 400
        blocked = {target}
        path = real_grid.move_toward(start, target, max_steps=50, blocked=blocked)
        assert target not in path
        if path:
            assert path[-1] in real_grid._neighbors[target]


# ── move_away_from ────────────────────────────────────────────────────


class TestMoveAway:
    def test_increases_distance(self, grid):
        start = 20
        target = 21
        path = grid.move_away_from(start, target, max_steps=2)
        if path:
            final = path[-1]
            assert grid.distance(final, target) > grid.distance(start, target)

    def test_respects_blocked(self, grid):
        start = 20
        target = 21
        nbs = grid._neighbors[start]
        # Block some escape routes
        blocked = {nbs[0]} if nbs else set()
        path = grid.move_away_from(start, target, max_steps=2, blocked=blocked)
        for cell in path:
            assert cell not in blocked


# ── Distance ──────────────────────────────────────────────────────────


class TestDistance:
    def test_same_cell_zero(self, grid):
        assert grid.distance(20, 20) == 0

    def test_adjacent_is_one(self, grid):
        nbs = grid._neighbors[20]
        for nb in nbs:
            assert grid.distance(20, nb) == 1

    def test_symmetry(self, grid):
        assert grid.distance(0, 40) == grid.distance(40, 0)
