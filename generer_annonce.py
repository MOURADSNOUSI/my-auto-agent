import json
from pathlib import Path

# Lire les données du véhicule
vehicule = json.loads(
    Path("annonce_auto.json").read_text(encoding="utf-8")
)

# Préparer le brouillon Facebook
annonce = f"""
🚗 M&Y AUTO EXPORT

🔥 {vehicule['marque']} {vehicule['modele']}

📅 Année : {vehicule['annee']}
⛽ Motorisation : {vehicule['carburant']}
🛣️ Kilométrage : {vehicule['kilometrage']:,} km
🌍 Provenance : {vehicule['pays']}
💶 Prix indicatif : {vehicule['prix_eur']:,} €

📩 Contactez M&Y AUTO EXPORT pour plus d'informations.
"""

Path("brouillon_facebook.txt").write_text(
    annonce.strip(),
    encoding="utf-8"
)

print(annonce)
print("Brouillon Facebook enregistré.")