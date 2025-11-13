"""Utilities to abstract over the optional :mod:`shapely` dependency.

The project historically shipped a tiny, home-grown ``shapely`` package that
implements only the handful of geometric operations required by the tests.
When users install the real third-party library we should defer to it instead
of our stub so the richer geometry types remain available (e.g. ``LineString``
required by ``osmnx``).

Importers should use the re-exported symbols from this module instead of
importing :mod:`shapely` directly. We first try to import the real library and
fall back to the in-repo stub for development environments that do not have the
compiled dependency available.
"""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING


def _is_within_repo(entry: str, repo_root: Path) -> bool:
    try:
        resolved = Path(entry).resolve()
    except OSError:
        return False
    try:
        return resolved.is_relative_to(repo_root)
    except AttributeError:  # Python < 3.9 compatibility (defensive)
        return repo_root in resolved.parents or resolved == repo_root

@contextmanager
def _without_local_stub():  # pragma: no cover - helper for optional dependency
    import sys

    repo_root = Path(__file__).resolve().parents[1]
    original = list(sys.path)
    try:
        sys.path = [
            entry
            for entry in original
            if not _is_within_repo(entry, repo_root)
        ]
        yield
    finally:
        sys.path = original


try:  # pragma: no cover - exercised when the optional dependency is installed
    with _without_local_stub():
        from shapely.geometry import Point, Polygon, mapping, shape  # type: ignore
        from shapely.geometry.base import BaseGeometry  # type: ignore
        from shapely import wkt  # type: ignore
    USING_STUB = False
except Exception:  # pragma: no cover - executed in CI where the stub is used
    from shapely.geometry import Point, Polygon, mapping, shape  # type: ignore
    from shapely.geometry.base import BaseGeometry  # type: ignore
    from shapely import wkt  # type: ignore
    USING_STUB = True

__all__ = [
    "BaseGeometry",
    "Point",
    "Polygon",
    "mapping",
    "shape",
    "wkt",
    "USING_STUB",
]


if TYPE_CHECKING:  # pragma: no cover
    # Help static type checkers understand the public contract.
    from typing import Any

    def __getattr__(name: str) -> Any:
        ...
