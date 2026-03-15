from flask import Flask, render_template, request, redirect, session, url_for, send_file
import pandas as pd
import os
from functools import wraps

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "supersecretkey")

# ================================
# 🔐 AUTHENTIFICATION
# ================================

participants_mdp = {
    "Padre": "padre123",
    "Amandine": "amandine123",
    "Sacha": "sacha123"
}

def login_requis(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "utilisateur" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        nom = request.form.get("nom", "").strip()
        mdp = request.form.get("mot_de_passe", "").strip()

        if nom in participants_mdp and participants_mdp[nom] == mdp:
            session["utilisateur"] = nom
            return redirect(url_for("index"))
        else:
            return render_template("login.html", erreur="Nom ou mot de passe incorrect")

    return render_template("login.html")


@app.route("/")
def redirection_accueil():
    return redirect(url_for("login"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ================================
# 📊 ACCUEIL (CORRIGÉ)
# ================================

@app.route("/accueil")
@login_requis
def index():
    try:
        nom_utilisateur = session.get("utilisateur", "Inconnu")

        classement_dernier_gp_dict = []
        classement_general_dict = []
        dernier_gp = None

        if os.path.exists("classement.csv"):
            classement_df = pd.read_csv("classement.csv")

            if "Total" in classement_df.columns:
                classement_df["Total"] = pd.to_numeric(
                    classement_df["Total"], errors="coerce"
                ).fillna(0).astype(int)

            if "Participant" in classement_df.columns:
                classement_df["Participant"] = classement_df["Participant"].astype(str).str.strip()

            if not classement_df.empty and "Grand Prix" in classement_df.columns:
                dernier_gp = classement_df["Grand Prix"].iloc[-1]

                classement_dernier_gp = classement_df[
                    classement_df["Grand Prix"] == dernier_gp
                ]
                classement_dernier_gp_dict = classement_dernier_gp.to_dict("records")

                classement_general = (
                    classement_df.groupby("Participant")["Total"]
                    .sum()
                    .reset_index()
                    .sort_values(by="Total", ascending=False)
                )
                classement_general_dict = classement_general.to_dict("records")

        return render_template(
            "index.html",
            classement=classement_dernier_gp_dict,
            classement_general=classement_general_dict,
            nom_utilisateur=nom_utilisateur,
            dernier_gp=dernier_gp
        )

    except Exception as e:
        import traceback
        return f"<pre>{traceback.format_exc()}</pre>", 500
        
# ================================
# 📥 AJOUT PRONOSTIC
# ================================

grands_prix = [
    "Australie", "Japon", "Chine", "Miami", "Barcelone", "Monaco",
    "Canada", "Espagne", "Autriche", "Grande-Bretagne", "Hongrie",
    "Belgique", "Pays-Bas", "Italie", "Azerbaidjan", "Singapour",
    "Etats-Unis", "Mexique", "Bresil", "Las Vegas", "Qatar", "Abu Dhabi"
]

pilotes = [
    "Max Verstappen", "Lewis Hamilton", "Charles Leclerc", "Kimi Antonelli",
    "George Russell", "Carlos Sainz", "Lando Norris", "Oscar Piastri",
    "Fernando Alonso", "Esteban Ocon", "Pierre Gasly", "Lance Stroll",
    "Gabriel Bortoleto", "Nico Hulkenberg", "Oliver Bearman",
    "Franco Colapinto", "Liam Lawson", "Alexander Albon",
    "Isack Hadjar", "Valteri Bottas", "Sergio Perez", "Arvid Lindblad",
]

def lire_csv_utf8(filename):
    try:
        df = pd.read_csv(filename, encoding="utf-8")
    except FileNotFoundError:
        df = pd.DataFrame()
    except UnicodeDecodeError:
        df = pd.read_csv(filename, encoding="ISO-8859-1")

    df.fillna("", inplace=True)
    return df


def recalculer_classement():
    pronostics_df = lire_csv_utf8("pronostics.csv")
    resultats_df = lire_csv_utf8("resultats.csv")

    colonnes_classement = ["Grand Prix", "Participant", "Points GP", "Bonus", "Total"]

    if pronostics_df.empty or resultats_df.empty:
        pd.DataFrame(columns=colonnes_classement).to_csv("classement.csv", index=False)
        return

    classement_lignes = []

    points_f1 = {
        1: 25, 2: 18, 3: 15, 4: 12, 5: 10,
        6: 8, 7: 6, 8: 4, 9: 2, 10: 1
    }

    # Nettoyage des colonnes Grand Prix
    if "Grand Prix" in pronostics_df.columns:
        pronostics_df["Grand Prix"] = pronostics_df["Grand Prix"].astype(str).str.strip()

    if "Grand Prix" in resultats_df.columns:
        resultats_df["Grand Prix"] = resultats_df["Grand Prix"].astype(str).str.strip()

    for _, row in pronostics_df.iterrows():
        gp = str(row.get("Grand Prix", "")).strip()
        participant = str(row.get("Participant", "")).strip()

        pronos = [
            str(row.get("1er", "")).strip(),
            str(row.get("2e", "")).strip(),
            str(row.get("3e", "")).strip()
        ]

        if not gp or not participant:
            continue

        resultat_gp = resultats_df[resultats_df["Grand Prix"] == gp]
        if resultat_gp.empty:
            continue

        ligne_resultat = resultat_gp.iloc[0]

        # Résultats attendus dans les colonnes pos1 à pos10
        resultats = [
            str(ligne_resultat.get(f"pos{i}", "")).strip()
            for i in range(1, 11)
        ]
        resultats = [r for r in resultats if r]

        if not resultats:
            continue

        # Points selon la place réelle du pilote
        points = 0
        for pilote in pronos:
            if pilote in resultats:
                position_reelle = resultats.index(pilote) + 1
                points += points_f1.get(position_reelle, 0)

        # Bonus
        podium_reel = resultats[:3]
        if pronos == podium_reel:
            bonus = 10
        elif set(pronos) == set(podium_reel):
            bonus = 3
        else:
            bonus = 0

        total_points = points + bonus

        classement_lignes.append({
            "Grand Prix": gp,
            "Participant": participant,
            "Points GP": points,
            "Bonus": bonus,
            "Total": total_points
        })

    classement_df = pd.DataFrame(classement_lignes, columns=colonnes_classement)
    classement_df.to_csv("classement.csv", index=False)

    if not classement_df.empty:
        classement_general_df = (
            classement_df.groupby("Participant")["Total"]
            .sum()
            .reset_index()
            .sort_values(by="Total", ascending=False)
        )
    else:
        classement_general_df = pd.DataFrame(columns=["Participant", "Total"])

    classement_general_df.to_csv("classement_general.csv", index=False)
    

@app.route("/ajouter_pronostic", methods=["GET", "POST"])
@login_requis
def ajouter_pronostic():

    if request.method == "POST":
        gp = request.form.get("grand_prix")
        participant = session.get("utilisateur")

        p1 = request.form.get("pilote1")
        p2 = request.form.get("pilote2")
        p3 = request.form.get("pilote3")

        nouvelle_ligne = pd.DataFrame([{
            "Grand Prix": gp,
            "Participant": participant,
            "1er": p1,
            "2e": p2,
            "3e": p3
        }])

        try:
            df = pd.read_csv("pronostics.csv")
            df = pd.concat([df, nouvelle_ligne], ignore_index=True)
        except:
            df = nouvelle_ligne

        df.to_csv("pronostics.csv", index=False)

        return redirect(url_for("index"))

    return render_template("ajouter_pronostic.html", grands_prix=grands_prix, pilotes=pilotes)

# ================================
# 📂 VOIR PRONOSTICS
# ================================

@app.route("/voir_pronostics")
@login_requis
def voir_pronostics():
    try:
        df = pd.read_csv("pronostics.csv")
        pronostics = df.to_dict(orient="records")
    except:
        pronostics = []

    return render_template("voir_pronostics.html", pronostics=pronostics)


@app.route("/tous_les_pronostics")
@login_requis
def voir_tous_les_pronostics():
    if session.get("utilisateur") != "Padre":
        return redirect(url_for("index"))

    pronostics_df = pd.read_csv("pronostics.csv")
    pronostics_df = pronostics_df.sort_values(by=["Grand Prix", "Participant"])
    return render_template("tous_les_pronostics.html", pronostics=pronostics_df.to_dict("records"))
        
# ================================
# 📥 AJOUT RESULTATS
# ================================

@app.route('/ajouter_resultat', methods=['GET', 'POST'])
@login_requis
def ajouter_resultat():
    if session.get("utilisateur") != "Padre":
        return redirect(url_for("index"))

    if request.method == 'POST':
        gp = request.form.get('grand_prix', '').strip()
        resultats = [request.form.get(f'pos{i}', '').strip() for i in range(1, 11)]

        try:
            resultats_df = lire_csv_utf8("resultats.csv")
        except Exception:
            resultats_df = pd.DataFrame(columns=["Grand Prix"] + [f"pos{i}" for i in range(1, 11)])

        # Supprime un éventuel ancien résultat pour ce GP avant d'ajouter le nouveau
        if not resultats_df.empty and "Grand Prix" in resultats_df.columns:
            resultats_df["Grand Prix"] = resultats_df["Grand Prix"].astype(str).str.strip()
            resultats_df = resultats_df[resultats_df["Grand Prix"] != gp]

        new_row = pd.DataFrame([{
            "Grand Prix": gp,
            **{f"pos{i}": resultats[i-1] for i in range(1, 11)}
        }])

        resultats_df = pd.concat([resultats_df, new_row], ignore_index=True)
        resultats_df.to_csv("resultats.csv", index=False, encoding='utf-8')

        # Recalcul automatique du classement
        recalculer_classement()

        return redirect(url_for("index"))

    return render_template('ajouter_resultat.html', grands_prix=grands_prix, pilotes=pilotes)        
# ================================
# 📂 VOIR CLASSEMENT DU JOUR
# ================================
@app.route('/classement_du_jour')
@login_requis
def classement_du_jour():
    try:
        if os.path.exists("classement.csv"):
            df = pd.read_csv("classement.csv")

            if not df.empty and "Grand Prix" in df.columns:
                dernier_gp = df["Grand Prix"].iloc[-1]
                df = df[df["Grand Prix"] == dernier_gp]
                records = df.to_dict(orient="records")
            else:
                records = []
        else:
            records = []

    except Exception as e:
        print("Erreur classement_du_jour :", e)
        records = []

    return render_template("classement_du_jour.html", records=records)

@app.route('/classement_general')
@login_requis
def classement_general():
    try:
        if os.path.exists("classement.csv"):
            df = pd.read_csv("classement.csv")

            if not df.empty and "Participant" in df.columns and "Total" in df.columns:
                df["Total"] = pd.to_numeric(df["Total"], errors="coerce").fillna(0)
                classement_general_df = (
                    df.groupby("Participant")["Total"]
                    .sum()
                    .reset_index()
                    .sort_values(by="Total", ascending=False)
                )
                records = classement_general_df.to_dict("records")
            else:
                records = []
        else:
            records = []

    except Exception as e:
        print("Erreur classement_general :", e)
        records = []

    return render_template("classement_general.html", classement_general=records)

@app.route("/historique")
@login_requis
def historique():
    try:
        if os.path.exists("classement.csv"):
            df = pd.read_csv("classement.csv")
        else:
            df = pd.DataFrame()

        historique_par_gp = []
        couleurs = ["#f8d7da", "#d4edda", "#d1ecf1", "#fff3cd", "#f0dfff"]

        if not df.empty and "Grand Prix" in df.columns:
            for i, gp in enumerate(df["Grand Prix"].dropna().unique()):
                lignes = df[df["Grand Prix"] == gp].to_dict(orient="records")
                historique_par_gp.append({
                    "nom": gp,
                    "couleur": couleurs[i % len(couleurs)],
                    "lignes": lignes
                })

    except Exception as e:
        print("Erreur historique :", e)
        historique_par_gp = []

    return render_template("historique.html", historique_par_gp=historique_par_gp)


# ================================
# 📥 TÉLÉCHARGEMENTS
# ================================

@app.route("/telechargements")
@login_requis
def page_telechargements():
    if session.get("utilisateur") != "Padre":
        return redirect(url_for("index"))
    return render_template("telechargements.html")


@app.route("/telecharger/<nom_fichier>")
@login_requis
def telecharger_fichier(nom_fichier):
    try:
        return send_file(nom_fichier, as_attachment=True)
    except Exception as e:
        return f"Erreur lors du téléchargement : {e}"


# ================================
# 🚀 LANCEMENT
# ================================
if not os.path.exists("pronostics.csv"):
    pd.DataFrame(columns=["Grand Prix", "Participant", "1er", "2e", "3e"]).to_csv("pronostics.csv", index=False)

if not os.path.exists("resultats.csv"):
    pd.DataFrame(columns=["Grand Prix"] + [f"pos{i}" for i in range(1, 11)]).to_csv("resultats.csv", index=False)

if not os.path.exists("classement.csv"):
    pd.DataFrame(columns=["Grand Prix", "Participant", "Points GP", "Bonus", "Total"]).to_csv("classement.csv", index=False)

if not os.path.exists("classement_general.csv"):
    pd.DataFrame(columns=["Participant", "Total"]).to_csv("classement_general.csv", index=False)
if __name__ == "__main__":
    app.run(debug=True)
