import json
import re
from pathlib import Path

from ecarstrade import lire_fiche

source = Path("vehicules_ecarstrade.json")
destination = Path("vehicules_structures.json")

vehicules_bruts = json.loads(
    source.read_text(encoding="utf-8")
)

resultats = []

for vehicule in vehicules_bruts:
    texte = vehicule["description_brute"]
    caracteristiques = lire_fiche(texte)
    reference = re.search(r"#(\d+)", texte)
    reference = reference.group(1) if reference else None

    fiche = {
        "source": "ecarstrade",
        "reference": reference,
        "marque": vehicule["marque_recherchee"],
        "designation": caracteristiques["designation"],
        "mise_en_circulation": caracteristiques["mise_en_circulation"],
        "kilometrage": caracteristiques["kilometrage"],
        "puissance_ch": caracteristiques["puissance_ch"],
        "pays": caracteristiques["pays"],
        "prix_eur": caracteristiques["prix_achat_eur"],
        "prix_type": (
            "prix_fixe" if caracteristiques["prix_achat_eur"] is not None else "offre"
        ),
        "tva_non_incluse": caracteristiques["tva_non_incluse"],
        "statut": "en_attente_validation"
    }

    resultats.append(fiche)

destination.write_text(
    json.dumps(resultats, ensure_ascii=False, indent=2),
    encoding="utf-8"
)

print(f"✅ {len(resultats)} véhicules structurés")

for v in resultats:
    print(
        v["reference"],
        "-",
        v["designation"],
        "-",
        v["kilometrage"],
        "km",
        "-",
        v["prix_eur"],
        "€"
    )

print("Fichier créé :", destination)
