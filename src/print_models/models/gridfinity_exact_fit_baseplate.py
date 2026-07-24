"""Dynamically tiled Gridfinity baseplate for an exact rectangular footprint."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from math import floor
from statistics import pstdev

NAME = "gridfinity_exact_fit_baseplate"
DESCRIPTION = (
    "Gridfinity baseplate sections that fill an exact outer footprint with the largest "
    "centered standard grid that fits."
)
PARAMETERS = {
    "outer_width": 407.0,
    "outer_depth": 298.0,
    "max_print_width": 240.0,
    "max_print_depth": 210.0,
    "allow_rotation": True,
    "include_full_plate": False,
}
PRINT_NOTES = (
    "Defaults make a 407 mm x 298 mm baseplate for a Prusa CORE One+ safe print area. "
    "The model computes the largest 42 mm Gridfinity grid that fits, centers it in the "
    "outer footprint, and splits printable tiles only on Gridfinity cell boundaries."
)

GRID_UNIT = 42.0


@dataclass(frozen=True)
class AxisTile:
    """One contiguous run of Gridfinity cells plus optional outer margin."""

    index: int
    cells: int
    start_cell: int
    before_margin: float
    after_margin: float

    @property
    def size(self) -> float:
        return self.before_margin + self.cells * GRID_UNIT + self.after_margin


@dataclass(frozen=True)
class TileLayout:
    """Computed printable tile layout."""

    cells_x: int
    cells_y: int
    x_margin: float
    y_margin: float
    x_tiles: tuple[AxisTile, ...]
    y_tiles: tuple[AxisTile, ...]


def build(
    outer_width: float = 407.0,
    outer_depth: float = 298.0,
    max_print_width: float = 240.0,
    max_print_depth: float = 210.0,
    allow_rotation: bool = True,
    include_full_plate: bool = False,
) -> Mapping[str, object]:
    """Build printable Gridfinity baseplate tiles for the requested footprint."""
    layout = _compute_layout(
        outer_width=outer_width,
        outer_depth=outer_depth,
        max_print_width=max_print_width,
        max_print_depth=max_print_depth,
        allow_rotation=allow_rotation,
    )

    results: dict[str, object] = {}

    if include_full_plate:
        results["full_plate"] = _build_tile(
            cells_x=layout.cells_x,
            cells_y=layout.cells_y,
            left_margin=layout.x_margin,
            right_margin=layout.x_margin,
            front_margin=layout.y_margin,
            back_margin=layout.y_margin,
        )

    row_count = len(layout.y_tiles)
    for y_tile in reversed(layout.y_tiles):
        row = row_count - y_tile.index
        for x_tile in layout.x_tiles:
            column = x_tile.index + 1
            name = f"tile_r{row}_c{column}_{x_tile.cells}x{y_tile.cells}u"
            results[name] = _build_tile(
                cells_x=x_tile.cells,
                cells_y=y_tile.cells,
                left_margin=x_tile.before_margin,
                right_margin=x_tile.after_margin,
                front_margin=y_tile.before_margin,
                back_margin=y_tile.after_margin,
            )

    return results


def _build_tile(
    *,
    cells_x: int,
    cells_y: int,
    left_margin: float,
    right_margin: float,
    front_margin: float,
    back_margin: float,
):
    """Build one tile, centered in its own local coordinate frame for slicing."""
    import cadquery as cq
    from cqgridfinity import GR_BASE_HEIGHT, GridfinityBaseplate

    grid = GridfinityBaseplate(cells_x, cells_y).render()
    grid_offset = ((left_margin - right_margin) / 2.0, (front_margin - back_margin) / 2.0, 0.0)
    grid = grid.translate(grid_offset)

    tile_width = left_margin + cells_x * GRID_UNIT + right_margin
    tile_depth = front_margin + cells_y * GRID_UNIT + back_margin
    grid_width = cells_x * GRID_UNIT

    result = grid

    margin_solids = []
    if left_margin > 0:
        margin_solids.append(
            _slab(cq, left_margin, tile_depth, GR_BASE_HEIGHT).translate(
                (-(tile_width - left_margin) / 2.0, 0.0, 0.0)
            )
        )
    if right_margin > 0:
        margin_solids.append(
            _slab(cq, right_margin, tile_depth, GR_BASE_HEIGHT).translate(
                ((tile_width - right_margin) / 2.0, 0.0, 0.0)
            )
        )
    if front_margin > 0:
        margin_solids.append(
            _slab(cq, grid_width, front_margin, GR_BASE_HEIGHT).translate(
                ((left_margin - right_margin) / 2.0, -(tile_depth - front_margin) / 2.0, 0.0)
            )
        )
    if back_margin > 0:
        margin_solids.append(
            _slab(cq, grid_width, back_margin, GR_BASE_HEIGHT).translate(
                ((left_margin - right_margin) / 2.0, (tile_depth - back_margin) / 2.0, 0.0)
            )
        )

    for solid in margin_solids:
        result = result.union(solid)

    return result


def _slab(cq, width: float, depth: float, height: float):
    return cq.Workplane("XY").rect(width, depth).extrude(height)


def _compute_layout(
    *,
    outer_width: float,
    outer_depth: float,
    max_print_width: float,
    max_print_depth: float,
    allow_rotation: bool,
) -> TileLayout:
    _validate_positive("outer_width", outer_width)
    _validate_positive("outer_depth", outer_depth)
    _validate_positive("max_print_width", max_print_width)
    _validate_positive("max_print_depth", max_print_depth)

    cells_x = floor(outer_width / GRID_UNIT)
    cells_y = floor(outer_depth / GRID_UNIT)
    if cells_x < 1 or cells_y < 1:
        raise ValueError(
            f"Footprint {outer_width} mm x {outer_depth} mm is too small for "
            f"one {GRID_UNIT:g} mm Gridfinity cell."
        )

    x_margin = (outer_width - cells_x * GRID_UNIT) / 2.0
    y_margin = (outer_depth - cells_y * GRID_UNIT) / 2.0

    best: tuple[tuple[float, ...], tuple[AxisTile, ...], tuple[AxisTile, ...]] | None = None

    for x_parts in range(1, cells_x + 1):
        for y_parts in range(1, cells_y + 1):
            x_tiles = _axis_tiles(cells_x, x_parts, x_margin)
            y_tiles = _axis_tiles(cells_y, y_parts, y_margin)

            if not _layout_fits(x_tiles, y_tiles, max_print_width, max_print_depth, allow_rotation):
                continue

            score = _layout_score(x_tiles, y_tiles)
            if best is None or score < best[0]:
                best = (score, x_tiles, y_tiles)

    if best is None:
        raise ValueError(
            "Could not split the baseplate into printable Gridfinity-boundary tiles for "
            f"a {max_print_width} mm x {max_print_depth} mm print area."
        )

    _, x_tiles, y_tiles = best
    return TileLayout(
        cells_x=cells_x,
        cells_y=cells_y,
        x_margin=x_margin,
        y_margin=y_margin,
        x_tiles=x_tiles,
        y_tiles=y_tiles,
    )


def _axis_tiles(cells: int, parts: int, outer_margin: float) -> tuple[AxisTile, ...]:
    cell_counts = _balanced_partition(cells, parts)
    tiles = []
    start_cell = 0

    for index, cell_count in enumerate(cell_counts):
        tiles.append(
            AxisTile(
                index=index,
                cells=cell_count,
                start_cell=start_cell,
                before_margin=outer_margin if index == 0 else 0.0,
                after_margin=outer_margin if index == parts - 1 else 0.0,
            )
        )
        start_cell += cell_count

    return tuple(tiles)


def _balanced_partition(total: int, parts: int) -> tuple[int, ...]:
    base = total // parts
    extra = total % parts
    return tuple(base + 1 if index < extra else base for index in range(parts))


def _layout_fits(
    x_tiles: tuple[AxisTile, ...],
    y_tiles: tuple[AxisTile, ...],
    max_print_width: float,
    max_print_depth: float,
    allow_rotation: bool,
) -> bool:
    for x_tile in x_tiles:
        for y_tile in y_tiles:
            if not _tile_fits(
                x_tile.size,
                y_tile.size,
                max_print_width,
                max_print_depth,
                allow_rotation,
            ):
                return False
    return True


def _tile_fits(
    width: float,
    depth: float,
    max_print_width: float,
    max_print_depth: float,
    allow_rotation: bool,
) -> bool:
    fits = width <= max_print_width and depth <= max_print_depth
    rotated_fits = allow_rotation and width <= max_print_depth and depth <= max_print_width
    return fits or rotated_fits


def _layout_score(
    x_tiles: tuple[AxisTile, ...], y_tiles: tuple[AxisTile, ...]
) -> tuple[float, ...]:
    tile_widths = [tile.size for tile in x_tiles]
    tile_depths = [tile.size for tile in y_tiles]
    return (
        len(x_tiles) * len(y_tiles),
        abs(len(x_tiles) - len(y_tiles)),
        pstdev(tile_widths) + pstdev(tile_depths),
        max(tile_widths) * max(tile_depths),
    )


def _validate_positive(name: str, value: float) -> None:
    if value <= 0:
        raise ValueError(f"{name} must be positive, got {value!r}.")
