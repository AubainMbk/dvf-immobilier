import streamlit as st
import polars as pl
import plotly.express as px
import folium
from streamlit_folium import st_folium
from pathlib import Path

st.set_page_config(
    page_title="Marché Immobilier France",
    page_icon="🏘️",
    layout="wide",
)

DEPT_LABELS = {"33": "Gironde (Bordeaux)", "75": "Paris", "69": "Rhône (Lyon)", "13": "Bouches-du-Rhône (Marseille)"}


@st.cache_data(ttl=3600)
def load_features() -> pl.DataFrame:
    f = Path("data/processed/features.parquet")
    if not f.exists():
        st.error("Lance `python src/features.py` pour générer les données.")
        st.stop()
    return pl.read_parquet(f)


@st.cache_data(ttl=3600)
def load_transactions() -> pl.DataFrame:
    files = list(Path("data/processed").glob("dvf_*.parquet"))
    if not files:
        st.stop()
    return pl.concat([pl.read_parquet(f) for f in files], how="diagonal")


df = load_features()

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
st.sidebar.title("🏘️ DVF Immobilier")
page = st.sidebar.radio(
    "Navigation",
    ["Vue d'ensemble", "Comparaison départements", "Carte interactive"],
)

type_bien = st.sidebar.radio("Type de bien", ["Appartement", "Maison"], horizontal=True)
annees = sorted(df["annee"].unique().to_list())
annee_sel = st.sidebar.selectbox("Année", annees, index=len(annees) - 1)

depts_dispo = sorted(df["code_departement"].unique().to_list())
depts_sel = st.sidebar.multiselect(
    "Départements",
    options=depts_dispo,
    default=depts_dispo,
    format_func=lambda x: DEPT_LABELS.get(x, x),
)

if not depts_sel:
    st.warning("Sélectionne au moins un département.")
    st.stop()

# ── FILTRE COMMUN ─────────────────────────────────────────────────────────────
df_page = df.filter(
    pl.col("type_local").eq(type_bien)
    & pl.col("annee").eq(annee_sel)
    & pl.col("code_departement").is_in(depts_sel)
)

# ─────────────────────────────────────────────────────────────────────────────
# PAGE 1 : VUE D'ENSEMBLE
# ─────────────────────────────────────────────────────────────────────────────
if page == "Vue d'ensemble":
    st.title("Vue d'ensemble : Marchés immobiliers")
    st.caption(f"{type_bien}s · {annee_sel} · {', '.join(DEPT_LABELS.get(d, d) for d in depts_sel)}")

    # KPIs par département
    cols = st.columns(len(depts_sel))
    for i, dept in enumerate(depts_sel):
        sub = df_page.filter(pl.col("code_departement").eq(dept))
        prix = sub["prix_m2_median"].median()
        nb = sub["nb_transactions"].sum()
        yoy = sub["variation_yoy_pct"].median()
        with cols[i]:
            st.metric(
                label=DEPT_LABELS.get(dept, dept),
                value=f"{prix:,.0f} €/m²" if prix else "N/A",
                delta=f"{yoy:+.1f}% vs N-1" if yoy else None,
            )
            st.caption(f"{nb:,} transactions")

    st.divider()

    # Top 15 communes prix/m² : tous depts confondus
    st.subheader(f"Top 15 communes les plus chères")
    top = df_page.sort("prix_m2_median", descending=True).head(15).to_pandas()
    fig = px.bar(
        top,
        x="prix_m2_median",
        y="nom_commune",
        color="nom_departement",
        orientation="h",
        labels={"prix_m2_median": "Prix médian/m² (€)", "nom_commune": "", "nom_departement": "Département"},
        color_discrete_sequence=px.colors.qualitative.Set2,
    )
    fig.update_layout(yaxis={"categoryorder": "total ascending"}, height=450, margin={"l": 0, "r": 0, "t": 0, "b": 0})
    st.plotly_chart(fig, use_container_width=True)

    # Distribution prix/m² par département : boxplot
    st.subheader("Distribution des prix/m² par département")
    dist = df_page.to_pandas()
    fig2 = px.box(
        dist,
        x="nom_departement",
        y="prix_m2_median",
        color="nom_departement",
        labels={"prix_m2_median": "Prix médian/m² (€)", "nom_departement": ""},
        color_discrete_sequence=px.colors.qualitative.Set2,
    )
    fig2.update_layout(showlegend=False, height=380, margin={"l": 0, "r": 0, "t": 0, "b": 0})
    st.plotly_chart(fig2, use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
# PAGE 2 : COMPARAISON DÉPARTEMENTS
# ─────────────────────────────────────────────────────────────────────────────
elif page == "Comparaison départements":
    st.title("Comparaison inter-départements")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Prix médian/m² : toutes années")
        evo = (
            df.filter(
                pl.col("type_local").eq(type_bien)
                & pl.col("code_departement").is_in(depts_sel)
            )
            .group_by(["annee", "nom_departement"])
            .agg(pl.col("prix_m2_median").median().alias("prix_m2_median"))
            .sort("annee")
            .to_pandas()
        )
        fig3 = px.line(
            evo,
            x="annee",
            y="prix_m2_median",
            color="nom_departement",
            markers=True,
            labels={"prix_m2_median": "Prix médian/m² (€)", "annee": "Année", "nom_departement": "Département"},
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        fig3.update_layout(height=380, margin={"l": 0, "r": 0, "t": 0, "b": 0})
        st.plotly_chart(fig3, use_container_width=True)

    with col2:
        st.subheader("Volume de transactions")
        vol = (
            df.filter(
                pl.col("type_local").eq(type_bien)
                & pl.col("code_departement").is_in(depts_sel)
            )
            .group_by(["annee", "nom_departement"])
            .agg(pl.col("nb_transactions").sum().alias("nb_transactions"))
            .sort("annee")
            .to_pandas()
        )
        fig4 = px.bar(
            vol,
            x="annee",
            y="nb_transactions",
            color="nom_departement",
            barmode="group",
            labels={"nb_transactions": "Nb transactions", "annee": "Année", "nom_departement": "Département"},
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        fig4.update_layout(height=380, margin={"l": 0, "r": 0, "t": 0, "b": 0})
        st.plotly_chart(fig4, use_container_width=True)

    # Tableau comparatif détaillé
    st.subheader(f"Tableau comparatif {annee_sel}")
    tableau = (
        df_page
        .group_by(["nom_departement", "type_local"])
        .agg([
            pl.col("prix_m2_median").median().alias("Prix médian/m²"),
            pl.col("prix_m2_q25").median().alias("Q25 €/m²"),
            pl.col("prix_m2_q75").median().alias("Q75 €/m²"),
            pl.col("nb_transactions").sum().alias("Transactions"),
            pl.col("variation_yoy_pct").median().alias("Évol. YoY %"),
            pl.col("surface_mediane").median().alias("Surface médiane m²"),
        ])
        .sort("Prix médian/m²", descending=True)
        .to_pandas()
    )
    st.dataframe(
        tableau.style.format({
            "Prix médian/m²": "{:,.0f} €",
            "Q25 €/m²": "{:,.0f} €",
            "Q75 €/m²": "{:,.0f} €",
            "Transactions": "{:,}",
            "Évol. YoY %": "{:+.1f}%",
            "Surface médiane m²": "{:.0f} m²",
        }),
        use_container_width=True,
        hide_index=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# PAGE 3 : CARTE INTERACTIVE
# ─────────────────────────────────────────────────────────────────────────────
elif page == "Carte interactive":
    st.title("Carte : Prix/m² par commune")

    dept_carte = st.selectbox(
        "Département à afficher",
        depts_sel,
        format_func=lambda x: DEPT_LABELS.get(x, x),
    )

    df_carte = df_page.filter(
        pl.col("code_departement").eq(dept_carte)
        & pl.col("lat").is_not_null()
        & pl.col("lon").is_not_null()
    ).to_pandas()

    if df_carte.empty:
        st.warning("Pas de données géolocalisées pour ce département.")
    else:
        center_lat = df_carte["lat"].mean()
        center_lon = df_carte["lon"].mean()

        m = folium.Map(location=[center_lat, center_lon], zoom_start=9, tiles="CartoDB positron")

        prix_min = df_carte["prix_m2_median"].quantile(0.05)
        prix_max = df_carte["prix_m2_median"].quantile(0.95)

        for _, row in df_carte.iterrows():
            norm = min(1.0, max(0.0, (row["prix_m2_median"] - prix_min) / (prix_max - prix_min + 1)))
            r_val = int(norm * 200 + 55)
            g_val = int((1 - norm) * 180 + 30)
            color = f"#{r_val:02x}{g_val:02x}30"

            folium.CircleMarker(
                location=[row["lat"], row["lon"]],
                radius=max(4, min(14, row["nb_transactions"] / 20)),
                color=color,
                fill=True,
                fill_opacity=0.75,
                popup=folium.Popup(
                    f"<b>{row['nom_commune']}</b><br>"
                    f"Prix médian/m² : <b>{row['prix_m2_median']:,.0f} €</b><br>"
                    f"Transactions : {row['nb_transactions']}<br>"
                    f"Surface médiane : {row['surface_mediane']:.0f} m²<br>"
                    f"Évol. YoY : {row['variation_yoy_pct']:+.1f}%" if row['variation_yoy_pct'] else "",
                    max_width=220,
                ),
                tooltip=f"{row['nom_commune']} : {row['prix_m2_median']:,.0f} €/m²",
            ).add_to(m)

        st_folium(m, width="100%", height=550)

        st.caption("Taille du cercle ∝ nombre de transactions · Couleur : vert=bas, rouge=élevé")