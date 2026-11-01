import argparse
import json
import re
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from urllib.parse import urlparse

from generer_brouillons import calculer_prix_tnd, convertir_prix_json

BASE = Path(__file__).resolve().parent
SOURCE_PAR_DEFAUT = BASE / "preparation" / "lots_valides.json"
SORTIE_PAR_DEFAUT = BASE.parent / "my-auto-export-site" / "my-auto-export" / "lots.json"
MAX_PHOTOS = 8
STATUTS_PUBLICABLES = {"open", "upcoming"}


def est_url_https(valeur):
    if not isinstance(valeur, str):
        return False
    url = urlparse(valeur.strip())
    return url.scheme == "https" and bool(url.netloc)


def valider_lot(lot):
    reference = str(lot.get("reference", "")).strip()
    if not re.fullmatch(r"[A-Za-z0-9_-]+", reference):
        raise ValueError("Référence absente ou invalide.")

    for champ in ("marque", "modele"):
        if not isinstance(lot.get(champ), str) or not lot[champ].strip():
            raise ValueError(f"{reference}: champ {champ} obligatoire.")

    if lot.get("publication_approuvee") is not True:
        raise ValueError(f"{reference}: approbation de publication manquante.")
    if lot.get("disponibilite_verifiee") is not True:
        raise ValueError(f"{reference}: disponibilité non vérifiée.")
    if not est_url_https(lot.get("url_source")):
        raise ValueError(f"{reference}: URL source HTTPS obligatoire.")

    statut = lot.get("statut_vente")
    if statut not in STATUTS_PUBLICABLES:
        raise ValueError(f"{reference}: statut de vente non publiable.")
    fin_vente = lot.get("fin_vente")
    if statut == "open":
        if not isinstance(fin_vente, str) or not fin_vente.strip():
            raise ValueError(f"{reference}: fin_vente obligatoire pour une vente ouverte.")
        try:
            echeance = datetime.fromisoformat(fin_vente.replace("Z", "+00:00"))
        except ValueError:
            raise ValueError(f"{reference}: fin_vente doit être une date ISO 8601.") from None
        if echeance.tzinfo is None:
            raise ValueError(f"{reference}: fin_vente doit inclure un fuseau horaire.")
        if echeance <= datetime.now(echeance.tzinfo):
            raise ValueError(f"{reference}: fin_vente doit être dans le futur.")

    photos = lot.get("photos_autorisees", [])
    if not isinstance(photos, list):
        raise ValueError(f"{reference}: photos_autorisees doit être une liste.")
    if any(not est_url_https(photo) for photo in photos):
        raise ValueError(f"{reference}: chaque photo autorisée doit avoir une URL HTTPS.")

    return reference


def construire_catalogue(donnees):
    if not isinstance(donnees, dict) or not isinstance(donnees.get("lots"), list):
        raise ValueError("La source doit contenir une liste 'lots'.")

    catalogue = []
    references = set()
    for lot in donnees["lots"]:
        if not isinstance(lot, dict):
            raise ValueError("Chaque lot doit être un objet JSON.")
        if lot.get("publication_approuvee") is not True:
            continue

        reference = valider_lot(lot)
        if reference in references:
            raise ValueError(f"Référence approuvée en doublon : {reference}.")
        references.add(reference)

        prix_eur = lot.get("prix_fournisseur_ht_eur")
        prix_tnd = calculer_prix_tnd(prix_eur) if prix_eur is not None else None
        catalogue.append({
            "reference": reference,
            "make": lot["marque"].strip(),
            "model": lot["modele"].strip(),
            "trim": lot.get("version") or "",
            "bodyType": lot.get("categorie"),
            "year": lot.get("annee"),
            "mileageKm": lot.get("kilometrage"),
            "fuel": lot.get("motorisation"),
            "country": lot.get("pays"),
            "indicativePriceTnd": convertir_prix_json(prix_tnd),
            "priceLabel": "Prix sur demande" if prix_tnd is None else "Prix indicatif",
            "status": lot["statut_vente"],
            "endsAt": fin_vente if (fin_vente := lot.get("fin_vente")) else None,
            "sourceUrl": lot["url_source"].strip(),
            "photos": [
                {"url": url.strip(), "authorized": True}
                for url in lot.get("photos_autorisees", [])[:MAX_PHOTOS]
            ],
        })

    return catalogue


def exporter(source, sortie):
    donnees = json.loads(source.read_text(encoding="utf-8"))
    catalogue = construire_catalogue(donnees)
    sortie.parent.mkdir(parents=True, exist_ok=True)
    sortie.write_text(
        json.dumps(catalogue, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8"
    )
    return catalogue


def main():
    parser = argparse.ArgumentParser(
        description="Exporte les lots approuvés vers le catalogue statique du site; ne commit ni ne déploie."
    )
    parser.add_argument("--source", type=Path, default=SOURCE_PAR_DEFAUT)
    parser.add_argument("--sortie", type=Path, default=SORTIE_PAR_DEFAUT)
    arguments = parser.parse_args()

    try:
        catalogue = exporter(arguments.source, arguments.sortie)
    except (OSError, json.JSONDecodeError, ValueError) as erreur:
        parser.error(f"Export interrompu : {erreur}")

    print(f"Lots exportés : {len(catalogue)}")
    print(f"Catalogue local : {arguments.sortie}")
    print("Aucun commit, push ou déploiement effectué.")


if __name__ == "__main__":
    main()