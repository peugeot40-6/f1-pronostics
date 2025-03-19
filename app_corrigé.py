from flask import Flask, render_template, request
import os
import pandas as pd

def nettoyer_resultats_csv():
    try:
        if not os.path.exists("resultats.csv"):
            print("Le fichier resultats.csv n'existe pas.")
            return

        df = pd.read_csv("resultats.csv", encoding='utf-8')

        # Afficher les colonnes disponibles pour débogage
        print("Colonnes disponibles dans resultats.csv:", df.columns.tolist())

        # Vérifier si la colonne "Grand Prix" est bien présente
        if "Grand Prix" not in df.columns:
            raise KeyError("La colonne 'Grand Prix' est introuvable dans resultats.csv")

        # Nettoyage des colonnes vides
        df = df.dropna(axis=1, how='all')

        # Suppression des espaces et des virgules parasites dans le nom du Grand Prix
        df["Grand Prix"] = df["Grand Prix"].astype(str).str.strip()

        # Sauvegarde du fichier nettoyé
        df.to_csv("resultats.csv", index=False, encoding='utf-8')

        print("Fichier resultats.csv nettoyé avec succès !")

    except Exception as e:
        print(f"Erreur lors du nettoyage du fichier resultats.csv: {e}")

# Exécuter la fonction au démarrage
nettoyer_resultats_csv()

app = Flask(__name__)

# Vérification et création des fichiers CSV nécessaires
for file in ["pronostics.csv", "resultats.csv", "classement.csv", "classement_general.csv"]:
    if not os.path.exists(file):
        with open(file, "w") as f:
            pass

# Points attribués par position
points_f1 = {1: 25, 2: 18, 3: 15, 4: 12, 5: 10, 6: 8, 7: 6, 8: 4, 9: 2, 10: 1}

# Nettoyage du fichier resultats.csv pour enlever les colonnes vides et les erreurs d'encodage
def nettoyer_resultats_csv():
    try:
        df = pd.read_csv("resultats.csv", encoding="utf-8")
        df.dropna(axis=1, how='all', inplace=True)
        df["Grand Prix"] = df["Grand Prix"].str.strip()
        df.to_csv("resultats.csv", index=False, encoding="utf-8")
    except Exception as e:
        print("Erreur lors du nettoyage du fichier resultats.csv:", e)

@app.route('/')
def index():
    classement_df = pd.read_csv("classement.csv") if os.path.exists("classement.csv") else pd.DataFrame()
    classement_general_df = pd.read_csv("classement_general.csv") if os.path.exists("classement_general.csv") else pd.DataFrame()
    return render_template('index.html', classement=classement_df.to_dict('records'), classement_general=classement_general_df.to_dict('records'))

@app.route('/ajouter_resultat', methods=['POST'])
def ajouter_resultat():
    try:
        gp = request.form['grand_prix']
        resultats = [request.form[f'pos{i}'] for i in range(1, 11)]
        df = pd.read_csv("resultats.csv")
        df = pd.concat([df, pd.DataFrame([[gp] + resultats], columns=["Grand Prix"] + [f'pos{i}' for i in range(1, 11)])], ignore_index=True)
        df.to_csv("resultats.csv", index=False)
    except Exception as e:
        return f"Erreur lors de l'ajout du résultat : {e}"
    return "Résultat ajouté avec succès !"

@app.route('/calculer_classement')
def calculer_classement():
    pronostics_df = pd.read_csv("pronostics.csv")
    resultats_df = pd.read_csv("resultats.csv")
    if pronostics_df.empty or resultats_df.empty:
        return "Aucun pronostic ou résultat disponible."
    classement_df = pd.DataFrame(columns=["Grand Prix", "Participant", "Points GP", "Bonus", "Total"])
    for _, row in pronostics_df.iterrows():
        gp = row["Grand Prix"]
        participant = row["Participant"]
        pronos = [row["1er"], row["2e"], row["3e"]]
        if gp not in resultats_df["Grand Prix"].values:
            continue
        resultats = resultats_df[resultats_df["Grand Prix"] == gp].iloc[0, 1:11].dropna().tolist()
        points = sum(points_f1.get(resultats.index(p) + 1, 0) for p in pronos if p in resultats)
        bonus = 10 if pronos == resultats[:3] else (3 if set(pronos) == set(resultats[:3]) else 0)
        total_points = points + bonus
        classement_df = pd.concat([classement_df, pd.DataFrame([{ "Grand Prix": gp, "Participant": participant, "Points GP": points, "Bonus": bonus, "Total": total_points }])], ignore_index=True)
    classement_df.to_csv("classement.csv", index=False)
    classement_general_df = classement_df.groupby("Participant")["Total"].sum().reset_index()
    classement_general_df.columns = ["Participant", "Total Points"]
    classement_general_df.to_csv("classement_general.csv", index=False)
    return "Classements mis à jour !"

if __name__ == '__main__':
    nettoyer_resultats_csv()
    app.run(debug=True)