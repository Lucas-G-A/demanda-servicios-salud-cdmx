# app/components/styling.py
import streamlit as st

def inject_custom_css():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Fraunces:wght@500;600&family=IBM+Plex+Sans:wght@400;500&display=swap');

        html, body, [class*="css"] {
            font-family: 'IBM Plex Sans', sans-serif;
        }

        h1, h2, h3 {
            font-family: 'Fraunces', serif;
            font-weight: 600;
            letter-spacing: -0.01em;
        }

        [data-testid="stMetricValue"] {
            font-family: 'Fraunces', serif;
            font-size: 2rem;
            color: #1B4B4F;
        }

        [data-testid="stMetricLabel"] {
            font-family: 'IBM Plex Sans', sans-serif;
            font-size: 0.8rem;
            color: #5A5A5A;
        }

        hr {
            border-top: 1px solid #E0DACE;
        }

        [data-testid="stSidebar"] {
            background-color: #F2EDE4;
        }
        </style>
    """, unsafe_allow_html=True)

def render_logo():
    st.markdown("""
        <div style="display:flex; align-items:baseline; gap:8px; margin-bottom:8px;">
            <span style="font-family:'Fraunces',serif; font-weight:600; font-size:1.4rem; color:#1B4B4F;">Zona</span><span style="font-family:'Fraunces',serif; font-weight:600; font-size:1.4rem; color:#D98E04;">Salud</span>
            <span style="font-family:'IBM Plex Sans',sans-serif; font-size:0.75rem; color:#8A8A8A;">CDMX</span>
        </div>
    """, unsafe_allow_html=True)