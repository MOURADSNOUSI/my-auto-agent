import json
import re
from pathlib import Path

source = Path("vehicules_ecarstrade.json")
destination = Path("vehicules_structures.json")

vehicules_bruts = json.loads(
    source.read_text(encoding="utf-8")
)

resultats = []

for vehicule in vehicules_bruts:
    texte = vehicule["description_brute"]
    lignes = [l.strip() for l in texte.splitlines() if l.strip()]

    def chercher(pattern):
        match = re.search(pattern, texte, re.IGNORECASE)
        return match.group(1) if match else None

    reference = chercher(r"#(\d+)")
    date = chercher(r"\b(\d{2}/\d{4})\b")
    km = chercher(r"([\d\s]+)\s*KM\b")
    puissance = chercher(r"(\d+)\s*Hp")
    pays = next(
        (p for p in ["France", "Belgique", "Allemagne"]
         if re.search(rf"(?m)^{p}$", texte)),
        None
    )

    prix = chercher(r"ACHETER\s*([\d\s]+)\s*€")

    fiche = {
        "source": "ecarstrade",
        "reference": reference,
        "marque": vehicule["marque_recherchee"],
        "designation": lignes[0],
        "mise_en_circulation": date,
        "kilometrage": (
            int(re.sub(r"\s", "", km)) if km else None
        ),
        "puissance_ch": (
            int(puissance) if puissance else None
        ),
        "pays": pays,
        "prix_eur": (
            int(re.sub(r"\s", "", prix)) if prix else None
        ),
        "prix_type": (
            "prix_fixe" if prix else "offre"
        ),
        "tva_non_incluse": "TVA non incluse" in texte,
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