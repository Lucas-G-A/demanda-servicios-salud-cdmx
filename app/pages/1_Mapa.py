# app/pages/1_Mapa.py
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

import streamlit as st
import pydeck as pdk
import pandas as pd
import h3
import geopandas as gpd

from app.components.data_loader import load_master, load_candidatos

from app.components.styling import inject_custom_css, render_logo
st.set_page_config(page_title="ZonaSalud CDMX", page_icon="🏥", layout="wide")
inject_custom_css()
render_logo()

master = load_master()
candidatos = load_candidatos()

st.markdown("# Dónde crece la necesidad")
st.caption("Servicios de salud · Ciudad de México · proyección a 3 años")

# app/pages/1_Mapa.py — reemplaza la función agregar_a_hexagonos() completa

def _coords_a_latlng(coords):
    # shapely da (x, y) = (lon, lat); h3 espera (lat, lon) -- hay que invertir
    return [(lat, lon) for lon, lat in coords]


def _ageb_a_celdas_h3(geom, resolucion):
    celdas = set()
    poligonos = geom.geoms if geom.geom_type == "MultiPolygon" else [geom]
    for poly in poligonos:
        exterior = _coords_a_latlng(poly.exterior.coords)
        huecos = [_coords_a_latlng(interior.coords) for interior in poly.interiors]
        try:
            h3poly = h3.LatLngPoly(exterior, *huecos)
            celdas.update(h3.polygon_to_cells(h3poly, resolucion))
        except Exception:
            # si el polígono es demasiado pequeño/raro para cubrir ninguna celda completa,
            # al menos no perder la AGEB -- usa su centroide como respaldo
            c = poly.centroid
            celdas.add(h3.latlng_to_cell(c.y, c.x, resolucion))
    return list(celdas)


@st.cache_data
def agregar_a_hexagonos(_master, resolucion=9):
    df = _master.copy()

    registros = []
    for _, row in df.iterrows():
        for celda in _ageb_a_celdas_h3(row.geometry, resolucion):
            registros.append({
                "h3_index": celda,
                "CVE_AGEB": row["CVE_AGEB"],
                "score_oportunidad": row["score_oportunidad"],
                "confianza": row["confianza"],
                "colonia": row["colonia"],
                "tipo_zona": row["tipo_zona"],
                "tiene_factibilidad_uso_suelo": row["tiene_factibilidad_uso_suelo"],
            })

    expandido = pd.DataFrame(registros)

    agregado = expandido.groupby("h3_index").agg(
        score_oportunidad=("score_oportunidad", "mean"),
        confianza=("confianza", "mean"),
        n_agebs=("CVE_AGEB", "nunique"),
        factible=("tiene_factibilidad_uso_suelo", "any"),
        colonia=("colonia", lambda s: s.mode().iloc[0] if not s.mode().empty else "Sin dato"),
        tipo_zona=("tipo_zona", lambda s: s.mode().iloc[0] if not s.mode().empty else "Sin dato"),
    ).reset_index()

    return agregado

hexagonos = agregar_a_hexagonos(master)

with st.sidebar:
    st.subheader("Filtros")

    horizonte = st.selectbox("Horizonte de proyección", ["1 año", "3 años", "5 años"], index=1)
    st.caption("Basado en necesidad insatisfecha actual, asumida persistente en el horizonte (ver limitaciones en README).")

    poblacion_objetivo = st.selectbox(
        "Población objetivo", ["General", "Adultos mayores", "Primera infancia"]
    )
    st.caption("Filtro informativo — no hay desagregación de edad disponible a nivel AGEB todavía.")

    tipo_zona_sel = st.selectbox(
        "Tipo de zona",
        ["Todas"] + sorted(master["tipo_zona"].dropna().unique().tolist())
    )

    factor_horizonte = {"1 año": 1.0, "3 años": 0.85, "5 años": 0.65}[horizonte]
    hexagonos = hexagonos.copy()
    hexagonos["confianza_ajustada"] = hexagonos["confianza"] * factor_horizonte

    nivel_riesgo = st.slider(
        "Confianza mínima aceptable", 0.0, 1.0, 0.3, step=0.05
    )

    solo_factibles = st.checkbox("Solo zonas con uso de suelo compatible", value=False)

    mostrar_candidatos = st.checkbox("Mostrar predios federales candidatos (INDAABIN)", value=True)

hex_filtrados = hexagonos[hexagonos["confianza_ajustada"] >= nivel_riesgo]
if solo_factibles:
    hex_filtrados = hex_filtrados[hex_filtrados["factible"]]

if tipo_zona_sel != "Todas":
    hex_filtrados = hex_filtrados[hex_filtrados["tipo_zona"] == tipo_zona_sel]


def score_a_color(score: float) -> list[int]:
    """Interpola petróleo (bajo) -> crema (medio) -> dorado (alto)."""
    import numpy as np
    score = np.clip(score, 0, 1)
    color_bajo = np.array([27, 75, 79])
    color_medio = np.array([242, 237, 228])
    color_alto = np.array([217, 142, 4])

    if score < 0.5:
        t = score / 0.5
        color = color_bajo * (1 - t) + color_medio * t
    else:
        t = (score - 0.5) / 0.5
        color = color_medio * (1 - t) + color_alto * t
    return [int(c) for c in color] + [200]

hex_filtrados = hex_filtrados.copy()
score_min, score_max = hex_filtrados["score_oportunidad"].min(), hex_filtrados["score_oportunidad"].max()
hex_filtrados["score_norm"] = (hex_filtrados["score_oportunidad"] - score_min) / (score_max - score_min)
hex_filtrados["color"] = hex_filtrados["score_norm"].apply(score_a_color)

# === NUEVO BLOQUE 1: tooltip propio de los hexágonos ===
hex_filtrados["titulo"] = hex_filtrados["colonia"]
hex_filtrados["linea1"] = hex_filtrados["score_oportunidad"].apply(lambda s: f"Score: {s:.2f}")
hex_filtrados["linea2"] = "Tipo de zona: " + hex_filtrados["tipo_zona"].astype(str)
hex_filtrados["linea3"] = "AGEBs agregadas: " + hex_filtrados["n_agebs"].astype(str)
# === FIN NUEVO BLOQUE 1 ===

capa_hex = pdk.Layer(
    "H3HexagonLayer",
    hex_filtrados,
    get_hexagon="h3_index",
    get_fill_color="color",
    get_line_color=[253, 252, 250],
    line_width_min_pixels=0.5,
    pickable=True,
    extruded=False,
)

capas = [capa_hex]

if mostrar_candidatos:
    candidatos_pd = pd.DataFrame({
        "lat": candidatos.geometry.y,
        "lon": candidatos.geometry.x,
        "direccion": candidatos["direccion"],
        "tramite": candidatos["tramite"],
    })

    # === NUEVO BLOQUE 2: tooltip propio de los candidatos INDAABIN ===
    candidatos_pd["titulo"] = candidatos_pd["direccion"]
    candidatos_pd["linea1"] = "Trámite: " + candidatos_pd["tramite"].astype(str)
    candidatos_pd["linea2"] = ""
    candidatos_pd["linea3"] = ""
    # === FIN NUEVO BLOQUE 2 ===

    capa_candidatos = pdk.Layer(
        "ScatterplotLayer",
        candidatos_pd,
        get_position=["lon", "lat"],
        get_radius=150,
        get_fill_color=[0, 100, 255, 220],
        pickable=True,
    )
    capas.append(capa_candidatos)

mostrar_metro = st.sidebar.checkbox("Mostrar estaciones de Metro", value=True)

if mostrar_metro:
    estaciones = gpd.read_parquet("data/processed/estaciones_metro.parquet")
    estaciones_pd = pd.DataFrame({
        "lat": estaciones.geometry.y,
        "lon": estaciones.geometry.x,
        "nombre": estaciones["NOMBRE"],
        "afluencia": estaciones["afluencia_total_historica"].fillna(0),
    })
    max_afluencia = estaciones_pd["afluencia"].max()
    estaciones_pd["radio"] = 40 + 120 * (estaciones_pd["afluencia"] / max_afluencia)

    # === NUEVO BLOQUE 3: tooltip propio de las estaciones de Metro ===
    estaciones_pd["titulo"] = estaciones_pd["nombre"]
    estaciones_pd["linea1"] = estaciones_pd["afluencia"].apply(lambda a: f"Afluencia histórica: {a:,.0f}")
    estaciones_pd["linea2"] = ""
    estaciones_pd["linea3"] = ""
    # === FIN NUEVO BLOQUE 3 ===

    capa_metro = pdk.Layer(
        "ScatterplotLayer",
        estaciones_pd,
        get_position=["lon", "lat"],
        get_radius="radio",
        get_fill_color=[27, 75, 79, 160],
        pickable=True,
    )
    capas.append(capa_metro)


if "ageb_a_centrar" in st.session_state:
    fila = master[master["CVE_AGEB"] == st.session_state["ageb_a_centrar"]]
    if not fila.empty:
        centroide = fila.geometry.centroid.iloc[0]
        view_state = pdk.ViewState(latitude=centroide.y, longitude=centroide.x, zoom=14, pitch=0, bearing=0)
        st.info(f"Mostrando zona: {fila.iloc[0]['colonia']}")
        del st.session_state["ageb_a_centrar"]
    else:
        view_state = pdk.ViewState(latitude=19.4326, longitude=-99.1332, zoom=10)
else:
    view_state = pdk.ViewState(latitude=19.4326, longitude=-99.1332, zoom=10)

# === CAMBIO: tooltip final usa un solo campo unificado ===
st.pydeck_chart(pdk.Deck(
    layers=capas,
    initial_view_state=view_state,
    tooltip={"html": "<b>{titulo}</b><br/>{linea1}<br/>{linea2}<br/>{linea3}"},
))

st.markdown("""
<div style="background: linear-gradient(to right, #1B4B4F, #F2EDE4, #D98E04); height:12px; border-radius:4px; margin-top:8px;"></div>
<div style="display:flex; justify-content:space-between; font-size:0.75rem; color:#5A5A5A;">
    <span>Baja oportunidad</span><span>Alta oportunidad</span>
</div>
""", unsafe_allow_html=True)

st.caption("🟤 Zonas por score de oportunidad · 🔵 Predios federales candidatos (INDAABIN) · ⬛ Estaciones de Metro (tamaño = afluencia)")

col1, col2, col3 = st.columns(3)
col1.metric("Zonas analizadas (hexágonos)", len(hex_filtrados))
col2.metric("Score promedio", f"{hex_filtrados['score_oportunidad'].mean():.2f}")
col3.metric("Predios candidatos mostrados", len(candidatos) if mostrar_candidatos else 0)