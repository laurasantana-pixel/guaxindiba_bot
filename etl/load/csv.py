"""Helpers to persist tabular and spatial data on disk."""

from __future__ import annotations

import json
from os import PathLike
from pathlib import Path
from typing import Any, Iterable

import pandas as pd
from shapely.geometry import mapping
from shapely.geometry.base import BaseGeometry


def _ensure_path(path: Path | str | PathLike[str]) -> Path:
    """Return ``path`` as :class:`pathlib.Path` enforcing valid types."""

    if isinstance(path, Path):
        return path
    if isinstance(path, (str, PathLike)):
        return Path(path)
    raise TypeError("path must be a string, Path or os.PathLike instance")


def save_dataframe(df: pd.DataFrame, path: Path | str | PathLike[str]) -> Path:
    """Persist a dataframe to CSV ensuring the parent directory exists."""

    target = _ensure_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)

    if hasattr(df, "to_csv"):
        df.to_csv(target, index=False)  # type: ignore[call-arg]
        return target

    columns: Iterable[str] | None = getattr(df, "columns", None)
    if columns is None:
        raise TypeError("dataframe must define a 'columns' attribute or a 'to_csv' method")

    columns = list(columns)
    if not columns:
        target.write_text("", encoding="utf-8")
        return target

    first_series = df[columns[0]]
    try:
        rows_length = len(first_series)
    except TypeError:  # pragma: no cover - fallback for exotic series implementations
        rows_length = len(list(first_series))

    with target.open("w", encoding="utf-8") as fh:
        fh.write(",".join(columns) + "\n")
        for row_index in range(rows_length):
            values: list[str] = []
            for column in columns:
                series = df[column]
                value = series[row_index]
                values.append(str(value))
            fh.write(",".join(values) + "\n")

    return target


def _geo_interface(obj: Any) -> dict[str, Any]:
    data = getattr(obj, "__geo_interface__", None)
    if isinstance(data, dict):
        return data
    raise TypeError("geometry must expose the __geo_interface__ protocol")


def _as_feature_collection(obj: Any) -> dict[str, Any]:
    if isinstance(obj, BaseGeometry):
        geometry = mapping(obj)
        return {
            "type": "FeatureCollection",
            "features": [
                {"type": "Feature", "properties": {}, "geometry": geometry},
            ],
        }

    data = _geo_interface(obj)
    data_type = data.get("type")

    if data_type == "FeatureCollection":
        return data
    if data_type == "Feature":
        return {"type": "FeatureCollection", "features": [data]}
    if data_type:
        return {
            "type": "FeatureCollection",
            "features": [
                {"type": "Feature", "properties": {}, "geometry": data},
            ],
        }

    raise ValueError("invalid GeoJSON object: missing 'type'")


def save_geometry(geom: Any, path: Path | str | PathLike[str]) -> Path:
    """Persist a geometry or GeoJSON-like object to disk as GeoJSON."""

    target = _ensure_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)

    feature_collection = _as_feature_collection(geom)
    target.write_text(json.dumps(feature_collection, ensure_ascii=False, indent=2), encoding="utf-8")
    return target


__all__ = ["save_dataframe", "save_geometry"]
