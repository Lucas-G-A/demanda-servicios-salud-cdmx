# app/pages/2_Dashboard.py
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd

from components.data_loader import load_master, load_candidatos

from components.styling import inject_custom_css, render_logo
st.set_page_config(page_title="ZonaSalud CDMX", page_icon="🏥", layout="wide")
inject_custom_css()
render_logo()

st.set_page_config(page_title="Dashboard — Demanda de Salud CDMX", layout="wide")
st.title("Dashboard")

master = load_master()
candidatos = load_candidatos()

# --- Mismos filtros que el Mapa, para consistencia entre páginas ---
with st.sidebar:
    st.subheader("Filtros")
    nivel_riesgo = st.slider("Confianza mínima aceptable", 0.0, 1.0, 0.3, step=0.05)
    solo_factibles = st.checkbox("Solo zonas con uso de suelo compatible", value=False)

df = master[master["confianza"] >= nivel_riesgo]
if solo_factibles:
    df = df[df["tiene_factibilidad_uso_suelo"]]

# --- Métricas generales ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("AGEBs analizadas", len(df))
col2.metric("Score promedio", f"{df['score_oportunidad'].mean():.3f}")
col3.metric("Zonas alta oportunidad", (df["score_oportunidad"] > df["score_oportunidad"].quantile(0.75)).sum())
col4.metric("Predios candidatos (INDAABIN)", len(candidatos))

st.divider()

# --- Ranking de zonas ---
st.subheader("Top zonas por oportunidad")
top_n = st.slider("Mostrar top N", 5, 50, 15)

top_zonas = (
    df.sort_values("score_oportunidad", ascending=False)
    .head(top_n)[["CVE_AGEB", "colonia", "score_oportunidad", "confianza",
                  "PSDSS", "n_salud_denue_2026", "tiene_factibilidad_uso_suelo"]]
    .rename(columns={
        "colonia": "Colonia",
        "score_oportunidad": "Score",
        "confianza": "Confianza",
        "PSDSS": "% sin serv. salud",
        "n_salud_denue_2026": "Establecimientos actuales",
        "tiene_factibilidad_uso_suelo": "Uso suelo compatible",
    })
)
st.dataframe(top_zonas, use_container_width=True, hide_index=True)

st.divider()
st.subheader("Conectividad y factibilidad")

col_izq, col_der = st.columns(2)

with col_izq:
    st.markdown("**Zonas con mayor afluencia de Metro**")
    top_metro = df.nlargest(10, "afluencia_metro_total")[["colonia", "afluencia_metro_total", "score_oportunidad"]]
    st.dataframe(
        top_metro.rename(columns={"colonia": "Colonia", "afluencia_metro_total": "Afluencia", "score_oportunidad": "Score"}),
        use_container_width=True, hide_index=True,
    )

with col_der:
    st.markdown("**Distribución por tipo de zona**")
    st.bar_chart(df["tipo_zona"].value_counts())

st.metric(
    "AGEBs con uso de suelo compatible (equipamiento)",
    f"{df['tiene_factibilidad_uso_suelo'].sum()} de {len(df)}",
)

st.divider()

# --- Distribución del score ---
col_izq, col_der = st.columns(2)

with col_izq:
    st.subheader("Distribución del score de oportunidad")
    st.bar_chart(df["score_oportunidad"].value_counts(bins=20).sort_index())

with col_der:
    st.subheader("Establecimientos de salud por año (DENUE)")
    cols_denue = [c for c in df.columns if c.startswith("n_salud_denue_")]
    totales_por_año = df[cols_denue].sum().reset_index()
    totales_por_año.columns = ["corte", "total"]
    totales_por_año["año"] = totales_por_año["corte"].str.extract(r"(\d{4})")
    st.line_chart(totales_por_año.set_index("año")["total"])

st.divider()

st.subheader("Predios federales candidatos")
st.dataframe(
    candidatos[["direccion", "tramite", "colonia", "score_oportunidad", "confianza"]]
    .sort_values("score_oportunidad", ascending=False)
    .rename(columns={"direccion": "Dirección", "tramite": "Trámite", "colonia": "Colonia",
                      "score_oportunidad": "Score", "confianza": "Confianza"}),
    use_container_width=True,
    hide_index=True,
)