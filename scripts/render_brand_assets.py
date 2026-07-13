from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw


def quadratic(start: tuple[float, float], control: tuple[float, float], end: tuple[float, float]) -> list[tuple[float, float]]:
    points: list[tuple[float, float]] = []
    for index in range(25):
        t = index / 24
        inverse = 1 - t
        points.append(
            (
                inverse * inverse * start[0] + 2 * inverse * t * control[0] + t * t * end[0],
                inverse * inverse * start[1] + 2 * inverse * t * control[1] + t * t * end[1],
            )
        )
    return points


def render(size: int, output: Path) -> None:
    scale = size / 64
    supersample = 4
    factor = scale * supersample
    image = Image.new("RGBA", (size * supersample, size * supersample), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    def point(value: tuple[float, float]) -> tuple[int, int]:
        return round(value[0] * factor), round(value[1] * factor)

    draw.rounded_rectangle(
        (0, 0, size * supersample - 1, size * supersample - 1),
        radius=round(14 * factor),
        fill="#07131f",
    )
    width = round(4 * factor)
    top = [(12, 18), (18, 18), *quadratic((18, 18), (26, 18), (32, 28))[1:]]
    bottom = [(12, 46), (18, 46), *quadratic((18, 46), (26, 46), (32, 36))[1:]]
    draw.line([point(value) for value in top], fill="#22d3ee", width=width, joint="curve")
    draw.line([point(value) for value in [(12, 32), (24, 32)]], fill="#34d399", width=width)
    draw.line([point(value) for value in bottom], fill="#fbbf24", width=width, joint="curve")
    for value, color in (((12, 18), "#22d3ee"), ((12, 32), "#34d399"), ((12, 46), "#fbbf24")):
        x, y = point(value)
        radius = width // 2
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=color)
    center = point((34, 32))
    outer = round(11 * factor)
    draw.ellipse(
        (center[0] - outer, center[1] - outer, center[0] + outer, center[1] + outer),
        fill="#07131f",
        outline="#f8fafc",
        width=width,
    )
    inner = round(3.5 * factor)
    draw.ellipse(
        (center[0] - inner, center[1] - inner, center[0] + inner, center[1] + inner),
        fill="#34d399",
    )
    draw.line([point((45, 32)), point((54, 32))], fill="#f8fafc", width=width)
    x, y = point((54, 32))
    radius = width // 2
    draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill="#f8fafc")

    image = image.resize((size, size), Image.Resampling.LANCZOS)
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output, optimize=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Render reproducible ZMLC plugin icons")
    parser.add_argument("--assets", type=Path, default=Path("plugins/zmlc-router/assets"))
    args = parser.parse_args()
    render(64, args.assets / "zmlc-router-64.png")
    render(512, args.assets / "zmlc-router-512.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
