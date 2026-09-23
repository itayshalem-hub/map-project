import geopandas as gpd
from shapely.geometry import Polygon

from core.postprocess import clean_polygons, drop_small_polygons, simplify_polygons


def _square(size: float) -> Polygon:
    return Polygon([(0, 0), (size, 0), (size, size), (0, size)])


def test_drop_small_polygons_removes_below_threshold():
    gdf = gpd.GeoDataFrame(
        {"geometry": [_square(5), _square(50)]}, crs="EPSG:32636"
    )
    result = drop_small_polygons(gdf, min_area_m2=100.0)
    assert len(result) == 1
    assert result.geometry.iloc[0].area == 2500.0


def test_drop_small_polygons_handles_empty_gdf():
    gdf = gpd.GeoDataFrame({"geometry": []}, crs="EPSG:32636")
    result = drop_small_polygons(gdf, min_area_m2=100.0)
    assert result.empty


def test_simplify_polygons_preserves_topology():
    # A near-collinear extra vertex that simplification should be able to remove.
    jagged = Polygon([(0, 0), (5, 0.01), (10, 0), (10, 10), (0, 10)])
    gdf = gpd.GeoDataFrame({"geometry": [jagged]}, crs="EPSG:32636")
    result = simplify_polygons(gdf, tolerance=1.0)
    assert len(result.geometry.iloc[0].exterior.coords) < len(jagged.exterior.coords)
    assert result.geometry.iloc[0].is_valid


def test_clean_polygons_runs_both_steps():
    gdf = gpd.GeoDataFrame(
        {"geometry": [_square(2), _square(50)]}, crs="EPSG:32636"
    )
    result = clean_polygons(gdf, tolerance=1.0, min_area_m2=100.0)
    assert len(result) == 1
