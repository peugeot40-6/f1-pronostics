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

if __name__ == "__main__":
    app.run(debug=True)
