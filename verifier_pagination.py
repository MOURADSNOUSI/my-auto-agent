from playwright.sync_api import sync_playwright

from ecarstrade import attendre_fiches, references_visibles, session_favoris

with sync_playwright() as p, session_favoris(p) as (context, page):
    attendre_fiches(page)

    page1 = sorted(references_visibles(page))

    print("\nPAGE 1")
    print("URL :", page.url)
    print("Nombre :", len(page1))
    print("Références :", page1)

    input(
        "\nOuvre la page 2 dans Chromium, "
        "puis appuie sur Entrée..."
    )

    page2 = sorted(references_visibles(page))

    print("\nPAGE 2")
    print("URL :", page.url)
    print("Nombre :", len(page2))
    print("Références :", page2)

    print("\nCOMPARAISON")
    print("Références communes :", len(set(page1) & set(page2)))
    print("Uniquement page 1 :", sorted(set(page1) - set(page2)))
    print("Uniquement page 2 :", sorted(set(page2) - set(page1)))
    print("Total unique :", len(set(page1) | set(page2)))
