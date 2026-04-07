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

    # ── coordinate lookups ──────────────────────────────────────────────

    def cell_from_xy(self, x: int, y: int) -> int | None:
        """Convert game (x, y) to cell_id. Public version of _xy_to_cell.

        Java formula (FieldClass.getCellFromXY):
            getCell(x + width - 1, y)
        Where getCell(col, row) returns cells[row * stride + col].
        Our _xy_to_cell uses the raw game coords directly.
        """
        return self._xy_to_cell(x, y)

    def is_on_same_line(self, c1: int, c2: int) -> bool:
        """True if cells share game x or y coordinate (same row/col on diamond)."""
        if c1 < 0 or c2 < 0 or c1 >= self.nb_cells or c2 >= self.nb_cells:
            return False
        return self._x[c1] == self._x[c2] or self._y[c1] == self._y[c2]

    # ── spatial queries (range + launch_type + LOS) ───────────────────

    def verify_range(self, caster: int, target: int,
                     min_range: int, max_range: int,
                     launch_type: int = 7) -> bool:
        """Check if target is within range and satisfies launch_type constraints.

        launch_type bitmask (from Attack.java):
          bit 0 (1): allow lines (dx==0 or dy==0)
          bit 1 (2): allow diagonals (|dx|==|dy|)
          bit 2 (4): allow rest (other directions)
        Value 7 = all bits set = circle (no direction constraint).
        """
        if caster < 0 or target < 0 or caster >= self.nb_cells or target >= self.nb_cells:
            return False
        dx = self._x[caster] - self._x[target]
        dy = self._y[caster] - self._y[target]
        dist = abs(dx) + abs(dy)
        if dist > max_range or dist < min_range:
            return False
        if caster == target:
            return True
        # Launch type direction constraints
        if (launch_type & 1) == 0 and (dx == 0 or dy == 0):
            return False  # lines excluded
        if (launch_type & 2) == 0 and abs(dx) == abs(dy):
            return False  # diagonals excluded
        if (launch_type & 4) == 0 and abs(dx) != abs(dy) and dx != 0 and dy != 0:
            return False  # rest excluded
        return True

    def can_use_attack(self, caster: int, target: int,
                       min_range: int, max_range: int,
                       los: bool, launch_type: int = 7,
                       blocking: set[int] | None = None) -> bool:
        """Full range + LOS check for weapon/chip use. Matches Map.canUseAttack."""
        if not self.verify_range(caster, target, min_range, max_range, launch_type):
            return False
        if los and caster != target:
            return self.line_of_sight(caster, target, blocking)
        return True

    def get_possible_cast_cells(
        self,
        target: int,
        min_range: int,
        max_range: int,
        los: bool,
        launch_type: int = 7,
        cells_to_ignore: set[int] | None = None,
        blocking_entities: set[int] | None = None,
    ) -> list[int]:
        """All cells from which an attack can reach target.

        Matches Map.getPossibleCastCellsForTarget from Java source.
        For inline (launch_type=1): trace 4 cardinal lines from target.
        For circle (launch_type=7): scan all cells within range ring.
        """
        if target < 0 or target >= self.nb_cells:
            return []
        if target in self.obstacles:
            return []

        ignore = cells_to_ignore or set()
        result: list[int] = []
        tx, ty = self._x[target], self._y[target]

        if launch_type == 1:
            # Inline: trace 4 cardinal directions from target
            dirs = [(1, 0), (-1, 0), (0, 1), (0, -1)]
            for ddx, ddy in dirs:
                blocked = False
                for i in range(1, max_range + 1):
                    cell = self._xy_to_cell(tx + i * ddx, ty + i * ddy)
                    if cell is None:
                        break
                    if cell in self.obstacles:
                        break
                    if los and not blocked:
                        # Check if cell is occupied by blocking entity (blocks further)
                        if blocking_entities and cell in blocking_entities and cell not in ignore:
                            blocked = True
                            continue
                    elif los and blocked:
                        break
                    if i >= min_range and cell not in self.obstacles:
                        # Cell must be walkable and not ignored
                        if cell not in ignore or True:  # ignore list is "cells to exclude from results"
                            if self._is_available(cell, ignore):
                                result.append(cell)
        else:
            # Circle/star/etc: scan all cells within range ring
            for cell in range(self.nb_cells):
                if cell in self.obstacles:
                    continue
                if not self._is_available(cell, ignore):
                    continue
                if not self.verify_range(cell, target, min_range, max_range, launch_type):
                    continue
                if los and cell != target:
                    blocking = (blocking_entities or set()) - {cell, target}
                    if not self.line_of_sight(cell, target, blocking):
                        continue
                result.append(cell)

        return result

    def _is_available(self, cell: int, ignore: set[int]) -> bool:
        """Cell is walkable and not occupied (unless in ignore set)."""
        if cell in self.obstacles:
            return False
        return True  # entity occupation checked separately by engine

    # ── path toward line ──────────────────────────────────────────────

    def path_toward_line(self, start: int, cell1: int, cell2: int) -> list[int]:
        """BFS path toward the closest point on the line through cell1 and cell2.

        Matches Map.getPathTowardLine from Java source:
        1. Compute direction vector from cell1 to cell2
        2. Extend line in both directions to get all cells on the line
        3. BFS from start toward any cell on that line
        """
        if start < 0 or cell1 < 0 or cell2 < 0:
            return []
        if start >= self.nb_cells or cell1 >= self.nb_cells or cell2 >= self.nb_cells:
            return []

        x1, y1 = self._x[cell1], self._y[cell1]
        x2, y2 = self._x[cell2], self._y[cell2]
        dx = 0 if x2 == x1 else (1 if x2 > x1 else -1)
        dy = 0 if y2 == y1 else (1 if y2 > y1 else -1)
        if dx == 0 and dy == 0:
            return []

        # Collect all cells on the infinite line
        line_cells: set[int] = set()
        # Forward from cell1
        cx, cy = x1, y1
        while True:
            c = self._xy_to_cell(cx, cy)
            if c is None:
                break
            line_cells.add(c)
            cx += dx
            cy += dy
        # Backward from cell1
        cx, cy = x1 - dx, y1 - dy
        while True:
            c = self._xy_to_cell(cx, cy)
            if c is None:
                break
            line_cells.add(c)
            cx -= dx
            cy -= dy

        if not line_cells:
            return []
        if start in line_cells:
            return []

        # BFS from start toward any line cell
        return self._bfs_to_any(start, line_cells)

    def _bfs_to_any(self, start: int, goals: set[int],
                    blocked: set[int] | None = None) -> list[int]:
        """BFS shortest path from start to any cell in goals."""
        if start in goals:
            return []
        blocked_set = blocked or set()
        visited: set[int] = {start}
        parent: dict[int, int] = {}
        queue = __import__("collections").deque([start])

        while queue:
            current = queue.popleft()
            for nb in self._neighbors[current]:
                if nb in visited or nb in self.obstacles:
                    continue
                if nb not in goals and nb in blocked_set:
                    continue
                visited.add(nb)
                parent[nb] = current
                if nb in goals:
                    path: list[int] = []
                    node = nb
                    while node != start:
                        path.append(node)
                        node = parent[node]
                    path.reverse()
                    return path
                queue.append(nb)
        return []

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
