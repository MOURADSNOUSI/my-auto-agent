import json
import re
from pathlib import Path

BASE = Path(__file__).resolve().parent

SOURCE = BASE / "vehicules_20_bruts.json"
DESTINATION = BASE / "vehicules_20_structures.json"


def rechercher(pattern, texte):
    resultat = re.search(pattern, texte, re.IGNORECASE)
    return resultat.group(1) if resultat else None


def convertir_nombre(valeur):
    if valeur is None:
        return None
    return int(re.sub(r"\s", "", valeur))


vehicules_bruts = json.loads(
    SOURCE.read_text(encoding="utf-8")
)

resultats = []
references_vues = set()

for vehicule in vehicules_bruts:
    texte = vehicule["description_brute"]
    reference = str(vehicule["reference"])

    if reference in references_vues:
        print(f"⚠️ Doublon ignoré : {reference}")
        continue

    references_vues.add(reference)

    lignes = [
        ligne.strip()
        for ligne in texte.splitlines()
        if ligne.strip()
    ]

    date = rechercher(r"\b(\d{2}/\d{4})\b", texte)
    kilometrage = rechercher(r"([\d\s]+)\s*KM\b", texte)
    puissance = rechercher(r"(\d+)\s*Hp\b", texte)

    prix = rechercher(
        r"ACHETER\s*([\d\s]+)\s*€",
        texte
    )

    pays = next(
        (
            p for p in ["France", "Belgique", "Allemagne"]
            if re.search(
                rf"(?mi)^{re.escape(p)}\s*$",
                texte
            )
        ),
        None
    )

    fiche = {
        "source": "ecarstrade",
        "reference": reference,
        "designation": lignes[0] if lignes else None,
        "mise_en_circulation": date,
        "kilometrage": convertir_nombre(kilometrage),
        "puissance_ch": (
            int(puissance) if puissance else None
        ),
        "pays": pays,
        "prix_achat_eur": convertir_nombre(prix),
        "prix_type": (
            "prix_fixe"
            if prix is not None
            else "offre_ou_non_renseigne"
        ),
        "tva_non_incluse": (
            "TVA non incluse" in texte
        ),
        "description_brute": texte,
        "statut": "en_attente_validation"
    }

    resultats.append(fiche)

DESTINATION.write_text(
    json.dumps(
        resultats,
        ensure_ascii=False,
        indent=2
    ),
    encoding="utf-8"
)

print("\n========== RÉSULTAT ==========")
print("Véhicules structurés :", len(resultats))

for v in resultats:
    print(
        v["reference"],
        "|",
        v["designation"],
        "|",
        v["kilometrage"],
        "km",
        "|",
        v["prix_achat_eur"],
        "€"
    )

print("\nFichier créé :", DESTINATION)