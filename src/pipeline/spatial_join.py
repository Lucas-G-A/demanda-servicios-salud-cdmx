import geopandas as gpd


def join_puntos_a_ageb(puntos: gpd.GeoDataFrame, ageb: gpd.GeoDataFrame, nombre_col: str) -> "pd.DataFrame":
    """Cuenta puntos por AGEB via sjoin espacial."""
    unidos = gpd.sjoin(
        puntos,
        ageb[["CVE_AGEB", "geometry"]],
        how="left",
        predicate="within",
    )
    conteo = unidos.groupby("CVE_AGEB").size().reset_index(name=nombre_col)
    return conteo