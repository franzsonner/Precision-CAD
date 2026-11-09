# Precision CAD – Testversion 0.5

Windows-x64-CAD mit deutscher Oberfläche, echten Open-CASCADE-Volumenkörpern,
Bearbeitungsschritten, Projektdateien und STEP. Die Werkzeuggruppen und eigenen
Vektorsymbole orientieren sich an üblichen CAD-Oberflächen. Kein Solid-Edge-Klon
und noch keine vollständige professionelle CAD-Anwendung.

## Direkt herunterladen und starten

**[Neueste Windows-Version direkt als ZIP herunterladen](https://github.com/franzsonner/Precision-CAD/releases/latest/download/Precision-CAD-Windows-x64.zip)**

1. ZIP **vollständig entpacken**.
2. `Precision-CAD.exe` doppelklicken. `_internal`, `licenses`, `sources` und
   `build-info.json` beim Programm belassen. Python muss nicht installiert sein.
3. Aktuellen Grafiktreiber mit OpenGL-Unterstützung verwenden.

Kein GitHub-Login erforderlich. [Release-Seite mit Prüfsumme](https://github.com/franzsonner/Precision-CAD/releases/latest).
Die Testversion ist nicht signiert; Windows kann einen unbekannten Herausgeber
anzeigen. Zusätzlich öffnet sich eine Diagnosekonsole.

Alternativ: [Actions-Builds](https://github.com/franzsonner/Precision-CAD/actions/workflows/windows-test-build.yml)
→ grünen Lauf öffnen → Artifact `Precision-CAD-Windows-x64` herunterladen
(GitHub-Anmeldung nötig; 30 Tage verfügbar). Nur erfolgreiche Builds werden als
öffentliches Update veröffentlicht.

## Updates im Programm

**Updates → Auf Updates prüfen → Update herunterladen und installieren**.
Das Programm holt ZIP und SHA-256 selbst von GitHub, prüft die Datei und installiert
unter `%LOCALAPPDATA%\Precision-CAD\versions\test-…`. Keine Administratorrechte
und kein GitHub-Login nötig. Abbrechen und Wiederholen sind möglich.

**Neue Version starten** öffnet die neue Installation; die bisherige Anwendung
bleibt geöffnet. Vor dem Wechsel das Projekt als `.pcad` speichern und in der
neuen Version öffnen. Alte Verknüpfungen zeigen weiterhin auf die alte EXE;
für spätere Starts die EXE aus dem angezeigten neuen Versionsordner verwenden.
Die alte Installation bleibt als Rückfallmöglichkeit erhalten.

## Sofort ausprobieren

**Start → Beispiel** öffnet eine editierbare Bohrplatte mit vier gesenkten
Durchgangsbohrungen, einer schrägen Sackbohrung und verrundeten Ecken.
Über **Schritte → Bearbeitungsschritte** lassen sich Durchmesser, Tiefe und
Radien verändern. Mit **Projekt speichern** eine eigene Kopie anlegen.
Die Datei liegt außerdem unter `examples/Bohrplatte.pcad` im Download.

## Grundbedienung und Auswahl

- Alle Längen in **Millimetern**, Winkel in **Grad**.
- **Start → Quader/Zylinder** erzeugt einen Körper aus den Maßen links. Beim
  Zylinder ist das erste Feld der **Radius**, nicht der Durchmesser.
- Die Bauteilliste erlaubt Mehrfachauswahl mit Strg/Shift. Auswahl wird orange.
- Links den 3D-Auswahlmodus **Bauteil**, **Fläche**, **Kante** oder **Messen**
  wählen und das gewünschte Element **mit Rechtsklick** auswählen. Strg-Rechtsklick
  fügt weitere Kanten für Radius/Fase hinzu. Der Infotext zeigt Auswahl und Maße.
- Linke Maustaste ziehen: Ansicht drehen. Mausrad: zoomen. Shift + linke
  Maustaste: **Ansicht** verschieben. **Ansicht → Einpassen** zeigt alle Körper.
- Bei kleinen Fenstern im linken Einstellbereich nach unten scrollen.

## Maße, Position, Mausverschieben und Drehen

Ein Bauteil auswählen, Werte links ändern und **Maße auf Auswahl anwenden**.
Bearbeitungen werden dabei neu berechnet; die Position bleibt erhalten.

**Position X/Y/Z → Position übernehmen** setzt einen einzelnen Körper.
**Verschiebung ΔX/ΔY/ΔZ → Auswahl verschieben** verschiebt auch mehrere Körper
unter Erhalt ihrer Abstände. Quader-Bezugspunkt: Mittelpunkt; Zylinder-Bezugspunkt:
Mitte der unteren Kreisfläche. Bei STEP-Importen bedeutet Position 0/0/0 die
ursprüngliche importierte Lage.

**Bearbeiten → Mausverschieben** aktiviert für den gewählten Körper einen
Verschieberahmen. Erst diesen Rahmen mit links ziehen und loslassen; das
gewöhnliche Anklicken verschiebt den Körper nicht. Loslassen ergibt einen
Rückgängig-Schritt. Bei Bedarf erneut aktivieren.

**Bearbeiten → Drehen** dreht um X/Y/Z durch den Bezugspunkt.
**Prüfen → Kantenmaß ändern** bearbeitet vollständige, gerade Grundkanten eines
ungedrehten Quaders oder die volle Zylinderhöhe. Verkürzte, schräge, importierte
oder beliebig bearbeitete Kanten sind bisher nur messbar.

## Bohrungen, schräges Bohren und Senkungen

1. Einen Körper wählen; optional im Modus **Fläche** die gewünschte Eintrittsstelle
   auf einer ebenen Fläche rechts anklicken.
2. **Bearbeiten → Bohrung** öffnen. Ohne Klick wird die Mitte der ausgewählten
   Startfläche benutzt; die Startfläche ist auch im Dialog wählbar.
3. Durchmesser, **Durch alles** oder Sacklochtiefe einstellen.
4. Optional Versatz U/V in der Fläche, Neigung 0–85° zur Flächennormalen und
   Azimut einstellen. 0° bohrt senkrecht in den Körper. U/V sind lokale
   Flächenrichtungen; der Azimut bestimmt die Richtung der Schrägbohrung.
5. Optional Zylinder- oder Kegelsenkung wählen. Beim Kegel ist das letzte Feld
   der eingeschlossene Senkwinkel, sonst die Senktiefe.
6. Bestätigen. Nicht mögliche Schnitte verändern das Dokument nicht.

**Gewindeoption:** M-Größe und Steigung wählen, z. B. M10 mit 1,5 mm (gängig)
oder M10×1. Das erzeugt ein voreingestelltes **Kernloch mit Gewindebezeichnung**,
kein spiralförmiges Gewindeprofil. Die Kernloch-Voreinstellung ist d−P, auf
0,1 mm gerundet. Geometrische Vollgewinde und detaillierte Gewindetoleranzen
sind noch nicht implementiert.

## Radius, Fase und Flächenneigung

- Kante(n) auswählen → **Bearbeiten → Radius** bzw. **Fase** → Wert eingeben.
  Der Geometriekern muss einen gültigen Körper erzeugen; zu große Werte werden
  verworfen. Fasen sind bisher gleichseitig, keine frei definierten Winkel-Fasen.
- Ebene Fläche auswählen → **Fläche neigen** → Zugrichtung X/Y/Z und zusätzlichen
  Neigungswinkel wählen. Die Neutralebene liegt an der kleinsten Körperkoordinate
  entlang der Zugrichtung. Der Körper wird wirklich umgeformt, nicht nur gedreht.
  Positive Winkel tragen Material ab. Wenn Fläche und Zugrichtung ungeeignet
  sind, andere Zugrichtung wählen. Für eine obere Quaderfläche beispielsweise X
  statt Z versuchen; für eine senkrechte Seitenfläche ist oft Z passend.

## Bearbeitungsschritte nachträglich ändern

**Schritte → Bearbeitungsschritte** zeigt den Aufbau des ausgewählten Körpers.
Ein vorhandenes Loch, einen Radius, eine Fase, Drehung oder Neigung auswählen
und **Schritt bearbeiten**. Alle folgenden Schritte werden neu berechnet.
Bei Bohrungsnachbearbeitung beziehen sich Eintrittskoordinaten auf den
Bauteil-Bezugspunkt; Neigung und Azimut auf die globale −Z-Richtung, nicht mehr
auf die ursprüngliche Flächenauswahl.

**Ab hier entfernen** entfernt den gewählten und alle folgenden Schritte;
Rückgängig ist möglich. Flächen-/Kantenreferenzen sind in dieser Testversion
noch indexbasiert. Änderungen an der Topologie werden anhand der Flächen- und
Kantenanzahl geprüft und gegebenenfalls abgewiesen. Eine vollständige stabile
Topologiebenennung fehlt; Ergebnisse nach größeren Änderungen kontrollieren.

## Körper kombinieren

Mehrere Körper in der Liste auswählen → **Vereinigen** oder **Abziehen**.
Beim Abziehen ist der **erste ausgewählte Körper in der Bauteilliste** das Ziel;
die anderen werden als Werkzeuge benutzt. Die gewählten Einzelkörper werden
durch das Ergebnis ersetzt; Rückgängig stellt sie wieder her.

Das Ergebnis ist eine neue Basisgeometrie. Die früheren Einzelteil-Grundmaße
sind darin noch nicht als parametrische Baugruppe verknüpft. Weitere Bohrungen,
Radien usw. sind möglich. Nicht zusammenhängende Körper bleiben auch nach dem
Vereinigen mehrere Volumen in einem Bauteileintrag. **Löschen** entfernt die
Auswahl mit Rückgängig-Möglichkeit.

## Schrauben, Muttern und Scheiben

**Normteile → Normteil einfügen** bietet Sechskantschrauben, Sechskantmuttern und
Unterlegscheiben M3–M16. Größe, Schraubenlänge und Gewindesteigung sind wählbar,
zum Beispiel M10, Steigung 1 oder 1,5 mm.

Es sind **vereinfachte Kataloggeometrien**, keine zertifizierte DIN-/ISO-Bibliothek:
glatter Schaft bzw. glatte Bohrung, ohne Helix, Gewindeflanken, Kopffasen und
Normtoleranzen. Einfügen, anschließend positionieren und drehen. Bei Schrauben
liegt die Kopfunterseite bei Z=0, der Schaft zeigt zunächst in +Z. Für einen
Schaft nach unten zuerst beispielsweise um X=180° drehen.

## Zeichnung und Bemaßung per Klick

Ein Bauteil auswählen → **Zeichnung → A4-Blatt / PDF / SVG**.

- Vorder-, Rechts- und Draufsicht mit verdeckten Kanten und Maßpfeilen.
- **Blaue Grundmaße anklicken**, neue Zahl eingeben: Modell und Zeichnung ändern
  sich gemeinsam. Das gilt für eindeutig zuordenbare Grundmaße von Quader und
  Zylinder; bei gedrehten/gegeneigten Körpern oder abweichenden Außenmaßen ist
  diese direkte Bearbeitung ausgeschaltet.
- **Im Blatt zwei Kanten anklicken** einschalten und Kante A, dann B wählen.
  Gemessen wird der **exakte 3D-Mindestabstand** der CAD-Kanten, nicht der
  Papierabstand und nicht ein beliebiger Punktabstand in der Projektion.
  Überlagerte Projektionskanten können mehrdeutig sein; dann im Hauptfenster
  im Modus **Messen (2 Kanten)** auswählen und **Prüfen → Maß in Zeichnung**.
- Eine einzelne Kante lässt sich als Länge übernehmen; zwei gerade Kanten zeigen
  zusätzlich den kleineren Winkel 0–90°. Es bleiben maximal fünf Zusatzmessungen.
- Ein zu einem Grundmaß passender Messwert ist blau und editierbar; andere
  Messungen sind nur Anzeigen und steuern das Modell nicht.
- Bei Geometrieänderungen werden zusätzliche Kantenmessungen entfernt, damit
  keine veralteten Referenzen als gültige Maße erscheinen. Neu messen.
- **PDF speichern** erzeugt ein A4-Blatt im Querformat; SVG ist eine Vektorgrafik.

Die Ansichten sind einzeln eingepasst und haben keinen gemeinsamen festen
Maßstab. Das ist noch **keine normgerechte Fertigungszeichnung**: feste Maßstäbe,
Schnitte, Toleranzen, Passungen, Oberflächenzeichen, GD&T und vollständige
Zeichnungsvorlagen fehlen.

## Projekt speichern, STEP und Rückgängig

**Start → Projekt speichern** schreibt `.pcad` mit Körpern, Grundmaßen,
Positionen, Bearbeitungsschritten und Zusatzmessungen. **Projekt öffnen**
rekonstruiert den Aufbau. Beim Schließen ungespeicherter Änderungen erscheint
jetzt eine Speicherfrage; `*` im Fenstertitel kennzeichnet Änderungen.

**STEP öffnen** fügt Geometrie hinzu; **STEP speichern** exportiert alle Körper.
STEP enthält hier keine editierbaren Grundmaße oder Bearbeitungshistorie.
Importierte Körper können trotzdem positioniert, gebohrt, verrundet usw. werden.

**Rückgängig** / Strg+Z und **Wiederholen** / Strg+Y oder Strg+Shift+Z gelten für
Erzeugen, Import, Maßänderungen, Bearbeitungen, Bewegungen, Kombinieren und
Löschen. Die letzten 100 Änderungen sind während der Sitzung verfügbar.
Die Rückgängig-Historie selbst wird noch nicht in `.pcad` gespeichert.
Formatgrenzen dieser Testversion: 1000 Bauteile, 200 Schritte pro Körper und
100 MB unkomprimierte Projektdaten.

## Text, Sprache und optionale KI

**Assistent → Text / Diktat / KI**.

Offline-Beispiele (feste Befehlsvorlagen; Zahlen als Ziffern):

```text
Quader 80 40 20
Zylinder 10 30
Bohrung 8
Bohrung 8 15 30
Radius 2
Fase 1
Verschieben 10 0 0
Drehen Z 45
```

Zylinder: Radius/Höhe. Bohrung mit einer Zahl: durchgehend. Drei Zahlen:
Durchmesser, Tiefe und Neigung. Radius/Fase benötigt zuvor ausgewählte Kanten.
Für Bearbeitungen zuerst ein Bauteil, bei Bedarf eine Startfläche auswählen.

**Windows-Diktat starten** öffnet Win+H mit Fokus auf dem Textfeld. Mikrofon und
Diktat müssen in Windows eingerichtet sein. Die Spracherkennung übernimmt
Windows; Precision CAD nimmt selbst kein Audio auf.

Optional **OpenAI-KI verwenden** einschalten und eigenen API-Schlüssel eingeben.
Der Schlüssel bleibt im Speicher der Sitzung und wird nicht im Projekt oder
Repository gespeichert. Ein ChatGPT-Abo ersetzt keinen API-Zugang. API-Nutzung
kann Kosten verursachen. Nur nach aktiviertem KI-Modus und Klick auf Vorschau
wird der eingegebene Text an OpenAI gesendet, keine CAD-Datei. Der Aufruf nutzt
`gpt-4.1-mini` und ein festes JSON-Befehlsschema.

Die KI darf nur die obigen unterstützten Operationen vorschlagen, **keinen Code
zur Ausführung**. Ein Befehl pro Vorschau; noch keine autonome Konstruktion
beliebig komplexer Teile. Grüne Geometrievorschau und Parameter prüfen, dann
**Vorschlag übernehmen**. Das ist ein Rückgängig-Schritt; Feinheiten anschließend
über Grundmaße oder Bearbeitungsschritte ändern.

Der kostenpflichtige Dienst wurde ohne hinterlegten API-Schlüssel nicht live
aufgerufen. Offline-Befehle und die strukturierte KI-Anbindung werden automatisch
mit simulierten API-Antworten geprüft.

## Entwicklung und Tests

Python 3.11 x64, PowerShell im Repository:

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

Der [Workflow](.github/workflows/windows-test-build.yml) baut die Windows-EXE,
prüft unter anderem Bohrvolumen, Senkungen, Neigung, Radius/Fase, Parameteränderung,
Rückgängig, Projekt-Rundlauf, Zeichnungsmaße, Befehlsassistent und Update-Integrität.
Der Starttest der **gepackten EXE** prüft zusätzlich die Oberflächenauswahl,
Locherstellung, bestehende Bearbeitungsschritte, Zeichnungsänderung, Klickmessung,
Mausverschieben, Normteil und native Projektdatei. `Windows-Testbild` enthält
Screenshots und Diagnoseprotokolle.

Der Windows-Server-Runner nutzt Mesa für Software-OpenGL; Mesa ist nicht im
Anwendungsdownload enthalten. Ein manueller Test auf einem echten Windows-11-PC
mit verschiedenen Grafiktreibern bleibt erforderlich. Das öffentliche Release
wird erst nach erfolgreichem Windows-Build und Starttest veröffentlicht.

## Open Source

Anwendung und eigene Symbole: [MIT](LICENSE). CadQuery/Open CASCADE, PySide6/Qt,
PyVista und VTK behalten ihre eigenen Lizenzen. [Drittanbieter und LGPL-Rechte](THIRD_PARTY.md).
Downloads enthalten Originalhinweise, native Bibliothekshinweise, Quellarchive,
Paketversionen und `source.zip` mit dem zum Build gehörenden Anwendungscode.
DLLs bleiben austauschbar. Normteilgeometrie und Symbole sind eigene Erzeugnisse;
keine übernommenen Herstellerbilder oder Normdokumente.

## Weitere Schritte / Grenzen

- Skizzen mit Zwangsbedingungen, Extrusionen, Taschen und vollständig parametrische Baugruppen.
- Freies Verschieben einzelner Kanten/Flächen; direkte Längensteuerung beliebiger STEP-Geometrie.
- Stabilere Flächen-/Kantenreferenzen bei geänderter Topologie und komfortables Bearbeitungsbaum-Umordnen.
- Echte Gewindeprofile und umfangreiche, geprüfte Normteilkataloge.
- Normgerechte Fertigungszeichnungen, feste Maßstäbe, Schnitte und Toleranzen.
- Mehrere verkettete KI-Befehle, automatische Spracherkennung im Programm statt Windows-Diktat.
- Installer, Codesignatur und Startverknüpfung für installierte Updates.
- Aufräumen alter Update-Versionen und spätere Smartphone-Bedienung.
