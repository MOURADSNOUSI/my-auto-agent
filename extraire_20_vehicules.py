import json
from pathlib import Path
from playwright.sync_api import sync_playwright

from ecarstrade import JS_FICHE, attendre_fiches, localiser_reference, session_favoris

BASE = Path(__file__).resolve().parent

inventaire = json.loads(
    (BASE / "inventaire_favoris.json").read_text(
        encoding="utf-8"
    )
)

references = inventaire["references"]

vehicules = []
manquants = []

with sync_playwright() as p, session_favoris(p) as (context, page):
    attendre_fiches(page)

    for reference in references:

        element = localiser_reference(page, reference)

        if element.count() == 0:
            manquants.append(reference)
            print(f"❌ {reference} introuvable")
            continue

        donnees = element.evaluate(JS_FICHE)

        if not donnees:
            manquants.append(reference)
            print(f"⚠️ Fiche non isolée : {reference}")
            continue

        vehicules.append({
            "source": "ecarstrade",
            "reference": reference,
            "description_brute": donnees["texte"],
            "statut": "en_attente_validation"
        })

        print(f"✅ Véhicule extrait : {reference}")

    sortie = BASE / "vehicules_20_bruts.json"

    sortie.write_text(
        json.dumps(
            vehicules,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )

    print("\n========== RÉSULTAT ==========")
    print("Références attendues :", len(references))
    print("Fiches extraites :", len(vehicules))
    print("Fiches manquantes :", len(manquants))
    print("Références manquantes :", manquants)
    print("Fichier :", sortie)
