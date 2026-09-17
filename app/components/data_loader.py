import streamlit as st
import geopandas as gpd

@st.cache_data
def load_master():
    return gpd.read_parquet("data/processed/tabla_maestra.parquet")

@st.cache_data
def load_candidatos():
    return gpd.read_parquet("data/processed/indaabin_candidatos.parquet")