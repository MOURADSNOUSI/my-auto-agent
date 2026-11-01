import unittest
from datetime import datetime, timedelta, timezone

from publier_catalogue_site import construire_catalogue


def lot_valide(**modifications):
    lot = {
        "reference": "LOT-1",
        "marque": "BMW",
        "modele": "X3",
        "version": "xDrive",
        "annee": 2022,
        "kilometrage": 45000,
        "motorisation": "Hybride",
        "pays": "France",
        "prix_fournisseur_ht_eur": 14100,
        "publication_approuvee": True,
        "disponibilite_verifiee": True,
        "url_source": "https://example.com/lot/LOT-1",
        "statut_vente": "open",
        "fin_vente": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
        "photos_autorisees": [f"https://example.com/photo-{index}.jpg" for index in range(10)],
    }
    lot.update(modifications)
    return lot


class CatalogueSiteTests(unittest.TestCase):
    def test_catalogue_vide_sans_lots_valides(self):
        self.assertEqual(construire_catalogue({"lots": []}), [])

    def test_ignore_un_lot_non_approuve(self):
        lot = lot_valide(publication_approuvee=False)

        self.assertEqual(construire_catalogue({"lots": [lot]}), [])

    def test_exige_disponibilite_et_url_source(self):
        with self.assertRaisesRegex(ValueError, "disponibilité"):
            construire_catalogue({"lots": [lot_valide(disponibilite_verifiee=False)]})
        with self.assertRaisesRegex(ValueError, "URL source"):
            construire_catalogue({"lots": [lot_valide(url_source="javascript:void(0)")]})

    def test_calcul_prix_photos_autorisees_et_limite_de_huit(self):
        catalogue = construire_catalogue({"lots": [lot_valide()]})
        exported = catalogue[0]

        self.assertEqual(exported["indicativePriceTnd"], 89850)
        self.assertEqual(len(exported["photos"]), 8)
        self.assertTrue(all(photo["authorized"] for photo in exported["photos"]))
        self.assertEqual(exported["sourceUrl"], "https://example.com/lot/LOT-1")

    def test_prix_sur_demande_si_prix_fixe_absent(self):
        exported = construire_catalogue({
            "lots": [lot_valide(prix_fournisseur_ht_eur=None)]
        })[0]

        self.assertIsNone(exported["indicativePriceTnd"])
        self.assertEqual(exported["priceLabel"], "Prix sur demande")

    def test_refuse_doublons_approuves(self):
        first = lot_valide()
        second = lot_valide()

        with self.assertRaisesRegex(ValueError, "doublon"):
            construire_catalogue({"lots": [first, second]})

    def test_vente_ouverte_exige_date_fuseau_horaire(self):
        with self.assertRaisesRegex(ValueError, "fuseau horaire"):
            construire_catalogue({"lots": [lot_valide(fin_vente="2030-01-01T10:00:00")]})

    def test_vente_ouverte_refusee_si_deja_echue(self):
        expired = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()

        with self.assertRaisesRegex(ValueError, "dans le futur"):
            construire_catalogue({"lots": [lot_valide(fin_vente=expired)]})


if __name__ == "__main__":
    unittest.main()