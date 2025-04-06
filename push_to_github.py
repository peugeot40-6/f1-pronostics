import os
import subprocess

def push_to_github(message="Mise à jour automatique des pronostics"):
    try:
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        subprocess.run(["git", "add", "pronostics.csv"], check=True)
        subprocess.run(["git", "commit", "-m", message], check=True)
        subprocess.run(["git", "push"], check=True)
        print("✔️ Pronostics envoyés sur GitHub avec succès.")
    except subprocess.CalledProcessError as e:
        print("❌ Une erreur est survenue lors du push :", e)

if __name__ == "__main__":
    push_to_github()