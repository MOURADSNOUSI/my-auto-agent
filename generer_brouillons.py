import argparse
import json
import re
from decimal import Decimal, InvalidOperation
from pathlib import Path

BASE = Path(__file__).resolve().parent
SOURCE_PAR_DEFAUT = BASE / "vehicules_avec_photos.json"
SORTIE_PAR_DEFAUT = BASE / "preparation"
MAX_PHOTOS = 8


def calculer_prix_tnd(prix_eur):
    if prix_eur is None:
        return None

    if isinstance(prix_eur, bool):
        raise ValueError("Le prix fournisseur doit être un nombre EUR.")

    try:
        montant_eur = Decimal(str(prix_eur))
    except (InvalidOperation, ValueError):
        raise ValueError(f"Prix fournisseur EUR invalide : {prix_eur!r}") from None

    if not montant_eur.is_finite() or montant_eur < 0:
        raise ValueError(f"Prix fournisseur EUR invalide : {prix_eur!r}")

    return (montant_eur + Decimal("3000")) * Decimal("3.5") + Decimal("30000")


def formater_prix_tnd(montant):
    if montant == montant.to_integral_value():
        return f"{int(montant):,}".replace(",", " ")

    partie_entiere, partie_decimale = format(montant, "f").split(".", 1)
    partie_entiere = f"{int(partie_entiere):,}".replace(",", " ")
    return f"{partie_entiere},{partie_decimale}"


def convertir_prix_json(montant):
    if montant is None:
        return None
    if montant == montant.to_integral_value():
        return int(montant)
    return format(montant.normalize(), "f")


def preparer_vehicules(vehicules):
    if not isinstance(vehicules, list):
        raise ValueError("Le JSON source doit contenir une liste de véhicules.")

    references = set()
    prepares = []

    for index, vehicule in enumerate(vehicules, start=1):
        if not isinstance(vehicule, dict):
            raise ValueError(f"L'entrée {index} n'est pas un objet véhicule.")

        reference = str(vehicule.get("reference", "")).strip()
        if not reference or not re.fullmatch(r"[A-Za-z0-9_-]+", reference):
            raise ValueError(f"Référence absente ou invalide à l'entrée {index}.")
        if reference in references:
            raise ValueError(f"Référence en doublon : {reference}.")
        references.add(reference)

        type_prix = vehicule.get("prix_type")
        if type_prix == "prix_fixe":
            cle_prix = "prix_achat_eur" if "prix_achat_eur" in vehicule else "prix_eur"
            prix_eur = vehicule.get(cle_prix)
            prix_tnd = calculer_prix_tnd(prix_eur)
        else:
            prix_tnd = None

        photos = vehicule.get("photos", [])
        if photos is None:
            photos = []
        if not isinstance(photos, list):
            raise ValueError(f"La liste de photos du véhicule {reference} est invalide.")

        photos_autorisees = [
            photo.strip()
            for photo in photos
            if isinstance(photo, str) and photo.strip()
        ][:MAX_PHOTOS]

        vehicule_prepare = dict(vehicule)
        vehicule_prepare["reference"] = reference
        vehicule_prepare["photos"] = photos_autorisees
        vehicule_prepare["prix_tnd_indicatif"] = convertir_prix_json(prix_tnd)
        vehicule_prepare["prix_tnd_libelle"] = (
            f"{formater_prix_tnd(prix_tnd)} TND (indicatif)"
            if prix_tnd is not None
            else "Prix sur demande"
        )
        vehicule_prepare["disponibilite_verifiee"] = False
        vehicule_prepare["statut_preparation"] = "brouillon_a_valider"
        prepares.append(vehicule_prepare)

    return prepares


def formater_valeur(valeur):
    return str(valeur) if valeur is not None else "À confirmer"


def formater_kilometrage(valeur):
    if not isinstance(valeur, int) or isinstance(valeur, bool):
        return "À confirmer"
    return f"{valeur:,}".replace(",", " ")


def generer_annonce(vehicule):
    prix = vehicule["prix_tnd_libelle"]
    mention_prix = (
        "Prix indicatif calculé selon la formule d'export; régime FCR ou dédouané à confirmer."
        if vehicule["prix_tnd_indicatif"] is not None
        else "Prix fournisseur fixe non disponible; régime FCR ou dédouané à confirmer."
    )
    photos = vehicule["photos"]
    texte_photos = (
        "\n".join(f"- {url}" for url in photos)
        if photos
        else "Aucune photo associée."
    )

    return f"""M&Y AUTO EXPORT

{formater_valeur(vehicule.get('designation'))}

Mise en circulation : {formater_valeur(vehicule.get('mise_en_circulation'))}
Kilométrage : {formater_kilometrage(vehicule.get('kilometrage'))} km
Puissance indiquée : {formater_valeur(vehicule.get('puissance_ch'))} ch
Provenance : {formater_valeur(vehicule.get('pays'))}

Prix : {prix}
{mention_prix}

Contact : contact.myautoexport@gmail.com
Référence : {vehicule['reference']}
Disponibilité et caractéristiques à confirmer.

Liens des photos associées (droits d'utilisation à confirmer) :
{texte_photos}
"""


def chemin_depuis_base(chemin):
    chemin = Path(chemin)
    return chemin if chemin.is_absolute() else BASE / chemin


def preparer_fichiers(source, dossier_sortie):
    vehicules = json.loads(source.read_text(encoding="utf-8"))
    prepares = preparer_vehicules(vehicules)

    dossier_sortie.mkdir(parents=True, exist_ok=True)
    catalogue = dossier_sortie / "vehicules_prepares.json"
    catalogue.write_text(
        json.dumps(prepares, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    for vehicule in prepares:
        fichier = dossier_sortie / f"{vehicule['reference']}.txt"
        fichier.write_text(generer_annonce(vehicule), encoding="utf-8")

    return prepares, catalogue


def main():
    parser = argparse.ArgumentParser(
        description="Prépare localement des brouillons et un catalogue JSON; ne publie rien."
    )
    parser.add_argument(
        "--source",
        default=str(SOURCE_PAR_DEFAUT),
        help="JSON de véhicules structurés avec photos."
    )
    parser.add_argument(
        "--sortie",
        default=str(SORTIE_PAR_DEFAUT),
        help="Dossier de sortie des brouillons locaux."
    )
    arguments = parser.parse_args()
    source = chemin_depuis_base(arguments.source)
    dossier_sortie = chemin_depuis_base(arguments.sortie)

    try:
        prepares, catalogue = preparer_fichiers(source, dossier_sortie)
    except (OSError, json.JSONDecodeError, ValueError) as erreur:
        parser.error(f"Préparation interrompue : {erreur}")

    avec_prix = sum(v["prix_tnd_indicatif"] is not None for v in prepares)
    avec_photos = sum(bool(v["photos"]) for v in prepares)
    print(f"Véhicules préparés : {len(prepares)}")
    print(f"Prix TND fixes calculés : {avec_prix}; prix sur demande : {len(prepares) - avec_prix}")
    print(f"Véhicules avec photos associées : {avec_photos}")
    print(f"Catalogue local : {catalogue}")
    print(f"Brouillons locaux : {dossier_sortie}")
    print("Disponibilité à confirmer. Aucune publication, modification Wix ou envoi Gmail effectué.")


if __name__ == "__main__":
    main()