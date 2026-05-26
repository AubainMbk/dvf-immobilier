# 🏘️ DVF Immobilier : Analyse des marchés immobiliers français

Dashboard data engineering construit sur les données open data DVF (Demandes de Valeurs Foncières) publiées par la DGFiP sur data.gouv.fr.

🔗 **[Application en ligne →](https://analyse-annonces-immobilieres-ef2klvapxupxp2x4qjxawx.streamlit.app/)**

---

## Problématique

Les acteurs de l'immobilier (agents, investisseurs, collectivités) manquent d'outils simples pour comparer les marchés entre grandes métropoles françaises et identifier les zones de tension.

## Périmètre

- **4 départements** : Gironde (33), Paris (75), Rhône (69), Bouches-du-Rhône (13)
- **Données** : transactions immobilières 2021–2023 : Maisons & Appartements
- **Source** : [data.gouv.fr : DVF géolocalisées](https://www.data.gouv.fr/datasets/demandes-de-valeurs-foncieres-geolocalisees)

## Fonctionnalités

- **Vue d'ensemble** : KPIs par département, top communes, distribution des prix
- **Comparaison inter-départements** : évolution temporelle, volumes, tableau détaillé
- **Carte interactive** : prix/m² par commune avec score de tension

## Stack technique

| Couche | Outil |
|---|---|
| Ingestion | Python · requests |
| Stockage intermédiaire | Parquet · PyArrow |
| Transformation | Polars |
| Feature engineering | Polars |
| Visualisation | Streamlit · Plotly · Folium |
| Déploiement | Streamlit Cloud |

## Architecture

```
data.gouv.fr (CSV.gz)
        │
        ▼
ingestion.py  ──►  data/raw/dvf_{year}_{dept}.parquet
        │
        ▼
transform.py  ──►  data/processed/dvf_{year}.parquet
        │
        ▼
features.py   ──►  data/processed/features.parquet
        │
        ▼
app.py (Streamlit Cloud)
```

## Structure du projet

```
dvf-immobilier/
├── data/
│   ├── raw/              # Parquet bruts par département (non versionnés)
│   └── processed/        # Parquet transformés et features (non versionnés)
├── src/
│   ├── ingestion.py      # Lecture CSV.gz → Parquet brut
│   ├── transform.py      # Nettoyage, filtrage, calcul prix/m²
│   └── features.py       # Agrégations, YoY, score de tension
├── app.py                # Dashboard Streamlit 3 pages
├── requirements.txt
├── .gitignore
└── README.md
```

## Lancement local

```bash
pip install -r requirements.txt
python src/ingestion.py
python src/transform.py
python src/features.py
streamlit run app.py
```

> Les fichiers CSV.gz sont à télécharger manuellement depuis :
> `https://files.data.gouv.fr/geo-dvf/latest/csv/{année}/departements/{dept}.csv.gz`

---

Projet réalisé par Aubain Mbokou