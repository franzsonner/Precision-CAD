# Drittanbieter und Rechte der Benutzer

Precision-CAD-Code: MIT, siehe LICENSE. Die Bibliotheken behalten ihre eigenen
Lizenzen. Der Windows-Download enthält unter `licenses/` die Original-Lizenztexte,
Copyright-Hinweise, Paket-Metadaten und eine versionsgenaue `inventory.json`.
Diese Dateien müssen bei Weitergabe erhalten bleiben. Im Ordner `sources/` liegen
die passenden QtBase-/QtSvg-, PySide-/Shiboken- und OCCT-Quellarchive einschließlich
ihrer Copyright- und Drittanbieterhinweise; `manifest.json` nennt Herkunft und
SHA-256. Die Lizenztexte stehen zusätzlich unter `licenses/additional-notices`.

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

## Native Bild- und Laufzeitbibliotheken

OCP bringt zusätzlich FreeImage (FIPL), FreeType (FTL), LibRaw (LGPL-2.1),
OpenEXR/Imath, TIFF, JPEG, PNG, WebP, OpenJPEG/OpenJPH, Lerc, LCMS,
libdeflate, XZ, zlib, Zstd und Microsoft-Laufzeit-DLLs mit.
Die Originalhinweise und zugehörigen Conda-Forge-Rezepte stehen im Archiv
`licenses/additional-notices/native-notices.zip`; dessen Inventar nennt die
Herkunft der Hinweispakete. Diese Versionsnummern bezeichnen die Hinweispakete,
nicht eine Behauptung über alle DLL-Versionen. FreeImage und LibRaw werden
unter FIPL bzw. LGPL verwendet. Die jeweiligen Quellarchive sowie die
OCP-Build-Rezepte einschließlich Patches liegen ebenfalls unter `sources/`.
Die LGPL-Austauschrechte gelten auch für LibRaw.

Portions of this software are copyright © The FreeType Project
(https://freetype.org). All rights reserved. Siehe `FreeType-FTL.txt`.

Unbenutzte QtDataVisualization-Module werden ausdrücklich vom Paketbau
ausgeschlossen. Die Anwendung benötigt QtCore, QtGui, QtWidgets, QtNetwork,
QtOpenGL/QtOpenGLWidgets und QtSvg/QtSvgWidgets.
