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

# --- Agregación a hexágonos H3 res 8, vía centroide de cada AGEB ---
@st.cache_data
def agregar_a_hexagonos(_master, resolucion=9):
    df = _master.copy()
    centroides = df.geometry.centroid
    df["h3_index"] = [
        h3.latlng_to_cell(pt.y, pt.x, resolucion) for pt in centroides
    ]

    agregado = df.groupby("h3_index").agg(
        score_oportunidad=("score_oportunidad", "mean"),
        confianza=("confianza", "mean"),
        n_agebs=("CVE_AGEB", "count"),
        factible=("tiene_factibilidad_uso_suelo", "any"),
    ).reset_index()

    return agregado

hexagonos = agregar_a_hexagonos(master)

# --- Sidebar de filtros ---
with st.sidebar:
    st.subheader("Filtros")

    horizonte = st.selectbox("Horizonte de proyección", ["1 año", "3 años", "5 años"], index=1)
    st.caption("Basado en necesidad insatisfecha actual, asumida persistente en el horizonte (ver limitaciones en README).")

    poblacion_objetivo = st.selectbox(
        "Población objetivo", ["General", "Adultos mayores", "Primera infancia"]
    )
    st.caption("Filtro informativo — no hay desagregación de edad disponible a nivel AGEB todavía.")

    tipo_zona = st.selectbox("Tipo de zona", ["Todas"])
    st.caption("Pendiente de implementar (requiere clasificación de zona adicional).")

    nivel_riesgo = st.slider(
        "Confianza mínima aceptable", 0.0, 1.0, 0.3, step=0.05
    )

    solo_factibles = st.checkbox("Solo zonas con uso de suelo compatible", value=False)

    mostrar_candidatos = st.checkbox("Mostrar predios federales candidatos (INDAABIN)", value=True)

# --- Aplicar filtros reales ---
hex_filtrados = hexagonos[hexagonos["confianza"] >= nivel_riesgo]
if solo_factibles:
    hex_filtrados = hex_filtrados[hex_filtrados["factible"]]

# app/pages/1_Mapa.py — agrega esta función, y úsala antes de crear el pydeck.Layer

def score_a_color(score: float) -> list[int]:
    """Interpola petróleo (bajo) -> crema (medio) -> dorado (alto)."""
    import numpy as np
    score = np.clip(score, 0, 1)
    color_bajo = np.array([27, 75, 79])      # #1B4B4F
    color_medio = np.array([242, 237, 228])  # #F2EDE4
    color_alto = np.array([217, 142, 4])     # #D98E04

    if score < 0.5:
        t = score / 0.5
        color = color_bajo * (1 - t) + color_medio * t
    else:
        t = (score - 0.5) / 0.5
        color = color_medio * (1 - t) + color_alto * t
    return [int(c) for c in color] + [200]  # alpha

hex_filtrados = hex_filtrados.copy()
# normaliza el score dentro del rango actual filtrado, no 0-1 absoluto -- más contraste visual real
score_min, score_max = hex_filtrados["score_oportunidad"].min(), hex_filtrados["score_oportunidad"].max()
hex_filtrados["score_norm"] = (hex_filtrados["score_oportunidad"] - score_min) / (score_max - score_min)
hex_filtrados["color"] = hex_filtrados["score_norm"].apply(score_a_color)

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

    capa_metro = pdk.Layer(
        "ScatterplotLayer",
        estaciones_pd,
        get_position=["lon", "lat"],
        get_radius="radio",
        get_fill_color=[27, 75, 79, 160],  # petróleo, distinto del dorado de candidatos
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

st.pydeck_chart(pdk.Deck(
    layers=capas,
    initial_view_state=view_state,
    tooltip={"html": "<b>{nombre}</b><br/>Afluencia: {afluencia}<br/>Score: {score_oportunidad}<br/>{direccion}"},
))

st.caption("🟤 Zonas por score de oportunidad · 🔵 Predios federales candidatos (INDAABIN) · ⬛ Estaciones de Metro (tamaño = afluencia)")

col1, col2, col3 = st.columns(3)
col1.metric("Zonas analizadas (hexágonos)", len(hex_filtrados))
col2.metric("Score promedio", f"{hex_filtrados['score_oportunidad'].mean():.2f}")
col3.metric("Predios candidatos mostrados", len(candidatos) if mostrar_candidatos else 0)