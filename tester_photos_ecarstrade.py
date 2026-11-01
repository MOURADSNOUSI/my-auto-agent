import json
import re
from pathlib import Path
from playwright.sync_api import sync_playwright

URL = "https://fr.ecarstrade.com/profile/selections"
PROFIL = str(Path.home() / ".my-auto-agent-browser")
REFERENCE = "7750872"

with sync_playwright() as p:
    context = p.chromium.launch_persistent_context(
        user_data_dir=PROFIL,
        headless=False,
        viewport={"width": 1400, "height": 900}
    )

    try:
        page = context.pages[0] if context.pages else context.new_page()
        page.goto(URL, wait_until="domcontentloaded")

        element = page.get_by_text(
            re.compile(rf"#{REFERENCE}\b")
        ).first

        element.wait_for(timeout=15000)

        resultat = element.evaluate("""
        element => {
            let parent = element;

            for (let i = 0; i < 12 && parent; i++) {
                const texte = parent.innerText || "";

                const references = [
                    ...texte.matchAll(/#\\d{6,9}\\b/g)
                ].map(x => x[0]);

                const uniques = [...new Set(references)];

                if (
                    texte.length >= 80 &&
                    texte.length <= 2000 &&
                    /\\bKM\\b/i.test(texte) &&
                    uniques.length === 1
                ) {
                    const images = [
                        ...parent.querySelectorAll("img")
                    ].map(img => ({
                        src: img.currentSrc || img.src || null,
                        data_src: img.getAttribute("data-src"),
                        srcset: img.getAttribute("srcset"),
                        alt: img.alt
                    }));

                    const liens = [
                        ...parent.querySelectorAll("a[href]")
                    ].map(a => ({
                        texte: (a.innerText || "").trim(),
                        href: a.href
                    }));

                    return {
                        description: texte.trim(),
                        images: images,
                        liens: liens
                    };
                }

                parent = parent.parentElement;
            }

            return null;
        }
        """)

        if resultat is None:
            print("❌ Fiche Porsche introuvable.")
        else:
            fichier = Path("diagnostic_photos_7750872.json")

            fichier.write_text(
                json.dumps(
                    resultat,
                    ensure_ascii=False,
                    indent=2
                ),
                encoding="utf-8"
            )

            print("✅ Fiche détectée")
            print("Images trouvées :", len(resultat["images"]))
            print("Liens trouvés :", len(resultat["liens"]))

            print("\nIMAGES :")
            for image in resultat["images"]:
                print(image["src"] or image["data_src"])

            print("\nFichier créé :", fichier)

    finally:
        context.close()