import json
import re
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE = Path(__file__).resolve().parent

URL = "https://fr.ecarstrade.com/profile/selections"
PROFIL = str(Path.home() / ".my-auto-agent-browser")

inventaire = json.loads(
    (BASE / "inventaire_favoris.json").read_text(
        encoding="utf-8"
    )
)

references = inventaire["references"]

vehicules = []
manquants = []

with sync_playwright() as p:

    context = p.chromium.launch_persistent_context(
        user_data_dir=PROFIL,
        headless=False
    )

    try:
        page = context.pages[0] if context.pages else context.new_page()

        page.goto(URL, wait_until="domcontentloaded")

        if "/login" in page.url:
            raise RuntimeError(
                "Session expirée : reconnecte-toi à eCarsTrade."
            )

        page.get_by_text(
            re.compile(r"#\d{6,9}")
        ).first.wait_for(timeout=15000)

        for reference in references:

            element = page.get_by_text(
                re.compile(rf"#{re.escape(reference)}\b")
            ).first

            if element.count() == 0:
                manquants.append(reference)
                print(f"❌ {reference} introuvable")
                continue

            donnees = element.evaluate("""
                element => {
                    let parent = element;

                    for (let i = 0; i < 12 && parent; i++) {
                        const texte = parent.innerText || "";

                        const refs = [
                            ...texte.matchAll(/#\\d{6,9}\\b/g)
                        ].map(x => x[0]);

                        const uniques = [...new Set(refs)];

                        if (
                            texte.length >= 80 &&
                            texte.length <= 2000 &&
                            /\\bKM\\b/i.test(texte) &&
                            uniques.length === 1
                        ) {
                            return {
                                texte: texte.trim()
                            };
                        }

                        parent = parent.parentElement;
                    }

                    return null;
                }
            """)

            if not donnees:
                manquants.append(reference)
                print(f"⚠️ Fiche non isolée : {reference}")
                continue

            fiche = {
                "source": "ecarstrade",
                "reference": reference,
                "description_brute": donnees["texte"],
                "statut": "en_attente_validation"
            }

            vehicules.append(fiche)

            print(f"✅ Véhicule extrait : {reference}")

        sortie = BASE / "vehicules_20_bruts.json"

        sortie.write_text(
            json.dumps(
                vehicules,
                ensure_ascii=False,
                indent=2
            ),
            encoding="utf-8"
        )

        print("\n========== RÉSULTAT ==========")
        print("Références attendues :", len(references))
        print("Fiches extraites :", len(vehicules))
        print("Fiches manquantes :", len(manquants))
        print("Références manquantes :", manquants)
        print("Fichier :", sortie)

    finally:
        context.close()