import pandas as pd
from src.pipeline.clean import (
    load_denue, load_ageb_geom, load_marginacion,
    load_centros_salud, load_hospitales, load_establecimientos_salud,
)
from src.pipeline.dedupe import unify_salud_supply
from src.pipeline.spatial_join import join_puntos_a_ageb
from src.pipeline.config import PATHS, PROCESSED


def main():
    print("Cargando AGEB...")
    ageb = load_ageb_geom()

    print("Cargando marginación...")
    marginacion = load_marginacion()

    print("Cargando DENUE (3 cortes)...")
    denue_2024 = load_denue(PATHS["denue_2024"])
    denue_2025 = load_denue(PATHS["denue_2025"])
    denue_2026 = load_denue(PATHS["denue_2026"])

    print("Cargando y unificando oferta de salud pública...")
    establecimientos = load_establecimientos_salud()
    hospitales = load_hospitales()
    centros_salud = load_centros_salud()
    salud_publica = unify_salud_supply(establecimientos, hospitales, centros_salud)

    print("Join espacial por corte temporal...")
    conteo_2024 = join_puntos_a_ageb(denue_2024, ageb, "n_salud_denue_2024")
    conteo_2025 = join_puntos_a_ageb(denue_2025, ageb, "n_salud_denue_2025")
    conteo_2026 = join_puntos_a_ageb(denue_2026, ageb, "n_salud_publica_2026")
    conteo_publica = join_puntos_a_ageb(salud_publica, ageb, "n_salud_publica")

    print("Ensamblando tabla maestra...")
    master = ageb.merge(marginacion, on="CVE_AGEB", how="left")
    for conteo in [conteo_2024, conteo_2025, conteo_2026, conteo_publica]:
        master = master.merge(conteo, on="CVE_AGEB", how="left")

    count_cols = [c for c in master.columns if c.startswith("n_salud")]
    master[count_cols] = master[count_cols].fillna(0)

    out_path = PROCESSED / "tabla_maestra.parquet"
    master.to_parquet(out_path)
    print(f"Listo: {out_path} ({len(master)} filas)")


if __name__ == "__main__":
    main()