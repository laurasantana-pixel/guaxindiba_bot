import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import json

import geopandas as gpd
import pandas as pd
import pytest

from compat import shapely as shapely_compat

from etl.transform.spatial import mark_points_inside


@pytest.fixture
def points_gdf():
    with open("tests/data/points.json", "r", encoding="utf-8") as fh:
        rows = json.load(fh)
    df = pd.DataFrame(rows)
    geometries = df["wkt"].apply(shapely_compat.wkt.loads)
    return gpd.GeoDataFrame(df.drop(columns=["wkt"]), geometry=geometries, crs="EPSG:4326")


@pytest.fixture
def areas_geodf():
    with open("tests/data/protected_areas.json", "r", encoding="utf-8") as fh:
        rows = json.load(fh)
    df = pd.DataFrame(rows)
    geometries = df["wkt"].apply(shapely_compat.wkt.loads)
    gdf = gpd.GeoDataFrame(df.drop(columns=["wkt"]), geometry=geometries, crs="EPSG:4326")
    return gdf


def test_mark_points_inside_single_geometry(points_gdf, areas_geodf):
    polygon = areas_geodf.geometry.tolist()[0]

    result = mark_points_inside(points_gdf, polygon)

    assert "inside" in result.columns
    assert result["inside"].tolist() == [True, True, False, True]


def test_mark_points_inside_multiple_geometries(points_gdf, areas_geodf):
    result = mark_points_inside(points_gdf, areas_geodf.set_index("name"))

    assert set(["Reserva Norte", "Reserva Sul"]).issubset(result.columns)
    assert result["Reserva Norte"].tolist() == [True, True, False, True]
    assert result["Reserva Sul"].tolist() == [False, True, False, False]


def test_mark_points_inside_mapping(points_gdf, areas_geodf):
    geometries = {
        name: geometry
        for name, geometry in zip(areas_geodf["name"].tolist(), areas_geodf.geometry.tolist())
    }
    result = mark_points_inside(points_gdf, geometries)

    assert result["Reserva Norte"].tolist() == [True, True, False, True]
    assert result["Reserva Sul"].tolist() == [False, True, False, False]


def test_mark_points_inside_requires_geometry_column():
    df = pd.DataFrame({"id": [1, 2]})
    with pytest.raises(ValueError):
        mark_points_inside(df, [])
