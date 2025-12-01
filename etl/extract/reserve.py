"""Tools to fetch reserve geometries from OpenStreetMap or local files."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Sequence

import json

import osmnx as ox
from shapely.geometry import mapping, shape
from shapely.geometry.base import BaseGeometry
from unidecode import unidecode

RESERVE_NAME = "Estação Ecológica Estadual de Guaxindiba"
SEARCH_PLACES = (
    "São Francisco de Itabapoana, Rio de Janeiro, Brazil",
    "Rio de Janeiro, Brazil",
    "Brazil",
)


def _normalize(text: str) -> str:
    """Normalize strings for name comparison."""

    return unidecode((text or "").lower().strip())


def _iter_places_and_tags(search_places: Sequence[str]) -> Iterable[tuple[str, dict[str, str]]]:
    tags_try = [
        {"boundary": "protected_area"},
        {"leisure": "nature_reserve"},
        {"boundary": "national_park"},
    ]

    for place in search_places:
        for tags in tags_try:
            yield place, tags


def fetch_reserve_polygon(
    reserve_name: str = RESERVE_NAME,
    *,
    search_places: Sequence[str] | None = None,
) -> BaseGeometry:
    """Fetch a reserve polygon directly from OpenStreetMap.

    Parameters
    ----------
    reserve_name:
        Name (or part of the name) of the reserve to be located.
    search_places:
        Optional list/tuple of place strings to scope the OSM search. If
        omitted, a broad search across Brazil is used.
    """

    name_norm = _normalize(reserve_name)
    places = tuple(search_places) if search_places else SEARCH_PLACES

    for place, tags in _iter_places_and_tags(places):
        try:
            gdf = ox.features_from_place(place, tags=tags)
        except Exception:  # pragma: no cover - network or API errors are ignored
            continue

        if gdf is None or gdf.empty:
            continue

        cols_to_check = [column for column in gdf.columns if column.startswith("name")]
        if not cols_to_check:
            continue

        mask = False
        for column in cols_to_check:
            mask = mask | gdf[column].apply(lambda value: name_norm in _normalize(str(value)))

        candidates = gdf[mask]

        if candidates.empty:
            continue

        candidates = candidates.to_crs(4326)
        geometry = candidates.unary_union
        if geometry.is_empty:
            continue

        return geometry

    raise ValueError("Could not find the reserve polygon on OSM.")


def _load_geometry_from_cache(cache_path: Path) -> BaseGeometry:
    data = json.loads(cache_path.read_text())
    if data.get("type") == "FeatureCollection":
        features = data.get("features") or []
        if not features:
            raise ValueError("Cached geometry does not contain features.")
        geometry_data = features[0]["geometry"]
    else:
        geometry_data = data

    return shape(geometry_data)


def _dump_geometry_to_cache(geometry: BaseGeometry, cache_path: Path) -> None:
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    feature_collection = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {},
                "geometry": mapping(geometry),
            }
        ],
    }
    cache_path.write_text(json.dumps(feature_collection))


def get_reserve_geometry(
    name: str = RESERVE_NAME,
    *,
    cache: Path | None = None,
    geometry_file: Path | None = None,
    search_places: Sequence[str] | None = None,
) -> BaseGeometry:
    """Return a reserve geometry, optionally reusing cache or a local file.

    Parameters
    ----------
    name:
        Reserve name to query on OpenStreetMap. Used only when ``geometry_file``
        is not provided.
    cache:
        Optional path to store/reuse the resolved geometry.
    geometry_file:
        Optional GeoJSON file containing the reserve geometry. When provided,
        the geometry is loaded from this path and (optionally) copied into
        ``cache`` for reuse.
    search_places:
        Optional list/tuple of place strings to scope the OSM search. Ignored
        when ``geometry_file`` is provided.
    """

    cache_path = cache if cache is None else Path(cache)

    if geometry_file is not None:
        geometry_path = Path(geometry_file)
        geometry = _load_geometry_from_cache(geometry_path)
        if cache_path is not None and cache_path != geometry_path:
            _dump_geometry_to_cache(geometry, cache_path)
        return geometry

    if cache_path is not None and cache_path.exists():
        return _load_geometry_from_cache(cache_path)

    geometry = fetch_reserve_polygon(name, search_places=search_places)

    if cache_path is not None:
        _dump_geometry_to_cache(geometry, cache_path)

    return geometry

