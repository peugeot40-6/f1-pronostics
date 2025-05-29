from flask import Flask, render_template, request, redirect, session, url_for
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from functools import wraps
import datetime

app = Flask(__name__)
app.secret_key = "votre_cle_secrete"

# Connexion Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)

doc_id = "1Te2XcNNeL5Ptrbq7NXeDfZYxYq17EIrGN7GcDqZbrvc"
sh = client.open_by_key(doc_id)

def login_requis(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if "utilisateur" in session:
            return f(*args, **kwargs)
        else:
            return redirect(url_for("login"))
    return wrap

@app.route("/", methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        utilisateur = request.form["utilisateur"]
        session["utilisateur"] = utilisateur
        return redirect(url_for("accueil"))
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/accueil")
@login_requis
def accueil():
    nom = session.get("utilisateur", "")
    try:
        ws = sh.worksheet("classements")
        data = ws.get_all_records()
        df = pd.DataFrame(data)
        if not df.empty:
            dernier_gp = df["Grand Prix"].iloc[-1]
            classement_gp = df[df["Grand Prix"] == dernier_gp].to_dict("records")
            classement_general = df.groupby("Participant")["Total"].sum().reset_index().sort_values(by="Total", ascending=False).to_dict("records")
        else:
            classement_gp = []
            classement_general = []
    except Exception as e:
        print("Erreur d'accès à Sheets:", e)
        classement_gp, classement_general = [], []

    return render_template("index.html", nom=nom, classement=classement_gp, classement_general=classement_general)

@app.route("/ajouter_pronostic", methods=["GET", "POST"])
@login_requis
def ajouter_pronostic():
    if request.method == "POST":
        participant = session["utilisateur"]
        grand_prix = request.form["grand_prix"]
        date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        donnees = [participant, grand_prix, date]
        for i in range(1, 6):
            donnees.append(request.form.get(f"pilote{i}", ""))

        try:
            ws = sh.worksheet("pronostics")
            ws.append_row(donnees)
        except Exception as e:
            print("Erreur enregistrement pronostic:", e)

        return redirect(url_for("accueil"))

    return render_template("ajouter_pronostic.html")

@app.route("/voir_pronostics")
@login_requis
def voir_pronostics():
    if session.get("utilisateur") != "Padre":
        return redirect(url_for("accueil"))
    try:
        ws = sh.worksheet("pronostics")
        data = ws.get_all_records()
    except Exception as e:
        print("Erreur lecture des pronostics:", e)
        data = []
    return render_template("voir_pronostics.html", pronostics=data)

@app.route("/ajouter_resultats", methods=["GET", "POST"])
@login_requis
def ajouter_resultats():
    if session.get("utilisateur") != "Padre":
        return redirect(url_for("accueil"))

    if request.method == "POST":
        grand_prix = request.form["grand_prix"]
        resultats = [grand_prix]
        for i in range(1, 6):
            resultats.append(request.form.get(f"pilote{i}", ""))
        try:
            ws = sh.worksheet("resultats")
            ws.append_row(resultats)
        except Exception as e:
            print("Erreur enregistrement des résultats:", e)
        return redirect(url_for("accueil"))

    return render_template("ajouter_resultats.html")

if __name__ == "__main__":
    app.run(debug=True)
