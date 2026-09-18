# app/pages/3_Agente.py
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))  # sube a la raíz del repo, no solo a app/

import streamlit as st
import anthropic

from app.components.data_loader import load_master, load_candidatos
from src.agent.tools import TOOLS_SCHEMA, ejecutar_tool

from components.styling import inject_custom_css, render_logo
st.set_page_config(page_title="ZonaSalud CDMX", page_icon="🏥", layout="wide")
inject_custom_css()
render_logo()

st.set_page_config(page_title="Agente — Demanda de Salud CDMX", layout="wide")
st.title("Agente conversacional")

master = load_master()
candidatos = load_candidatos()

client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])

if "mensajes" not in st.session_state:
    st.session_state.mensajes = []

SYSTEM_PROMPT = """Eres un asistente que responde preguntas sobre demanda de servicios de salud
en la Ciudad de México, usando exclusivamente los datos que te dan las herramientas disponibles.
Nunca inventes cifras -- si una herramienta no te da la información, dilo explícitamente.
Responde en español, de forma breve y clara para una audiencia no técnica."""

for msg in st.session_state.mensajes:
    if msg["role"] in ("user", "assistant") and isinstance(msg["content"], str):
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

pregunta = st.chat_input("Pregunta sobre zonas, oportunidad, predios disponibles...")

if pregunta:
    st.session_state.mensajes.append({"role": "user", "content": pregunta})
    with st.chat_message("user"):
        st.write(pregunta)

    with st.chat_message("assistant"):
        with st.spinner("Consultando datos..."):
            respuesta = client.messages.create(
                model="claude-sonnet-5",
                max_tokens=1024,
                system=SYSTEM_PROMPT,
                tools=TOOLS_SCHEMA,
                messages=st.session_state.mensajes,
            )

            # ciclo de tool use -- puede llamar más de una herramienta antes de responder texto
            while respuesta.stop_reason == "tool_use":
                st.session_state.mensajes.append({"role": "assistant", "content": respuesta.content})

                tool_results = []
                for block in respuesta.content:
                    if block.type == "tool_use":
                        resultado = ejecutar_tool(block.name, block.input, master, candidatos)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": resultado,
                        })

                st.session_state.mensajes.append({"role": "user", "content": tool_results})

                respuesta = client.messages.create(
                    model="claude-sonnet-5",
                    max_tokens=1024,
                    system=SYSTEM_PROMPT,
                    tools=TOOLS_SCHEMA,
                    messages=st.session_state.mensajes,
                )

            texto_final = "".join(b.text for b in respuesta.content if b.type == "text")
            st.write(texto_final)
            st.session_state.mensajes.append({"role": "assistant", "content": texto_final})
