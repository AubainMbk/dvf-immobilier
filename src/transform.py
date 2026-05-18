import polars as pl
from pathlib import Path
from tqdm import tqdm

RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

COLS_UTILES = [
    "date_mutation",
    "nature_mutation",
    "valeur_fonciere",
    "code_postal",
    "code_commune",
    "nom_commune",
    "code_departement",
    "type_local",
    "surface_reelle_bati",
    "nombre_pieces_principales",
    "longitude",
    "latitude",
]


def transform_dept(year: int, dept: str) -> pl.DataFrame | None:
    src = RAW_DIR / f"dvf_{year}_{dept}.parquet"
    if not src.exists():
        print(f"  [{year}][{dept}] Parquet brut introuvable, lance ingestion.py d'abord.")
        return None

    df = pl.read_parquet(src)

    # Garde uniquement les colonnes présentes dans ce fichier
    cols_present = [c for c in COLS_UTILES if c in df.columns]
    df = df.select(cols_present)

    df = (
        df
        .with_columns([
            pl.col("valeur_fonciere").cast(pl.Float64, strict=False),
            pl.col("surface_reelle_bati").cast(pl.Float64, strict=False),
            pl.col("code_departement").cast(pl.Utf8),
        ])
        .filter(
            pl.col("nature_mutation").is_in(["Vente", "Vente en l'état futur d'achèvement"])
            & pl.col("type_local").is_in(["Maison", "Appartement"])
            & pl.col("valeur_fonciere").is_not_null()
            & (pl.col("valeur_fonciere") > 10_000)
            & pl.col("surface_reelle_bati").is_not_null()
            & (pl.col("surface_reelle_bati") > 9)
        )
        .with_columns(
            pl.col("date_mutation").str.to_date(format="%Y-%m-%d", strict=False)
        )
        .with_columns([
            pl.col("date_mutation").dt.year().alias("annee"),
            pl.col("date_mutation").dt.month().alias("mois"),
            (pl.col("valeur_fonciere") / pl.col("surface_reelle_bati")).alias("prix_m2"),
        ])
        .filter(pl.col("prix_m2") > 500)
    )

    print(f"  [{year}][{dept}] {len(df):,} lignes après filtrage")
    return df


def transform_all():
    """
    Détecte automatiquement tous les Parquet bruts dans data/raw/
    et produit un Parquet propre par année dans data/processed/.
    """
    parquet_files = list(RAW_DIR.glob("dvf_*.parquet"))
    if not parquet_files:
        print("Aucun Parquet brut trouvé. Lance ingestion.py d'abord.")
        return

    # Regroupe par année
    from collections import defaultdict
    by_year = defaultdict(list)
    for f in parquet_files:
        # nom : dvf_2023_33.parquet → year=2023, dept=33
        parts = f.stem.split("_")  # ["dvf", "2023", "33"]
        if len(parts) == 3:
            year, dept = int(parts[1]), parts[2]
            by_year[year].append(dept)

    for year, depts in sorted(by_year.items()):
        print(f"\n=== Transform {year} — depts : {depts} ===")
        frames = []
        for dept in tqdm(depts, desc=f"{year}"):
            df = transform_dept(year, dept)
            if df is not None and len(df) > 0:
                frames.append(df)

        if frames:
            combined = pl.concat(frames, how="diagonal")
            dest = PROCESSED_DIR / f"dvf_{year}.parquet"
            combined.write_parquet(dest)
            print(f"  → {len(combined):,} lignes exportées : {dest}")


if __name__ == "__main__":
    transform_all()