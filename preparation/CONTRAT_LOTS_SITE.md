# Contrat des lots du site

`lots_valides.json` est le fichier de validation interne. Un lot ne peut être exporté que si `publication_approuvee` et `disponibilite_verifiee` valent tous deux `true`.

Champs requis :
- `reference`, `marque`, `modele`
- `publication_approuvee`: approbation manuelle individuelle
- `disponibilite_verifiee`: contrôle récent auprès de la source
- `url_source`: URL HTTPS de la fiche fournisseur
- `statut_vente`: `open` ou `upcoming`
- `fin_vente`: date ISO 8601 avec fuseau obligatoire pour `open`
- `photos_autorisees`: liste d'URL HTTPS dont la réutilisation est autorisée; maximum 8 exportées

Champs facultatifs : `version`, `categorie`, `annee`, `kilometrage`, `motorisation`, `pays`, `prix_fournisseur_ht_eur` et `fin_vente` pour les ventes à venir.

Le prix TND est calculé par l'exporteur depuis le prix fournisseur fixe. Sans prix fixe, le site affiche « Prix sur demande ». Ne pas saisir un prix TND dédouané déduit.

Lancer depuis `my-auto-agent` :

```bash
python3 publier_catalogue_site.py
```

Le script met à jour `../my-auto-export-site/my-auto-export/lots.json` : les lots approuvés sont ajoutés ou remplacent le lot de même référence, les autres lots du site (ajoutés par `ajouter_lot.py` ou `importer_wix.py`) sont conservés. Pour retirer un lot du site, supprime son entrée dans `lots.json`. Il ne commit, ne pousse et ne déploie rien. Un push GitHub peut déclencher Cloudflare Pages; il exige une confirmation distincte.