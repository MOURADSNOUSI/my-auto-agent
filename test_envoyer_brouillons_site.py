import io
import json
import tempfile
import unittest
import unittest.mock
import urllib.error
from datetime import datetime, timedelta, timezone
from pathlib import Path

from envoyer_brouillons_site import appeler_outil, construire_brouillons, main

MAINTENANT = datetime(2026, 11, 27, tzinfo=timezone.utc)


def lot_valide(**modifications):
    lot = {
        "reference": "7750872",
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
        "url_source": "https://fr.ecarstrade.com/cars/7750872",
        "statut_vente": "open",
        "fin_vente": (MAINTENANT + timedelta(days=1)).isoformat(),
        "photos_autorisees": [f"https://example.com/photo-{index}.jpg" for index in range(10)],
    }
    lot.update(modifications)
    return lot


class FausseReponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def faux_site(resultat, erreur=False):
    requetes = []

    def ouvrir(requete, timeout):
        requetes.append(requete)
        texte = resultat if erreur else json.dumps(resultat)
        corps = {"jsonrpc": "2.0", "id": 1, "result": {"content": [{"type": "text", "text": texte}], **({"isError": True} if erreur else {})}}
        return FausseReponse(json.dumps(corps).encode())

    return ouvrir, requetes


class ConstruireBrouillonsTests(unittest.TestCase):
    def test_lot_approuve_devient_un_brouillon_en_vente_directe(self):
        brouillons, ecartes = construire_brouillons({"lots": [lot_valide()]}, MAINTENANT)
        self.assertEqual(ecartes, [])
        brouillon = brouillons[0]
        self.assertEqual((brouillon["source"], brouillon["numero"]), ("ecarstrade", "7750872"))
        champs = brouillon["champs"]
        self.assertEqual((champs["make"], champs["model"], champs["status"], champs["indicativePriceTnd"], champs["prixEur"]),
                         ("BMW", "X3", "stock", 89850, 14100))
        self.assertEqual(len(champs["photos"]), 8)
        self.assertNotIn("endsAt", champs)

    def test_lot_non_approuve_ignore_sans_motif(self):
        self.assertEqual(construire_brouillons({"lots": [lot_valide(publication_approuvee=False)]}, MAINTENANT), ([], []))

    def test_motifs_de_refus(self):
        lots = [
            lot_valide(reference="1", disponibilite_verifiee=False),
            lot_valide(reference="2", url_source="http://exemple.com"),
            lot_valide(reference="3", fin_vente="2026-11-01T15:00:00Z"),
            lot_valide(reference="../4"),
            lot_valide(reference="5", photos_autorisees=["javascript:alert(1)"]),
            lot_valide(reference="6", marque=" "),
        ]
        brouillons, ecartes = construire_brouillons({"lots": lots}, MAINTENANT)
        self.assertEqual(brouillons, [])
        self.assertEqual(len(ecartes), 6)
        self.assertIn("vente terminée", ecartes[2])

    def test_sans_prix_fixe_ni_champs_vides(self):
        champs = construire_brouillons({"lots": [lot_valide(prix_fournisseur_ht_eur=None, pays=None, fin_vente=None)]}, MAINTENANT)[0][0]["champs"]
        self.assertNotIn("indicativePriceTnd", champs)
        self.assertNotIn("country", champs)

    def test_doublon_ecarte(self):
        brouillons, ecartes = construire_brouillons({"lots": [lot_valide(), lot_valide()]}, MAINTENANT)
        self.assertEqual((len(brouillons), len(ecartes)), (1, 1))


class AppelSiteTests(unittest.TestCase):
    def test_appel_outil_avec_jeton(self):
        ouvrir, requetes = faux_site({"reference": "EC-7750872", "created": True})
        arguments = {"source": "ecarstrade", "numero": "7750872", "champs": {}}
        self.assertEqual(appeler_outil("https://site.test/mcp", "j" * 40, arguments, ouvrir)["reference"], "EC-7750872")
        corps = json.loads(requetes[0].data)
        self.assertEqual((corps["method"], corps["params"]["name"], corps["params"]["arguments"]), ("tools/call", "importer_brouillon", arguments))
        self.assertEqual(requetes[0].get_header("Authorization"), "Bearer " + "j" * 40)

    def test_erreur_metier_remontee(self):
        ouvrir, _ = faux_site("L'agent local n'a accès qu'aux outils en lecture.", erreur=True)
        with self.assertRaisesRegex(RuntimeError, "lecture"):
            appeler_outil("https://site.test/mcp", "j" * 40, {}, ouvrir)

    def test_jeton_refuse(self):
        def ouvrir(requete, timeout):
            raise urllib.error.HTTPError(requete.full_url, 401, "Unauthorized", {}, None)
        with self.assertRaisesRegex(RuntimeError, "401"):
            appeler_outil("https://site.test/mcp", "j" * 40, {}, ouvrir)

    def test_apercu_par_defaut_et_jeton_obligatoire(self):
        with tempfile.TemporaryDirectory() as dossier:
            source = Path(dossier) / "lots.json"
            source.write_text(json.dumps({"lots": [lot_valide(fin_vente=None)]}), encoding="utf-8")
            self.assertEqual(main(["--source", str(source)]), 0)
            with unittest.mock.patch.dict("os.environ", {"MYAUTO_AGENT_TOKEN": ""}), self.assertRaises(SystemExit):
                main(["--source", str(source), "--envoyer"])


if __name__ == "__main__":
    unittest.main()
