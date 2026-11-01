import json
import re
from pathlib import Path
from playwright.sync_api import sync_playwright

URL = "https://fr.ecarstrade.com/profile/selections"
PROFIL = str(Path.home() / ".my-auto-agent-browser")


def extraire_references(page):
    texte = page.locator("body").inner_text()
    return re.findall(r"#(\d{6,9})\b", texte)


with sync_playwright() as p:
    context = p.chromium.launch_persistent_context(
        user_data_dir=PROFIL,
        headless=False
    )

    try:
        page = context.pages[0] if context.pages else context.new_page()
        page.goto(URL, wait_until="domcontentloaded")

        if "/login" in page.url:
            raise RuntimeError("Connexion eCarsTrade nécessaire.")

        page.get_by_text(
            re.compile(r"#\d{6,9}")
        ).first.wait_for(timeout=15000)

        references = extraire_references(page)

        print("Page 1 :", len(set(references)), "références")

        input(
            "\nDans Chromium, ouvre manuellement "
            "la page 2 des favoris, puis appuie sur Entrée..."
        )

        references += extraire_references(page)

        references = list(dict.fromkeys(references))

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

    finally:
        context.close()