"""Build a tiny, dependency-free Windows icon matching the app's radar logo."""
from __future__ import annotations

import math
import struct
import zlib
from pathlib import Path

SIZE = 256
pixels = [[(16, 25, 28, 255) for _ in range(SIZE)] for _ in range(SIZE)]


def blend(x: int, y: int, color: tuple[int, int, int, int]) -> None:
    if 0 <= x < SIZE and 0 <= y < SIZE:
        pixels[y][x] = color


def line(x0: int, y0: int, x1: int, y1: int, color: tuple[int, int, int, int], width: int = 1) -> None:
    dx, dy = abs(x1 - x0), abs(y1 - y0)
    sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
    err = dx - dy
    while True:
        half = width // 2
        for ox in range(-half, half + 1):
            for oy in range(-half, half + 1):
                blend(x0 + ox, y0 + oy, color)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy; x0 += sx
        if e2 < dx:
            err += dx; y0 += sy


def circle(cx: int, cy: int, radius: int, color: tuple[int, int, int, int], width: int = 3) -> None:
    steps = max(120, radius * 8)
    for i in range(steps):
        angle = math.tau * i / steps
        x, y = round(cx + radius * math.cos(angle)), round(cy + radius * math.sin(angle))
        half = width // 2
        for ox in range(-half, half + 1):
            for oy in range(-half, half + 1):
                blend(x + ox, y + oy, color)


def filled_circle(cx: int, cy: int, radius: int, color: tuple[int, int, int, int]) -> None:
    for y in range(cy - radius, cy + radius + 1):
        for x in range(cx - radius, cx + radius + 1):
            if (x - cx) ** 2 + (y - cy) ** 2 <= radius ** 2:
                blend(x, y, color)


# Transparent rounded corners around a dark, standalone app icon.
for y in range(SIZE):
    for x in range(SIZE):
        qx, qy = min(max(x, 32), 223), min(max(y, 32), 223)
        if (x - qx) ** 2 + (y - qy) ** 2 > 32 ** 2:
            pixels[y][x] = (0, 0, 0, 0)

cx, cy = 126, 137
grid = (70, 100, 92, 255)
for radius in (70, 47, 23): circle(cx, cy, radius, grid, 5)
line(cx, 49, cx, 225, grid, 3)
line(38, cy, 214, cy, grid, 3)
line(cx, cy, 191, 72, (168, 240, 120, 255), 9)
filled_circle(cx, cy, 9, (168, 240, 120, 255))
filled_circle(191, 72, 8, (229, 255, 208, 255))

raw = b"".join(b"\0" + b"".join(bytes(px) for px in row) for row in reversed(pixels))
def chunk(name: bytes, data: bytes) -> bytes:
    return struct.pack(">I", len(data)) + name + data + struct.pack(">I", zlib.crc32(name + data) & 0xFFFFFFFF)

png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", SIZE, SIZE, 8, 6, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")
ico_header = struct.pack("<HHH", 0, 1, 1)
ico_entry = struct.pack("<BBBBHHII", 0, 0, 0, 0, 1, 32, len(png), 22)
output = Path(__file__).resolve().parents[1] / "app" / "static" / "brand.ico"
output.write_bytes(ico_header + ico_entry + png)
output.with_suffix(".png").write_bytes(png)
print(output)
