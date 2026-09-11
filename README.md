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
```
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
```

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

## Validación retrospectiva — hallazgos

Se probó un modelo de tendencia lineal simple (extrapolación de 3 cortes de DENUE:
2024, 2025, 2026) para predecir el número de establecimientos de salud por zona,
tanto a nivel AGEB como a nivel colonia.

**Resultado**: el modelo no superó un baseline ingenuo de persistencia ("la zona
se mantiene igual que el último corte conocido"):

| Nivel | Accuracy modelo | Accuracy baseline (persistencia) | Precision clase "sube" |
|---|---|---|---|
| AGEB | ~40-57%* | 96.2% | — |
| Colonia | 57.5% | 57.6% | 7.4% |

*varía según banda de tolerancia usada para clasificar sube/baja/estable.

**Conclusión**: con solo 3 momentos históricos y conteos de establecimientos
pequeños y discretos por zona (mayoría entre 0-3), la extrapolación lineal no
tiene poder predictivo real — no es un error de implementación, se validó en
dos granularidades geográficas distintas con el mismo resultado.

**Decisión de modelo**: el score de oportunidad final pondera `tendencia = 0`.
El componente de proyección se apoya en variables estáticas de necesidad
insatisfecha (`PSDSS`, marginación CONAPO) en vez de en tendencia de oferta —
se asume que la necesidad insatisfecha actual persiste o se agrava en el
horizonte proyectado, no que la oferta crecerá de forma extrapolable.

Esto se documenta como limitación reconocida, no como fallo oculto — es
resultado directo de la validación retrospectiva que pide el reto.

**Próximo paso evaluado**: probar con más cortes históricos de DENUE (5-6 en
vez de 3) para ver si la tendencia a nivel colonia mejora con más densidad
temporal, con límite de tiempo definido para no bloquear el resto del proyecto.

## Fixes de datos durante el desarrollo

- `CVE_AGEB` del shapefile de marco geoestadístico son solo 4 dígitos (no
  únicos a nivel ciudad) — se usó `CVEGEO` (13 caracteres, ENT+MUN+LOC+AGEB)
  como llave real para el merge con marginación CONAPO.
- Normalización del score cambiada de min-max a rank-percentil — el min-max
  se veía distorsionado por outliers extremos (torres médicas con 200+
  establecimientos en una sola dirección), comprimiendo el resto de las
  zonas a un rango angosto y sin poder de diferenciación.
- Identificadas concentraciones legítimas de oferta médica en una sola
  dirección (ej. Tlacotalpan, Roma Norte — 289 establecimientos, mismo
  número exterior, confirmado que no es error de geocodificación).
  Marcadas con `n_en_misma_direccion` para uso futuro, no filtradas.


## Validación retrospectiva — hallazgos (actualizado con 6 cortes)

Se probó tendencia lineal con 6 cortes de DENUE (2018, 2020, 2022, 2024, 2025, 2026)
usando validación leave-last-out (se entrena con 2018-2025, se predice 2026, se
compara contra el valor real).

| Métrica | Valor |
|---|---|
| Correlación de Spearman | 0.995 |
| Accuracy modelo (sube/baja/estable) | 92.8% |
| Accuracy baseline (persistencia) | 96.2% |

**Conclusión**: incluso con el doble de historia temporal (6 cortes vs. 3), la
tendencia lineal sigue sin superar la predicción ingenua de "la zona no cambia".
Se confirma en 3 configuraciones distintas (AGEB/3 cortes, colonia/3 cortes,
AGEB/6 cortes) que el problema es estructural — conteos de establecimientos por
zona demasiado pequeños y discretos para que una tendencia temporal aporte señal
confiable — no una limitación de cantidad de datos históricos.

**Decisión final de modelo**: `w_tendencia = 0`. El score de oportunidad se basa
en demanda insatisfecha (marginación/PSDSS) y saturación de oferta actual,
ambas señales estáticas pero validadas y con variación real entre zonas.

## Stack

Python, `uv`, pandas, geopandas, Streamlit, pydeck (hexágonos H3), Anthropic API (agente).
