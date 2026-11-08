# Precision CAD – Entwicklungsstand

**Ziel:** Kostenlose, eigenständige CAD-Anwendung für Windows mit deutscher Oberfläche, später auch weiteren Sprachen, Baugruppen, Blech, Zeichnungen und Simulation.

**Aktueller Stand:** Erste Quellcodedateien für einen unabhängigen Desktop-Prototyp. **Noch keine fertige oder getestete Windows-Installationsdatei.** Die Anwendung verwendet vorhandene Open-Source-Bibliotheken, aber benötigt zur Entwicklung Python und weitere Pakete.

## Geplante erste Funktionen

- Quader und Zylinder aus Maßen erzeugen
- 3D-Ansicht mit Maus drehen und zoomen
- STEP-Dateien laden und exportieren
- Einfache Bauteilliste

## Entwicklerstart (noch nicht auf Windows geprüft)

1. Python 3.11 installieren.
2. Im Projektverzeichnis eine virtuelle Umgebung anlegen: `python -m venv .venv`
3. Umgebung aktivieren: `.venv\\Scripts\\activate`
4. Pakete installieren: `python -m pip install -r requirements.txt`
5. Starten: `python src/main.py`

**Hinweis:** Die Abhängigkeiten sind groß und können unter manchen Python-/Windows-Kombinationen Probleme machen. Die Bedienung und das Paket müssen noch praktisch getestet werden. Keine produktive Verwendung.

## Nächste Schritte

- Windows-Build automatisieren und echte Starttests durchführen
- Geometrie- und STEP-Tests ergänzen
- Einfache native Projektdatei ergänzen
- Skizzen, Extrusionen, Bearbeitungsfunktionen und Maße
- Später Baugruppen, Blech, Zeichnungen, FEM und Mobilansicht

Open-Source-Abhängigkeiten und deren Lizenzbedingungen sind vor Veröffentlichung einer Distribution gesondert zu prüfen. Die MIT-Lizenz dieses Repositories gilt nicht automatisch für Drittbibliotheken.
