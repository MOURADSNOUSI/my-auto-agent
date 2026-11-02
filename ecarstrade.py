import re
from contextlib import contextmanager
from pathlib import Path

URL_FAVORIS = "https://fr.ecarstrade.com/profile/selections"

# Profil Chromium conservé sur ton ordinateur : la connexion manuelle y reste mémorisée.
PROFIL = str(Path.home() / ".my-auto-agent-browser")

MOTIF_REFERENCE = re.compile(r"#(\d{6,9})\b")
PAYS = ["France", "Belgique", "Allemagne"]

# Séparateurs de milliers possibles, sans jamais franchir un saut de ligne.
CHIFFRES = r"\d[\d   ]*"

# Remonte depuis l'élément jusqu'au plus petit bloc qui ne contient qu'une seule fiche.
JS_FICHE = """
element => {
    let parent = element;

    for (let i = 0; i < 12 && parent; i++) {
        const texte = parent.innerText || "";

        const references = [
            ...texte.matchAll(/#\\d{6,9}\\b/g)
        ].map(x => x[0]);

        if (
            texte.length >= 80 &&
            texte.length <= 2000 &&
            /\\bKM\\b/i.test(texte) &&
            new Set(references).size === 1
        ) {
            return {
                texte: texte.trim(),
                images: [...parent.querySelectorAll("img")].map(img => ({
                    src: img.currentSrc || img.src || null,
                    data_src: img.getAttribute("data-src"),
                    srcset: img.getAttribute("srcset"),
                    alt: img.alt
                })),
                liens: [...parent.querySelectorAll("a[href]")].map(a => ({
                    texte: (a.innerText || "").trim(),
                    href: a.href
                }))
            };
        }

        parent = parent.parentElement;
    }

    return null;
}
"""


@contextmanager
def session_favoris(playwright, connexion_manuelle=False, **options):
    """Ouvre les favoris dans le profil persistant et rend (context, page) connectés."""
    context = playwright.chromium.launch_persistent_context(
        user_data_dir=PROFIL,
        headless=False,
        **options
    )

    try:
        page = context.pages[0] if context.pages else context.new_page()
        page.goto(URL_FAVORIS, wait_until="domcontentloaded", timeout=30000)

        if "/login" in page.url and connexion_manuelle:
            print("Première connexion nécessaire.")
            print("Connecte-toi dans Chromium.")
            input("Une fois connecté, appuie sur Entrée...")
            page.goto(URL_FAVORIS, wait_until="domcontentloaded")

        if "/login" in page.url:
            raise RuntimeError("Connexion eCarsTrade nécessaire.")

        yield context, page

    finally:
        context.close()


def attendre_fiches(page):
    page.get_by_text(MOTIF_REFERENCE).first.wait_for(timeout=15000)


def references_visibles(page):
    """Références de la page, dans l'ordre d'affichage et sans doublon."""
    texte = page.locator("body").inner_text()
    return list(dict.fromkeys(MOTIF_REFERENCE.findall(texte)))


def localiser_reference(page, reference):
    return page.get_by_text(re.compile(rf"#{re.escape(reference)}\b")).first


def _nombre(motif, texte):
    resultat = re.search(motif, texte, re.IGNORECASE | re.MULTILINE)
    return int(re.sub(r"\D", "", resultat.group(1))) if resultat else None


def lire_fiche(texte):
    """Extrait les caractéristiques du texte brut d'une fiche eCarsTrade."""
    lignes = [ligne.strip() for ligne in texte.splitlines() if ligne.strip()]
    date = re.search(r"\b(\d{2}/\d{4})\b", texte)

    return {
        "designation": lignes[0] if lignes else None,
        "mise_en_circulation": date.group(1) if date else None,
        # Le kilométrage occupe sa propre ligne : « 21 632 KM ».
        "kilometrage": _nombre(rf"^[ \t]*({CHIFFRES}?)[ \t ]*KM[ \t]*$", texte),
        "puissance_ch": _nombre(r"\b(\d+)\s*Hp\b", texte),
        "pays": next(
            (
                pays for pays in PAYS
                if re.search(rf"(?mi)^{re.escape(pays)}\s*$", texte)
            ),
            None
        ),
        "prix_achat_eur": _nombre(rf"ACHETER\s*({CHIFFRES}?)\s*€", texte),
        "tva_non_incluse": "TVA non incluse" in texte,
    }
