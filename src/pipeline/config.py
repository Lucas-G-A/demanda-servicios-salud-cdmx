from pathlib import Path

RAW = Path("/Users/lucasgarcia/Desktop/Dataton/demanda_servicios_salud_cdmx/data/raw")
PROCESSED = Path("/Users/lucasgarcia/Desktop/Dataton/demanda_servicios_salud_cdmx/data/processed")
PROCESSED.mkdir(parents=True, exist_ok=True)

CRS_STANDARD = "EPSG:4326"

# Prefijo SCIAN de "Servicios de salud y asistencia social"
SCIAN_SALUD_PREFIX = "62"

# Ajusta estas rutas a tu repo
PATHS = {
    "denue_2018": RAW / "denue_09_03_2018_csv/conjunto_de_datos/denue_inegi_09_.csv",
    "denue_2020": RAW / "denue_09_04_2020_csv/conjunto_de_datos/denue_inegi_09_.csv",
    "denue_2022": RAW / "denue_09_05_2022_csv/conjunto_de_datos/denue_inegi_09_.csv",
    "denue_2024": RAW / "denue_09_05_2024_csv/conjunto_de_datos/denue_inegi_09_.csv",
    "denue_2025": RAW / "denue_09_05_2025_csv/conjunto_de_datos/denue_inegi_09_.csv",
    "denue_2026": RAW / "denue_09_05_2026_csv/conjunto_de_datos/denue_inegi_09_.csv",
    "ageb_urbana": RAW / "09_ciudaddemexico/conjunto_de_datos/09a.shp",
    "ageb_rural": RAW / "09_ciudaddemexico/conjunto_de_datos/09ar.shp",
    "marginacion_ageb": RAW / "AGEB_2020.xls",
    "centros_salud": RAW / "Centros de Salud datos geograficos/Centros_de_salud.shp",
    "hospitales": RAW / "Hospitales en Mexico/72262636-b579-48bc-a274-85b5d89aec7f/hospitales_publicos_privados_zmvm_operacion.shp",
    "establecimientos_salud": RAW / "ESTABLECIMIENTO_SALUD_202607.xlsx",
    "equipamiento_basico": RAW / "Equipamiento Basico de Salud/Equipamiento_b sico_de_salud.shp",
    "cartografia_colonia": RAW / "indice_marginacion-cartografia2020_shp/colonias_imc2020.shp",
    
}