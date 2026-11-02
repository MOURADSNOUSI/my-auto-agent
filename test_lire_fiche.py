import unittest

from ecarstrade import lire_fiche

FICHE_HILUX = (
    "Toyota Hilux pick up 2.8 diesel 204pk AT AWD MHEV DC Invincible + ACCESSORIES\n"
    "#7523309 - Toyota Hilux\n"
    "3j 12h 26m 13s\n"
    "04 nov. 2026, 14:40\n"
    "07/2026\n"
    "4x4\n"
    "18 KM\n"
    "Diesel , 2755 cc\n"
    "204 Hp (150 kW)\n"
    "TVA non incluse\n"
    "Belgique\n"
    "ACHETER 49600€"
)


class LireFicheTests(unittest.TestCase):
    def test_kilometrage_ne_deborde_pas_sur_la_ligne_precedente(self):
        fiche = lire_fiche(FICHE_HILUX)

        self.assertEqual(fiche["kilometrage"], 18)

    def test_extrait_les_caracteristiques(self):
        fiche = lire_fiche(FICHE_HILUX)

        self.assertEqual(fiche["designation"], FICHE_HILUX.splitlines()[0])
        self.assertEqual(fiche["mise_en_circulation"], "07/2026")
        self.assertEqual(fiche["puissance_ch"], 204)
        self.assertEqual(fiche["pays"], "Belgique")
        self.assertEqual(fiche["prix_achat_eur"], 49600)
        self.assertTrue(fiche["tva_non_incluse"])

    def test_separateurs_de_milliers(self):
        fiche = lire_fiche("Porsche\n2024\n21 632 KM\nACHETER 14 100 €")

        self.assertEqual(fiche["kilometrage"], 21632)
        self.assertEqual(fiche["prix_achat_eur"], 14100)

    def test_offre_sans_prix_ni_pays(self):
        fiche = lire_fiche("Volvo XC60\n#7778590\n85 433 KM\nFAIRE UNE OFFRE")

        self.assertIsNone(fiche["prix_achat_eur"])
        self.assertIsNone(fiche["pays"])
        self.assertFalse(fiche["tva_non_incluse"])

    def test_texte_vide(self):
        self.assertIsNone(lire_fiche("")["designation"])


if __name__ == "__main__":
    unittest.main()
