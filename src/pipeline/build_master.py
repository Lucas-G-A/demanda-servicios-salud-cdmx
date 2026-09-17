import pandas as pd
from src.pipeline.clean import (
    load_denue, load_ageb_geom, load_marginacion,
    load_centros_salud, load_hospitales, load_establecimientos_salud,
    load_cartografia_colonia,
)
from src.pipeline.dedupe import unify_salud_supply
from src.pipeline.spatial_join import join_puntos_a_ageb, construir_ageb_a_colonia
from src.pipeline.config import PATHS, PROCESSED
from src.model.trend import compute_trend_generico, compute_opportunity_score
from src.pipeline.clean import load_estaciones_con_afluencia
from src.pipeline.spatial_join import join_afluencia_a_ageb
from src.pipeline.clean import load_indaabin_candidatos
from src.pipeline.spatial_join import join_candidatos_a_ageb
from src.pipeline.clean import load_uso_suelo
from src.pipeline.spatial_join import compute_factibilidad_uso_suelo
from src.model.trend import compute_factibilidad_flag
from src.model.trend import compute_tipo_zona

AÑOS_DENUE = {
    2018: "denue_2018",
    2020: "denue_2020",
    2022: "denue_2022",
    2024: "denue_2024",
    2025: "denue_2025",
    2026: "denue_2026",
}


def main():
    print("Cargando AGEB...")
    ageb = load_ageb_geom()

    print("Cargando cartografía de colonia y cruzando con AGEB...")
    cartografia_colonia = load_cartografia_colonia()
    ageb_a_colonia = construir_ageb_a_colonia(ageb, cartografia_colonia)

    print("Cargando marginación...")
    marginacion = load_marginacion()

    print("Cargando DENUE (6 cortes)...")
    denue_por_año = {año: load_denue(PATHS[key]) for año, key in AÑOS_DENUE.items()}

    print("Cargando y unificando oferta de salud pública...")
    establecimientos = load_establecimientos_salud()
    hospitales = load_hospitales()
    centros_salud = load_centros_salud()
    salud_publica = unify_salud_supply(establecimientos, hospitales, centros_salud)

    print("Ensamblando tabla maestra...")
    master = ageb.merge(marginacion, on="CVE_AGEB", how="left")
    master = master.merge(ageb_a_colonia, on="CVE_AGEB", how="left")

    print("Join espacial por corte temporal (DENUE)...")
    cols_por_año = {}
    for año, denue in denue_por_año.items():
        col_nombre = f"n_salud_denue_{año}"
        conteo = join_puntos_a_ageb(denue, ageb, col_nombre)
        master = master.merge(conteo, on="CVE_AGEB", how="left")
        cols_por_año[año] = col_nombre

    print("Cargando afluencia de Metro...")
    estaciones_con_afluencia = load_estaciones_con_afluencia()
    conteo_metro = join_afluencia_a_ageb(estaciones_con_afluencia, ageb)
    master = master.merge(conteo_metro, on="CVE_AGEB", how="left")
    master["n_estaciones_metro"] = master["n_estaciones_metro"].fillna(0)
    master["afluencia_metro_total"] = master["afluencia_metro_total"].fillna(0)
    
    estaciones_out_path = PROCESSED / "estaciones_metro.parquet"
    estaciones_con_afluencia.to_parquet(estaciones_out_path)
    print(f"Listo: {estaciones_out_path}")

    print("Join espacial de oferta pública unificada...")
    conteo_publica = join_puntos_a_ageb(salud_publica, ageb, "n_salud_publica")
    master = master.merge(conteo_publica, on="CVE_AGEB", how="left")

    count_cols = [c for c in master.columns if c.startswith("n_salud")]
    master[count_cols] = master[count_cols].fillna(0)

    print("Calculando tendencia (6 cortes)...")
    master = compute_trend_generico(master, cols_por_año)

    print("Computando score de oportunidad...")
    master = compute_opportunity_score(master)

    print("Cruzando predios candidatos INDAABIN...")
    candidatos = load_indaabin_candidatos()
    candidatos_con_ageb = join_candidatos_a_ageb(candidatos, master)

    candidatos_out_path = PROCESSED / "indaabin_candidatos.parquet"
    candidatos_con_ageb.to_parquet(candidatos_out_path)
    print(f"Listo: {candidatos_out_path} ({len(candidatos_con_ageb)} predios)")

    agebs_con_candidato = set(candidatos_con_ageb["CVE_AGEB"].dropna())
    master["tiene_predio_candidato"] = master["CVE_AGEB"].isin(agebs_con_candidato)

    print("Cargando uso de suelo...")
    uso_suelo = load_uso_suelo()
    factibilidad = compute_factibilidad_uso_suelo(uso_suelo, ageb)
    master = master.merge(factibilidad, on="CVE_AGEB", how="left")

    master = compute_factibilidad_flag(master)
    master = compute_tipo_zona(master)

    out_path = PROCESSED / "tabla_maestra.parquet"
    master.to_parquet(out_path)
    print(f"Listo: {out_path} ({len(master)} filas)")



if __name__ == "__main__":
    main()