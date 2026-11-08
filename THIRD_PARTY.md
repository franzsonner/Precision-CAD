# Drittanbieter und Rechte der Benutzer

Precision-CAD-Code: MIT, siehe LICENSE. Die Bibliotheken behalten ihre eigenen
Lizenzen. Der Windows-Download enthält unter `licenses/` die Original-Lizenztexte,
Copyright-Hinweise, Paket-Metadaten und eine versionsgenaue `inventory.json`.
Diese Dateien müssen bei Weitergabe erhalten bleiben.

| Komponente | Lizenz | Quellcode |
| --- | --- | --- |
| CadQuery | Apache-2.0 | https://github.com/CadQuery/cadquery |
| cadquery-ocp / Open CASCADE | Apache-2.0 (Bindings); LGPL-2.1 mit OCCT-Ausnahme (Kernel) | https://github.com/CadQuery/OCP / https://github.com/Open-Cascade-SAS/OCCT |
| PySide6 / Shiboken6 / Qt | LGPL-3.0, verwendete Qt-Komponenten LGPL-3.0/BSD | https://download.qt.io/official_releases/QtForPython/ / https://download.qt.io/archive/qt/ |
| PyVista / PyVistaQt | MIT | https://github.com/pyvista/pyvista / https://github.com/pyvista/pyvistaqt |
| VTK | BSD-3-Clause und eingebettete Drittanbieterhinweise | https://github.com/Kitware/VTK |
| NumPy | BSD-3-Clause und eingebettete Drittanbieterhinweise | https://github.com/numpy/numpy |
| PyInstaller (Build-Werkzeug) | GPL-2.0-or-later mit Bootloader-Ausnahme | https://github.com/pyinstaller/pyinstaller |

Die vollständige Liste der transitiven Abhängigkeiten mit Version und Herkunft
steht im Download. Upstream-Code wird unverändert aus den offiziellen Wheels
verwendet. Passende Quellversionen sind über die Versionsnummern in inventory.json
und die oben genannten Quellarchive/Release-Tags erhältlich. Die OCCT-Ausnahme:
https://dev.opencascade.org/resources/licensing

## LGPL: Bibliotheken austauschen und Anwendung neu bauen

Die portable Distribution verwendet dynamische DLLs in `_internal`, keine
statisch eingebettete Qt-/OCCT-Kopie. Sie dürfen die LGPL-Bibliotheken verändern,
austauschen und für die Fehlersuche an diesen Änderungen Reverse Engineering
betreiben. Es gibt keine Aktivierung und keine technische Austausch-Sperre.
Den vollständigen Anwendungscode erhalten Sie unter
https://github.com/franzsonner/Precision-CAD . Die Build-Anweisungen und der
GitHub-Actions-Workflow liegen dort bei. Mit einer kompatiblen selbst gebauten
PySide6-/OCP-Wheel können Sie diese in der Build-Umgebung per pip installieren
und den PyInstaller-Aufruf erneut ausführen. Alternativ kompatible DLLs im
entpackten `_internal`-Ordner ersetzen. Vorher eine Kopie des Ordners anlegen.

Die automatisch kopierten Lizenztexte sind Bestandteil des Builds. Zusätzliche
Qt-Module dürfen nur aufgenommen werden, wenn deren Lizenz die Weitergabe erlaubt.
