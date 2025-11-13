from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, List, Sequence


class Series:
    def __init__(self, data: Iterable[Any], index: Iterable[Any] | None = None):
        self._data = list(data)
        if index is None:
            self.index = list(range(len(self._data)))
        else:
            self.index = list(index)

    def apply(self, func: Callable[[Any], Any]) -> "Series":
        return Series((func(value) for value in self._data), index=self.index)

    def tolist(self) -> List[Any]:
        return list(self._data)

    def __len__(self):
        return len(self._data)

    def __getitem__(self, item: int) -> Any:
        return self._data[item]

    def __iter__(self):
        return iter(self._data)

    def items(self):
        return zip(self.index, self._data)

    def copy(self) -> "Series":
        return Series(self._data, index=self.index)


class DataFrame:
    def __init__(
        self,
        data: Dict[str, Iterable[Any]] | Sequence[Dict[str, Any]],
        index: Sequence[Any] | None = None,
    ):
        if isinstance(data, dict):
            self._data = {key: list(values) for key, values in data.items()}
        else:
            self._data = {}
            for row in data:
                for key, value in row.items():
                    self._data.setdefault(key, []).append(value)
        self._ensure_lengths()
        if index is None:
            length = len(next(iter(self._data.values()), []))
            self._index = list(range(length))
        else:
            self._index = list(index)

    def _ensure_lengths(self) -> None:
        lengths = {len(values) for values in self._data.values()}
        if lengths and len(lengths) != 1:
            raise ValueError("All columns must have the same length")

    @property
    def columns(self) -> List[str]:
        return list(self._data.keys())

    def __getitem__(self, key: str) -> Series:
        if key not in self._data:
            raise KeyError(key)
        return Series(self._data[key], index=self._index)

    def __setitem__(self, key: str, values: Iterable[Any]):
        if isinstance(values, Series):
            values = values.tolist()
        values_list = list(values)
        if len(self._index) != len(values_list):
            if not self._data:
                self._index = list(range(len(values_list)))
            else:
                raise ValueError("Column length does not match DataFrame length")
        self._data[key] = values_list
        self._ensure_lengths()

    def drop(self, *, columns: Sequence[str]) -> "DataFrame":
        return DataFrame(
            {key: values for key, values in self._data.items() if key not in columns},
            index=self._index,
        )

    def copy(self) -> "DataFrame":
        return DataFrame({key: list(values) for key, values in self._data.items()}, index=self._index)

    def set_index(self, column: str) -> "DataFrame":
        series = self[column]
        return DataFrame({key: list(values) for key, values in self._data.items()}, index=series.tolist())


def read_csv(path: str) -> DataFrame:
    rows: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as fh:
        header = None
        for line in fh:
            line = line.strip()
            if not line:
                continue
            if header is None:
                header = [column.strip() for column in line.split(",")]
                continue
            values = [value.strip() for value in line.split(",")]
            rows.append(dict(zip(header, values)))
    return DataFrame(rows)


__all__ = ["DataFrame", "Series", "read_csv"]
