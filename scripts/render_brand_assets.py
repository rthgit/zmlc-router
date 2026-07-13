from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


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


def _font(size: int, *, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    names = (
        ("DejaVuSans-Bold.ttf", "arialbd.ttf")
        if bold
        else ("DejaVuSansMono.ttf", "consola.ttf")
    )
    for name in names:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def render_demo(output: Path) -> None:
    width, height = 1200, 675
    image = Image.new("RGB", (width, height), "#07131f")
    draw = ImageDraw.Draw(image)
    title = _font(38, bold=True)
    body = _font(24)
    small = _font(19)
    draw.text((64, 52), "ZMLC // fail-closed Codex preflight", font=title, fill="#f8fafc")
    draw.text(
        (66, 108),
        "Stop spending model tokens on work bounded code can prove.",
        font=small,
        fill="#94a3b8",
    )

    panels = (
        (
            64,
            "VERIFIED PATH",
            "$ zmlc codex \"What is 25% of 80?\"",
            ("20", "Route: deterministic", "Codex calls: 0"),
            "#34d399",
        ),
        (
            620,
            "ABSTAIN + DELEGATE",
            "$ zmlc codex \"Review this repository\" --cd .",
            ("No verified solver", "Route: delegate_to_codex", "Prompt: unchanged"),
            "#22d3ee",
        ),
    )
    for left, label, command, lines, accent in panels:
        right = left + 516
        draw.rounded_rectangle(
            (left, 170, right, 574), radius=16, fill="#0d1d2d", outline="#24364a", width=2
        )
        draw.rounded_rectangle((left, 170, right, 218), radius=16, fill="#12263a")
        draw.rectangle((left, 202, right, 218), fill="#12263a")
        draw.ellipse((left + 20, 188, left + 32, 200), fill="#fb7185")
        draw.ellipse((left + 42, 188, left + 54, 200), fill="#fbbf24")
        draw.ellipse((left + 64, 188, left + 76, 200), fill="#34d399")
        draw.text((left + 22, 246), label, font=small, fill=accent)
        draw.text((left + 22, 294), command, font=small, fill="#e2e8f0")
        for index, line in enumerate(lines):
            fill = accent if index == 0 else "#cbd5e1"
            draw.text((left + 22, 372 + index * 48), line, font=body, fill=fill)
    draw.text(
        (64, 619),
        "No second model  |  No additional API key  |  Independent verification",
        font=small,
        fill="#94a3b8",
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output, optimize=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Render reproducible ZMLC plugin icons")
    parser.add_argument("--assets", type=Path, default=Path("plugins/zmlc-router/assets"))
    args = parser.parse_args()
    render(64, args.assets / "zmlc-router-64.png")
    render(512, args.assets / "zmlc-router-512.png")
    render_demo(args.assets / "zmlc-preflight-demo.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
