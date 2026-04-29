"""Verify that required third-party dependencies are importable in QGIS Python."""

import importlib
import sys

REQUIRED_MODULES = [
    "numpy",
    "pandas",
    "scipy",
    "matplotlib",
    "seaborn",
    "shapely",
    "geopandas",
    "plotly",
]


def main() -> int:
    failures = []
    for name in REQUIRED_MODULES:
        try:
            importlib.import_module(name)
            print(f"OK: {name}")
        except Exception as exc:  # pragma: no cover - runtime dependency check
            failures.append((name, exc))
            print(f"FAIL: {name} -> {exc}")

    if failures:
        print("\nMissing or broken dependencies detected.")
        return 1

    print("\nAll required dependencies are available in this QGIS Python environment.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
