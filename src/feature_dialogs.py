import math
import cadquery as cq
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLabel, QComboBox,
    QDoubleSpinBox, QCheckBox, QDialogButtonBox)
from features import Feature, METRIC, drilling_direction, catalogue, unit
from model import Part


def number(default, minimum=.01, maximum=100000):
    field = QDoubleSpinBox()
    field.setDecimals(3); field.setRange(minimum, maximum); field.setValue(default)
    return field


class FormDialog(QDialog):
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(480, 400)
        self.layout = QVBoxLayout(self)
        self.form = QFormLayout()
        self.layout.addLayout(self.form)

    def finish(self, note=''):
        label = QLabel(note); label.setWordWrap(True); self.layout.addWidget(label)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept); buttons.rejected.connect(self.reject)
        self.layout.addWidget(buttons)


class HoleDialog(FormDialog):
    def __init__(self, part, face_index=None, point=None, parent=None):
        super().__init__('Bohrung / Senkung / Gewindekernloch', parent)
        self.part, self.point, self.initial = part, point, face_index
        self.faces = [i for i, f in enumerate(part.shape.Faces()) if f.geomType() == 'PLANE']
        if not self.faces:
            raise ValueError('Für die Bohrung wird eine ebene Startfläche benötigt.')
        self.face = QComboBox()
        for i in self.faces:
            n = part.shape.Faces()[i].normalAt()
            self.face.addItem(f'Fläche {i+1}, Normale ({n.x:.1f}, {n.y:.1f}, {n.z:.1f})')
        default = self.faces.index(face_index) if face_index in self.faces else max(range(len(self.faces)), key=lambda j:part.shape.Faces()[self.faces[j]].Center().z)
        self.face.setCurrentIndex(default)
        self.form.addRow('Startfläche', self.face)
        self.form.addRow(QLabel('Ohne Flächenklick: Flächenmitte; sonst der angeklickte Punkt.'))
        self.offset_u, self.offset_v = number(0, -100000), number(0, -100000)
        self.form.addRow('Versatz U in Fläche (mm)', self.offset_u); self.form.addRow('Versatz V in Fläche (mm)', self.offset_v)
        self.diameter = number(10); self.form.addRow('Durchmesser (mm)', self.diameter)
        self.thread = QComboBox(); self.thread.addItem('Kein Gewinde', None)
        for d in METRIC:self.thread.addItem(f'M{d}', d)
        self.pitch = number(1.5, .1, 8)
        self.form.addRow('Gewindekennzeichnung', self.thread); self.form.addRow('Steigung (mm)', self.pitch)
        self.thread.currentIndexChanged.connect(self.thread_changed); self.pitch.valueChanged.connect(self.thread_changed)
        self.through = QCheckBox('Durch alles'); self.through.setChecked(True)
        self.depth = number(20); self.depth.setEnabled(False)
        self.through.toggled.connect(lambda on:self.depth.setEnabled(not on))
        self.form.addRow(self.through); self.form.addRow('Tiefe entlang Bohrachse (mm)', self.depth)
        self.tilt, self.azimuth = number(0, 0, 85), number(0, -360, 360)
        self.form.addRow('Neigung zur Flächennormalen (°)', self.tilt); self.form.addRow('Richtung in Fläche / Azimut (°)', self.azimuth)
        self.counter = QComboBox(); self.counter.addItems(['Keine', 'Zylindersenkung', 'Kegelsenkung'])
        self.head_d, self.head_depth = number(16), number(3, .01, 170)
        self.form.addRow('Senkung', self.counter); self.form.addRow('Senkdurchmesser (mm)', self.head_d)
        self.form.addRow('Senktiefe (mm) / Kegelwinkel (°)', self.head_depth)
        self.counter.currentIndexChanged.connect(lambda i:self.head_depth.setValue(90 if i == 2 else 3))
        self.finish('Gewinde werden als Kernloch mit Bezeichnung angelegt, ohne spiralförmiges Gewindeprofil. U/V folgen einer lokalen Flächenbasis. 0° Neigung bohrt senkrecht in den Körper.')

    def thread_changed(self, *_):
        d = self.thread.currentData()
        self.diameter.setEnabled(d is None)
        if d is not None:
            self.pitch.setMaximum(d/2)
            if self.sender() is self.thread:
                self.pitch.setValue(METRIC[d][0])
            self.diameter.setValue(round(d-self.pitch.value(),1))

    def feature(self):
        index = self.faces[self.face.currentIndex()]
        face = self.part.shape.Faces()[index]
        normal = face.normalAt().toTuple()
        n = unit(normal)
        reference = cq.Vector(0,0,1) if abs(n.z)<.9 else cq.Vector(1,0,0)
        u = n.cross(reference).normalized(); v = n.cross(u).normalized()
        p = cq.Vector(*self.point) if self.point is not None and index == self.initial else face.Center()
        p = p + u.multiply(self.offset_u.value()) + v.multiply(self.offset_v.value()) - cq.Vector(*self.part.position)
        thread = '' if self.thread.currentData() is None else f'M{self.thread.currentData()}×{self.pitch.value():g}'
        return Feature('hole', (p.toTuple(), drilling_direction(normal,self.tilt.value(),self.azimuth.value()),
            self.diameter.value(),self.depth.value(),self.through.isChecked(),
            ('none','counterbore','countersink')[self.counter.currentIndex()],self.head_d.value(),self.head_depth.value(),thread))


class ValueDialog(FormDialog):
    def __init__(self, title, label, value=2, minimum=.01, maximum=100000, parent=None):
        super().__init__(title,parent); self.value=number(value,minimum,maximum)
        self.form.addRow(label,self.value); self.finish('Die Bearbeitung wird nur übernommen, wenn ein gültiger Volumenkörper entsteht.')


class AngleDialog(FormDialog):
    def __init__(self, title, draft=False, parent=None):
        super().__init__(title,parent)
        self.axis=QComboBox();self.axis.addItems(['X','Y','Z']);self.axis.setCurrentIndex(2)
        self.angle=number(5,-60 if draft else -360,60 if draft else 360)
        self.form.addRow('Zugrichtung' if draft else 'Drehachse durch Bauteil-Bezugspunkt',self.axis)
        self.form.addRow('Winkel (°)',self.angle)
        self.finish('Flächenneigung: ebene Seitenfläche; Neutralebene liegt an der kleinsten Körperkoordinate der Zugrichtung. Positive Winkel tragen Material ab.' if draft else 'Dreht das gesamte ausgewählte Bauteil. Rückgängig ist möglich.')


class CatalogueDialog(FormDialog):
    def __init__(self,parent=None):
        super().__init__('Normteil-Auswahl – vereinfachte Kataloggeometrie',parent)
        self.kind=QComboBox();self.kind.addItems(['Sechskantschraube','Sechskantmutter','Unterlegscheibe'])
        self.size=QComboBox()
        for d in METRIC:self.size.addItem(f'M{d}',d)
        self.size.setCurrentIndex(list(METRIC).index(10))
        self.length=number(30,.1,1000);self.pitch=number(1.5,.1,8)
        self.form.addRow('Teil',self.kind);self.form.addRow('Größe',self.size);self.form.addRow('Länge unter Kopf (mm)',self.length);self.form.addRow('Gewindesteigung (mm)',self.pitch)
        self.size.currentIndexChanged.connect(lambda _:self.pitch.setValue(METRIC[self.size.currentData()][0]))
        self.kind.currentIndexChanged.connect(lambda i:(self.length.setEnabled(i==0),self.pitch.setEnabled(i!=2)))
        self.finish('Vereinfachte Katalogteile, keine zertifizierte Normteilbibliothek. Glatter Schaft / glatte Bohrung, Gewinde nur als Bezeichnung. M10 Standard: 1,5 mm; Feingewinde z. B. 1 mm. Nach dem Einfügen separat positionieren oder drehen.')

    def part(self):
        name,shape=catalogue(('bolt','nut','washer')[self.kind.currentIndex()],self.size.currentData(),self.length.value(),self.pitch.value())
        return Part(name,shape,base_shape=shape)
