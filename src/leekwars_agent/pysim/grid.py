"""PySim grid — diamond (rotated square) grid matching LeekWars game engine.

The real LeekWars grid is a rotated square: width=18, height=18 gives
stride = 2*18-1 = 35 and ~613 cells. Cell IDs are sequential.

Coordinate systems:
- cell_id: sequential integer 0..nb_cells-1
- (row, col): row = id // stride, col = id % stride
- (x, y): game coordinates used for distance/pathfinding
  y = row - (col % width)
  x = (id - (width-1)*y) / width

Distance = Manhattan on game (x, y): |x1-x2| + |y1-y2|
Movement = 4-directional (N/S/E/W) on the diamond grid.

Source: Cell.java, Pathfinding.java from leek-wars-generator.
"""

from __future__ import annotations

from collections import deque


class Grid:
    """Diamond grid matching the real LeekWars game engine."""

    def __init__(self, width: int = 18, height: int = 18,
                 obstacles: set[int] | None = None):
        self.width = width
        self.height = height
        self.stride = 2 * width - 1
        self.nb_cells = self.stride * height - (width - 1)
        self.obstacles: set[int] = obstacles or set()

        # Precompute game (x, y) for each cell
        self._x: list[int] = [0] * self.nb_cells
        self._y: list[int] = [0] * self.nb_cells
        # Precompute neighbors (N/S/E/W) for each cell
        self._neighbors: list[list[int]] = [[] for _ in range(self.nb_cells)]
        # Precompute direction availability (matching Cell.java boundary checks)
        self._init_cells()

    def _init_cells(self):
        """Precompute coordinates and neighbors for all cells.

        Matches Cell.java constructor and Map.java neighbor logic exactly.
        """
        w = self.width
        h = self.height
        stride = self.stride

        for cell_id in range(self.nb_cells):
            row = cell_id // stride
            col = cell_id % stride

            # Game coordinates (from Cell.java lines 48-50)
            y = row - (col % w)
            x = (cell_id - (w - 1) * y) // w
            self._x[cell_id] = x
            self._y[cell_id] = y

            # Direction availability (from Cell.java lines 32-46)
            north = True
            south = True
            east = True
            west = True

            if row == 0 and col < w:
                north = False
                west = False
            elif row + 1 == h and col >= w:
                east = False
                south = False
            if col == 0:
                south = False
                west = False
            elif col + 1 == w:
                north = False
                east = False

            # Neighbors from Map.getCellByDir() (Java source lines 725-738):
            # NORTH (NE): cell_id - width + 1  (= -17 for width=18)
            # EAST  (SE): cell_id + width       (= +18)
            # SOUTH (SW): cell_id + width - 1   (= +17)
            # WEST  (NW): cell_id - width       (= -18)
            neighbors = []
            if north:
                nb = cell_id - w + 1
                if 0 <= nb < self.nb_cells:
                    neighbors.append(nb)
            if east:
                nb = cell_id + w
                if 0 <= nb < self.nb_cells:
                    neighbors.append(nb)
            if south:
                nb = cell_id + w - 1
                if 0 <= nb < self.nb_cells:
                    neighbors.append(nb)
            if west:
                nb = cell_id - w
                if 0 <= nb < self.nb_cells:
                    neighbors.append(nb)

            self._neighbors[cell_id] = neighbors

    # For backward compatibility
    WIDTH = 18
    HEIGHT = 18
    CELLS = 613  # approximate — actual is nb_cells

    # ── coordinate helpers ────────────────────────────────────────────

    def cell_x(self, cell: int) -> int:
        """Game x-coordinate for cell."""
        if 0 <= cell < self.nb_cells:
            return self._x[cell]
        return 0

    def cell_y(self, cell: int) -> int:
        """Game y-coordinate for cell."""
        if 0 <= cell < self.nb_cells:
            return self._y[cell]
        return 0

    def distance(self, c1: int, c2: int) -> int:
        """Manhattan distance on game (x,y) coordinates.

        This matches Pathfinding.getCaseDistance() from the Java source:
        Math.abs(c1.getX() - c2.getX()) + Math.abs(c1.getY() - c2.getY())
        """
        if c1 < 0 or c2 < 0 or c1 >= self.nb_cells or c2 >= self.nb_cells:
            return 999
        return abs(self._x[c1] - self._x[c2]) + abs(self._y[c1] - self._y[c2])

    # ── cell queries ──────────────────────────────────────────────────

    def is_valid(self, cell: int) -> bool:
        """Cell in bounds and not obstacle."""
        return 0 <= cell < self.nb_cells and cell not in self.obstacles

    def neighbors(self, cell: int) -> list[int]:
        """4-directional walkable neighbors on the diamond grid."""
        if 0 <= cell < self.nb_cells:
            return [nb for nb in self._neighbors[cell] if nb not in self.obstacles]
        return []

    # ── line of sight (Bresenham on game x,y) ─────────────────────────

    def line_of_sight(
        self,
        c1: int,
        c2: int,
        blocking_entities: set[int] | None = None,
    ) -> bool:
        """Bresenham line rasterization in game (x,y) space.

        Obstacles and blocking_entities block LOS. Start/end cells don't block.
        """
        blockers = blocking_entities or set()
        x0, y0 = self._x[c1], self._y[c1]
        x1, y1 = self._x[c2], self._y[c2]

        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy

        while True:
            # Find cell at (x0, y0)
            cell = self._xy_to_cell(x0, y0)
            if cell is not None and cell != c1 and cell != c2:
                if cell in self.obstacles or cell in blockers:
                    return False
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

        return True

    def _xy_to_cell(self, x: int, y: int) -> int | None:
        """Convert game (x, y) back to cell_id. Returns None if out of bounds."""
        # Reverse of: y = row - (col % w), x = (id - (w-1)*y) / w
        # id = x * w + (w - 1) * y
        cell_id = x * self.width + (self.width - 1) * y
        if 0 <= cell_id < self.nb_cells:
            # Verify it maps back correctly
            if self._x[cell_id] == x and self._y[cell_id] == y:
                return cell_id
        return None

    # ── pathfinding ───────────────────────────────────────────────────

    def find_path_bfs(
        self, start: int, goal: int, blocked: set[int] | None = None
    ) -> list[int]:
        """BFS shortest path. Returns cells excluding start, including goal."""
        if start == goal:
            return []
        if start < 0 or goal < 0 or start >= self.nb_cells or goal >= self.nb_cells:
            return []

        blocked_set = blocked or set()
        visited: set[int] = {start}
        parent: dict[int, int] = {}
        queue: deque[int] = deque([start])

        while queue:
            current = queue.popleft()
            for nb in self._neighbors[current]:
                if nb in visited or nb in self.obstacles:
                    continue
                if nb != goal and nb in blocked_set:
                    continue
                visited.add(nb)
                parent[nb] = current
                if nb == goal:
                    path: list[int] = []
                    node = goal
                    while node != start:
                        path.append(node)
                        node = parent[node]
                    path.reverse()
                    return path
                queue.append(nb)

        return []

    def move_toward(
        self,
        start: int,
        target: int,
        max_steps: int,
        blocked: set[int] | None = None,
    ) -> list[int]:
        """Move up to max_steps cells toward target using BFS."""
        path = self.find_path_bfs(start, target, blocked)
        return path[:max_steps]

    def move_away_from(
        self,
        start: int,
        target: int,
        max_steps: int,
        blocked: set[int] | None = None,
    ) -> list[int]:
        """Move up to max_steps cells away from target (greedy)."""
        blocked_set = blocked or set()
        path: list[int] = []
        current = start
        visited = {start}

        for _ in range(max_steps):
            cur_dist = self.distance(current, target)
            best_cell: int | None = None
            best_dist = cur_dist

            for nb in self._neighbors[current]:
                if nb in self.obstacles or nb in blocked_set or nb in visited:
                    continue
                d = self.distance(nb, target)
                if d > best_dist:
                    best_dist = d
                    best_cell = nb

            if best_cell is None:
                break
            path.append(best_cell)
            visited.add(best_cell)
            current = best_cell

        return path
