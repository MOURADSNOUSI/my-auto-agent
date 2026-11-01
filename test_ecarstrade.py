from playwright.sync_api import sync_playwright

URL = "https://fr.ecarstrade.com/profile/selections"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()

    try:
        page.goto(URL, wait_until="domcontentloaded")

        print("Page ouverte :", page.url)

        input(
            "\nConnecte-toi manuellement dans Chromium. "
            "Une fois connecté, appuie sur Entrée ici..."
        )

        # Vérifier l'accès aux sélections
        page.goto(URL, wait_until="domcontentloaded")

        print("\nURL finale :", page.url)
        print("Titre final :", page.title())

        if "/login" in page.url:
            print("❌ Connexion non confirmée.")
        elif "/profile/selections" in page.url:
            print("✅ Page des sélections accessible.")
        else:
            print("⚠️ Redirection vers une autre page.")

        input("\nAppuie sur Entrée pour fermer Chromium...")

    finally:
        browser.close()