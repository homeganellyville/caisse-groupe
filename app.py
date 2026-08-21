import json
import os
import pandas as pd
import streamlit as st

# Configuration de la page
st.set_page_config(
    page_title="Gestion de Caisse & Cotisations",
    layout="wide",
    initial_sidebar_state="expanded",
)

DATA_FILE = "data_caisse.json"

# Liste des 12 mois
MOIS_LIST = [
    "AOUT",
    "SEPTEMBRE",
    "OCTOBRE",
    "NOVEMBRE",
    "DECEMBRE",
    "JANVIER",
    "FEVRIER",
    "MARS",
    "AVRIL",
    "MAI",
    "JUIN",
    "JUILLET",
]


# Chargement / Sauvegarde des données
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        # Initialisation avec 40 membres par défaut
        return {
            "membres": [f"EXEMPLE NOM{i}" for i in range(1, 41)],
            "cotisations": {},
            "depenses": {
                m: {"montant": 0.0, "motif": ""} for m in MOIS_LIST
            },
        }


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


data = load_data()

st.title("📊 Gestion de Caisse & Cotisations (40 Membres)")

# Barre latérale : Gestion des membres
st.sidebar.header("👥 Gestion des Membres")
st.sidebar.write(f"**Nombre actuel de membres :** {len(data['membres'])}")

nouveau_membre = st.sidebar.text_input("Ajouter un membre :")
if st.sidebar.button("Ajouter Membre"):
    if nouveau_membre and nouveau_membre not in data["membres"]:
        data["membres"].append(nouveau_membre)
        save_data(data)
        st.sidebar.success(f"{nouveau_membre} ajouté !")
        st.rerun()

membre_a_supprimer = st.sidebar.selectbox(
    "Supprimer un membre :", [""] + data["membres"]
)
if st.sidebar.button("Supprimer Membre"):
    if membre_a_supprimer in data["membres"]:
        data["membres"].remove(membre_a_supprimer)
        if membre_a_supprimer in data["cotisations"]:
            del data["cotisations"][membre_a_supprimer]
        save_data(data)
        st.sidebar.warning(f"{membre_a_supprimer} supprimé !")
        st.rerun()

if st.sidebar.button("Réinitialiser à 40 membres d'exemple"):
    data["membres"] = [f"EXEMPLE NOM{i}" for i in range(1, 41)]
    save_data(data)
    st.sidebar.success("Liste réinitialisée à 40 membres !")
    st.rerun()

# Onglets principaux
tab1, tab2, tab3 = st.tabs(
    ["📋 Tableau Récapitulatif", "💵 Saisie Cotisations", "💸 Saisie Dépenses"]
)

# --- TAB 1 : Tableau Général ---
with tab1:
    st.subheader("Aperçu Général de la Caisse")

    df_data = []
    for m in data["membres"]:
        row = {"Membre": m}
        cotis_m = data["cotisations"].get(m, {})
        for mois in MOIS_LIST:
            row[mois] = float(cotis_m.get(mois, 0.0))
        df_data.append(row)

    df_cotis = pd.DataFrame(df_data)

    totaux_cotis = {}
    for mois in MOIS_LIST:
        totaux_cotis[mois] = (
            df_cotis[mois].sum() if not df_cotis.empty else 0.0
        )

    row_total = {"Membre": "TOTAL COTISATIONS"}
    row_total.update(totaux_cotis)

    row_depense = {"Membre": "DÉPENSES"}
    row_motif = {"Membre": "MOTIF DÉPENSE"}
    row_solde = {"Membre": "SOLDE CAISSE"}

    solde_cumule = 0.0
    for mois in MOIS_LIST:
        dep = float(data["depenses"].get(mois, {}).get("montant", 0.0))
        mot = data["depenses"].get(mois, {}).get("motif", "")
        tot = totaux_cotis[mois]

        solde_cumule += tot - dep

        row_depense[mois] = dep
        row_motif[mois] = mot
        row_solde[mois] = solde_cumule

    df_full = pd.concat(
        [
            df_cotis,
            pd.DataFrame([row_total]),
            pd.DataFrame([row_depense]),
            pd.DataFrame([row_motif]),
            pd.DataFrame([row_solde]),
        ],
        ignore_index=True,
    )

    st.dataframe(df_full, use_container_width=True, height=600)

    st.metric(
        label="💰 Solde Général Actuel de la Caisse",
        value=f"{solde_cumule:,.2f} $",
    )

# --- TAB 2 : Saisie des Cotisations ---
with tab2:
    st.subheader("Enregistrer une cotisation")
    col1, col2, col3 = st.columns(3)
    with col1:
        selected_membre = st.selectbox("Sélectionner le membre", data["membres"])
    with col2:
        selected_mois = st.selectbox("Sélectionner le mois", MOIS_LIST)
    with col3:
        val_actuelle = (
            data["cotisations"]
            .get(selected_membre, {})
            .get(selected_mois, 0.0)
        )
        montant_cotis = st.number_input(
            "Montant de la cotisation ($)", value=float(val_actuelle), step=1.0
        )

    if st.button("Enregistrer Cotisation"):
        if selected_membre not in data["cotisations"]:
            data["cotisations"][selected_membre] = {}
        data["cotisations"][selected_membre][selected_mois] = montant_cotis
        save_data(data)
        st.success(
            f"Cotisation enregistrée pour {selected_membre} ({selected_mois}) !"
        )
        st.rerun()

# --- TAB 3 : Saisie des Dépenses ---
with tab3:
    st.subheader("Enregistrer une dépense mensuelle")
    col1, col2, col3 = st.columns(3)
    with col1:
        dep_mois = st.selectbox("Mois de la dépense", MOIS_LIST, key="dep_m")
    with col2:
        curr_dep = data["depenses"].get(dep_mois, {}).get("montant", 0.0)
        dep_montant = st.number_input(
            "Montant de la dépense ($)", value=float(curr_dep), step=1.0
        )
    with col3:
        curr_mot = data["depenses"].get(dep_mois, {}).get("motif", "")
        dep_motif = st.text_input("Motif de la dépense", value=curr_mot)

    if st.button("Enregistrer Dépense"):
        data["depenses"][dep_mois] = {
            "montant": dep_montant,
            "motif": dep_motif,
        }
        save_data(data)
        st.success(f"Dépense enregistrée pour {dep_mois} !")
        st.rerun()