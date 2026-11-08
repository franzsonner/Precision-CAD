# Precision-CAD – Windows-Testversion

Einfache Desktop-CAD-Anwendung für Windows 11 x64 mit deutscher Oberfläche.
Quader und Zylinder erzeugen, deren Maße ändern, die Ansicht drehen/zoomen sowie
STEP-Dateien öffnen und speichern. Experimenteller Stand; keine produktive Freigabe.

## Windows-Version herunterladen und starten

1. [GitHub Actions: Windows-Testbuild](https://github.com/franzsonner/Precision-CAD/actions/workflows/windows-test-build.yml) öffnen und bei GitHub anmelden.
2. Den neuesten **grünen** Lauf für `main` öffnen. Bei fehlgeschlagenem/noch laufendem Build gibt es keinen geprüften neuen Download.
3. Unten unter **Artifacts** `Precision-CAD-Windows-x64` herunterladen. Artefakte bleiben 30 Tage verfügbar. Bei Bedarf mit **Run workflow** neu bauen.
4. ZIP über **Alle extrahieren** vollständig in einen beschreibbaren Ordner entpacken.
5. `Precision-CAD.exe` im entpackten Ordner doppelklicken. `_internal` und `licenses` beim Programm belassen. Python muss nicht installiert sein.

Der Build ist nicht signiert. Windows kann den unbekannten Herausgeber melden.
Vor dem Start Herkunft und erfolgreichen Build prüfen. Aktuelle Grafiktreiber mit
OpenGL-Unterstützung werden benötigt. Der erste Start kann etwas dauern.

## Bedienung

- Maße sind Millimeter. **Länge / Radius** bedeutet beim Quader Länge, beim Zylinder Radius (halber Durchmesser). Breite gilt nur für Quader.
- Maße eingeben, **Quader erstellen** oder **Zylinder erstellen** wählen. Körper liegen am Ursprung und können sich überlappen.
- In **Bauteile** einen erzeugten Körper auswählen, Werte ändern und **Maße auf Auswahl anwenden** drücken. Die Kameraposition bleibt dabei erhalten.
- Linke Maustaste ziehen: drehen; Mausrad: zoomen; Shift + linke Maustaste: verschieben. **Ansicht einpassen** zeigt alle Körper.
- **STEP öffnen** fügt die Geometrie zur Bauteilliste hinzu. **STEP exportieren** speichert alle Körper als STEP.
- Importierte STEP-Geometrie hat keine editierbaren Grundmaße. STEP speichert keine parametrische Historie; nach erneutem Öffnen sind auch exportierte Quader/Zylinder importierte Geometrie.

## Entwicklung und Prüfung

Python 3.11 x64; in PowerShell im Repository:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:QT_API = 'pyside6'
python src/main.py
$env:PYTHONPATH = 'src'
python -m pip install pytest==8.3.5
python -m pytest -q
python src/main.py --smoke-test
```

Den vollständigen Paketbau beschreibt `.github/workflows/windows-test-build.yml`.
Actions prüft Volumen, Maßänderungen, ungültige Maße und STEP-Rundlauf mit mehreren
Körpern. Danach startet die **gepackte Windows-EXE**, erzeugt und ändert Geometrie,
speichert/öffnet STEP und rendert eine gedrehte Ansicht als `Windows-Testbild`.
Der Anwendungsdownload wird erst nach bestandenem Starttest hochgeladen.

## Open Source und Lizenzen

Anwendung: [MIT](LICENSE). Geometrie: CadQuery/Open CASCADE; Oberfläche:
PySide6/Qt; Darstellung: PyVista/VTK. Siehe [Drittanbieter und LGPL-Rechte](THIRD_PARTY.md).
Der Download enthält Lizenztexte, Copyright-Hinweise, genaue Paketversionen und
`source.zip` mit dem zum Build gehörenden Anwendungscode. DLLs bleiben austauschbar.

## To-do / Grenzen

- Manueller Bedienungstest auf einem echten Windows-11-PC mit verschiedenen Grafiktreibern; der automatisierte Runner ersetzt diesen Test nicht.
- Installer, Codesignatur und dauerhafte Release-Downloads ergänzen.
- Native Projektdatei zum Erhalten der Maße, Rückgängig/Wiederholen und Löschfunktion.
- Auswahl im 3D-Fenster, Positionieren, Skizzen und weitere Bearbeitungsfunktionen.
- STEP-Baugruppenstruktur, Farben und Namen erhalten; derzeit Geometrieimport ohne Baugruppenbaum.
- Änderungen gehen beim Schließen ohne Export verloren; noch keine Speicherwarnung.
