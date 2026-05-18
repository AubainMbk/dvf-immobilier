# DVF Immobilier : Analyse des marchés immobiliers français

Dashboard data engineering construit sur les données open data DVF (Demandes de Valeurs Foncières)
publiées par la DGFiP sur data.gouv.fr.

## Problématique

Les acteurs de l'immobilier (agents, investisseurs, collectivités) manquent d'outils simples
pour comparer les marchés entre grandes métropoles françaises et identifier les zones de tension.

## Périmètre

- **4 départements** : Gironde (33), Paris (75), Rhône (69), Bouches-du-Rhône (13)
- **Données** : transactions immobilières 2021–2023 (Maisons & Appartements)
- **Source** : [data.gouv.fr : DVF géolocalisées](https://www.data.gouv.fr/datasets/demandes-de-valeurs-foncieres-geolocalisees)

## Fonctionnalités

- Vue d'ensemble : KPIs par département, top communes, distribution des prix
- Comparaison inter-départements : évolution temporelle, volumes, tableau détaillé
- Carte interactive : prix/m² par commune avec score de tension

## Stack technique

| Couche | Outil |
|---|---|
| Ingestion | Python / requests |
| Stockage intermédiaire | Parquet (PyArrow) |
| Transformation | Polars + DuckDB |
| Feature engineering | Polars |
| Visualisation | Streamlit · Plotly · Folium |
| Déploiement | Streamlit Cloud |

## Architecture

data.gouv.fr (CSV.gz)
│
▼
ingestion.py  ──►  data/raw/dvf_{year}{dept}.parquet
│
▼
transform.py  ──►  data/processed/dvf{year}.parquet
│
▼
features.py   ──►  data/processed/features.parquet
│
▼
app.py (Streamlit)

## Lancement

```bash
# 1. Installer les dépendances
pip install -r requirements.txt

# 2. Placer les fichiers CSV.gz dans data/raw/
#    Télécharger depuis : https://files.data.gouv.fr/geo-dvf/latest/csv/{année}/departements/{dept}.csv.gz

# 3. Exécuter le pipeline
python src/ingestion.py
python src/transform.py
python src/features.py

# 4. Lancer le dashboard
streamlit run app.py
```

## Structure du projet

dvf-immobilier/
├── data/
│   ├── raw/            # Parquet bruts par département (non versionnés)
│   └── processed/      # Parquet transformés et features (non versionnés)
├── src/
│   ├── ingestion.py    # Lecture CSV.gz → Parquet brut
│   ├── transform.py    # Nettoyage, filtrage, feature de base
│   └── features.py     # Agrégations, YoY, score de tension
├── app.py              # Dashboard Streamlit (3 pages)
├── requirements.txt
├── .gitignore
└── README.md

## Auteur

Aubain Mbokou