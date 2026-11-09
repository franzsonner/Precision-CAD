"""Download in a worker thread; never replace an open application or its files."""
import os
from pathlib import Path
import subprocess
import sys
from urllib.error import HTTPError
from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QMessageBox
from updates import latest_release, is_newer, install_release


class UpdateWorker(QThread):
    result = Signal(object)
    error = Signal(str)
    progress = Signal(str)

    def __init__(self, release=None, parent=None):
        super().__init__(parent)
        self.release = release

    def report(self, text):
        if self.isInterruptionRequested():
            raise RuntimeError("Update abgebrochen.")
        self.progress.emit(text)

    def run(self):
        try:
            if self.release is None:
                release = latest_release()
                self.report("GitHub geprüft.")
                self.result.emit(release)
            else:
                root = Path(os.environ['LOCALAPPDATA']) / 'Precision-CAD' / 'versions'
                self.result.emit(install_release(self.release, root, self.report))
        except HTTPError as exc:
            self.error.emit('Noch kein öffentliches Update verfügbar.' if exc.code == 404 else f'GitHub meldet HTTP {exc.code}. Bitte später erneut versuchen.')
        except Exception as exc:
            self.error.emit(str(exc))


class UpdateDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Precision CAD – Updates von GitHub')
        self.resize(480, 220)
        self.release = None
        self.installed = None
        self.worker = None
        self.workers = []
        layout = QVBoxLayout(self)
        self.label = QLabel('Öffentliche Updates direkt von franzsonner/Precision-CAD laden.\nDie bisherige Installation bleibt erhalten.')
        self.label.setWordWrap(True)
        layout.addWidget(self.label)
        self.button = QPushButton('Auf Updates prüfen')
        self.button.clicked.connect(self.perform)
        layout.addWidget(self.button)
        self.cancel = QPushButton("Vorgang abbrechen")
        self.cancel.setEnabled(False)
        self.cancel.clicked.connect(self.cancel_update)
        layout.addWidget(self.cancel)
        self.notice = QLabel('Vor dem Wechsel offene Änderungen als Projekt (.pcad) speichern.\nSTEP erhält nur Geometrie; nicht Maße und Bearbeitungsschritte.')
        self.notice.setWordWrap(True)
        layout.addWidget(self.notice)

    def perform(self):
        if self.installed:
            answer = QMessageBox.question(self, 'Neue Version starten', 'Offene Änderungen zuerst als Projekt (.pcad) speichern. Die neue Version startet mit einem leeren Dokument.\nNeue Version jetzt starten? Die aktuelle Anwendung bleibt geöffnet.')
            if answer == QMessageBox.StandardButton.Yes:
                try:
                    subprocess.Popen([str(self.installed)], cwd=str(self.installed.parent), close_fds=True)
                    self.accept()
                except OSError as exc:
                    QMessageBox.critical(self, 'Startfehler', str(exc))
            return
        if self.release and sys.platform != 'win32':
            QMessageBox.information(self, 'Windows-Update', 'Die automatische Installation ist für Windows verfügbar.')
            return
        self.button.setEnabled(False)
        self.cancel.setEnabled(True)
        self.label.setText('Update herunterladen …' if self.release else 'GitHub auf Updates prüfen …')
        worker = UpdateWorker(self.release, self)
        self.worker = worker
        self.workers.append(worker)
        worker.progress.connect(self.label.setText)
        worker.result.connect(self.received)
        worker.error.connect(self.failed)
        worker.finished.connect(lambda: self.button.setEnabled(True))
        worker.finished.connect(lambda: self.cancel.setEnabled(False))
        worker.start()

    def received(self, result):
        if isinstance(result, dict):
            if not is_newer(result):
                self.label.setText('Diese Version ist aktuell. Keine neuere Testversion auf GitHub verfügbar.')
                self.release = None
                return
            self.release = result
            self.label.setText(f'Neue Testversion verfügbar: {result.get("name", result["tag_name"])}\nDownload und Installation erfolgen im Hintergrund in einen separaten Versionsordner.')
            self.button.setText('Update herunterladen und installieren')
        else:
            self.installed = Path(result)
            self.label.setText(f'Update installiert:\n{result}\nDie bisherige Installation wurde nicht verändert.')
            self.button.setText('Neue Version starten')

    def failed(self, message):
        self.label.setText('Update nicht installiert. Die bisherige Installation bleibt erhalten.\n' + message)

    def cancel_update(self):
        if self.worker and self.worker.isRunning():
            self.worker.requestInterruption()
            self.label.setText("Vorgang wird abgebrochen. Eine laufende Netzwerkanfrage kann noch bis zu 60 Sekunden benötigen.")

    def closeEvent(self, event):
        if any(worker.isRunning() for worker in self.workers):
            self.cancel_update()
            event.ignore()
        else:
            event.accept()

    def reject(self):
        if any(worker.isRunning() for worker in self.workers):
            self.cancel_update()
        else:
            super().reject()
