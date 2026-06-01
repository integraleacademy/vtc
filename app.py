import json
import os
from datetime import datetime, timezone

from flask import Flask, redirect, render_template, request, url_for

app = Flask(__name__)

DATA_FILE = "/mnt/data/data.json"

DEFAULT_CONTACT = {
    "nom": "",
    "prenom": "",
    "email": "",
    "telephone": "",
    "formation": "",
    "campus": "",
    "message": "",
    "statut": "A CONTACTER",
    "commentaire": "",
    "created_at": "",
}


def normalize_contact(item):
    """Garantit une structure stable pour les demandes historiques et nouvelles."""
    for key, value in DEFAULT_CONTACT.items():
        item.setdefault(key, value)

    # Compatibilité avec les anciennes demandes déjà enregistrées.
    if not item.get("email") and item.get("identifiant"):
        item["email"] = item.get("identifiant", "")
    if not item.get("formation"):
        item["formation"] = "Ancienne demande" if item.get("identifiant") else ""
    if not item.get("statut") or item.get("statut") == "A INSCRIRE A L'EXAMEN":
        item["statut"] = "A CONTACTER"
    if item.get("statut") == "INSCRIT A L'EXAMEN":
        item["statut"] = "CONTACTÉ"

    return item


def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [normalize_contact(item) for item in data]

    return []


def save_data(data):
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        data = load_data()
        data.append(normalize_contact({
            "nom": request.form.get("nom", "").strip(),
            "prenom": request.form.get("prenom", "").strip(),
            "email": request.form.get("email", "").strip(),
            "telephone": request.form.get("telephone", "").strip(),
            "formation": request.form.get("formation", "").strip(),
            "campus": request.form.get("campus", "").strip(),
            "message": request.form.get("message", "").strip(),
            "statut": "A CONTACTER",
            "commentaire": "",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }))
        save_data(data)
        return render_template("merci.html")

    return render_template("index.html")


@app.route("/btsmos")
def bts_mos():
    return render_template("bts_mos.html")


@app.route("/admin", methods=["GET", "POST"])
def admin():
    data = load_data()

    if request.method == "POST":
        action = request.form.get("action")
        index = int(request.form.get("index"))

        if action == "toggle":
            data[index]["statut"] = "A CONTACTER" if data[index].get("statut") == "CONTACTÉ" else "CONTACTÉ"
            save_data(data)
            return redirect(url_for("admin"))

        if action == "save":
            data[index]["commentaire"] = request.form.get("commentaire", "")
            save_data(data)
            return redirect(url_for("admin"))

        if action == "delete":
            data.pop(index)
            save_data(data)
            return redirect(url_for("admin"))

    return render_template("admin.html", inscrits=data)


@app.route("/data.json")
def data_json():
    """Renvoie les demandes de contact pour les intégrations externes."""
    try:
        contenu = json.dumps(load_data(), indent=4, ensure_ascii=False)
        headers = {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        }
        return contenu, 200, headers
    except Exception as e:
        print("Erreur lecture data.json:", e)
        return {"error": "impossible de lire les données"}, 500


@app.route("/summary.json")
def summary_json():
    """Résumé des demandes à traiter pour un tableau de bord."""
    data = load_data()

    summary = {
        "a_contacter": sum(1 for x in data if x.get("statut") == "A CONTACTER"),
        "contactes": sum(1 for x in data if x.get("statut") == "CONTACTÉ"),
        "total": len(data),
    }

    return summary, 200, {"Access-Control-Allow-Origin": "*"}


if __name__ == "__main__":
    os.makedirs("/mnt/data", exist_ok=True)
    app.run(host="0.0.0.0", port=10000)
