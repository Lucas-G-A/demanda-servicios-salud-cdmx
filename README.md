# Predicción de demanda urbana — Servicios de salud CDMX

Proyecto para el Datatón 2026 (ITAM). Predicción de zonas de la Ciudad de México donde aumentará la demanda de servicios de salud en los próximos años, con mapa interactivo, dashboard y agente conversacional.

## Categoría

Farmacias, consultorios y atención médica primaria — sector salud.

## Unidad de análisis

AGEB (Área Geoestadística Básica), Marco Geoestadístico 2020 de INEGI. Se usa `CVEGEO` (clave completa ENT+MUN+LOC+AGEB, 13 caracteres) como llave única — **no** `CVE_AGEB` del shapefile, que solo trae los últimos 4 dígitos y no es única a nivel ciudad.

## Fuentes de datos

| Fuente | Nivel geográfico | Año / corte | Notas |
|---|---|---|---|
| DENUE (INEGI) | Punto (lat/lon) | 2024, 2025, 2026 | Filtrado a SCIAN 62xxxx (salud y asistencia social). 3 cortes para tendencia y validación retrospectiva. |
| Marco Geoestadístico (INEGI) | AGEB urbana + rural | 2020 | Polígonos, capa `09a`/`09ar` de `conjunto_de_datos` |
| Índice de marginación urbana (CONAPO) | AGEB | 2020 | ~2.9% de AGEBs sin valor — CONAPO excluye AGEBs con población insuficiente para calcular el índice de forma confiable |
| Centros de Salud (Datos Abiertos CDMX / Secretaría de Salud) | Punto | ~2020 (verificar en diccionario) | Oferta pública |
| Hospitales públicos/privados ZMVM | Punto, con clave CLUES | 2020 | Se cruza con CLUES para evitar doble conteo |
| Establecimientos de Salud (CLUES, DGIS) | Punto, con clave CLUES | Julio 2026 | Fuente de verdad principal de oferta pública/privada registrada |
| Equipamiento Básico de Salud (Datos Abiertos CDMX) | Colonia (agregado) | Población base 2010 | No es punto — se usa como variable de contexto, no se suma al conteo de establecimientos |
| Censo Económico (INEGI) | Municipal | 2019, 2024 | Documentar que no baja a nivel AGEB |
| Población con servicios de salud (Datos Abiertos CDMX) | Alcaldía | — | % población con/sin derechohabiencia por institución |

**Diferencias temporales y geográficas documentadas**: DENUE (2024-2026, puntual) vs. marginación CONAPO (2020, AGEB) vs. equipamiento básico (base 2010, colonia) — hay hasta 6 años de desfase entre fuentes, y 3 niveles de agregación distintos. Se homogeneiza todo a nivel AGEB vía join espacial o por clave `CVEGEO`.

## Limitaciones y supuestos conocidos

- **Torres médicas**: algunos AGEBs concentran cientos de consultorios privados en una sola dirección real (ej. Tlacotalpan, Roma Norte — confirmado por dirección y número exterior idénticos, no es error de geocodificación). Esta oferta es de alcance regional/citywide, no de barrio — puede sesgar el score de saturación local si se trata igual que una clínica de vecindario. Marcado en la columna `n_en_misma_direccion`.
- **Censo Económico** solo a nivel municipal — no aporta variables a nivel AGEB directamente.
- **Equipamiento Básico de Salud** usa población base 2010, desfasada ~10-15 años del resto de las fuentes.
- Posible doble conteo entre `hospitales`, `establecimientos_salud` (CLUES) y `centros_salud` — resuelto por merge exacto en CLUES donde existe, y dedup espacial (<100m) para `centros_salud` que no trae CLUES.

## Estructura del repo
dataton-salud/
├── data/
│ ├── raw/ # no versionado
│ └── processed/ # tabla_maestra.parquet
├── notebooks/
│ └── 01_explore.ipynb
├── src/
│ ├── pipeline/ # limpieza, dedup, join espacial, tabla maestra
│ ├── model/ # tendencia + validación retrospectiva (pendiente)
│ └── agent/ # herramientas del agente conversacional (pendiente)
├── app/ # Streamlit — Mapa / Dashboard / Agente (pendiente)
├── pyproject.toml
└── uv.lock


## Cómo correr el pipeline

```bash
uv sync
uv run python -m src.pipeline.build_master
```

Genera `data/processed/tabla_maestra.parquet`: una fila por AGEB, con geometría, indicadores de marginación, y conteos de establecimientos de salud por corte temporal.

## Estado actual

- [x] Pipeline de datos: limpieza, dedup de fuentes de salud, join espacial DENUE/salud pública → AGEB
- [x] Tabla maestra validada (0 duplicados de clave, geometrías válidas)
- [ ] Score de oportunidad (tendencia + demanda − saturación)
- [ ] Validación retrospectiva
- [ ] App Streamlit (mapa hexagonal, dashboard, agente)
- [ ] Deploy en Streamlit Community Cloud

## Stack

Python, `uv`, pandas, geopandas, Streamlit, pydeck (hexágonos H3), Anthropic API (agente).
