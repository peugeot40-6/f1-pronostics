import os
from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = "secret_key"  # Nécessaire pour gérer la session

UTILISATEURS_AUTORISES = ["Amandine", "Sacha", "Padre"]

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        nom = request.form.get("nom")
        if nom in UTILISATEURS_AUTORISES:
            session["nom"] = nom
            return redirect(url_for("accueil"))  # Redirige vers la page principale
        else:
            return render_template("login.html", erreur="Nom invalide. Essayez encore.")
    return render_template("login.html")

import os
template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=template_dir)

import pandas as pd

# Charger les données
df_classement = pd.read_csv("classement.csv", encoding="utf-8", on_bad_lines="skip")

# Vérifier s'il y a des données
if not df_classement.empty:
    # Trouver le dernier Grand Prix en fonction de l'ordre d'apparition dans le fichier
    dernier_gp = df_classement["Grand Prix"].iloc[-1]  # Prend le dernier GP inscrit
    classement_dernier_gp = df_classement[df_classement["Grand Prix"] == dernier_gp]
else:
    classement_dernier_gp = pd.DataFrame()  # Tableau vide si aucun GP n'est trouvé

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

# Fonction pour lire un fichier CSV et corriger les erreurs d'encodage
def lire_csv_utf8(fichier):
    with open(fichier, "r", encoding="utf-8") as f:
        lignes = f.readlines()  # Lire tout le contenu du fichier ligne par ligne
    with open(fichier, "w", encoding="utf-8") as f:
        f.writelines(lignes)  # Réécrire le fichier propre
    return pd.read_csv(fichier, encoding="utf-8", on_bad_lines='skip')  # Ignore les lignes mal formatées


@app.route('/')
def indes():
    try:
        df_classement = pd.read_csv("classement.csv", encoding="utf-8", on_bad_lines="skip")

        if df_classement.empty:
            classement_dernier_gp = pd.DataFrame()  # Si aucun résultat, retourne un tableau vide
        else:
            dernier_gp = df_classement["Grand Prix"].iloc[-1]
            classement_dernier_gp = df_classement[df_classement["Grand Prix"] == dernier_gp]
        
        classement_general_df = pd.read_csv("classement_general.csv")
        
        return render_template("index.html", classement_dernier_gp=classement_dernier_gp.to_dict('records'), classement_general=classement_general_df.to_dict('records'))

    except Exception as e:
        return f"Erreur lors du chargement de l'accueil : {e}"
        # Récupérer le dernier Grand Prix en fonction de la dernière ligne du fichier
        dernier_gp = df_classement["Grand Prix"].iloc[-1]
        classement_du_gp = df_classement[df_classement["Grand Prix"] == dernier_gp]

        df_general = pd.read_csv("classement_general.csv", encoding="utf-8", on_bad_lines="skip")

        return render_template("index.html", classement_du_gp=classement_du_gp.to_dict(orient="records"),
                               classement_general=df_general.to_dict(orient="records"))

    except Exception as e:
        return f"Erreur lors du chargement de l'accueil : {e}"

from functools import wraps

def login_requis(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "nom" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

@app.route("/ajouter_pronostic", methods=["GET", "POST"])
@login_requis
def ajouter_pronostic():
    nom_utilisateur = session["nom"]
    # Logique pour ajouter un pronostic en vérifiant que l'utilisateur n'en modifie pas un autre
    if request.method == 'POST':
        if 'grand_prix' in request.form and 'participant' in request.form:
            gp = request.form['grand_prix']
            participant = request.form['participant']
            p1 = request.form.get('p1', '')
            p2 = request.form.get('p2', '')
            p3 = request.form.get('p3', '')

            pronostics_df = lire_csv_utf8("pronostics.csv")
            new_row = pd.DataFrame([{"Grand Prix": gp, "Participant": participant, "1er": p1, "2e": p2, "3e": p3}])
            pronostics_df = pd.concat([pronostics_df, new_row], ignore_index=True)
            pronostics_df.to_csv("pronostics.csv", index=False)

            return render_template('confirmation.html', message="Pronostic ajouté avec succès !")

    return render_template('ajouter_pronostic.html', grands_prix=grands_prix, participants=participants, pilotes=pilotes)

@app.route('/ajouter_resultat', methods=['GET', 'POST'])
def ajouter_resultat():
    if request.method == 'POST':
        if 'grand_prix' in request.form:
            gp = request.form['grand_prix']
            resultats = [request.form.get(f'pos{i}', '') for i in range(1, 11)]

            resultats_df = lire_csv_utf8("resultats.csv")
            new_row = pd.DataFrame([{**{"Grand Prix": gp}, **{f"pos{i}": resultats[i-1] for i in range(1, 11)}}])
            resultats_df = pd.concat([resultats_df, new_row], ignore_index=True)
            resultats_df.to_csv("resultats.csv", index=False, mode='w', encoding='utf-8')

            return render_template('confirmation.html', message="Résultat ajouté avec succès !")
        if "Grand Prix" not in resultats_df.columns:
            print("🚨 Erreur: Colonne 'Grand Prix' introuvable. Colonnes trouvées :", resultats_df.columns.tolist())
            exit()

    return render_template('ajouter_resultat.html', grands_prix=grands_prix, pilotes=pilotes)


# Initialisation des données
participants = ["Amandine", "Sacha", "Padre"]
grands_prix = [
    "Bahrein", "Arabie Saoudite", "Australie", "Japon", "Chine", "Miami",
    "Emilie-Romagne", "Monaco", "Canada", "Espagne", "Autriche", "Grande-Bretagne",
    "Hongrie", "Belgique", "Pays-Bas", "Italie", "Azerbaidjan", "Singapour",
    "Etats-Unis", "Mexique", "Bresil", "Las Vegas", "Qatar", "Abu Dhabi"
]

pilotes = [
    "Max Verstappen", "Lewis Hamilton", "Charles Leclerc", "Kimi Antonelli", "George Russell",
    "Carlos Sainz", "Lando Norris", "Oscar Piastri", "Fernando Alonso", "Esteban Ocon",
    "Pierre Gasly", "Lance Stroll", "Kevin Magnussen", "Nico Hulkenberg", "Oliver Bearman",
    "Jack Doohan", "Yuki Tsunoda", "Liam Lawson", "Alexander Albon", "Isack Hadjar"
]

# Points attribués par position
points_f1 = {1: 25, 2: 18, 3: 15, 4: 12, 5: 10, 6: 8, 7: 6, 8: 4, 9: 2, 10: 1}

# Vérification et création des fichiers CSV pour stocker les données
if not os.path.exists("pronostics.csv"):
    pd.DataFrame(columns=["Grand Prix", "Participant", "1er", "2e", "3e"]).to_csv("pronostics.csv", index=False)

if not os.path.exists("resultats.csv"):
    pd.DataFrame(columns=["Grand Prix", "1er", "2e", "3e", "4e", "5e", "6e", "7e", "8e", "9e", "10e"]).to_csv("resultats.csv", index=False)

if not os.path.exists("classement.csv"):
    pd.DataFrame(columns=["Grand Prix", "Participant", "Points GP", "Bonus", "Total"]).to_csv("classement.csv", index=False)

if not os.path.exists("classement_general.csv"):
    pd.DataFrame(columns=["Participant", "Total Points"]).to_csv("classement_general.csv", index=False)

@app.route('/calculer_classement')
def calculer_classement():
    # Charger les données des fichiers CSV
    pronostics_df = lire_csv_utf8("pronostics.csv")
    resultats_df = lire_csv_utf8("resultats.csv")

    # Vérifier que les fichiers ne sont pas vides
    if pronostics_df.empty or resultats_df.empty:
        return "Aucun pronostic ou résultat disponible."

    classement_df = pd.DataFrame(columns=["Grand Prix", "Participant", "Points GP", "Bonus", "Total"])
    points_f1 = {1: 25, 2: 18, 3: 15, 4: 12, 5: 10, 6: 8, 7: 6, 8: 4, 9: 2, 10: 1}

    debug_output = "<h2>Débogage - Calcul des Points</h2><ul>"

    for index, row in pronostics_df.iterrows():
        gp = row["Grand Prix"].strip()  # Supprime les espaces inutiles
        participant = row["Participant"]
        pronos = [row["1er"], row["2e"], row["3e"]]

        # Vérifier si le Grand Prix existe bien dans resultats.csv
        if gp not in resultats_df["Grand Prix"].values:
            debug_output += f"<li>Grand Prix {gp} PAS TROUVÉ dans resultats.csv</li>"
            continue
        
        # Récupération des résultats et suppression des valeurs NaN
        resultats = resultats_df[resultats_df["Grand Prix"] == gp].iloc[0, 1:11].dropna().tolist()
        debug_output += f"<li>GP: {gp}, Résultats: {resultats}</li>"

        # Calcul des points F1
        points = sum(points_f1.get(resultats.index(p) + 1, 0) for p in pronos if p in resultats)

        # Calcul du bonus
        bonus = 10 if pronos == resultats[:3] else (3 if set(pronos) == set(resultats[:3]) else 0)
        total_points = points + bonus

        debug_output += f"<li>{participant} - Pronostics: {pronos}, Points: {points}, Bonus: {bonus}, Total: {total_points}</li>"

        # Mise à jour du classement
        classement_df = pd.concat([classement_df, pd.DataFrame([{
    "Grand Prix": gp,
    "Participant": participant,
    "Points GP": points,
    "Bonus": bonus,
    "Total": total_points
}])], ignore_index=True)


    # Sauvegarde des classements
    if os.path.exists("classement.csv"):
        os.remove("classement.csv")  # Supprime le fichier pour éviter les doublons

    classement_df.to_csv("classement.csv", index=False, mode="a", header=not os.path.exists("classement.csv"))


    # Mise à jour du classement général
    classement_general_df = classement_df.groupby("Participant")["Total"].sum().reset_index()
    classement_general_df.columns = ["Participant", "Total Points"]
    classement_general_df.to_csv("classement_general.csv", index=False)

    debug_output += "</ul><h3>Classements mis à jour !</h3>"

    return debug_output  # Pour voir si les calculs sont corrects


@app.route('/classement_du_jour')
def classement_du_jour():
    # Recalculer le classement avant l'affichage
    calculer_classement()
    classement_df = pd.read_csv("classement.csv")
    return render_template('classement.html', classement=classement_df.to_dict('records'))
    
@app.route('/classement_general')
def classement_general():
    # Recalculer le classement avant l'affichage
    calculer_classement()
    classement_general_df = pd.read_csv("classement_general.csv")
    return render_template('classement_general.html', classement_general=classement_general_df.to_dict('records'))

@app.route('/classement')
def afficher_classement():
    return """
    <h1>Classements</h1>
    <ul>
        <li><a href='/classement_du_jour'>Classement du Grand Prix</a></li>
        <li><a href='/classement_general'>Classement Général</a></li>
    </ul>
    """
# Fonction pour charger correctement les résultats
def lire_csv_utf8(filename):
    try:
        df = pd.read_csv(filename, encoding='utf-8')
    except UnicodeDecodeError:
        df = pd.read_csv(filename, encoding='ISO-8859-1')

    # Remplacer les NaN par une chaîne vide pour éviter les erreurs
    df.fillna("", inplace=True)
    return df


# 🔹 Vérifie et nettoie le fichier resultats.csv
def nettoyer_resultats_csv():
    try:
        if os.path.exists("resultats.csv"):
            # Ouvre et nettoie le fichier
            with open("resultats.csv", "r+", encoding="utf-8") as f:
                df = pd.read_csv(f)

            # Suppression des colonnes vides
            df = df.dropna(axis=1, how='all')

            # Suppression des espaces et virgules en trop après le nom du Grand Prix
            df["Grand Prix"] = df["Grand Prix"].str.strip().str.replace(r",+$", "", regex=True)

            # Sauvegarde des modifications
            df.to_csv("resultats.csv", index=False, encoding='utf-8')
    except PermissionError:
        print("❌ ERREUR : Fichier 'resultats.csv' est en cours d'utilisation. Fermez-le et réessayez.")

# 🔹 Appel du nettoyage avant lancement de Flask
nettoyer_resultats_csv()

@app.route('/historique')
def historique():
    try:
        # Lire les fichiers CSV contenant les résultats et le classement
        df_resultats = pd.read_csv("resultats.csv", encoding="utf-8", on_bad_lines="skip")
        resultats_df = lire_csv_utf8("resultats.csv")
        classement_df = lire_csv_utf8("classement.csv")

        # Vérifier que les fichiers ne sont pas vides
        if resultats_df.empty or classement_df.empty:
            return "Aucun historique disponible pour le moment."

        # Convertir les données en dictionnaire pour l'affichage
        resultats_data = resultats_df.to_dict('records')
        classement_data = classement_df.to_dict('records')

        return render_template('historique.html', resultats=resultats_data, classement=classement_data)

    except Exception as e:
        return f"Erreur lors de la récupération de l'historique : {e}"


if __name__ == '__main__':
    app.run(debug=True)
