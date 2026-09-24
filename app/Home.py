# app/Home.py
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import streamlit as st
from components.data_loader import load_master
from components.styling import inject_custom_css, render_logo

st.set_page_config(page_title="ZonaSalud CDMX", page_icon="🏥", layout="wide")
inject_custom_css()
render_logo()

master = load_master()

st.markdown("# Predicción de demanda de salud en la Ciudad de México")
st.caption("Datatón 2026 · ITAM")

st.write(
    "¿Dónde crece la necesidad de atención médica en CDMX, y dónde además se puede construir? "
    "Esta app cruza demanda insatisfecha, saturación de oferta actual y factibilidad de uso de suelo "
    f"en {len(master)} zonas (AGEB) de la ciudad."
)

col1, col2, col3 = st.columns(3)
col1.metric("AGEBs analizadas", len(master))
col2.metric("Zonas alta oportunidad", (master["score_oportunidad"] > master["score_oportunidad"].quantile(0.75)).sum())
col3.metric("Predios candidatos", 8)

st.info("Usa el menú de la izquierda para navegar: **Mapa**, **Dashboard**, **Agente**.")