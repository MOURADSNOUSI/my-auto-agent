import json
from pathlib import Path
from playwright.sync_api import sync_playwright

from ecarstrade import JS_FICHE, localiser_reference, session_favoris

REFERENCE = "7750872"

with sync_playwright() as p, session_favoris(
    p, viewport={"width": 1400, "height": 900}
) as (context, page):
    element = localiser_reference(page, REFERENCE)
    element.wait_for(timeout=15000)

    fiche = element.evaluate(JS_FICHE)

    if fiche is None:
        print("❌ Fiche Porsche introuvable.")
    else:
        resultat = {
            "description": fiche["texte"],
            "images": fiche["images"],
            "liens": fiche["liens"]
        }

        fichier = Path("diagnostic_photos_7750872.json")

        fichier.write_text(
            json.dumps(
                resultat,
                ensure_ascii=False,
                indent=2
            ),
            encoding="utf-8"
        )

        print("✅ Fiche détectée")
        print("Images trouvées :", len(resultat["images"]))
        print("Liens trouvés :", len(resultat["liens"]))

        print("\nIMAGES :")
        for image in resultat["images"]:
            print(image["src"] or image["data_src"])

        print("\nFichier créé :", fichier)
