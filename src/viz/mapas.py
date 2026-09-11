# src/viz/mapas.py
import geopandas as gpd
import matplotlib.pyplot as plt


def plot_score_oportunidad(
    master: gpd.GeoDataFrame,
    columna: str = "score_oportunidad",
    cmap: str = "RdYlGn",
    figsize: tuple = (9, 9),
    guardar_en: str | None = None,
):
    """Mapa choropleth de CDMX coloreado por la columna dada."""
    fig, ax = plt.subplots(figsize=figsize)

    master.plot(
        column=columna,
        cmap=cmap,
        legend=True,
        ax=ax,
        edgecolor="white",
        linewidth=0.1,
        legend_kwds={"shrink": 0.6, "label": columna},
    )
    ax.set_axis_off()  # sin ejes de lat/lon, se ve más limpio

    if guardar_en:
        fig.savefig(guardar_en, dpi=150, bbox_inches="tight")

    plt.show()
    return fig, ax

# src/viz/mapas.py — agrega esta función nueva

def plot_score_con_metro(
    master: gpd.GeoDataFrame,
    estaciones_con_afluencia: gpd.GeoDataFrame,
    columna: str = "score_oportunidad",
    cmap: str = "RdYlGn",
    figsize: tuple = (10, 10),
    guardar_en: str | None = None,
):
    """Choropleth de score + estaciones de Metro superpuestas (tamaño = afluencia)."""
    fig, ax = plt.subplots(figsize=figsize)

    master.plot(
        column=columna,
        cmap=cmap,
        legend=True,
        ax=ax,
        edgecolor="white",
        linewidth=0.1,
        legend_kwds={"shrink": 0.6, "label": columna},
        alpha=0.85,
    )

    # tamaño de punto proporcional a afluencia -- normalizado para que no se vea absurdo
    afluencia = estaciones_con_afluencia["afluencia_total_historica"].fillna(0)
    tamaños = 15 + 60 * (afluencia / afluencia.max())

    estaciones_con_afluencia.plot(
        ax=ax,
        markersize=tamaños,
        color="black",
        edgecolor="white",
        linewidth=0.5,
        alpha=0.7,
    )

    ax.set_axis_off()
    ax.set_title(f"{columna} + estaciones de Metro (tamaño = afluencia)", fontsize=11)

    if guardar_en:
        fig.savefig(guardar_en, dpi=150, bbox_inches="tight")

    plt.show()
    return fig, ax


if __name__ == "__main__":
    master = gpd.read_parquet("data/processed/tabla_maestra.parquet")
    plot_score_oportunidad(master)