import os
import json
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

DATA_FILE = "/mnt/data/data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        nom = request.form.get("nom")
        prenom = request.form.get("prenom")
        identifiant = request.form.get("identifiant")
        motdepasse = request.form.get("motdepasse")

        data = load_data()
        data.append({
            "nom": nom,
            "prenom": prenom,
            "identifiant": identifiant,
            "motdepasse": motdepasse,
            "statut": "A INSCRIRE A L'EXAMEN",
            "commentaire": ""
        })
        save_data(data)

        return render_template("merci.html")

    return render_template("index.html")

@app.route("/admin", methods=["GET", "POST"])
def admin():
    data = load_data()

    if request.method == "POST":
        action = request.form.get("action")
        index = int(request.form.get("index"))

        # 🔁 TOGGLE DU STATUT  
        if action == "toggle":
            if data[index]["statut"] == "INSCRIT A L'EXAMEN":
                data[index]["statut"] = "A INSCRIRE A L'EXAMEN"
            else:
                data[index]["statut"] = "INSCRIT A L'EXAMEN"

            save_data(data)
            return redirect(url_for("admin"))

        # 💾 ENREGISTRER COMMENTAIRE  
        elif action == "save":
            data[index]["commentaire"] = request.form.get("commentaire")
            save_data(data)
            return redirect(url_for("admin"))

        # 🗑️ SUPPRESSION  
        elif action == "delete":
            data.pop(index)
            save_data(data)
            return redirect(url_for("admin"))

    return render_template("admin.html", inscrits=data)

# -----------------------
# Route publique pour exposer data.json (avec CORS)
# -----------------------
@app.route("/data.json")
def data_json():
    """Renvoie le contenu du fichier data.json pour la plateforme VTC"""
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            contenu = f.read()
        headers = {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        }
        return contenu, 200, headers
    except Exception as e:
        print("Erreur lecture data.json:", e)
        return {"error": "impossible de lire les données"}, 500


if __name__ == "__main__":
    os.makedirs("/mnt/data", exist_ok=True)
    app.run(host="0.0.0.0", port=10000)
