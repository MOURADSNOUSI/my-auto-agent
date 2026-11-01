import json
from pathlib import Path

from ecarstrade import lire_fiche

BASE = Path(__file__).resolve().parent

SOURCE = BASE / "vehicules_20_bruts.json"
DESTINATION = BASE / "vehicules_20_structures.json"


def structurer(vehicules_bruts):
    resultats = []
    references_vues = set()

    for vehicule in vehicules_bruts:
        texte = vehicule["description_brute"]
        reference = str(vehicule["reference"])

        if reference in references_vues:
            print(f"⚠️ Doublon ignoré : {reference}")
            continue

        references_vues.add(reference)
        caracteristiques = lire_fiche(texte)

        resultats.append({
            "source": "ecarstrade",
            "reference": reference,
            "designation": caracteristiques["designation"],
            "mise_en_circulation": caracteristiques["mise_en_circulation"],
            "kilometrage": caracteristiques["kilometrage"],
            "puissance_ch": caracteristiques["puissance_ch"],
            "pays": caracteristiques["pays"],
            "prix_achat_eur": caracteristiques["prix_achat_eur"],
            "prix_type": (
                "prix_fixe"
                if caracteristiques["prix_achat_eur"] is not None
                else "offre_ou_non_renseigne"
            ),
            "tva_non_incluse": caracteristiques["tva_non_incluse"],
            "description_brute": texte,
            "statut": "en_attente_validation"
        })

    return resultats


def main():
    resultats = structurer(json.loads(SOURCE.read_text(encoding="utf-8")))

    DESTINATION.write_text(
        json.dumps(resultats, ensure_ascii=False, indent=2),
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


if __name__ == "__main__":
    main()
