import json
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    page.goto("https://quotes.toscrape.com/")

    citations = page.locator(".quote")

    resultats = []

    for citation in citations.all():
        resultats.append({
            "texte": citation.locator(".text").inner_text(),
            "auteur": citation.locator(".author").inner_text()
        })

    with open("extraction.json", "w", encoding="utf-8") as f:
        json.dump(resultats, f, ensure_ascii=False, indent=2)

    print(f"{len(resultats)} éléments récupérés")
    browser.close()