from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence


class BaseGeometry:
    """Minimal base geometry implementation."""

    def intersects(self, other: "BaseGeometry") -> bool:
        raise NotImplementedError

    def contains(self, other: "BaseGeometry") -> bool:
        return other.within(self)

    def within(self, other: "BaseGeometry") -> bool:
        return other.contains(self)

    def equals(self, other: object) -> bool:
        return self is other

    @property
    def is_empty(self) -> bool:
        return False


@dataclass(frozen=True)
class Point(BaseGeometry):
    x: float
    y: float

    def intersects(self, other: BaseGeometry) -> bool:
        if isinstance(other, Polygon):
            return other.contains_point(self)
        if isinstance(other, Point):
            return self.x == other.x and self.y == other.y
        raise TypeError("Unsupported geometry type for intersection")

    def within(self, other: BaseGeometry) -> bool:
        return other.contains(self)


class Polygon(BaseGeometry):
    def __init__(self, coordinates: Sequence[Sequence[float]]):
        if len(coordinates) < 3:
            raise ValueError("Polygon requires at least three coordinates")
        self._coordinates = [(float(x), float(y)) for x, y in coordinates]
        if self._coordinates[0] != self._coordinates[-1]:
            self._coordinates.append(self._coordinates[0])

    @property
    def coordinates(self) -> Sequence[tuple[float, float]]:
        return self._coordinates

    def contains_point(self, point: Point) -> bool:
        x, y = point.x, point.y
        num = len(self._coordinates)
        inside = False
        for i in range(num):
            x1, y1 = self._coordinates[i]
            x2, y2 = self._coordinates[(i + 1) % num]
            if ((y1 > y) != (y2 > y)):
                slope = (x2 - x1) / (y2 - y1) if (y2 - y1) != 0 else float("inf")
                intersect_x = slope * (y - y1) + x1
                if x < intersect_x:
                    inside = not inside
            if ((y == y1 == y2) and min(x1, x2) <= x <= max(x1, x2)):
                return True
            if y1 == y2 == y and min(x1, x2) <= x <= max(x1, x2):
                return True
        return inside or self._point_on_boundary(point)

    def _point_on_boundary(self, point: Point) -> bool:
        x, y = point.x, point.y
        for i in range(len(self._coordinates) - 1):
            x1, y1 = self._coordinates[i]
            x2, y2 = self._coordinates[i + 1]
            if self._point_on_segment(x, y, x1, y1, x2, y2):
                return True
        return False

    @staticmethod
    def _point_on_segment(x: float, y: float, x1: float, y1: float, x2: float, y2: float) -> bool:
        if (x2 - x1) == 0 and (y2 - y1) == 0:
            return x == x1 and y == y1
        cross = (x - x1) * (y2 - y1) - (y - y1) * (x2 - x1)
        if abs(cross) > 1e-9:
            return False
        dot = (x - x1) * (x2 - x1) + (y - y1) * (y2 - y1)
        if dot < 0:
            return False
        squared_length = (x2 - x1) ** 2 + (y2 - y1) ** 2
        if dot > squared_length:
            return False
        return True

    def intersects(self, other: BaseGeometry) -> bool:
        if isinstance(other, Point):
            return self.contains_point(other)
        raise TypeError("Unsupported geometry type for intersection")

    def contains(self, other: BaseGeometry) -> bool:
        if isinstance(other, Point):
            return self.contains_point(other)
        raise TypeError("Unsupported geometry type for containment")

    def within(self, other: BaseGeometry) -> bool:
        if isinstance(other, Polygon):
            return all(Point(x, y).within(other) for x, y in self._coordinates)
        return False

    def equals(self, other: object) -> bool:
        if isinstance(other, Polygon):
            other_coords = other._coordinates
        elif hasattr(other, "coordinates"):
            other_coords = list(other.coordinates)
        else:
            return False
        return _normalize(self._coordinates) == _normalize(other_coords)

    @property
    def is_empty(self) -> bool:
        return len(self._coordinates) == 0


def as_point(coords: Iterable[float]) -> Point:
    x, y = coords
    return Point(float(x), float(y))


def shape(obj: Mapping[str, object]) -> BaseGeometry:
    geom_type = obj.get("type")
    if geom_type == "Polygon":
        coordinates = obj["coordinates"][0]
        return Polygon(coordinates)
    raise ValueError("Unsupported geometry type")


def mapping(geometry: BaseGeometry) -> Mapping[str, object]:
    coords = getattr(geometry, "coordinates", None)
    if coords is not None:
        return {"type": "Polygon", "coordinates": (tuple(coords),)}
    raise ValueError("Unsupported geometry type")


def _normalize(coords: Sequence[Sequence[float]]) -> list[tuple[float, float]]:
    coord_list = [tuple(point) for point in coords]
    if coord_list and coord_list[0] == coord_list[-1]:
        coord_list = coord_list[:-1]
    return coord_list
