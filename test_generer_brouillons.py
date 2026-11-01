import json
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from generer_brouillons import (
    calculer_prix_tnd,
    formater_prix_tnd,
    generer_annonce,
    preparer_fichiers,
    preparer_vehicules,
)


class PreparationBrouillonsTests(unittest.TestCase):
    def test_formule_preserve_les_demi_dinars(self):
        prix = calculer_prix_tnd(14101)

        self.assertEqual(prix, Decimal("89853.5"))
        self.assertEqual(formater_prix_tnd(prix), "89 853,5")

    def test_json_preserve_les_decimales_exactes(self):
        vehicule = {
            "reference": "A-0",
            "prix_type": "prix_fixe",
            "prix_achat_eur": "14100.10",
        }

        prepare = preparer_vehicules([vehicule])[0]

        self.assertEqual(prepare["prix_tnd_indicatif"], "89850.35")

    def test_offre_sans_prix_fixe_reste_sur_demande(self):
        vehicule = {
            "reference": "A-1",
            "prix_type": "offre_ou_non_renseigne",
            "prix_achat_eur": None,
        }

        prepare = preparer_vehicules([vehicule])[0]

        self.assertIsNone(prepare["prix_tnd_indicatif"])
        self.assertEqual(prepare["prix_tnd_libelle"], "Prix sur demande")
        annonce = generer_annonce(prepare)
        self.assertIn("Prix fournisseur fixe non disponible", annonce)
        self.assertNotIn("Prix indicatif calculé selon la formule", annonce)

    def test_limite_les_photos_a_huit_et_marque_disponibilite_non_verifiee(self):
        vehicule = {
            "reference": "A-2",
            "prix_type": "prix_fixe",
            "prix_achat_eur": 14100,
            "photos": [f"https://photos.example/{index}.jpg" for index in range(10)],
        }

        prepare = preparer_vehicules([vehicule])[0]

        self.assertEqual(len(prepare["photos"]), 8)
        self.assertEqual(prepare["prix_tnd_indicatif"], 89850)
        self.assertFalse(prepare["disponibilite_verifiee"])

    def test_refuse_les_doublons(self):
        vehicules = [{"reference": "A-3"}, {"reference": "A-3"}]

        with self.assertRaisesRegex(ValueError, "doublon"):
            preparer_vehicules(vehicules)

    def test_genere_catalogue_et_brouillon_sans_publier(self):
        vehicule = {
            "reference": "A-4",
            "designation": "Berline",
            "mise_en_circulation": "01/2024",
            "kilometrage": 12000,
            "puissance_ch": 100,
            "pays": "France",
            "prix_type": "prix_fixe",
            "prix_achat_eur": 14100,
            "photos": ["https://photos.example/1.jpg"],
        }

        with tempfile.TemporaryDirectory() as temporaire:
            dossier = Path(temporaire)
            source = dossier / "source.json"
            sortie = dossier / "sortie"
            source.write_text(json.dumps([vehicule]), encoding="utf-8")

            prepares, catalogue = preparer_fichiers(source, sortie)
            annonce = (sortie / "A-4.txt").read_text(encoding="utf-8")
            catalogue_json = json.loads(catalogue.read_text(encoding="utf-8"))

        self.assertEqual(len(prepares), 1)
        self.assertEqual(catalogue_json[0]["prix_tnd_indicatif"], 89850)
        self.assertIn("Prix : 89 850 TND (indicatif)", annonce)
        self.assertIn("Disponibilité et caractéristiques à confirmer.", annonce)
        self.assertIn("https://photos.example/1.jpg", annonce)
        self.assertIn("droits d'utilisation à confirmer", annonce)


if __name__ == "__main__":
    unittest.main()