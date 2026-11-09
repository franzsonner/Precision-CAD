# Precision-CAD – Windows-Testversion

Einfache Desktop-CAD-Anwendung für Windows 11 x64 mit deutscher Oberfläche.
Quader und Zylinder erzeugen, deren Maße und Position ändern, einzelne oder mehrere
Bauteile verschieben, Änderungen rückgängig machen und die Ansicht drehen/zoomen sowie
STEP-Dateien öffnen und speichern. A4-Zeichnungsübersichten mit drei Ansichten
als PDF/SVG ausgeben. Experimenteller Stand; keine produktive Freigabe.

## Windows-Version herunterladen und starten

**Direkter Download ohne GitHub-Anmeldung:**
[Neueste Windows-Testversion als ZIP](https://github.com/franzsonner/Precision-CAD/releases/latest/download/Precision-CAD-Windows-x64.zip).
Die [Release-Seite](https://github.com/franzsonner/Precision-CAD/releases/latest)
enthält zusätzlich die SHA-256-Prüfsumme. Ein öffentliches Update erscheint erst,
wenn Tests und Starttest der gepackten Windows-EXE bestanden sind.
ZIP vollständig entpacken und `Precision-CAD.exe` starten.

Alternativ stehen Build-Artefakte über GitHub Actions bereit:

1. [GitHub Actions: Windows-Testbuild](https://github.com/franzsonner/Precision-CAD/actions/workflows/windows-test-build.yml) öffnen und bei GitHub anmelden.
2. Den neuesten **grünen** Lauf für `main` öffnen. Bei fehlgeschlagenem/noch laufendem Build gibt es keinen geprüften neuen Download.
3. Unten unter **Artifacts** `Precision-CAD-Windows-x64` herunterladen. Artefakte bleiben 30 Tage verfügbar. Bei Bedarf mit **Run workflow** neu bauen.
4. ZIP über **Alle extrahieren** vollständig in einen beschreibbaren Ordner entpacken.
5. `Precision-CAD.exe` im entpackten Ordner doppelklicken. `_internal` und `licenses` beim Programm belassen. Python muss nicht installiert sein.

Während der Testversion öffnet sich zusätzlich eine Konsole mit Diagnosemeldungen.
Sie schließt sich mit der Anwendung.

Der Build ist nicht signiert. Windows kann den unbekannten Herausgeber melden.
Vor dem Start Herkunft und erfolgreichen Build prüfen. Aktuelle Grafiktreiber mit
OpenGL-Unterstützung werden benötigt. Der erste Start kann etwas dauern.

## Updates direkt im Programm

Ab Version 0.4: Oben **Updates** anklicken, dann **Auf Updates prüfen**.
Bei einer neuen Version **Update herunterladen und installieren** wählen.
Precision CAD lädt die öffentliche ZIP-Datei und ihre Prüfsumme selbst von GitHub,
prüft SHA-256 und entpackt sie unter
`%LOCALAPPDATA%\Precision-CAD\versions\test-…`. Es ist keine GitHub-Anmeldung
und kein Administratorrecht nötig. Der Vorgang läuft im Hintergrund und lässt
sich abbrechen. Bei Fehlern bleibt die bisherige Installation erhalten.

Nach der Installation **Neue Version starten** wählen. Die bisherige Anwendung
bleibt geöffnet, damit keine ungespeicherten Änderungen verloren gehen. Vor dem
Wechsel Geometrie als STEP exportieren; Maße und Verlauf werden nicht übertragen.
Für spätere Starts die EXE aus dem angezeigten neuen Versionsordner verwenden.
Vorhandene alte Verknüpfungen zeigen weiterhin auf die alte Installation.
Die alte Installation bleibt als Rückfallmöglichkeit erhalten.

Versionen ohne Update-Button müssen einmal über den direkten ZIP-Link oben
aktualisiert werden. Linux-Entwicklungsstarts können nach Releases suchen;
die automatische Installation ist für Windows vorgesehen.

## Bedienung

- Maße sind Millimeter. **Länge / Radius** bedeutet beim Quader Länge, beim Zylinder Radius (halber Durchmesser). Breite gilt nur für Quader.
- Maße eingeben, oben unter **Start → Quader** oder **Start → Zylinder** wählen. Neue Körper liegen zunächst am Ursprung. Die Bauteilliste und Positionsfelder befinden sich links; bei kleinen Fenstern im Bereich nach unten scrollen.
- In **Bauteile** einen erzeugten Körper auswählen, Werte ändern und **Maße auf Auswahl anwenden** drücken. Die Kameraposition bleibt dabei erhalten.
- **Rückgängig**: Schaltfläche oben oder Strg+Z. **Wiederholen**: Strg+Y oder Strg+Shift+Z. Erzeugen, STEP-Import, Maßänderungen und Bewegungen werden für die letzten 100 Änderungen dieser Sitzung gespeichert. Eine neue Änderung nach Rückgängig verwirft die Wiederholen-Historie.
- Ein Bauteil in der Liste auswählen (orange markiert), unter **Position X / Y / Z** Werte eingeben und **Position übernehmen** drücken. Negative Koordinaten sind möglich. Maße lassen sich anschließend weiter ändern, ohne die Position zu verlieren.
- Für eine gemeinsame Bewegung mit Strg/Shift mehrere Bauteile in der Liste auswählen. Unter **Verschiebung ΔX / ΔY / ΔZ** den gewünschten Weg eingeben und **Auswahl verschieben** drücken. Die Abstände bleiben erhalten; Rückgängig nimmt die gesamte gemeinsame Bewegung zurück. Es entsteht dabei keine dauerhafte Baugruppe oder geometrische Vereinigung.
- Linke Maustaste ziehen: drehen; Mausrad: zoomen; Shift + linke Maustaste: verschieben. **Ansicht einpassen** zeigt alle Körper.
- **STEP öffnen** fügt die Geometrie zur Bauteilliste hinzu. **STEP exportieren** speichert alle Körper als STEP.
- Importierte STEP-Geometrie hat keine editierbaren Grundmaße. STEP speichert keine parametrische Historie; nach erneutem Öffnen sind auch exportierte Quader/Zylinder importierte Geometrie.

## Beispiel: Zylinder auf einem Quader positionieren

1. Quader mit Länge 50, Breite 30 und Höhe 20 erstellen. Sein Mittelpunkt liegt bei X=0, Y=0, Z=0; seine Oberseite liegt also bei Z=10.
2. Zylinder erzeugen und in der Liste auswählen. Sein Bezugspunkt ist die Mitte der unteren Kreisfläche.
3. Position X=12, Y=5, Z=10 eingeben und **Position übernehmen** drücken. Der Zylinder steht nun außermittig auf dem Quader.
4. Radius oder Höhe des ausgewählten Zylinders ändern und **Maße auf Auswahl anwenden** drücken. Sein Bezugspunkt bleibt erhalten.
5. Quader und Zylinder mit Strg auswählen und gemeinsam beispielsweise um ΔX=25 verschieben.

Bei Quadern bezeichnet die Position den Mittelpunkt, bei Zylindern den Mittelpunkt
der Grundfläche. Bei STEP-Importen ist sie ein zusätzlicher Versatz zur importierten
Lage; die ursprüngliche importierte Lage wird als Position 0/0/0 angezeigt.
Die Bauteilauswahl erfolgt bisher über die Liste, nicht durch Anklicken im 3D-Fenster.
STEP speichert die verschobene Geometrie, aber weder die ursprünglichen Grundmaße
noch die Bearbeitungshistorie. Auch eine gemeinsame Auswahl wird nicht gespeichert.

## Erste technische Zeichnung

1. Bauteil in der Liste auswählen.
2. Oben den Reiter **Zeichnung** öffnen und **A4-Blatt / PDF / SVG** wählen.
3. Die Vorschau zeigt Vorder-, Rechts- und Draufsicht mit verdeckten Kanten,
   Gesamtabmessungen und bei erzeugten Zylindern den Durchmesser.
4. **PDF speichern** erzeugt ein A4-Blatt im Querformat; **SVG speichern** eine
   editierbare Vektorgrafik, z. B. für Inkscape.

Die Ansichten sind einzeln eingepasst und haben keinen gemeinsamen festen Maßstab.
Maße stehen als Tabelle neben den Ansichten. Einzelbemaßung mit Maßpfeilen,
Toleranzen, Passungen, Schnitte und normgerechte Zeichnungsvorlagen fehlen noch.
Das Blatt ist eine Übersicht, keine Fertigungsfreigabe.

Die Oberfläche besitzt die Bereiche **Start**, **Ansicht** und **Zeichnung** sowie
eine Bauteilliste und ein Maßfeld. Sie orientiert sich an üblichen CAD-Abläufen.
Sie ist kein Solid-Edge-Klon und ersetzt zum Erlernen der konkreten Solid-Edge-
Befehle und Bedienwege keine Übung in Solid Edge selbst.

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
Actions prüft Volumen, Maßänderungen, Positionen, gemeinsame Bewegungen,
Rückgängig/Wiederholen, ungültige Eingaben und STEP-Rundlauf mit mehreren
Körpern. Danach startet die **gepackte Windows-EXE**, erzeugt und ändert Geometrie, prüft Einzel- und Gruppenbewegungen mit Rückgängig/Wiederholen,
speichert/öffnet STEP, erzeugt eine PDF-Zeichnung und rendert eine gedrehte Ansicht als `Windows-Testbild`.
Der Anwendungsdownload wird erst nach bestandenem Starttest hochgeladen.
Danach veröffentlicht Actions den Build mit ZIP und SHA-256 als öffentliches GitHub-Release.
Auch Update-Erkennung, Prüfsummenfehler, sichere ZIP-Pfade und Erhalt alter
Installationen werden automatisch getestet.
Der Windows-Runner verwendet Mesa als Software-OpenGL-Treiber für diesen Test.
Mesa wird nicht im Download mitgeliefert; der eigene PC benötigt einen geeigneten
Grafiktreiber. Die Prüfung echter Windows-11-Grafiktreiber bleibt ein To-do.

## Open Source und Lizenzen

Anwendung: [MIT](LICENSE). Geometrie: CadQuery/Open CASCADE; Oberfläche:
PySide6/Qt; Darstellung: PyVista/VTK. Siehe [Drittanbieter und LGPL-Rechte](THIRD_PARTY.md).
Der Download enthält Lizenztexte, Copyright-Hinweise, genaue Paketversionen und
`source.zip` mit dem zum Build gehörenden Anwendungscode. DLLs bleiben austauschbar.

## To-do / Grenzen

- Manueller Bedienungstest auf einem echten Windows-11-PC mit verschiedenen Grafiktreibern; der automatisierte Runner ersetzt diesen Test nicht.
- Installer, Codesignatur und komfortable Startverknüpfung für installierte Updates ergänzen.
- Native Projektdatei zum Erhalten von Maßen, Positionen und Bauteilstruktur; Löschfunktion.
- Dauerhafte Baugruppen, Ausrichten an Flächen und geometrisches Vereinigen.
- Zeichnungen: Maßpfeile, Maßstab, Toleranzen, Schnitte, Schriftfeld und DIN/ISO-Vorlagen.
- Auswahl und Verschieben direkt im 3D-Fenster, Drehen einzelner Körper, Skizzen und weitere Bearbeitungsfunktionen.
- Spätere Ziele: Smartphone-Bedienung und KI-Hilfen für nachvollziehbare CAD-Befehle.
- STEP-Baugruppenstruktur, Farben und Namen erhalten; derzeit Geometrieimport ohne Baugruppenbaum.
- Änderungen gehen beim Schließen ohne Export verloren; noch keine Speicherwarnung.
