from __future__ import annotations

import sys
import types
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class FakeGeometry:
    def __init__(self, coordinates: Sequence[tuple[float, float]]):
        self.coordinates = tuple(tuple(point) for point in coordinates)

    def equals(self, other: object) -> bool:
        return isinstance(other, FakeGeometry) and self.coordinates == other.coordinates

    @property
    def is_empty(self) -> bool:
        return len(self.coordinates) == 0


def _fake_shape(obj) -> FakeGeometry:
    if obj.get("type") != "Polygon":  # pragma: no cover - defensive branch
        raise ValueError("Only simple polygons are supported in tests")
    coordinates = obj["coordinates"][0]
    return FakeGeometry(coordinates)


def _fake_mapping(geometry: FakeGeometry):
    return {"type": "Polygon", "coordinates": (geometry.coordinates,)}


def _ensure_shapely_stubs() -> None:
    try:
        import shapely  # type: ignore # noqa: F401
    except ModuleNotFoundError:
        geometry_module = types.ModuleType("shapely.geometry")
        geometry_module.shape = _fake_shape
        geometry_module.mapping = _fake_mapping

        base_module = types.ModuleType("shapely.geometry.base")
        base_module.BaseGeometry = FakeGeometry

        sys.modules.setdefault("shapely", types.ModuleType("shapely"))
        sys.modules["shapely.geometry"] = geometry_module
        sys.modules["shapely.geometry.base"] = base_module


_ensure_shapely_stubs()


def _ensure_osmnx_stub() -> None:
    if "osmnx" not in sys.modules:
        module = types.ModuleType("osmnx")
        module.features_from_place = None
        sys.modules["osmnx"] = module


_ensure_osmnx_stub()


def _ensure_unidecode_stub() -> None:
    if "unidecode" not in sys.modules:
        module = types.ModuleType("unidecode")

        def _unidecode(value: str) -> str:
            return value

        module.unidecode = _unidecode
        sys.modules["unidecode"] = module


_ensure_unidecode_stub()

import importlib.util

_RESERVE_SPEC = importlib.util.spec_from_file_location(
    "etl.extract.reserve",
    PROJECT_ROOT / "etl" / "extract" / "reserve.py",
)
assert _RESERVE_SPEC and _RESERVE_SPEC.loader  # pragma: no cover - sanity check
reserve = importlib.util.module_from_spec(_RESERVE_SPEC)
_RESERVE_SPEC.loader.exec_module(reserve)


@dataclass
class FakeSeries:
    data: Sequence[object]

    def apply(self, func):
        return FakeSeries([func(value) for value in self.data])

    def __iter__(self) -> Iterator[object]:
        return iter(self.data)

    def __or__(self, other):
        other_data = _coerce_to_sequence(other, len(self.data))
        return FakeSeries([a or b for a, b in zip(_as_bools(self.data), other_data)])

    def __ror__(self, other):
        other_data = _coerce_to_sequence(other, len(self.data))
        return FakeSeries([a or b for a, b in zip(other_data, _as_bools(self.data))])


def _as_bools(values: Iterable[object]) -> list[bool]:
    return [bool(value) for value in values]


def _coerce_to_sequence(value, size: int) -> list[bool]:
    if isinstance(value, FakeSeries):
        return _as_bools(value.data)
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return _as_bools(value)
    return [bool(value)] * size


class FakeGeoDataFrame:
    def __init__(self, names: Sequence[str], geometry: Sequence[FakeGeometry]):
        self._names = list(names)
        self._geometry = list(geometry)

    @property
    def columns(self) -> list[str]:
        return ["name"]

    @property
    def empty(self) -> bool:
        return not self._names

    def __getitem__(self, key):
        if isinstance(key, str):
            if key == "name":
                return FakeSeries(self._names)
            raise KeyError(key)
        mask = _coerce_to_sequence(key, len(self._names))
        names = [name for name, keep in zip(self._names, mask) if keep]
        geometries = [geom for geom, keep in zip(self._geometry, mask) if keep]
        return FakeGeoDataFrame(names, geometries)

    def to_crs(self, _):
        return self

    @property
    def unary_union(self):
        return self._geometry[0] if self._geometry else FakeGeometry(())


def _make_polygon(*coordinates: tuple[float, float]) -> FakeGeometry:
    return FakeGeometry(coordinates)


def test_get_reserve_geometry_fetches_from_osm(monkeypatch):
    polygon = _make_polygon((0, 0), (1, 0), (1, 1), (0, 1))
    call_count = 0

    def fake_features(place: str, *, tags: dict[str, str]):
        nonlocal call_count
        call_count += 1
        return FakeGeoDataFrame([reserve.RESERVE_NAME], [polygon])

    monkeypatch.setattr(reserve.ox, "features_from_place", fake_features)

    geometry = reserve.get_reserve_geometry()

    assert call_count == 1
    assert geometry.equals(polygon)


def test_get_reserve_geometry_uses_cache(tmp_path: Path, monkeypatch):
    polygon = _make_polygon((0, 0), (2, 0), (2, 2), (0, 2))
    cache_path = tmp_path / "reserve.geojson"
    call_count = 0

    def fake_features(place: str, *, tags: dict[str, str]):
        nonlocal call_count
        call_count += 1
        return FakeGeoDataFrame([reserve.RESERVE_NAME], [polygon])

    monkeypatch.setattr(reserve.ox, "features_from_place", fake_features)

    first_geometry = reserve.get_reserve_geometry(cache=cache_path)

    assert call_count == 1
    assert cache_path.exists()

    def fail(*args, **kwargs):  # pragma: no cover - defensive assertion
        raise AssertionError("OSM should not be queried when cache exists")

    monkeypatch.setattr(reserve.ox, "features_from_place", fail)

    second_geometry = reserve.get_reserve_geometry(cache=cache_path)

    assert second_geometry.equals(first_geometry)
