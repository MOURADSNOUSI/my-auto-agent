import json
from pathlib import Path
from playwright.sync_api import sync_playwright

from ecarstrade import attendre_fiches, references_visibles, session_favoris

with sync_playwright() as p, session_favoris(p) as (context, page):
    attendre_fiches(page)

    references = references_visibles(page)

    print("Page 1 :", len(references), "références")

    input(
        "\nDans Chromium, ouvre manuellement "
        "la page 2 des favoris, puis appuie sur Entrée..."
    )

    references = list(dict.fromkeys(references + references_visibles(page)))

    resultat = {
        "source": "ecarstrade",
        "references": references,
        "nombre": len(references)
    }

    Path("inventaire_favoris.json").write_text(
        json.dumps(resultat, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    print("\nRéférences trouvées :", references)
    print("Total unique :", len(references))
    print("Fichier créé : inventaire_favoris.json")
