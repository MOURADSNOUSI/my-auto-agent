import re
from pathlib import Path
from playwright.sync_api import sync_playwright

URL = "https://fr.ecarstrade.com/profile/selections"
PROFIL = str(Path.home() / ".my-auto-agent-browser")


def references_visibles(page):
    texte = page.locator("body").inner_text()

    return sorted(set(
        re.findall(r"#(\d{6,9})\b", texte)
    ))


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

        page1 = references_visibles(page)

        print("\nPAGE 1")
        print("URL :", page.url)
        print("Nombre :", len(page1))
        print("Références :", page1)

        input(
            "\nOuvre la page 2 dans Chromium, "
            "puis appuie sur Entrée..."
        )

        page2 = references_visibles(page)

        print("\nPAGE 2")
        print("URL :", page.url)
        print("Nombre :", len(page2))
        print("Références :", page2)

        print("\nCOMPARAISON")
        print("Références communes :", len(set(page1) & set(page2)))
        print("Uniquement page 1 :", sorted(set(page1) - set(page2)))
        print("Uniquement page 2 :", sorted(set(page2) - set(page1)))
        print("Total unique :", len(set(page1) | set(page2)))

    finally:
        context.close()