import json
from pathlib import Path
from playwright.sync_api import sync_playwright

from ecarstrade import session_favoris

REFERENCE = "7750872"

with sync_playwright() as p, session_favoris(
    p, viewport={"width": 1400, "height": 900}
) as (context, page):
    print("Ouvre la fiche Porsche Cayenne #7750872.")
    print("Si une galerie apparaît, ouvre-la également.")

    input("Une fois la galerie ouverte, appuie sur Entrée...")

    page = context.pages[-1]

    images = page.evaluate("""
        () => {
            const elements = document.querySelectorAll("img");
            const resultat = [];

            for (const img of elements) {
                const urls = [
                    img.currentSrc,
                    img.src,
                    img.getAttribute("data-src")
                ];

                for (const url of urls) {
                    if (url && url.includes("carsphotos")) {
                        resultat.push(url);
                    }
                }
            }

            return [...new Set(resultat)];
        }
    """)

    resultat = {
        "reference": REFERENCE,
        "url_fiche": page.url,
        "images": images
    }

    Path("galerie_7750872.json").write_text(
        json.dumps(resultat, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    print("URL :", page.url)
    print("Photos trouvées :", len(images))

    for i, url in enumerate(images, 1):
        print(f"{i}. {url}")
