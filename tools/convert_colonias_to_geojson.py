"""
One-time utility script to convert the colonias shapefile to GeoJSON.

This script is not used by Streamlit at runtime. It is intended to be
executed manually by a developer to generate a GeoJSON file that the
dashboard will later consume.
"""

from pathlib import Path

import geopandas as gpd  # Requires geopandas installed in the environment


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SHAPEFILE_PATH = PROJECT_ROOT / "Geodata" / "colonias_iecm.shp"
GEOJSON_PATH = PROJECT_ROOT / "Geodata" / "colonias_iecm.geojson"


def main() -> None:
    """Read the shapefile, ensure WGS84 coordinates, and export as GeoJSON."""
    print(f"Reading shapefile from: {SHAPEFILE_PATH}")
    gdf = gpd.read_file(SHAPEFILE_PATH)

    # Ensure coordinates are in WGS84 (latitude/longitude)
    if gdf.crs is not None and gdf.crs.to_epsg() != 4326:
        print("Reprojecting to EPSG:4326 (WGS84)…")
        gdf = gdf.to_crs(epsg=4326)

    print(f"Writing GeoJSON to: {GEOJSON_PATH}")
    gdf.to_file(GEOJSON_PATH, driver="GeoJSON")
    print("Conversion completed successfully.")


if __name__ == "__main__":
    main()
