from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple

Point = Tuple[float, float]


@dataclass(frozen=True)
class Shape:
    """A polygon shape represented by ordered points."""

    points: Tuple[Point, ...]

    @classmethod
    def from_points(cls, points: Sequence[Point]) -> "Shape":
        if len(points) < 3:
            raise ValueError("A shape needs at least 3 points")
        return cls(tuple(points))


def _fmt(value: float) -> str:
    return f"{value:g}"


def replicate_shape(
    shape: Shape,
    count: int,
    spacing: Point = (0.0, 0.0),
    start_offset: Point = (0.0, 0.0),
) -> List[Shape]:
    """Replicate a shape count times with configurable spacing and start offset."""
    if count < 1:
        raise ValueError("count must be >= 1")

    dx, dy = spacing
    sx, sy = start_offset
    replicas: List[Shape] = []
    for i in range(count):
        x_off = sx + i * dx
        y_off = sy + i * dy
        moved_points = tuple((x + x_off, y + y_off) for x, y in shape.points)
        replicas.append(Shape(moved_points))
    return replicas


def plot_shapes(shapes: Iterable[Shape], title: str = "Replicated Shapes"):
    """Plot shapes using matplotlib and return (fig, ax, plt)."""
    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise ImportError("matplotlib is required to plot shapes") from exc

    fig, ax = plt.subplots()
    for shape in shapes:
        xs = [p[0] for p in shape.points] + [shape.points[0][0]]
        ys = [p[1] for p in shape.points] + [shape.points[0][1]]
        ax.plot(xs, ys)
    ax.set_aspect("equal", adjustable="box")
    ax.set_title(title)
    return fig, ax, plt


def export_shapes_to_svg(
    shapes: Iterable[Shape],
    output_path: str | Path,
    stroke: str = "black",
    fill: str = "none",
    stroke_width: float = 1.0,
    padding: float = 10.0,
) -> Path:
    """Export shapes to an SVG file."""
    shape_list = list(shapes)
    if not shape_list:
        raise ValueError("At least one shape is required")

    all_points = [point for shape in shape_list for point in shape.points]
    min_x = min(point[0] for point in all_points)
    min_y = min(point[1] for point in all_points)
    max_x = max(point[0] for point in all_points)
    max_y = max(point[1] for point in all_points)

    width = (max_x - min_x) + 2 * padding
    height = (max_y - min_y) + 2 * padding
    x_offset = padding - min_x
    y_offset = padding - min_y

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    polygons = []
    for shape in shape_list:
        points_str = " ".join(
            f"{_fmt(x + x_offset)},{_fmt(y + y_offset)}" for x, y in shape.points
        )
        polygons.append(
            f'<polygon points="{points_str}" stroke="{stroke}" fill="{fill}" stroke-width="{stroke_width}" />'
        )

    width_text = _fmt(width)
    height_text = _fmt(height)
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width_text}" height="{height_text}" '
        f'viewBox="0 0 {width_text} {height_text}">\n'
        + "\n".join(polygons)
        + "\n</svg>\n"
    )
    path.write_text(svg, encoding="utf-8")
    return path


if __name__ == "__main__":
    base = Shape.from_points([(0, 0), (20, 0), (10, 15)])
    copies = replicate_shape(base, count=4, spacing=(30, 10))

    # Graph the shapes if matplotlib is available
    try:
        fig, _, plt = plot_shapes(copies)
        fig.savefig("replicated_shapes_plot.svg", format="svg")
        plt.close(fig)
    except ImportError:
        pass

    # Export as an SVG using the direct exporter
    export_shapes_to_svg(copies, "replicated_shapes.svg")
