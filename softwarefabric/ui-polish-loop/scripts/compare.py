"""Vorher/Nachher-Vergleich zweier Screenshot-Runden mit rot markierten Änderungen.

    python3 compare.py <vorher-ordner> <nachher-ordner> <ausgabeordner>

Benötigt Pillow und NumPy. Schreibt für jedes Paar mit Änderungen ein Bild
`<name>-vergleich.png` (links vorher, rechts nachher, gleiche Rahmen auf
beiden Seiten) und gibt je Screenshot die Zahl markierter Bereiche aus.
Verschiebt sich ein ganzer Block, entstehen große Rahmen: Sie zeigen, wo sich
etwas geändert hat, nicht jede Einzeländerung.
"""
import os
import sys
from collections import deque

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ZELLE = 12        # Rastergröße in Bildpixeln
SCHWELLE = 18     # mittlere Farbabweichung je Zelle, ab der sie als geändert gilt
POLSTER = 10      # Rand um markierte Bereiche
REICHWEITE = 2    # Nachbarzellen, die zu einem Bereich zusammenfallen (Textzeilen)
ROT = (255, 64, 96)
ZIELBREITE = 2400


def bereiche(a, b):
    w, h = max(a.width, b.width), max(a.height, b.height)
    fa = Image.new('RGB', (w, h)); fa.paste(a)
    fb = Image.new('RGB', (w, h)); fb.paste(b)
    d = np.abs(np.asarray(fa, dtype=np.int16) - np.asarray(fb, dtype=np.int16)).sum(axis=2)
    gh, gw = -(-h // ZELLE), -(-w // ZELLE)
    pad = np.zeros((gh * ZELLE, gw * ZELLE), dtype=np.int32)
    pad[:h, :w] = d
    raster = pad.reshape(gh, ZELLE, gw, ZELLE).mean(axis=(1, 3)) > SCHWELLE
    gesehen = np.zeros_like(raster)
    boxen = []
    for y in range(gh):
        for x in range(gw):
            if not raster[y, x] or gesehen[y, x]:
                continue
            q = deque([(y, x)]); gesehen[y, x] = True
            x0 = x1 = x; y0 = y1 = y
            while q:
                cy, cx = q.popleft()
                x0, x1, y0, y1 = min(x0, cx), max(x1, cx), min(y0, cy), max(y1, cy)
                for dy in range(-REICHWEITE, REICHWEITE + 1):
                    for dx in range(-REICHWEITE, REICHWEITE + 1):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < gh and 0 <= nx < gw and raster[ny, nx] and not gesehen[ny, nx]:
                            gesehen[ny, nx] = True
                            q.append((ny, nx))
            boxen.append([x0 * ZELLE - POLSTER, y0 * ZELLE - POLSTER,
                          (x1 + 1) * ZELLE + POLSTER, (y1 + 1) * ZELLE + POLSTER])
    return zusammenfuehren(boxen)


def zusammenfuehren(boxen):
    """Überlappende Rahmen vereinigen, bis keiner mehr einen anderen schneidet."""
    geaendert = True
    while geaendert:
        geaendert = False
        for i in range(len(boxen)):
            for j in range(i + 1, len(boxen)):
                a, b = boxen[i], boxen[j]
                if a[0] <= b[2] and b[0] <= a[2] and a[1] <= b[3] and b[1] <= a[3]:
                    boxen[i] = [min(a[0], b[0]), min(a[1], b[1]), max(a[2], b[2]), max(a[3], b[3])]
                    boxen.pop(j)
                    geaendert = True
                    break
            if geaendert:
                break
    return boxen


def schrift(groesse):
    for pfad in ('/System/Library/Fonts/SFNS.ttf', '/System/Library/Fonts/Helvetica.ttc',
                 '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'):
        if os.path.exists(pfad):
            return ImageFont.truetype(pfad, groesse)
    return ImageFont.load_default()


def markieren(bild, boxen):
    kopie = bild.copy()
    zeichnen = ImageDraw.Draw(kopie)
    strich = max(3, bild.width // 400)
    for box in boxen:
        zeichnen.rectangle(box, outline=ROT, width=strich)
    return kopie


def vergleichsbild(name, a, b, boxen):
    va, nb = markieren(a, boxen), markieren(b, boxen)
    luecke, kopf = 40, 90
    bild = Image.new('RGB', (va.width + nb.width + luecke, max(va.height, nb.height) + kopf), (24, 26, 32))
    bild.paste(va, (0, kopf)); bild.paste(nb, (va.width + luecke, kopf))
    z = ImageDraw.Draw(bild)
    f = schrift(44)
    z.text((16, 20), f'Vorher · {name}', fill=(220, 224, 230), font=f)
    z.text((va.width + luecke + 16, 20), f'Nachher · {len(boxen)} markierte Bereiche', fill=ROT, font=f)
    if bild.width > ZIELBREITE:
        bild = bild.resize((ZIELBREITE, round(bild.height * ZIELBREITE / bild.width)), Image.LANCZOS)
    return bild


def main(vorher, nachher, ausgabe):
    os.makedirs(ausgabe, exist_ok=True)
    for name in sorted(os.listdir(nachher)):
        alt = os.path.join(vorher, name)
        if not name.endswith('.png') or not os.path.exists(alt):
            continue
        a = Image.open(alt).convert('RGB')
        b = Image.open(os.path.join(nachher, name)).convert('RGB')
        boxen = bereiche(a, b)
        print(f'{name}: {len(boxen)}')
        if boxen:
            vergleichsbild(name, a, b, boxen).save(
                os.path.join(ausgabe, name.replace('.png', '-vergleich.png')), optimize=True)


if __name__ == '__main__':
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    main(*sys.argv[1:4])
