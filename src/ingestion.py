import polars as pl
from pathlib import Path

RAW_DIR = Path("data/raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)


def load_local(dept: str, year: int = 2023) -> Path:
    """
    Lit un fichier CSV.gz local et le convertit en Parquet.
    Nomme ton fichier téléchargé : data/raw/{dept}.csv.gz
    """
    src = RAW_DIR / f"{dept}.csv.gz"
    dest = RAW_DIR / f"dvf_{year}_{dept}.parquet"

    if not src.exists():
        raise FileNotFoundError(
            f"Fichier introuvable : {src}\n"
            f"Télécharge-le manuellement depuis :\n"
            f"https://files.data.gouv.fr/geo-dvf/latest/csv/{year}/departements/{dept}.csv.gz"
        )

    if dest.exists():
        print(f"[{dept}] Parquet déjà présent : {dest}")
        return dest

    print(f"[{dept}] Lecture de {src}...")
    df = pl.read_csv(
        src,
        infer_schema_length=10000,
        ignore_errors=True,
        null_values=["", "NULL"],
    )
    print(f"[{dept}] {len(df):,} lignes lues")

    df.write_parquet(dest)
    print(f"[{dept}] Exporté → {dest}")
    return dest


def load_all_local():
    """
    Convertit tous les CSV.gz présents dans data/raw/ en Parquet.
    Détecte automatiquement les fichiers disponibles.
    """
    csv_files = list(RAW_DIR.glob("*.csv.gz"))
    if not csv_files:
        print("Aucun fichier .csv.gz trouvé dans data/raw/")
        print("Télécharge d'abord des fichiers depuis :")
        print("https://files.data.gouv.fr/geo-dvf/latest/csv/2023/departements/")
        return

    print(f"{len(csv_files)} fichier(s) trouvé(s) : {[f.name for f in csv_files]}")
    for f in csv_files:
        dept = f.stem.replace(".csv", "")  # "33.csv.gz" → "33"
        load_local(dept)


if __name__ == "__main__":
    import sys
    if len(sys.argv) == 3:
        load_local(dept=sys.argv[1], year=int(sys.argv[2]))
    elif len(sys.argv) == 2:
        load_local(dept=sys.argv[1])
    else:
        load_all_local()