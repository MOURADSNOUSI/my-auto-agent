import json
import re
from pathlib import Path
from urllib.parse import urljoin

BASE = Path(__file__).resolve().parent

source_images = BASE / "galerie_7750872.json"
source_vehicules = BASE / "vehicules_20_structures.json"
destination = BASE / "vehicules_avec_photos.json"

galerie = json.loads(source_images.read_text(encoding="utf-8"))
vehicules = json.loads(source_vehicules.read_text(encoding="utf-8"))

# Regroupe les images par référence et numéro de photo.
photos = {}

pattern = re.compile(
    r"/carsphotos/[^/]+/(\d+)/"
    r"(photo_\d+)/(\d+)x0__r\.jpg",
    re.IGNORECASE
)

for adresse in galerie["images"]:
    url = urljoin("https://fr.ecarstrade.com/", adresse)

    match = pattern.search(url)
    if not match:
        continue

    reference, numero_photo, largeur = match.groups()
    largeur = int(largeur)
    photos_reference = photos.setdefault(reference, {})
    photo_existante = photos_reference.get(numero_photo)

    if photo_existante is None or largeur > photo_existante[0]:
        photos_reference[numero_photo] = (largeur, url)

vehicules_avec_photos = []
for vehicule in vehicules:
    vehicule_avec_photos = dict(vehicule)
    reference = str(vehicule.get("reference", ""))
    photos_vehicule = photos.get(reference, {})
    vehicule_avec_photos["photos"] = [
        url
        for _, (_, url) in sorted(photos_vehicule.items())
    ]
    vehicules_avec_photos.append(vehicule_avec_photos)

destination.write_text(
    json.dumps(vehicules_avec_photos, ensure_ascii=False, indent=2),
    encoding="utf-8"
)

vehicules_avec_images = sum(bool(vehicule["photos"]) for vehicule in vehicules_avec_photos)
print(
    f"Association terminée : {len(vehicules_avec_photos)} véhicules, "
    f"{vehicules_avec_images} avec photos."
)
print(f"Fichier créé : {destination}")

for vehicule in vehicules_avec_photos[:3]:
    print(
        f"{vehicule.get('reference', 'sans référence')} - "
        f"{vehicule.get('designation', 'sans désignation')} : "
        f"{len(vehicule['photos'])} photo(s)"
    )