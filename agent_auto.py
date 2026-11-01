import json
from pathlib import Path

# Données de démonstration, pas une annonce réelle
vehicule = {
    "source": "demo",
    "marque": "Mercedes-Benz",
    "modele": "CLA 250e",
    "annee": 2023,
    "carburant": "Hybride rechargeable",
    "kilometrage": 45000,
    "prix_eur": 23500,
    "pays": "Allemagne",
    "photos": [],
    "statut": "en_attente_validation"
}

destination = Path("annonce_auto.json")

destination.write_text(
    json.dumps(vehicule, ensure_ascii=False, indent=2),
    encoding="utf-8"
)

print("Annonce automobile enregistrée")
print(f"Fichier : {destination.resolve()}")