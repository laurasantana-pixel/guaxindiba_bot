from __future__ import annotations

from .geometry import Point, Polygon


def loads(text: str):
    text = text.strip()
    if text.upper().startswith("POINT"):
        coords = _parse_point(text)
        return Point(*coords)
    if text.upper().startswith("POLYGON"):
        rings = _parse_polygon(text)
        return Polygon(rings[0])
    raise ValueError("Unsupported WKT geometry type")


def _parse_point(text: str) -> tuple[float, float]:
    inside = text[text.find("(") + 1 : text.rfind(")")]
    x_str, y_str = inside.strip().split()
    return float(x_str), float(y_str)


def _parse_polygon(text: str) -> list[list[tuple[float, float]]]:
    inside = text[text.find("((") + 2 : text.rfind("))")]
    rings = []
    for ring_text in inside.split("), ("):
        coords = []
        for pair in ring_text.split(","):
            x_str, y_str = pair.strip().split()
            coords.append((float(x_str), float(y_str)))
        rings.append(coords)
    return rings
