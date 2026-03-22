# Importation des bibliothèques nécessaires au dashboard interactif
from dash import Dash, dcc, html, Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import calendar



#Cellule 1

import os

# Chargement du jeu de données principal
donnees = pd.read_csv("data.csv")

# Sélection des colonnes utiles à l'analyse
cols_utiles = ['Transaction_Date', 'Gender', 'Location', 'Product_Category',
               'Quantity', 'Avg_Price', 'Discount_pct', 'Month', 'CustomerID']
donnees = donnees[cols_utiles]

# Conversion de la date en format datetime
donnees['Transaction_Date'] = pd.to_datetime(donnees['Transaction_Date'])

# Remplacement des identifiants clients manquants par 0 et conversion en entier
donnees['CustomerID'] = donnees['CustomerID'].fillna(0).astype(int)

# Calcul du prix total après remise
donnees['Total_price'] = donnees['Quantity'] * donnees['Avg_Price'] * (1 - donnees['Discount_pct'] / 100)

donnees.head(5)


#cellule 2 

# Calcule le chiffre d'affaires total à partir d'un dataframe
def get_ca_total(dataset):
    return round(dataset['Total_price'].sum())

get_ca_total(donnees)


#cellule 3

# Retourne un tableau pivot des top N catégories de produits par genre
def top_categories_par_genre(dataset, top=10, ascending=False):
    # Suppression des lignes sans information de genre
    data_filtre = dataset.dropna(subset=['Gender'])

    # Agrégation des quantités vendues par catégorie et genre
    tableau = (
        data_filtre
        .groupby(['Product_Category', 'Gender'])['Quantity']
        .sum()
        .unstack(fill_value=0)
        .reset_index()
    )

    # Ajout des colonnes manquantes si un genre est absent du jeu de données
    for genre in ['F', 'M']:
        if genre not in tableau.columns:
            tableau[genre] = 0

    # Calcul du total toutes catégories confondues et tri
    tableau['Total_vente'] = tableau['F'] + tableau['M']
    tableau = tableau.sort_values('Total_vente', ascending=ascending).head(top)

    return tableau[['Product_Category', 'F', 'M', 'Total_vente']].reset_index(drop=True)

top_categories_par_genre(dataset=donnees)


#cellule 4

# Calcule les indicateurs du mois courant et la variation par rapport au mois précédent
def stats_mensuelles(dataset, mois_actuel=12, mode_freq=True, abr=False):
    mois_precedent = mois_actuel - 1 if mois_actuel > 1 else 12

    # Nom du mois en toutes lettres ou abrégé
    nom_mois = calendar.month_abbr[mois_actuel] if abr else calendar.month_name[mois_actuel]

    df_cur  = dataset[dataset['Month'] == mois_actuel]
    df_prev = dataset[dataset['Month'] == mois_precedent]

    # Choix entre fréquence (nombre de transactions) ou chiffre d'affaires
    if mode_freq:
        val_cur  = len(df_cur)
        val_prev = len(df_prev)
    else:
        val_cur  = round(df_cur['Total_price'].sum(), 2)
        val_prev = round(df_prev['Total_price'].sum(), 2)

    return {
        'month_name': nom_mois,
        'value': val_cur,
        'delta': round(val_cur - val_prev, 2)
    }

stats_mensuelles(donnees)


#cellule 5

def graphique_top_ventes(dataset):
    top10 = top_categories_par_genre(dataset, ascending=True)

    fig = go.Figure()

    # Barres pour les femmes
    fig.add_trace(go.Bar(
        y=top10['Product_Category'],
        x=top10['F'],
        name='Femme',                          # ← modifié
        orientation='h',
        marker_color='#7B8CDE'
    ))

    # Barres pour les hommes
    fig.add_trace(go.Bar(
        y=top10['Product_Category'],
        x=top10['M'],
        name='Homme',                          # ← modifié
        orientation='h',
        marker_color='#E8453C'
    ))

    fig.update_layout(
        barmode='overlay',
        title='Fréquence des 10 meilleures ventes',
        height=600,
        legend_title_text='Sexe'               # ← ajouté
    )

    return fig

#graphique_top_ventes(donnees).show()


#cellule 6

# Trace l'évolution hebdomadaire du chiffre d'affaires sur la période
def courbe_ca_hebdo(dataset):
    # Regroupement par semaine et somme des revenus
    hebdo = (
        dataset.groupby(pd.Grouper(key='Transaction_Date', freq='W'))['Total_price']
        .sum()
        .reset_index()
    )
    hebdo.columns = ['Semaine', 'CA']

    fig = px.line(
        hebdo,
        x='Semaine',
        y='CA',
        title="Évolution du chiffre d'affaire par semaine",
        height=600
    )

    return fig

#courbe_ca_hebdo(donnees).show()

#cellule 7 

# Affiche les KPI du mois sous forme de cartes indicateurs (CA + nb transactions)
def carte_kpi_mensuel(dataset, abr=False):
    kpi_ca     = stats_mensuelles(dataset, mois_actuel=12, mode_freq=False, abr=abr)
    kpi_ventes = stats_mensuelles(dataset, mois_actuel=12, mode_freq=True,  abr=abr)

    fig = go.Figure()

    # Indicateur chiffre d'affaires
    fig.add_trace(go.Indicator(
        mode='number+delta',
        value=kpi_ca['value'],
        delta={'reference': kpi_ca['value'] - kpi_ca['delta']},
        title={'text': kpi_ca['month_name']},
        domain={'x': [0, 0.5], 'y': [0, 1]}
    ))

    # Indicateur nombre de transactions
    fig.add_trace(go.Indicator(
        mode='number+delta',
        value=kpi_ventes['value'],
        delta={'reference': kpi_ventes['value'] - kpi_ventes['delta']},
        title={'text': kpi_ventes['month_name']},
        domain={'x': [0.5, 1], 'y': [0, 1]}
    ))

    fig.update_layout(height=280)

    return fig

#carte_kpi_mensuel(donnees).show()


#cellule 8


def tableau_dernieres_ventes(dataset):
    colonnes_affichees = ['Transaction_Date', 'Gender', 'Location',
                          'Product_Category', 'Quantity', 'Avg_Price', 'Discount_pct']

    df_recent = (
        dataset.sort_values('Transaction_Date', ascending=False)
        .head(100)[colonnes_affichees]
        .copy()
    )
    df_recent['Transaction_Date'] = df_recent['Transaction_Date'].dt.strftime('%Y-%m-%d')

    # ← NOUVEAU : on retourne aussi le dataframe filtré pour la recherche
    return df_recent, colonnes_affichees


def build_figure_tableau(df_recent, colonnes_affichees):
    """Construit la figure Plotly Table à partir d'un dataframe déjà filtré."""
    fig = go.Figure(data=[go.Table(
        header=dict(
            values=['Date', 'Gender', 'Location', 'Product Category',
                    'Quantity', 'Avg Price', 'Discount Pct'],
            fill_color='#4472C4',
            font=dict(color='white', size=12),
            align='right'
        ),
        cells=dict(
            values=[df_recent[col] for col in colonnes_affichees],
            fill_color='white',
            align='right'
        )
    )])

    fig.update_layout(
        title='Table des 100 dernières ventes',
        height=400,
        margin=dict(l=0, r=0, t=40, b=0)
    )
    return fig


#cellule 9

from dash import Dash, dcc, html, Input, Output
import dash_bootstrap_components as dbc

# 1. Initialisation de l'application
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

# 2. Layout
app.layout = html.Div([

    # Barre de navigation
    html.Div([
        html.H1('ECAP Store', style={'color': 'white', 'margin': '0', 'fontSize': '22px'}),
        dcc.Dropdown(
            id='filtre-localisation',
            options=[{'label': 'Toutes les zones', 'value': 'ALL'}] +
                    [{'label': loc, 'value': loc} for loc in sorted(donnees['Location'].dropna().unique())],
            value='ALL',
            clearable=False,
            style={'width': '250px'}
        )
    ], style={
        'background': '#6aabbd', 'padding': '14px 28px',
        'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center'
    }),

    # Corps
    html.Div([

        # Colonne gauche
        html.Div([
            html.Div([
                dcc.Graph(id='vis-kpi')
            ], style={'height': '200px', 'overflow': 'hidden'}),
            dcc.Graph(id='vis-barres', style={'marginTop': '50px'})
        ], style={'flex': '1', 'background': 'white', 'padding': '10px'}),

        # Colonne droite
        html.Div([
            dcc.Graph(id='vis-courbe'),
            dcc.Input(
                id='recherche-tableau',
                type='text',
                placeholder='🔍 Rechercher dans la table...',
                debounce=True,
                style={
                    'width': '100%',
                    'padding': '8px 12px',
                    'marginBottom': '4px',
                    'marginTop': '10px',
                    'border': '1px solid #ccc',
                    'borderRadius': '4px',
                    'fontSize': '13px'
                }
            ),
            dcc.Graph(id='vis-tableau')
        ], style={'flex': '1.3', 'background': 'white', 'padding': '10px'})

    ], style={
        'display': 'flex', 'gap': '10px',
        'padding': '20px', 'background': '#f4f6fb', 'width': '100%'
    })
])

# 3. Callback — APRÈS app et layout
@app.callback(
    Output('vis-kpi',    'figure'),
    Output('vis-barres', 'figure'),
    Output('vis-courbe', 'figure'),
    Output('vis-tableau','figure'),
    Input('filtre-localisation', 'value'),
    Input('recherche-tableau', 'value')
)
def actualiser_dashboard(zone, terme_recherche):
    df_filtre = donnees if zone == 'ALL' else donnees[donnees['Location'] == zone]

    df_recent, colonnes_affichees = tableau_dernieres_ventes(df_filtre)
    if terme_recherche:
        masque = df_recent.apply(
            lambda col: col.astype(str).str.contains(terme_recherche, case=False, na=False)
        ).any(axis=1)
        df_recent = df_recent[masque]

    return (
        carte_kpi_mensuel(df_filtre),
        graphique_top_ventes(df_filtre),
        courbe_ca_hebdo(df_filtre),
        build_figure_tableau(df_recent, colonnes_affichees)
    )

# 4. Lancement
#app.run(debug=False, jupyter_mode='external', port=8054)

if __name__ == "__main__":
    app.run_server(debug=True)

