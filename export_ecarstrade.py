import json
import re
from pathlib import Path
from playwright.sync_api import sync_playwright

URL = "https://fr.ecarstrade.com/profile/selections"
PROFIL = str(Path.home() / ".my-auto-agent-browser")

MARQUES = ["Porsche", "Range Rover", "Volkswagen"]

with sync_playwright() as p:

    context = p.chromium.launch_persistent_context(
        user_data_dir=PROFIL,
        headless=False
    )

    try:
        page = context.pages[0] if context.pages else context.new_page()

        page.goto(URL, wait_until="domcontentloaded")

        if "/login" in page.url:
            print("Connexion nécessaire.")
        else:
            page.get_by_text(
                re.compile(r"Porsche|Range Rover|Volkswagen", re.I)
            ).first.wait_for(timeout=15000)

            vehicules = []

            for marque in MARQUES:

                elements = page.get_by_text(
                    re.compile(re.escape(marque), re.I)
                )

                for i in range(min(elements.count(), 10)):

                    element = elements.nth(i)

                    if not element.is_visible():
                        continue

                    # Remonter vers la fiche du véhicule
                    donnees = element.evaluate("""
                        el => {
                            let parent = el;

                            for (let i = 0; i < 8; i++) {
                                if (!parent) break;

                                const texte = parent.innerText || "";

                                if (
                                    texte.length > 80 &&
                                    texte.length < 1500 &&
                                    /km/i.test(texte)
                                ) {
                                    const lien = parent.querySelector("a[href]");

                                    return {
                                        texte: texte,
                                        lien: lien ? lien.href : null
                                    };
                                }

                                parent = parent.parentElement;
                            }

                            return null;
                        }
                    """)

                    if donnees:
                        vehicules.append({
                            "source": "ecarstrade",
                            "marque_recherchee": marque,
                            "description_brute": donnees["texte"],
                            "url": donnees["lien"],
                            "statut": "en_attente_validation"
                        })

                        break

            fichier = Path("vehicules_ecarstrade.json")

            fichier.write_text(
                json.dumps(
                    vehicules,
                    ensure_ascii=False,
                    indent=2
                ),
                encoding="utf-8"
            )

            print(f"\n✅ {len(vehicules)} fiches exportées")
            print(f"Fichier : {fichier}")

    finally:
        context.close()