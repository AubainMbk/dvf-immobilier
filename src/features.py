import polars as pl
from pathlib import Path

PROCESSED_DIR = Path("data/processed")


def compute_features() -> pl.DataFrame:
    parquet_files = list(PROCESSED_DIR.glob("dvf_*.parquet"))
    if not parquet_files:
        raise RuntimeError("Aucun Parquet dans data/processed/. Lance transform.py d'abord.")

    dfs = [pl.read_parquet(f) for f in parquet_files]
    df = pl.concat(dfs, how="diagonal")

    # Agrégation par commune × type_local × année
    agg = (
        df
        .group_by(["code_commune", "nom_commune", "code_departement", "type_local", "annee"])
        .agg([
            pl.col("prix_m2").median().alias("prix_m2_median"),
            pl.col("prix_m2").mean().alias("prix_m2_moyen"),
            pl.col("prix_m2").quantile(0.25).alias("prix_m2_q25"),
            pl.col("prix_m2").quantile(0.75).alias("prix_m2_q75"),
            pl.col("valeur_fonciere").count().alias("nb_transactions"),
            pl.col("valeur_fonciere").median().alias("prix_median"),
            pl.col("surface_reelle_bati").median().alias("surface_mediane"),
            pl.col("latitude").mean().alias("lat"),
            pl.col("longitude").mean().alias("lon"),
        ])
        .sort(["code_departement", "code_commune", "type_local", "annee"])
    )

    # Variation YoY
    agg = agg.with_columns(
        pl.col("prix_m2_median")
          .shift(1)
          .over(["code_commune", "type_local"])
          .alias("prix_m2_n_minus_1")
    ).with_columns(
        ((pl.col("prix_m2_median") - pl.col("prix_m2_n_minus_1"))
         / pl.col("prix_m2_n_minus_1") * 100)
        .alias("variation_yoy_pct")
    ).drop("prix_m2_n_minus_1")

    # Score de tension : rang du nb de transactions dans le département
    agg = agg.with_columns(
        pl.col("nb_transactions")
          .rank("dense")
          .over(["code_departement", "type_local", "annee"])
          .alias("score_tension")
    )

    # Label département lisible
    DEPT_LABELS = {"33": "Gironde", "75": "Paris", "69": "Rhône", "13": "Bouches-du-Rhône"}
    agg = agg.with_columns(
        pl.col("code_departement")
          .replace(DEPT_LABELS)
          .alias("nom_departement")
    )

    dest = PROCESSED_DIR / "features.parquet"
    agg.write_parquet(dest)
    print(f"Features : {len(agg):,} lignes → {dest}")
    return agg


if __name__ == "__main__":
    compute_features()