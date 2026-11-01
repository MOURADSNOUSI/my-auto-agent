import re
from playwright.sync_api import sync_playwright

from ecarstrade import session_favoris

MARQUES = ["Porsche", "Range Rover", "Volkswagen"]

# Première connexion : manuelle, puis mémorisée dans le profil persistant
with sync_playwright() as p, session_favoris(
    p, connexion_manuelle=True, viewport={"width": 1400, "height": 900}
) as (context, page):
    print("✅ Navigation vers les favoris réussie.")

    # Attendre les annonces
    try:
        page.get_by_text(
            re.compile("|".join(MARQUES), re.IGNORECASE)
        ).first.wait_for(timeout=15000)

    except Exception:
        print("Annonces non détectées dans le délai.")

    texte = page.locator("body").inner_text()

    print("URL :", page.url)

    for nom in MARQUES:
        print(
            f"{nom} détecté :",
            nom.lower() in texte.lower()
        )

    input("\nEntrée pour fermer Chromium...")
