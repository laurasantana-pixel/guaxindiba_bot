from __future__ import annotations

import pandas as pd
from shapely.geometry import Point, Polygon

from etl.pipeline import PipelineConfig, run_pipeline


def _assert_frame_equal(df: pd.DataFrame, other: pd.DataFrame) -> None:
    assert list(df.columns) == list(other.columns)
    for column in df.columns:
        assert list(df[column]) == list(other[column])


def test_run_pipeline_executes_all_steps(tmp_path):
    point = Point(0, 0)
    base_df = pd.DataFrame({"geometry": [point], "value": [10]})
    reserve_geometry = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
    transformed_df = pd.DataFrame({"geometry": [point], "value": [10], "processed": [True]})

    def fake_fetch_fire_data(**kwargs):
        return base_df

    def fake_get_reserve_geometry(**kwargs):
        return reserve_geometry

    def fake_transformer(df, geom):
        assert geom is reserve_geometry
        _assert_frame_equal(df, base_df)
        return transformed_df

    saved: dict[str, object] = {}

    def fake_dataframe_loader(df, path):
        saved["dataframe"] = df.copy()
        saved["dataframe_path"] = path

    def fake_geometry_loader(geom, path):
        saved["geometry"] = geom
        saved["geometry_path"] = path

    cfg = PipelineConfig(
        dataframe_output=tmp_path / "fires.csv",
        geometry_output=tmp_path / "reserve.geojson",
        fetch_fire_data=fake_fetch_fire_data,
        get_reserve_geometry=fake_get_reserve_geometry,
        transformer=fake_transformer,
        dataframe_loader=fake_dataframe_loader,
        geometry_loader=fake_geometry_loader,
    )

    result = run_pipeline(cfg)

    assert result.fires is base_df
    assert result.geometry is reserve_geometry
    assert result.result is transformed_df

    _assert_frame_equal(saved["dataframe"], transformed_df)
    assert saved["dataframe_path"] == tmp_path / "fires.csv"
    assert saved["geometry"] is reserve_geometry
    assert saved["geometry_path"] == tmp_path / "reserve.geojson"


def test_run_pipeline_can_skip_transformation(tmp_path):
    base_df = pd.DataFrame({"value": [1]})
    reserve_geometry = Polygon([(0, 0), (2, 0), (2, 2), (0, 2)])

    loader_calls: list[pd.DataFrame] = []

    def fake_dataframe_loader(df, path):
        loader_calls.append(df)

    def failing_transformer(*args, **kwargs):  # pragma: no cover - used to ensure skipping
        raise AssertionError("should not run")

    cfg = PipelineConfig(
        dataframe_output=tmp_path / "fires.csv",
        geometry_output=None,
        apply_transform=False,
        fetch_fire_data=lambda **_: base_df,
        get_reserve_geometry=lambda **_: reserve_geometry,
        transformer=failing_transformer,
        dataframe_loader=fake_dataframe_loader,
    )

    result = run_pipeline(cfg)

    assert result.fires is base_df
    assert result.geometry is reserve_geometry
    _assert_frame_equal(result.result, base_df)
    assert len(loader_calls) == 1
    _assert_frame_equal(loader_calls[0], base_df)


def test_run_pipeline_builds_geometry_from_lat_lon(tmp_path):
    base_df = pd.DataFrame({"lat": [0, 1], "lon": [0, 1]})
    reserve_geometry = Polygon([(0, 0), (2, 0), (2, 2), (0, 2)])

    cfg = PipelineConfig(
        dataframe_output=tmp_path / "fires.csv",
        geometry_output=None,
        fetch_fire_data=lambda **_: base_df,
        get_reserve_geometry=lambda **_: reserve_geometry,
    )

    result = run_pipeline(cfg)

    assert "geometry" in result.result.columns
    assert all(isinstance(geom, Point) for geom in result.result.geometry)
    assert result.result["inside"].tolist() == [True, True]
