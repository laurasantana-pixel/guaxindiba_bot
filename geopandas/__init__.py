from __future__ import annotations

from typing import Any, Iterable

from pandas import DataFrame, Series

from shapely.geometry import BaseGeometry


class GeoSeries(Series):
    def __init__(self, data: Iterable[Any], index: Iterable[Any] | None = None, crs: str | None = None):
        if isinstance(data, Series):
            index = data.index
            data = list(data)
        super().__init__(data, index=index)
        self.crs = crs

    def intersects(self, other: BaseGeometry) -> Series:
        return Series(geom.intersects(other) for geom in self)

    def copy(self):
        return GeoSeries(list(self), index=self.index, crs=self.crs)


class GeoDataFrame(DataFrame):
    def __init__(self, data: Any = None, geometry: str | Iterable[Any] = "geometry", crs: str | None = None):
        if data is None:
            data = {}
        if isinstance(data, DataFrame):
            base_data = {key: list(values) for key, values in data._data.items()}
            base_index = data._index
        else:
            base_data = data
            base_index = None
        super().__init__(base_data, index=base_index)
        if isinstance(geometry, str):
            geom_values = self[geometry]
            geom_series = GeoSeries(geom_values, index=geom_values.index, crs=crs)
            self._geometry_column_name = geometry
        else:
            if isinstance(geometry, GeoSeries):
                geom_series = GeoSeries(list(geometry), index=geometry.index, crs=geometry.crs or crs)
            else:
                geom_series = GeoSeries(geometry, crs=crs)
            self._geometry_column_name = "geometry"
            self[self._geometry_column_name] = geom_series
        self.crs = crs
        self.__dict__[self._geometry_column_name] = geom_series

    @property
    def geometry(self) -> GeoSeries:
        geom_series = self[self._geometry_column_name]
        geom = GeoSeries(geom_series, index=geom_series.index, crs=self.crs)
        return geom

    def set_crs(self, crs: str, inplace: bool = False):
        if inplace:
            self.crs = crs
            return None
        result = GeoDataFrame(self.copy(), geometry=self.geometry, crs=crs)
        return result

    def copy(self):
        return GeoDataFrame({key: list(values) for key, values in self._data.items()}, geometry=self.geometry, crs=self.crs)

    def set_index(self, column: str):
        series = self[column]
        result = GeoDataFrame({key: list(values) for key, values in self._data.items()}, geometry=self.geometry, crs=self.crs)
        result._index = series.tolist()
        return result


__all__ = ["GeoDataFrame", "GeoSeries"]
