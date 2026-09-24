# Predicción de demanda urbana — Servicios de salud CDMX

**App en vivo:** [demanda-servicios-salud-cdmx.streamlit.app](https://demanda-servicios-salud-cdmx.streamlit.app/)

Proyecto para el Datatón 2026 (ITAM). Predicción de zonas de la Ciudad de México donde aumentará la demanda de servicios de salud en los próximos años, con mapa interactivo, dashboard y agente conversacional.

Proyecto para el Datatón 2026 (ITAM). Predicción de zonas de la Ciudad de México donde aumentará la demanda de servicios de salud en los próximos años, con mapa interactivo, dashboard y agente conversacional.

## Categoría

Farmacias, consultorios y atención médica primaria — sector salud.

## Unidad de análisis

AGEB (Área Geoestadística Básica), Marco Geoestadístico 2020 de INEGI. Se usa `CVEGEO` (clave completa ENT+MUN+LOC+AGEB, 13 caracteres) como llave única — **no** `CVE_AGEB` del shapefile, que solo trae los últimos 4 dígitos y no es única a nivel ciudad.

## Fuentes de datos

| Fuente | Nivel geográfico | Año / corte | Notas |
|---|---|---|---|
| DENUE (INEGI) | Punto (lat/lon) | 2018, 2020, 2022, 2024, 2025, 2026 | Filtrado a SCIAN 62xxxx (salud). 6 cortes para tendencia y validación retrospectiva. |
| Marco Geoestadístico (INEGI) | AGEB urbana + rural | 2020 | Polígonos, capa `09a`/`09ar` de `conjunto_de_datos` |
| Índice de marginación urbana (CONAPO) | AGEB | 2020 | ~2.9% de AGEBs sin valor — CONAPO excluye AGEBs con población insuficiente para calcular el índice de forma confiable |
| Cartografía de marginación por colonia (CONAPO) | Colonia | 2020 | Usada para el cruce AGEB→colonia (nombre legible) |
| Centros de Salud (Datos Abiertos CDMX / Secretaría de Salud) | Punto | ~2020 | Oferta pública |
| Hospitales públicos/privados ZMVM | Punto, con clave CLUES | 2020 | Se cruza con CLUES para evitar doble conteo |
| Establecimientos de Salud (CLUES, DGIS) | Punto, con clave CLUES | Julio 2026 | Fuente de verdad principal de oferta pública/privada registrada |
| Equipamiento Básico de Salud (Datos Abiertos CDMX) | Colonia (agregado) | Población base 2010 | Variable de contexto, no se suma al conteo de establecimientos |
| Uso de suelo (SEDUVI, Datos Abiertos CDMX) | Punto (~800,000 predios) | — | Clasificado en `equipamiento` / `mixto_compatible` / `otro`; base de la capa de factibilidad |
| Afluencia de Metro + estaciones (STC/CDMX) | Punto (estación) | Histórico | Cruzado por estación+línea; variable de contexto/conectividad |
| Inmuebles federales candidatos (INDAABIN) | Punto (8 predios, geocodificados a mano) | 2026 | "Enajenación a título gratuito" y "adjudicación directa" en CDMX |
| Censo Económico (INEGI) | Municipal | 2019, 2024 | Cargado, no integrado al score (nivel demasiado agregado) |
| ITER (INEGI) | Alcaldía (no AGEB) | 2020 | Explorado, **no integrado** — grano demasiado grueso para diferenciar AGEBs |

**Diferencias temporales y geográficas documentadas**: DENUE (2018-2026, puntual) vs. marginación CONAPO (2020, AGEB) vs. equipamiento básico (base 2010, colonia) vs. uso de suelo (sin fecha de corte clara en el dato) — hasta 8 años de desfase entre fuentes, y 3 niveles de agregación distintos. Se homogeneiza todo a nivel AGEB vía join espacial o por clave `CVEGEO`.

## Score de oportunidad

`score_oportunidad = 0.65 × demanda_norm + 0.0 × tendencia_norm − 0.35 × saturacion_norm`

- **Demanda**: `PSDSS` (% población sin servicios de salud, CONAPO), normalizado por rank-percentil.
- **Saturación**: establecimientos de salud por cada 1,000 habitantes, normalizado por rank-percentil.
- **Tendencia**: ponderada en 0 — ver "Validación retrospectiva" abajo, es una decisión basada en evidencia, no un componente pendiente.
- **Confianza**: baja (0.3) si falta marginación en esa AGEB; si no, `0.5 + 0.5 × R²` de la tendencia (aunque no se use para el score, sí se usa como proxy de calidad de dato).

## Capa de factibilidad (separada del score)

No se mezcla con `score_oportunidad` a propósito — responde una pregunta distinta ("¿se puede construir aquí?" vs. "¿hace falta aquí?").

- `tiene_factibilidad_uso_suelo`: AGEB en el percentil 75+ de `pct_uso_equipamiento`, exigiendo un mínimo de 20 predios registrados en la zona (para no dejar pasar AGEBs rurales con denominador chico).
- `tipo_zona`: clasificación dominante por AGEB (`Equipamiento/Institucional`, `Mixto/Comercial`, `Habitacional`, `Sin dato`).
- Predios candidatos INDAABIN mostrados como capa de puntos independiente, cruzados contra su AGEB para saber su score.

## Visualización — agregación a hexágonos H3

El mapa agrega las 2,452 AGEB a hexágonos H3 (resolución 9, ~175m) para la vista de calor. Cada AGEB se asigna a **todos los hexágonos que su polígono real cubre** (`h3.polygon_to_cells` sobre la geometría completa, con manejo de multipolígonos y huecos interiores) — no solo al hexágono de su centroide. Esto evita huecos visuales en AGEBs grandes o irregulares (común en el Centro Histórico y zonas institucionales), donde un solo punto central dejaba sin pintar el resto del área que la AGEB realmente ocupa. Como respaldo, si un polígono es demasiado pequeño o irregular para que `polygon_to_cells` le asigne una celda completa, se usa su centroide para no perder esa AGEB del mapa.

## Validación retrospectiva — hallazgos

Se probó tendencia lineal (extrapolación de conteos de DENUE) como componente predictivo, en 3 configuraciones distintas:

| Configuración | Accuracy modelo | Accuracy baseline (persistencia) |
|---|---|---|
| AGEB, 3 cortes | ~40-57%* | 96.2% |
| Colonia, 3 cortes | 57.5% | 57.6% (precision "sube": 7.4%) |
| AGEB, 6 cortes, leave-last-out | 92.8% | 96.2% |

*varía según banda de tolerancia para clasificar sube/baja/estable.

**Conclusión**: en las 3 configuraciones, el modelo no supera un baseline ingenuo de "la zona no cambia" — ni con el doble de historia temporal. El problema es estructural: conteos de establecimientos por zona demasiado pequeños y discretos para que una tendencia temporal aporte señal confiable, no una limitación de cantidad de datos.

**Decisión de modelo**: `w_tendencia = 0`. El horizonte de proyección (1/3/5 años) por eso no cambia el ranking de zonas — se asume que la necesidad insatisfecha actual persiste en el horizonte, no que la oferta crecerá de forma extrapolable. Lo que sí varía por horizonte es la confianza (proyectar más lejos es más incierto por definición).

## Limitaciones y supuestos conocidos

- **Torres médicas**: algunos AGEBs concentran cientos de consultorios privados en una sola dirección real (ej. Tlacotalpan, Roma Norte — confirmado por dirección y número exterior idénticos, no es error de geocodificación). Oferta de alcance regional, no de barrio — columna `n_en_misma_direccion` disponible para tratarlo distinto si se necesita.
- **Censo Económico e ITER**: solo a nivel municipal/alcaldía — no aportan variables a nivel AGEB. Explorados y descartados del score por esta razón, no por falta de calidad del dato en sí.
- **Equipamiento Básico de Salud**: población base 2010, desfasada del resto de las fuentes.
- **Predios candidatos INDAABIN**: 8 en total en CDMX, algunos geocodificados a mano por no traer coordenadas ni número exterior en la fuente (ej. "Anillo Periférico s/n") — aproximación al centroide de colonia en esos casos, no dirección exacta.
- **Filtro "Población objetivo"**: informativo en el UI por ahora — no hay desagregación de edad confiable a nivel AGEB (ver ITER arriba).
- Posible doble conteo entre `hospitales`, `establecimientos_salud` (CLUES) y `centros_salud` — resuelto por merge exacto en CLUES donde existe, y dedup espacial (<100m) para `centros_salud`.

## Estructura del repo
```
demanda_servicios_salud_cdmx/
├── data/
│ ├── raw/ # no versionado
│ └── processed/ # tabla_maestra.parquet, indaabin_candidatos.parquet, estaciones_metro.parquet
├── notebooks/
│ └── 01_explore.ipynb
├── src/
│ ├── pipeline/ # clean.py, spatial_join.py, dedupe.py, build_master.py
│ ├── model/ # trend.py (score), validate.py (validación retrospectiva)
│ └── agent/ # tools.py (herramientas del agente)
├── app/
│ ├── Home.py
│ ├── pages/ # 1_Mapa.py, 2_Dashboard.py, 3_Agente.py
│ └── components/ # data_loader.py, styling.py
├── pyproject.toml
└── uv.lock
```


## Cómo correr el pipeline

```bash
uv sync
uv run python -m src.pipeline.build_master
```

## Cómo correr la app

```bash
uv run streamlit run app/Home.py
```

## Deploy

Streamlit Community Cloud, lee `pyproject.toml` directo. API key de Anthropic en Secrets (`ANTHROPIC_API_KEY`), nunca en el repo (`.streamlit/secrets.toml` está en `.gitignore`).

## Trabajo futuro (fuera de alcance por tiempo, no por descuido)

- **Inmuebles24 / portales inmobiliarios**: señal de mercado (precio, disponibilidad real) que complementaría la factibilidad, hoy basada solo en uso de suelo normativo.
- **Licencias de construcción**: único proxy honesto de crecimiento futuro identificado y no integrado — resolvería el componente de tendencia sin depender de extrapolar oferta existente.
- **RESAGEBURB (INEGI)**: activaría de verdad el filtro de población objetivo (adultos mayores / primera infancia) a nivel AGEB — ITER solo llega a nivel alcaldía.
- **Movilidad completa**: Metrobús (requiere shapefile de líneas, señal más gruesa que Metro) y RTP (sin paradas geolocalizadas públicas) quedaron fuera por costo/beneficio.

## Estado actual

- [x] Pipeline de datos: 9 fuentes limpiadas, deduplicadas, unidas por AGEB
- [x] Score de oportunidad (demanda + saturación, tendencia validada y descartada con evidencia)
- [x] Capa de factibilidad (uso de suelo + INDAABIN)
- [x] Validación retrospectiva documentada
- [x] App Streamlit: Home, Mapa (hexágonos H3 por cobertura real de polígono, Metro, candidatos INDAABIN), Dashboard, Agente (tool use)
- [x] Estilos y logo consistentes en las 4 páginas
- [x] Deploy en Streamlit Community Cloud
- [ ] Filtro de población objetivo por edad (bloqueado por falta de dato a nivel AGEB)

## Stack

Python, `uv`, pandas, geopandas, Streamlit, pydeck (hexágonos H3), Anthropic API (agente, tool use).