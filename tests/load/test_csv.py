from __future__ import annotations

import json

import pandas as pd

from compat.shapely import Polygon

from etl.load.csv import save_dataframe, save_geometry


def test_save_dataframe_creates_parent_dirs(tmp_path):
    df = pd.DataFrame({"a": [1, 2], "b": ["x", "y"]})
    output = tmp_path / "nested" / "data.csv"

    returned_path = save_dataframe(df, output)

    assert output.exists()
    assert returned_path == output
    assert output.read_text(encoding="utf-8").strip().splitlines() == [
        "a,b",
        "1,x",
        "2,y",
    ]


def test_save_geometry_from_shapely(tmp_path):
    polygon = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
    output = tmp_path / "reserve.geojson"

    returned_path = save_geometry(polygon, output)

    assert output.exists()
    assert returned_path == output

    data = json.loads(output.read_text())
    assert data["type"] == "FeatureCollection"
    assert len(data["features"]) == 1
    feature = data["features"][0]
    assert feature["type"] == "Feature"
    assert feature["geometry"]["type"] == "Polygon"
