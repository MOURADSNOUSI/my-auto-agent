import re
from pathlib import Path
from playwright.sync_api import sync_playwright

URL = "https://fr.ecarstrade.com/profile/selections"

# Profil Chromium conservé sur ton ordinateur
PROFIL = str(Path.home() / ".my-auto-agent-browser")

with sync_playwright() as p:

    # Navigateur avec session persistante
    context = p.chromium.launch_persistent_context(
        user_data_dir=PROFIL,
        headless=False,
        viewport={"width": 1400, "height": 900}
    )

    try:
        page = context.pages[0] if context.pages else context.new_page()

        page.goto(
            URL,
            wait_until="domcontentloaded",
            timeout=30000
        )

        # Première connexion : manuelle
        if "/login" in page.url:

            print("Première connexion nécessaire.")
            print("Connecte-toi dans Chromium.")

            input(
                "Une fois connecté, appuie sur Entrée..."
            )

            page.goto(
                URL,
                wait_until="domcontentloaded"
            )

        if "/login" in page.url:
            print("❌ Session non authentifiée.")

        else:
            print("✅ Navigation vers les favoris réussie.")

            # Attendre les annonces
            try:
                page.get_by_text(
                    re.compile(
                        r"Porsche|Range Rover|Volkswagen",
                        re.IGNORECASE
                    )
                ).first.wait_for(timeout=15000)

            except Exception:
                print("Annonces non détectées dans le délai.")

            texte = page.locator("body").inner_text()

            print("URL :", page.url)

            for nom in ["Porsche", "Range Rover", "Volkswagen"]:
                print(
                    f"{nom} détecté :",
                    nom.lower() in texte.lower()
                )

        input("\nEntrée pour fermer Chromium...")

    finally:
        context.close()