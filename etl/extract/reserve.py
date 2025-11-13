"""Tools to fetch the Guaxindiba reserve geometry from OpenStreetMap."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import json

import osmnx as ox

from compat.shapely import BaseGeometry, mapping, shape
from unidecode import unidecode

RESERVE_NAME = "Estação Ecológica Estadual de Guaxindiba"
SEARCH_PLACES = [
    "São Francisco de Itabapoana, Rio de Janeiro, Brazil",
    "Rio de Janeiro, Brazil",
    "Brazil",
]


def _normalize(text: str) -> str:
    """Normalize strings for name comparison."""

    return unidecode((text or "").lower().strip())


def _iter_places_and_tags() -> Iterable[tuple[str, dict[str, str]]]:
    tags_try = [
        {"boundary": "protected_area"},
        {"leisure": "nature_reserve"},
        {"boundary": "national_park"},
    ]

    for place in SEARCH_PLACES:
        for tags in tags_try:
            yield place, tags


def fetch_reserve_polygon(reserve_name: str = RESERVE_NAME) -> BaseGeometry:
    """Fetch the reserve polygon directly from OpenStreetMap."""

    name_norm = _normalize(reserve_name)

    for place, tags in _iter_places_and_tags():
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
            mask = False
            for column in cols_to_check:
                mask = mask | gdf[column].apply(lambda value: "guaxindiba" in _normalize(str(value)))
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
) -> BaseGeometry:
    """Return the reserve geometry, optionally reusing a cached GeoJSON file."""

    cache_path = cache if cache is None else Path(cache)

    if cache_path is not None and cache_path.exists():
        return _load_geometry_from_cache(cache_path)

    geometry = fetch_reserve_polygon(name)

    if cache_path is not None:
        _dump_geometry_to_cache(geometry, cache_path)

    return geometry

