import json
import os
import sys
from PySide6.QtCore import QThread,Signal
from PySide6.QtWidgets import QDialog,QVBoxLayout,QLabel,QTextEdit,QCheckBox,QLineEdit,QPushButton,QMessageBox
import pyvista as pv
from assistant_core import offline_command,ai_command,proposal


class AIWorker(QThread):
    result=Signal(object);error=Signal(str)
    def __init__(self,text,key,parent):super().__init__(parent);self.text=text;self.key=key
    def run(self):
        try:self.result.emit(ai_command(self.text,self.key))
        except Exception as exc:self.error.emit(str(exc))
        finally:self.key=''


class AssistantDialog(QDialog):
    def __init__(self,main):
        super().__init__(main);self.main=main;self.candidate=None;self.worker=None
        self.setWindowTitle('Befehlsassistent – Text, Windows-Diktat und optionale KI');self.resize(620,600)
        layout=QVBoxLayout(self)
        tip=QLabel('Text eingeben oder unter Windows in das Textfeld klicken und Win+H zum Diktieren drücken. Offline stehen feste Befehlsvorlagen zur Verfügung.');tip.setWordWrap(True);layout.addWidget(tip)
        self.prompt=QTextEdit();self.prompt.setPlaceholderText('Quader 80 40 20\nBohrung 8 15 30\nRadius 2\nVerschieben 10 0 0');layout.addWidget(self.prompt)
        dictate=QPushButton("Windows-Diktat starten (Win+H)");dictate.setEnabled(sys.platform=="win32");dictate.clicked.connect(self.dictate);layout.addWidget(dictate)
        self.ai=QCheckBox('OpenAI-KI verwenden (eigener API-Schlüssel; mögliche API-Kosten)');layout.addWidget(self.ai)
        self.key=QLineEdit();self.key.setEchoMode(QLineEdit.EchoMode.Password);self.key.setPlaceholderText('API-Schlüssel – nur für diese Sitzung');self.key.setText(os.environ.get('OPENAI_API_KEY',''));layout.addWidget(self.key)
        privacy=QLabel('Nur bei eingeschalteter KI wird der eingegebene Text an OpenAI gesendet. Keine CAD-Dateien; keine automatische Ausführung. Ein ChatGPT-Abo ersetzt keinen API-Zugang.');privacy.setWordWrap(True);layout.addWidget(privacy)
        self.preview=QPushButton('Befehl prüfen und Geometrie vorschauen');self.preview.clicked.connect(self.prepare);layout.addWidget(self.preview)
        self.result=QTextEdit();self.result.setReadOnly(True);layout.addWidget(self.result)
        self.apply=QPushButton('Vorschlag übernehmen');self.apply.setEnabled(False);self.apply.clicked.connect(self.commit);layout.addWidget(self.apply)
        self.prompt.textChanged.connect(self.invalidate);self.ai.toggled.connect(self.invalidate)

    def dictate(self):
        if sys.platform != "win32":return
        self.prompt.setFocus()
        import ctypes
        user=ctypes.windll.user32
        try:
            user.keybd_event(0x5B,0,0,0);user.keybd_event(0x48,0,0,0)
        finally:
            user.keybd_event(0x48,0,2,0);user.keybd_event(0x5B,0,2,0)

    def invalidate(self,*_):
        self.candidate=None;self.apply.setEnabled(False)
        self.main.viewer.remove_actor('assistant-preview',render=True)

    def prepare(self):
        self.invalidate()
        if self.ai.isChecked():
            self.preview.setEnabled(False);self.prompt.setEnabled(False)
            self.worker=AIWorker(self.prompt.toPlainText(),self.key.text(),self)
            self.worker.result.connect(self.show_proposal);self.worker.error.connect(self.result.setPlainText)
            self.worker.finished.connect(lambda:self.preview.setEnabled(True));self.worker.finished.connect(lambda:self.prompt.setEnabled(True))
            self.worker.start()
        else:
            try:self.show_proposal(offline_command(self.prompt.toPlainText()))
            except Exception as exc:self.result.setPlainText(str(exc))

    def show_proposal(self,command):
        try:
            rows=self.main.selected_rows();row=rows[0] if len(rows)==1 else None
            entity=self.main.entity
            face=entity[2] if entity and entity[1]=='face' else None
            part,target=proposal(command,self.main.parts,row,face,self.main.picked_point,self.main.edge_selection)
            vertices,triangles=part.shape.tessellate(.2)
            mesh=pv.PolyData([v.toTuple() for v in vertices],[v for tri in triangles for v in (3,*tri)])
            self.main.viewer.add_mesh(mesh,name='assistant-preview',color='#45cc95',opacity=.55,pickable=False)
            self.main.viewer.reset_camera()
            self.candidate=(part,target);self.apply.setEnabled(True)
            self.result.setPlainText(json.dumps(command,ensure_ascii=False,indent=2)+f'\n\nVolumen: {part.shape.Volume():.3f} mm³\nGrüne Vorschau; noch keine Änderung am Dokument.')
        except Exception as exc:self.result.setPlainText(str(exc))

    def commit(self):
        if self.candidate:
            part,row=self.candidate
            if row is None:self.main.append_part(part)
            else:self.main.document.replace_part(row,part);self.main.refresh([row])
            self.key.clear();self.accept()

    def closeEvent(self,event):
        if self.worker and self.worker.isRunning():
            self.result.setPlainText('KI-Anfrage läuft noch (maximale Netzwerkwartezeit 60 s).');event.ignore()
        else:self.invalidate();self.key.clear();event.accept()

    def reject(self):
        if self.worker and self.worker.isRunning():return
        self.invalidate();self.key.clear();super().reject()
