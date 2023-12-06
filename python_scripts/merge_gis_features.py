"""Helper functions for merging GIS parcel data. Requires geopandas library."""
import datetime
import geopandas as gpd
from typing import Any, Union


# Field names where all values in that field will be added together
# Use for overlapping features for different parcels, like multi-story condos
# Customize for your parcel data
FIELDS_TO_SUM = (
    "ACRE_DEEDED",
    "LAND_SQFT",
    "ACRES",
    "FMV_LAND",
    "FMV_BLDG",
    "FMV_TOTAL",
    "ASV_LAND",
    "ASV_BLDG",
    "ASV_TOTAL",
    "SHAPE.area",
    "SHAPE.len",
)

# Field names where only the maximum value will be used.
# Use for duplicate and overlapping features of the same parcel.
# In my data, there would sometimes be 4 features for 1 parcel, some features
# would have null or 0 values, so I just want the highest, as it's most likely to be the correct one.
# Customize for your parcel data
FIELDS_TO_MAX = (
    "OBJECTID",
    "OBJECTID_1",
    "PARCEL_TYPE",
    "ACRE_DEEDED",
    "LAND_SQFT",
    "ACRES",
    "FMV_LAND",
    "FMV_BLDG",
    "FMV_TOTAL",
    "ASV_LAND",
    "ASV_BLDG",
    "ASV_TOTAL",
    "SHAPE.area",
    "SHAPE.len",
    "ST_NUMBER",
)


def utc_now() -> datetime.datetime:
    """Return timezone-aware datetime object.

    Returns:
        datetime.datetime: Current datetime in UTC.
    """
    return datetime.datetime.now(datetime.UTC)


def first_non_null(series: gpd.Series) -> Union[Any, None]:
    """Find the first non-null value in a series.

    Mostly used for filling in columns with some closely related
    data when merging parcel features.

    Args:
        series (gpd.Series): The series to parse through.

    Returns:
        Union[Any, None]: The matching value (or None).
    """
    idx = series.first_valid_index()
    if idx:
        value = series.loc[idx]
    else:
        value = None
    return value


def combine_attrs_to_csv(series: gpd.Series) -> str:
    """Combined multiple rows of an attribute into one comma-separated string.

    Mainly used to track all the original Parcel IDs
    when merging parcel features into one.

    Args:
        series (gpd.Series): The attribute column (field) to merge.

    Returns:
        str: Merged CSV output.
    """
    if len(series) == 0:
        return ""
    return ",".join(map(str, series))


def merge_dupe_parcels(
    gdf: gpd.GeoDataFrame,
    parcel_id_col_name: str = "PARID",
    geometry_col_name: str = "geometry",
) -> gpd.GeoDataFrame:
    """Merge multiple features/polygons into one where the Parcel ID is the same.

    Args:
        gdf (gpd.GeoDataFrame): The input data to search through.
        parcel_id_col_name (str, optional): Name of the column that has the Parcel ID.
            Defaults to "PARID".
        geometry_col_name (str, optional): Name of the column that has the feature geometry.
            Defaults to "geometry".

    Returns:
        gpd.GeoDataFrame: The new dataframe with all duplicate parcel features merged.
    """
    aggregation_rules_parid = {}  # Holds all the aggregation operation rules for each column.
    for col in gdf.columns:
        if col in FIELDS_TO_MAX:
            method = "max"
        elif col in (parcel_id_col_name, geometry_col_name):
            continue  # We don't want to define a custom aggregation operation for these.
        else:
            method = first_non_null  # We don't care as much about these values, so just use the first valid.
        aggregation_rules_parid[col] = method

    merged = (
        gdf[~gdf[parcel_id_col_name].isna()]
        .dissolve(by=parcel_id_col_name, aggfunc=aggregation_rules_parid)
        .reset_index()
    )
    return merged


def merge_shared_pins(
    gdf: gpd.GeoDataFrame,
    parcel_id_col_name: str = "PARID",
    feature_pin_col_name: str = "PIN",
    geometry_col_name: str = "geometry",
) -> gpd.GeoDataFrame:
    """Merge multiple features/polygons when they share the same feature PIN.

    This is for multi-story condos typically, where multiple separate tax parcels are layered on top of each other.
    In my data, these would all have separate Parcel IDs, but share the same Feature PIN (or just PIN) since they were one structure.

    Args:
        gdf (gpd.GeoDataFrame): The input data to search through.
        parcel_id_col_name (str, optional): Name of the column that has the Parcel ID. Defaults to "PARID".
        feature_pin_col_name (str, optional): Name of the column that has the feature PIN, NOT PARCEL ID. Defaults to "PIN".
        geometry_col_name (str, optional): Name of the column that has the feature geometry.. Defaults to "geometry".

    Returns:
        gpd.GeoDataFrame: New dataframe with all merged features.
    """
    aggregation_rules_pin = {}  # Holds all the aggregation operation rules for each column.
    for col in gdf.columns:
        if col in FIELDS_TO_SUM:
            method = "sum"
        elif col == parcel_id_col_name:
            method = combine_attrs_to_csv  # We want to keep track of the orignal Parcel IDs just in case.
        elif col in (feature_pin_col_name, geometry_col_name):
            continue  # We don't want to define a custom aggregation operation for these.
        else:
            method = first_non_null  # We don't care as much about these values, so just use the first valid.
        aggregation_rules_pin[col] = method

    pin_dissolved_gdf = gdf.dissolve(
        by=feature_pin_col_name, aggfunc=aggregation_rules_pin
    ).reset_index()

    return pin_dissolved_gdf


def merge_parcel_data(geopackage_file_path):
    gdf = gpd.read_file(geopackage_file_path)

    # Merge duplicate features for same Parcel ID
    parid_dissolved_gdf = merge_dupe_parcels(gdf)
    # Merge features that share the same PIN (same building usually)
    pin_dissolved_gdf = merge_shared_pins(parid_dissolved_gdf)
    # Write to file with next line
    # pin_dissolved_gdf.to_file(output_file_path, driver='GPKG')
    return pin_dissolved_gdf
