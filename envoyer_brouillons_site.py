"""Envoie les lots validés (preparation/lots_valides.json) au site M&Y AUTO EXPORT, en brouillons non publiés.

Remplace l'export vers lots.json, que le site n'affiche plus depuis la refonte du catalogue. Chaque lot approuvé devient
un brouillon de référence EC-<numéro> via l'outil MCP « importer_brouillon » du site. Un brouillon déjà présent n'est
jamais modifié. La mise en ligne reste une décision manuelle dans /admin (rubrique Retirés, « Remettre en ligne »).

Par défaut, le script n'envoie rien et affiche ce qu'il enverrait. Avec --envoyer, il lit le jeton de l'agent dans la
variable d'environnement MYAUTO_AGENT_TOKEN (même valeur que le secret AGENT_TOKEN du Worker). Le réglage
« Écriture autorisée à l'agent » doit être activé dans /admin.
"""
import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from generer_brouillons import calculer_prix_tnd, convertir_prix_json
from publier_catalogue_site import MAX_PHOTOS, est_url_https

BASE = Path(__file__).resolve().parent
SOURCE_PAR_DEFAUT = BASE / "preparation" / "lots_valides.json"
URL_PAR_DEFAUT = "https://www.myautoexport.com/mcp"
VARIABLE_JETON = "MYAUTO_AGENT_TOKEN"
DELAI_SECONDES = 30


def valider_brouillon(lot, maintenant):
    """Renvoie (numero, champs) pour un lot approuvé, ou lève ValueError avec le motif du refus."""
    numero = str(lot.get("reference", "")).strip()
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,30}", numero):
        raise ValueError("Référence absente ou invalide.")
    for champ in ("marque", "modele"):
        if not isinstance(lot.get(champ), str) or not lot[champ].strip():
            raise ValueError(f"{numero}: champ {champ} obligatoire.")
    if lot.get("disponibilite_verifiee") is not True:
        raise ValueError(f"{numero}: disponibilité non vérifiée.")
    if not est_url_https(lot.get("url_source")):
        raise ValueError(f"{numero}: URL source HTTPS obligatoire.")
    photos = lot.get("photos_autorisees", [])
    if not isinstance(photos, list) or any(not est_url_https(photo) for photo in photos):
        raise ValueError(f"{numero}: photos_autorisees doit être une liste d'URL HTTPS.")
    fin_vente = lot.get("fin_vente")
    if isinstance(fin_vente, str) and fin_vente.strip():
        try:
            echeance = datetime.fromisoformat(fin_vente.replace("Z", "+00:00"))
        except ValueError:
            raise ValueError(f"{numero}: fin_vente doit être une date ISO 8601.") from None
        if echeance.tzinfo is None:
            raise ValueError(f"{numero}: fin_vente doit inclure un fuseau horaire.")
        if echeance <= maintenant:
            raise ValueError(f"{numero}: vente terminée chez la source ({fin_vente}).")

    prix_eur = lot.get("prix_fournisseur_ht_eur")
    champs = {
        "make": lot["marque"].strip(),
        "model": lot["modele"].strip(),
        "trim": lot.get("version"),
        "bodyType": lot.get("categorie"),
        "year": lot.get("annee"),
        "mileageKm": lot.get("kilometrage"),
        "fuel": lot.get("motorisation"),
        "country": lot.get("pays"),
        "prixEur": prix_eur,
        "indicativePriceTnd": convertir_prix_json(calculer_prix_tnd(prix_eur)) if prix_eur is not None else None,
        # Le site vend sur offre ou sur mandat (enchères désactivées) : le brouillon est une vente directe.
        "status": "stock",
        "sourceUrl": lot["url_source"].strip(),
        "photos": [url.strip() for url in photos[:MAX_PHOTOS]],
    }
    return numero, {cle: valeur for cle, valeur in champs.items() if valeur not in (None, "")}


def construire_brouillons(donnees, maintenant=None):
    """Lots approuvés prêts à l'envoi, et lots écartés avec leur motif. Un lot non approuvé est ignoré sans motif."""
    if not isinstance(donnees, dict) or not isinstance(donnees.get("lots"), list):
        raise ValueError("La source doit contenir une liste 'lots'.")
    maintenant = maintenant or datetime.now(timezone.utc)
    brouillons, ecartes, vus = [], [], set()
    for lot in donnees["lots"]:
        if not isinstance(lot, dict) or lot.get("publication_approuvee") is not True:
            continue
        try:
            numero, champs = valider_brouillon(lot, maintenant)
        except ValueError as erreur:
            ecartes.append(str(erreur))
            continue
        if numero in vus:
            ecartes.append(f"{numero}: référence en doublon.")
            continue
        vus.add(numero)
        brouillons.append({"source": "ecarstrade", "numero": numero, "champs": champs})
    return brouillons, ecartes


def appeler_outil(url, jeton, arguments, ouvrir=urllib.request.urlopen):
    """Appelle l'outil MCP importer_brouillon ; renvoie le résultat décodé ou lève RuntimeError avec le message du site."""
    corps = {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "importer_brouillon", "arguments": arguments}}
    requete = urllib.request.Request(url, data=json.dumps(corps).encode(), method="POST", headers={
        "Authorization": f"Bearer {jeton}", "Content-Type": "application/json", "Accept": "application/json"})
    try:
        with ouvrir(requete, timeout=DELAI_SECONDES) as reponse:
            message = json.loads(reponse.read())
    except urllib.error.HTTPError as erreur:
        raise RuntimeError(f"le site a répondu {erreur.code} (jeton refusé ou adresse incorrecte)") from None
    if "error" in message:
        raise RuntimeError(message["error"].get("message", "erreur du serveur MCP"))
    resultat = message["result"]
    texte = resultat["content"][0]["text"]
    if resultat.get("isError"):
        raise RuntimeError(texte)
    return json.loads(texte)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Envoie les lots validés au site en brouillons non publiés.")
    parser.add_argument("--source", type=Path, default=SOURCE_PAR_DEFAUT)
    parser.add_argument("--url", default=URL_PAR_DEFAUT, help="Adresse du serveur MCP du site.")
    parser.add_argument("--envoyer", action="store_true", help="Envoyer réellement (sinon simple aperçu).")
    arguments = parser.parse_args(argv)

    try:
        brouillons, ecartes = construire_brouillons(json.loads(arguments.source.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError, ValueError) as erreur:
        parser.error(f"Lecture impossible : {erreur}")

    for motif in ecartes:
        print(f"Écarté : {motif}")
    if not arguments.envoyer:
        for brouillon in brouillons:
            champs = brouillon["champs"]
            print(f"À envoyer : EC-{brouillon['numero']} {champs['make']} {champs['model']} "
                  f"({champs.get('year', '?')}, {len(champs.get('photos', []))} photos)")
        print(f"{len(brouillons)} brouillon(s) prêt(s). Aperçu seulement : relancer avec --envoyer pour les créer sur le site.")
        return 0

    jeton = os.environ.get(VARIABLE_JETON, "")
    if len(jeton) < 32:
        parser.error(f"Définir la variable {VARIABLE_JETON} (jeton de l'agent, 32 caractères au moins).")
    echecs = 0
    for brouillon in brouillons:
        try:
            resultat = appeler_outil(arguments.url, jeton, brouillon)
        except (RuntimeError, OSError) as erreur:
            echecs += 1
            print(f"Échec : EC-{brouillon['numero']} : {erreur}")
            continue
        etat = "créé" if resultat.get("created") else "déjà présent, inchangé"
        print(f"{resultat['reference']} : brouillon {etat}")
    print(f"Terminé : {len(brouillons) - echecs} envoyé(s), {echecs} échec(s). À relire et publier dans /admin.")
    return 1 if echecs else 0


if __name__ == "__main__":
    sys.exit(main())
