"""Render the canonical web LogoMark as macOS PNG and ICNS assets."""

from __future__ import annotations

import shutil
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
ICONS = ROOT / "src-tauri/icons"


def cubic(start, first, second, end, steps=80):
    for index in range(steps + 1):
        t = index / steps
        u = 1 - t
        yield (
            u**3 * start[0]
            + 3 * u**2 * t * first[0]
            + 3 * u * t**2 * second[0]
            + t**3 * end[0],
            u**3 * start[1]
            + 3 * u**2 * t * first[1]
            + 3 * u * t**2 * second[1]
            + t**3 * end[1],
        )


def render(size: int) -> Image.Image:
    scale = 4
    canvas = Image.new("RGBA", (size * scale, size * scale), (0, 0, 0, 0))
    shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    margin = size * scale * 0.075
    bounds = (margin, margin, size * scale - margin, size * scale - margin)
    radius = size * scale * 0.21
    shadow_draw.rounded_rectangle(
        (bounds[0], bounds[1] + size * scale * 0.025, bounds[2], bounds[3] + size * scale * 0.025),
        radius=radius,
        fill=(45, 37, 168, 80),
    )
    canvas.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(size * scale * 0.025)))
    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle(bounds, radius=radius, fill="#635bff")

    left, top = size * scale * 0.245, size * scale * 0.245
    width, height = size * scale * 0.51, size * scale * 0.51

    def point(x, y):
        return (left + x / 24 * width, top + y / 24 * height)

    stroke = max(2, round(size * scale * 0.05))
    for x in (5, 12, 19):
        points = list(
            cubic(
                point(x, 3.5),
                point(x + 4, 7.5),
                point(x - 4, 16.5),
                point(x, 20.5),
            )
        )
        half = stroke / 2
        left_edge = []
        right_edge = []
        for index, (px, py) in enumerate(points):
            previous = points[max(0, index - 1)]
            following = points[min(len(points) - 1, index + 1)]
            dx, dy = following[0] - previous[0], following[1] - previous[1]
            length = max((dx * dx + dy * dy) ** 0.5, 1)
            nx, ny = -dy / length * half, dx / length * half
            left_edge.append((px + nx, py + ny))
            right_edge.append((px - nx, py - ny))
        draw.polygon(left_edge + list(reversed(right_edge)), fill="white")
        radius_end = stroke / 2
        for px, py in (points[0], points[-1]):
            draw.ellipse(
                (px - radius_end, py - radius_end, px + radius_end, py + radius_end),
                fill="white",
            )
    return canvas.resize((size, size), Image.Resampling.LANCZOS)


def main():
    ICONS.mkdir(parents=True, exist_ok=True)
    master = render(1024)
    master.save(ICONS / "icon.png")
    master.save(
        ICONS / "RealityLocal.icns",
        format="ICNS",
        append_images=[render(size) for size in (32, 64, 128, 256, 512)],
    )
    shutil.copy2(ICONS / "icon.png", ICONS / "icon-1024.png")


if __name__ == "__main__":
    main()
