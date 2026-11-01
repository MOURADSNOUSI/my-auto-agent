# my-auto-agent

Automatisation locale de préparation d'annonces et d'export catalogue pour lots automobiles.

## Objectif

Ce dépôt sert à :
- extraire des données depuis eCarsTrade (session utilisateur locale),
- structurer les véhicules,
- préparer des brouillons textuels et un catalogue JSON local,
- exporter uniquement des lots approuvés vers un fichier de catalogue statique.

Aucun script ne fait de `git commit`, de `git push` ou de déploiement automatique.

## Pré-requis

- Python 3.10+
- Dépendances Python nécessaires (notamment Playwright pour les scripts navigateur)
- Session Chromium persistante locale pour eCarsTrade : `~/.my-auto-agent-browser`

## Vue d'ensemble du flux

1. Inventaire favoris eCarsTrade : `inventaire_favoris.py` -> `inventaire_favoris.json`
2. Extraction des fiches : `extraire_20_vehicules.py` -> `vehicules_20_bruts.json`
3. Structuration : `structurer_20_vehicules.py` -> `vehicules_20_structures.json`
4. Association photos : `associer_photos.py` -> `vehicules_avec_photos.json`
5. Préparation brouillons : `generer_brouillons.py` -> `preparation/vehicules_prepares.json` + `preparation/*.txt`
6. Validation manuelle des lots : `preparation/lots_valides.json`
7. Export site statique : `publier_catalogue_site.py` -> `../my-auto-export-site/my-auto-export/lots.json`

## Commandes locales principales

```bash
python3 generer_brouillons.py
python3 publier_catalogue_site.py
```

Exemples avec paramètres explicites :

```bash
python3 generer_brouillons.py --source vehicules_avec_photos.json --sortie preparation
python3 publier_catalogue_site.py --source preparation/lots_valides.json --sortie ../my-auto-export-site/my-auto-export/lots.json
```

## Contrôles métier déjà implémentés

- Références véhicule/lot valides et sans doublon sur les entrées approuvées
- Validation des URLs HTTPS
- Limite d'export à 8 photos par véhicule/lot
- Prix TND indicatif calculé depuis le prix fournisseur fixe
- `Prix sur demande` si prix fixe absent
- Pour `statut_vente=open`, `fin_vente` ISO 8601 avec fuseau et date future obligatoire
- Export limité aux lots avec `publication_approuvee=true` et `disponibilite_verifiee=true`

## Tests existants

Exécuter les tests unitaires présents :

```bash
python3 -m unittest -v test_generer_brouillons.py test_publier_catalogue_site.py test_extraction.py test_ecarstrade.py
```

## Documentation complémentaire

- Contrat des lots exportables : `preparation/CONTRAT_LOTS_SITE.md`
