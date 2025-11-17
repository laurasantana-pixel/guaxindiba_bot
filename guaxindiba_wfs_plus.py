# pip install osmnx geopandas shapely unidecode pandas
import osmnx as ox
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point
from shapely.prepared import prep
from unidecode import unidecode

RESERVE_NAME = "Estação Ecológica Estadual de Guaxindiba"
SEARCH_PLACES = [
    "São Francisco de Itabapoana, Rio de Janeiro, Brazil",
    "Rio de Janeiro, Brazil",
    "Brazil",
]

def _normalize(s: str) -> str:
    return unidecode((s or "").lower().strip())

def fetch_reserve_polygon(reserve_name=RESERVE_NAME):
    name_norm = _normalize(reserve_name)
    tags_try = [
        {"boundary": "protected_area"},
        {"leisure": "nature_reserve"},
        {"boundary": "national_park"},
    ]

    for place in SEARCH_PLACES:
        for tags in tags_try:
            try:
                gdf = ox.features_from_place(place, tags=tags)
            except Exception:
                continue
            if gdf is None or gdf.empty:
                continue

            cols_to_check = [c for c in gdf.columns if c.startswith("name")]
            if not cols_to_check:
                continue

            mask = False
            for c in cols_to_check:
                mask = mask | gdf[c].apply(lambda v: name_norm in _normalize(str(v)))
            candidates = gdf[mask]

            if candidates.empty:
                mask2 = False
                for c in cols_to_check:
                    mask2 = mask2 | gdf[c].apply(lambda v: "guaxindiba" in _normalize(str(v)))
                candidates = gdf[mask2]

            if candidates.empty:
                continue

            candidates = candidates.to_crs(4326)
            geom = candidates.unary_union
            if geom.is_empty:
                continue
            return geom

    raise ValueError("Could not find the reserve polygon on OSM.")

def filter_points_in_reserve(csv_path: str, output_path: str, geom=None):
    if geom is None:
        geom = fetch_reserve_polygon()
    prepared = prep(geom)

    df = pd.read_csv(csv_path)
    df["inside"] = df.apply(
        lambda row: prepared.contains(Point(row["lon"], row["lat"])) or 
                    prepared.intersects(Point(row["lon"], row["lat"])),
        axis=1
    )

    inside_df = df[df["inside"]]
    inside_df.to_csv(output_path, index=False)
    print(f"✅ Salvo {len(inside_df)} pontos dentro da reserva em '{output_path}'.")

if __name__ == "__main__":
    print("🔍 Buscando polígono da Estação Ecológica de Guaxindiba...")
    reserve_geom = fetch_reserve_polygon()

    # Salva o polígono para visualização
    gpd.GeoSeries([reserve_geom], crs=4326).to_file("EEEG_polygon.geojson", driver="GeoJSON")
    print("🗺️ Arquivo 'EEEG_polygon.geojson' salvo! Abra em https://geojson.io para visualizar.")

    # Filtra os focos de incêndio
    print("🔥 Verificando quais focos estão dentro da reserva...")
    filter_points_in_reserve("focos_ficticios.csv", "focos_dentro_EEEG.csv", reserve_geom)
