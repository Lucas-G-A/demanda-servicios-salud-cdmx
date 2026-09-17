import pandas as pd
import geopandas as gpd

TOOLS_SCHEMA = [
    {
        "name": "top_zonas_oportunidad",
        "description": "Devuelve las N zonas (AGEB) con mayor score de oportunidad, opcionalmente filtradas por factibilidad de uso de suelo o confianza mínima.",
        "input_schema": {
            "type": "object",
            "properties": {
                "n": {"type": "integer", "description": "Cuántas zonas devolver", "default": 5},
                "solo_factibles": {"type": "boolean", "default": False},
                "confianza_minima": {"type": "number", "default": 0.0},
            },
        },
    },
    {
        "name": "detalle_zona",
        "description": "Devuelve todos los indicadores de una zona específica por CVE_AGEB o nombre de colonia.",
        "input_schema": {
            "type": "object",
            "properties": {
                "colonia": {"type": "string", "description": "Nombre de colonia (búsqueda parcial, no exacta)"},
                "cve_ageb": {"type": "string"},
            },
        },
    },
    {
        "name": "comparar_zonas",
        "description": "Compara indicadores clave entre dos o más colonias.",
        "input_schema": {
            "type": "object",
            "properties": {
                "colonias": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["colonias"],
        },
    },
    {
        "name": "predios_candidatos_cercanos",
        "description": "Lista los predios federales candidatos (INDAABIN) disponibles, con su score de oportunidad.",
        "input_schema": {"type": "object", "properties": {}},
    },
]


def ejecutar_tool(nombre: str, args: dict, master: gpd.GeoDataFrame, candidatos: gpd.GeoDataFrame) -> str:
    if nombre == "top_zonas_oportunidad":
        df = master.copy()
        if args.get("solo_factibles"):
            df = df[df["tiene_factibilidad_uso_suelo"]]
        df = df[df["confianza"] >= args.get("confianza_minima", 0.0)]
        n = args.get("n", 5)
        top = df.nlargest(n, "score_oportunidad")[
            ["CVE_AGEB", "colonia", "score_oportunidad", "confianza", "PSDSS"]
        ]
        return top.to_json(orient="records", force_ascii=False)

    if nombre == "detalle_zona":
        df = master
        if args.get("cve_ageb"):
            resultado = df[df["CVE_AGEB"] == args["cve_ageb"]]
        elif args.get("colonia"):
            resultado = df[df["colonia"].str.contains(args["colonia"], case=False, na=False)]
        else:
            return "Se necesita colonia o cve_ageb."
        if resultado.empty:
            return "No se encontró esa zona."
        cols = ["CVE_AGEB", "colonia", "score_oportunidad", "confianza", "PSDSS",
                "n_salud_denue_2026", "tiene_factibilidad_uso_suelo", "afluencia_metro_total"]
        return resultado[cols].head(5).to_json(orient="records", force_ascii=False)

    if nombre == "comparar_zonas":
        cols = ["colonia", "score_oportunidad", "confianza", "PSDSS", "n_salud_denue_2026"]
        resultados = []
        for colonia in args["colonias"]:
            match = master[master["colonia"].str.contains(colonia, case=False, na=False)]
            if not match.empty:
                promedio = match[cols[1:]].mean()
                resultados.append({"colonia": colonia, **promedio.to_dict()})
        return pd.DataFrame(resultados).to_json(orient="records", force_ascii=False)

    if nombre == "predios_candidatos_cercanos":
        cols = ["direccion", "tramite", "colonia", "score_oportunidad"]
        return candidatos[cols].to_json(orient="records", force_ascii=False)

    return f"Herramienta desconocida: {nombre}"