import json
from pathlib import Path
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    try:
        response = page.goto(
            "https://example.com",
            wait_until="domcontentloaded",
            timeout=15000
        )

        heading = page.locator("h1")

        data = {
            "url": page.url,
            "status": response.status if response else None,
            "title": page.title(),
            "heading": heading.first.inner_text() if heading.count() else None
        }

        page.screenshot(path="capture.png", full_page=True)

        Path("resultat.json").write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )

        print("Résultat :", data)
        print("Capture enregistrée : capture.png")

    except Exception as e:
        print("Erreur :", e)
        print("URL actuelle :", page.url)
        page.screenshot(path="erreur.png", full_page=True)

    finally:
        browser.close()