import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
import streamlit as st
from components.data_loader import load_master

from components.styling import inject_custom_css, render_logo
st.set_page_config(page_title="ZonaSalud CDMX", page_icon="🏥", layout="wide")
inject_custom_css()
render_logo()

st.set_page_config(page_title="Demanda de Salud CDMX", layout="wide")
st.title("Predicción de demanda urbana — Servicios de salud CDMX")

master = load_master()
st.write(f"AGEBs cargadas: {len(master)}")
st.write(master[["CVE_AGEB", "score_oportunidad", "confianza"]].head())