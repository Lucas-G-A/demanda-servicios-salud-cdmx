import pandas as pd
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

def construir_ageb_a_colonia(ageb: gpd.GeoDataFrame, cartografia_colonia: gpd.GeoDataFrame) -> pd.DataFrame:
    ageb_centroides = ageb.copy()
    ageb_centroides["geometry"] = ageb_centroides.geometry.to_crs(6372).centroid.to_crs(4326)

    cruce = gpd.sjoin(
        ageb_centroides,
        cartografia_colonia[["COLONIA", "geometry"]],
        how="left",
        predicate="within",
    )
    cruce = cruce.rename(columns={"COLONIA": "colonia"})
    return cruce[["CVE_AGEB", "colonia"]]