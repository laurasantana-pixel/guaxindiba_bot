"""Spatial transformation helpers."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

import geopandas as gpd
import pandas as pd
from shapely.geometry.base import BaseGeometry

GeometryLike = Any


def _to_geodataframe(df: pd.DataFrame | gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Return a GeoDataFrame copy ensuring the geometry column exists."""
    if isinstance(df, gpd.GeoDataFrame):
        return df.copy()
    if "geometry" not in df.columns:
        raise ValueError("input DataFrame must contain a 'geometry' column")
    return gpd.GeoDataFrame(df.copy(), geometry="geometry")


def _geometries_from_input(
    geom: GeometryLike,
) -> tuple[gpd.GeoSeries | None, dict[str, BaseGeometry] | None]:
    """Normalize geometry input.

    Returns a tuple of (series, mapping).
    If ``series`` is not ``None`` it contains ordered geometries whose index will
    be used as column names. Otherwise, ``mapping`` holds the geometries with
    their explicit names.
    """
    if isinstance(geom, BaseGeometry):
        return None, {"inside": geom}

    if isinstance(geom, gpd.GeoSeries):
        series = geom.copy()
        index = getattr(series, "index", None)
        if index is None:
            raise ValueError("GeoSeries used as geometry input must have a valid index")
        index_values = [str(value) for value in index]
        series.index = index_values
        return series, None

    if isinstance(geom, gpd.GeoDataFrame):
        series = geom.geometry.copy()
        if "name" in geom.columns:
            names = [str(value) for value in geom["name"]]
            series.index = names
        else:
            series.index = [str(value) for value in getattr(series, "index", [])]
        return series, None

    if isinstance(geom, Mapping):
        normalized = {}
        for key, value in geom.items():
            if not isinstance(value, BaseGeometry):
                raise TypeError("Mapping values must be shapely geometries")
            normalized[str(key)] = value
        return None, normalized

    if isinstance(geom, Iterable) and not isinstance(geom, (str, bytes)):
        normalized = {}
        for index, value in enumerate(geom):
            if isinstance(value, tuple) and len(value) == 2:
                name, geometry = value
            else:
                name, geometry = f"inside_{index}", value
            if not isinstance(geometry, BaseGeometry):
                raise TypeError("Iterable values must be shapely geometries or (name, geometry) tuples")
            normalized[str(name)] = geometry
        if normalized:
            return None, normalized

    raise TypeError(
        "geom must be a shapely geometry, GeoSeries, GeoDataFrame, a mapping of names to geometries, "
        "or an iterable of geometries/(name, geometry) tuples",
    )


def _check_crs(gdf: gpd.GeoDataFrame, geom_series: gpd.GeoSeries | None) -> None:
    if geom_series is not None and geom_series.crs is not None:
        if gdf.crs is not None and gdf.crs != geom_series.crs:
            raise ValueError("Geometry CRS does not match the GeoDataFrame CRS")
        if gdf.crs is None:
            gdf.set_crs(geom_series.crs, inplace=True)


def mark_points_inside(
    df: pd.DataFrame | gpd.GeoDataFrame,
    geom: GeometryLike,
) -> gpd.GeoDataFrame:
    """Return a GeoDataFrame with boolean columns marking points inside geometries.

    Parameters
    ----------
    df:
        DataFrame or GeoDataFrame containing point geometries under the ``geometry`` column.
    geom:
        Single geometry, collection or mapping of geometries. When multiple geometries
        are provided, each will result in a boolean column indicating whether a point
        lies inside/intersects the respective geometry.
    """

    gdf = _to_geodataframe(df)
    geom_series, geom_mapping = _geometries_from_input(geom)

    if geom_series is not None:
        _check_crs(gdf, geom_series)
        for name, geometry in geom_series.items():
            gdf[name] = gdf.geometry.intersects(geometry)
        return gdf

    assert geom_mapping is not None
    for name, geometry in geom_mapping.items():
        gdf[name] = gdf.geometry.intersects(geometry)
    return gdf


__all__ = ["mark_points_inside"]
