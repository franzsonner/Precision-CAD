"""Precision CAD desktop test application."""
import os
os.environ.setdefault("QT_API", "pyside6")
import sys
from pathlib import Path
from model import Part, Document, read_step, write_step
from features import Feature, edge_measure, exact_box
from ui_icons import icon_for
import math
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtCore import Qt, QTimer, QSize
import pyvista as pv
from pyvistaqt import QtInteractor
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QDoubleSpinBox, QLabel, QFileDialog, QMessageBox, QListWidget, QTabWidget, QAbstractItemView, QScrollArea, QComboBox, QToolButton, QDialog
)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Precision CAD – Windows-Testversion 0.5")
        self.resize(1100, 720)
        self.document = Document()
        self.saved_signature = ()
        self.test_mode = "--smoke-test" in sys.argv
        self.entity = None
        self.edge_selection = []
        self.measure_selection = []
        self.picked_point = None
        self.actor_entities = {}
        self.drag_session = None
        toolbar = self.addToolBar("Bearbeiten")
        self.undo_action = QAction("Rückgängig", self)
        self.undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        self.undo_action.triggered.connect(self.undo)
        toolbar.addAction(self.undo_action)
        self.redo_action = QAction("Wiederholen", self)
        self.redo_action.setShortcuts([QKeySequence("Ctrl+Y"), QKeySequence("Ctrl+Shift+Z")])
        self.redo_action.triggered.connect(self.redo)
        toolbar.addAction(self.redo_action)
        toolbar.addSeparator()
        updates = QAction("Updates", self)
        updates.triggered.connect(self.open_updates)
        toolbar.addAction(updates)
        self.undo_action.setEnabled(False)
        self.redo_action.setEnabled(False)
        root = QWidget()
        self.setCentralWidget(root)
        outer = QVBoxLayout(root)
        ribbon = QTabWidget()
        outer.addWidget(ribbon)
        body = QWidget()
        outer.addWidget(body, 1)
        layout = QHBoxLayout(body)
        for title, actions in [
            ("Start", [("Quader", self.add_box), ("Zylinder", self.add_cylinder), ("Projekt öffnen", self.open_project), ("Beispiel", self.open_example), ("Projekt speichern", self.save_project), ("STEP öffnen", self.open_step), ("STEP speichern", self.save_step)]),
            ("Bearbeiten", [("Bohrung", self.make_hole), ("Radius", lambda:self.round_edges(False)), ("Fase", lambda:self.round_edges(True)), ("Fläche neigen", self.draft_face), ("Drehen", self.rotate_part), ("Mausverschieben", self.drag_part), ("Vereinigen", lambda:self.combine_parts(False)), ("Abziehen", lambda:self.combine_parts(True)), ("Löschen", self.delete_parts)]),
            ("Schritte", [("Bearbeitungsschritte", self.open_feature_history)]),
            ("Prüfen", [("Kantenmaß ändern", self.edit_edge_length), ("Maß in Zeichnung", self.record_measurement)]),
            ("Normteile", [("Normteil einfügen", self.open_catalogue)]),
            ("Assistent", [("Text / Diktat / KI", self.open_assistant)]),
            ("Ansicht", [("Einpassen", lambda: self.viewer.reset_camera()),
                         ("Isometrisch", lambda: self.viewer.view_isometric()),
                         ("Vorne", lambda: self.viewer.view_xz()),
                         ("Oben", lambda: self.viewer.view_xy()),
                         ("Rechts", lambda: self.viewer.view_yz())]),
            ("Zeichnung", [("A4-Blatt / PDF / SVG", self.open_drawing)]),
        ]:
            tab = QWidget()
            bar = QHBoxLayout(tab)
            for label, callback in actions:
                button = QToolButton()
                button.setText(label)
                button.setIcon(icon_for(label))
                button.setIconSize(QSize(36,36))
                button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
                button.setMinimumHeight(65)
                button.clicked.connect(callback)
                bar.addWidget(button)
            bar.addStretch()
            ribbon.addTab(tab, title)
        ribbon.setMaximumHeight(110)
        self.statusBar().showMessage("Bauteil auswählen → Maße ändern → Anwenden | Zeichnung: A4-Vorschau und PDF/SVG")
        sidebar = QWidget()
        controls = QVBoxLayout(sidebar)
        self.pick_mode = QComboBox()
        self.pick_mode.addItems(["Bauteil", "Fläche", "Kante", "Messen (2 Kanten)"])
        controls.addWidget(QLabel("3D-Auswahl mit Rechtsklick"))
        controls.addWidget(self.pick_mode)
        self.entity_label = QLabel("Kein geometrisches Element gewählt.")
        controls.addWidget(self.entity_label)
        controls.addWidget(QLabel("Maße in Millimetern"))
        self.sizes = []
        for name, default in [("Länge / Radius", 50), ("Breite", 30), ("Höhe", 20)]:
            controls.addWidget(QLabel(name))
            field = QDoubleSpinBox()
            field.setRange(0.1, 100000)
            field.setValue(default)
            self.sizes.append(field)
            controls.addWidget(field)
        for title, fn in [
            ("Maße auf Auswahl anwenden", self.resize_selected),
            ("Ansicht einpassen", lambda: self.viewer.reset_camera()),
        ]:
            button = QPushButton(title)
            button.clicked.connect(fn)
            controls.addWidget(button)
        self.items = QListWidget()
        controls.addWidget(QLabel("Bauteile"))
        controls.addWidget(self.items)
        self.items.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.items.setMinimumHeight(100)
        self.items.setMaximumHeight(160)
        controls.addWidget(QLabel("Strg/Shift: mehrere Bauteile auswählen"))
        controls.addWidget(QLabel("Position X / Y / Z (mm), einzelnes Bauteil"))
        self.positions = self.vector_fields(controls)
        self.position_button = QPushButton("Position übernehmen")
        self.position_button.clicked.connect(self.position_selected)
        controls.addWidget(self.position_button)
        controls.addWidget(QLabel("Verschiebung ΔX / ΔY / ΔZ (mm), gesamte Auswahl"))
        self.deltas = self.vector_fields(controls)
        move = QPushButton("Auswahl verschieben")
        move.clicked.connect(self.move_selected)
        controls.addWidget(move)
        controls.addWidget(QLabel("Linke Maustaste: drehen\nMausrad: zoomen\nShift + linke Maustaste: Ansicht verschieben"))
        controls.addStretch()
        for label in sidebar.findChildren(QLabel):
            label.setWordWrap(True)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(sidebar)
        scroll.setMinimumWidth(290)
        layout.addWidget(scroll, 1)
        self.viewer = QtInteractor(root)
        layout.addWidget(self.viewer, 4)
        self.viewer.enable_trackball_style()
        self.viewer.enable_parallel_projection()
        self.viewer.set_background("#f3f6fa")
        self.viewer.add_axes()
        self.items.itemSelectionChanged.connect(self.selection_changed)
        self.pick_mode.currentIndexChanged.connect(lambda _:self.redraw(reset=False))
        self.viewer.enable_surface_point_picking(callback=self.pick_callback, use_picker=True, show_message=False, show_point=False, tolerance=.008)
        self.selection_changed()

    @property
    def parts(self):
        return self.document.parts

    def vector_fields(self, controls):
        fields = []
        for axis in "XYZ":
            field = QDoubleSpinBox()
            field.setRange(-100000, 100000)
            field.setDecimals(3)
            field.setPrefix(axis + ": ")
            controls.addWidget(field)
            fields.append(field)
        return fields

    def selected_rows(self):
        return sorted(self.items.row(item) for item in self.items.selectedItems())

    def refresh(self, rows=None, reset=False):
        self.drag_session = None
        self.viewer.clear_box_widgets()
        if rows is None:
            rows = self.selected_rows()
        self.items.blockSignals(True)
        self.items.clear()
        for index, part in enumerate(self.parts):
            self.items.addItem(f"{part.name} {index + 1}")
        for row in rows:
            if 0 <= row < len(self.parts):
                self.items.item(row).setSelected(True)
        self.items.blockSignals(False)
        self.undo_action.setEnabled(bool(self.document.undo_stack))
        self.redo_action.setEnabled(bool(self.document.redo_stack))
        self.selection_changed()
        self.setWindowTitle("Precision CAD – Windows-Testversion 0.5"+(" *" if self.state_signature()!=self.saved_signature else ""))
        if reset:
            self.viewer.reset_camera()

    def undo(self):
        self.document.undo()
        self.refresh()

    def redo(self):
        self.document.redo()
        self.refresh()

    def selection_changed(self):
        self.drag_session = None
        self.viewer.clear_box_widgets()
        self.entity = None
        self.edge_selection = []
        self.measure_selection = []
        self.entity_label.setText("Kein geometrisches Element gewählt.")
        rows = self.selected_rows()
        self.select_part(rows[0] if len(rows) == 1 else -1)
        for field in self.positions:
            field.setEnabled(len(rows) == 1)
        self.position_button.setEnabled(len(rows) == 1)
        if len(rows) == 1:
            for field, value in zip(self.positions, self.parts[rows[0]].position):
                field.setValue(value)
        self.redraw(reset=False)

    def position_selected(self):
        rows = self.selected_rows()
        if len(rows) != 1:
            return
        try:
            self.document.position(rows[0], [field.value() for field in self.positions])
            self.refresh(rows)
        except Exception as exc:
            QMessageBox.critical(self, "Position", str(exc))

    def move_selected(self):
        rows = self.selected_rows()
        try:
            self.document.translate(rows, [field.value() for field in self.deltas])
            self.refresh(rows)
            for field in self.deltas:
                field.setValue(0)
        except Exception as exc:
            QMessageBox.critical(self, "Verschieben", str(exc))

    def values(self):
        return [f.value() for f in self.sizes]

    def add_box(self):
        x, y, z = self.values()
        self.create_part("Quader", (x, y, z))

    def add_cylinder(self):
        radius, _, height = self.values()
        self.create_part("Zylinder", (radius, self.values()[1], height))

    def create_part(self, kind, dimensions):
        try:
            self.append_part(Part.create(kind, dimensions))
        except Exception as exc:
            QMessageBox.critical(self, "Geometriefehler", str(exc))

    def append_part(self, part):
        self.document.add(part)
        self.refresh([len(self.parts) - 1], reset=True)

    def select_part(self, row):
        part = self.parts[row] if row >= 0 else None
        for field in self.sizes:
            field.setEnabled(part is None or part.kind is not None)
        if part and part.dimensions:
            for field, value in zip(self.sizes, part.dimensions):
                field.setValue(value)
        self.sizes[1].setEnabled(part is None or part.kind == "Quader")

    def resize_selected(self):
        rows = self.selected_rows()
        row = rows[0] if len(rows) == 1 else -1
        if row < 0 or self.parts[row].kind is None:
            QMessageBox.information(self, "Maße", "Bitte einen erzeugten Quader oder Zylinder auswählen.")
            return
        try:
            self.document.resize(row, self.values())
            self.refresh([row])
        except Exception as exc:
            QMessageBox.critical(self, "Geometriefehler", str(exc))

    def redraw(self, reset=True):
        self.viewer.clear()
        self.viewer.add_axes()
        selected = self.selected_rows()
        self.actor_entities = {}
        edge_mode = self.pick_mode.currentIndex() >= 2
        for index, part in enumerate(self.parts):
            for fi, face in enumerate(part.shape.Faces()):
                vertices, triangles = face.tessellate(.15)
                if not vertices or not triangles:
                    continue
                points = [[v.x,v.y,v.z] for v in vertices]
                faces = [value for triangle in triangles for value in (3,*triangle)]
                mesh = pv.PolyData(points,faces)
                active = self.entity == (index,'face',fi)
                actor = self.viewer.add_mesh(mesh,color='#ef9251' if active else '#f6b75d' if index in selected else '#9ebfe3',smooth_shading=True,pickable=not edge_mode)
                self.actor_entities[actor.GetAddressAsString('')] = (index,'face',fi)
            for ei, edge in enumerate(part.shape.Edges()):
                points,_ = edge.sample(2 if edge.geomType() == 'LINE' else 80)
                if len(points)<2:
                    continue
                mesh=pv.lines_from_points([p.toTuple() for p in points])
                active=index in selected and ei in self.edge_selection
                actor=self.viewer.add_mesh(mesh,color='#dc3f83' if active else '#31475f',line_width=5 if active else 3 if edge_mode else 1.3,pickable=edge_mode)
                self.actor_entities[actor.GetAddressAsString('')] = (index,'edge',ei)
        if reset:
            self.viewer.reset_camera()

    def one_row(self):
        rows = self.selected_rows()
        if len(rows) != 1:
            raise ValueError('Bitte genau ein Bauteil auswählen.')
        return rows[0]

    def error(self, exc):
        QMessageBox.warning(self, 'Bearbeitung nicht übernommen', str(exc) or 'Geometrie nicht möglich. Kleinere Werte oder eine andere Auswahl versuchen.')

    def pick_callback(self, point, picker):
        actor=picker.GetActor()
        info=self.actor_entities.get(actor.GetAddressAsString('')) if actor else None
        if info:
            ctrl=bool(QApplication.keyboardModifiers() & Qt.KeyboardModifier.ControlModifier)
            QTimer.singleShot(0,lambda:self.apply_pick(info,tuple(point),ctrl))

    def apply_pick(self, info, point, ctrl=False):
        row,kind,index=info
        if row>=len(self.parts):return
        previous=list(self.edge_selection) if self.entity and self.entity[0]==row else []
        measured=list(self.measure_selection) if self.entity and self.entity[0]==row else []
        self.items.blockSignals(True)
        self.items.clearSelection();self.items.item(row).setSelected(True)
        self.items.blockSignals(False)
        self.selection_changed()
        self.entity=(row,kind,index);self.picked_point=point
        if kind=='edge':
            self.edge_selection=list(dict.fromkeys([*previous,index])) if ctrl else [index]
            self.measure_selection=([*measured,index][-2:] if self.pick_mode.currentIndex()==3 else [index])
            length,_=edge_measure(self.parts[row].shape,index)
            text=f'Kante {index+1}: Länge {length:.3f} mm'
            if len(self.measure_selection)==2:
                distance,angle=edge_measure(self.parts[row].shape,*self.measure_selection)
                text+=f' | Abstand: {distance:.3f} mm'
                if angle is not None:text+=f' | kleiner Winkel: {angle:.3f}°'
                self.edge_selection=self.measure_selection[:]
            self.entity_label.setText(text)
        else:
            face=self.parts[row].shape.Faces()[index]
            self.entity_label.setText(f'Fläche {index+1}: {face.geomType()}, {face.Area():.3f} mm²')
        self.redraw(reset=False)

    def make_hole(self):
        try:
            from feature_dialogs import HoleDialog
            row=self.one_row()
            fi=self.entity[2] if self.entity and self.entity[1]=='face' else None
            dialog=HoleDialog(self.parts[row],fi,self.picked_point if fi is not None else None,self)
            if dialog.exec()==QDialog.DialogCode.Accepted:
                self.document.feature(row,dialog.feature());self.refresh([row])
        except Exception as exc:self.error(exc)

    def round_edges(self, chamfer=False):
        try:
            from feature_dialogs import ValueDialog
            row=self.one_row()
            if not self.edge_selection:raise ValueError('Auswahlmodus Kante wählen und Kanten mit Rechtsklick auswählen. Strg fügt weitere Kanten hinzu.')
            indices=tuple(self.edge_selection)
            dialog=ValueDialog('Fase' if chamfer else 'Radius','Fasenbreite / Radius (mm)',parent=self)
            if dialog.exec()==QDialog.DialogCode.Accepted:
                self.document.feature(row,Feature('chamfer' if chamfer else 'fillet',(indices,dialog.value.value())));self.refresh([row])
        except Exception as exc:self.error(exc)

    def draft_face(self):
        try:
            from feature_dialogs import AngleDialog
            row=self.one_row()
            if not self.entity or self.entity[1]!='face':raise ValueError('Zuerst eine ebene Seitenfläche im Modus Fläche per Rechtsklick auswählen.')
            index=self.entity[2]
            dialog=AngleDialog('Fläche neigen',True,self)
            if dialog.exec()==QDialog.DialogCode.Accepted:
                self.document.feature(row,Feature('draft',(index,dialog.axis.currentIndex(),dialog.angle.value())));self.refresh([row])
        except Exception as exc:self.error(exc)

    def rotate_part(self):
        try:
            from feature_dialogs import AngleDialog
            row=self.one_row();dialog=AngleDialog('Bauteil drehen',False,self)
            if dialog.exec()==QDialog.DialogCode.Accepted:
                self.document.feature(row,Feature('rotate',(dialog.axis.currentIndex(),dialog.angle.value())));self.refresh([row])
        except Exception as exc:self.error(exc)

    def edit_edge_length(self):
        try:
            from feature_dialogs import ValueDialog
            row=self.one_row();part=self.parts[row]
            if not self.entity or self.entity[1]!='edge':raise ValueError('Zuerst eine gerade Kante auswählen.')
            edge=part.shape.Edges()[self.entity[2]]
            if edge.geomType()!='LINE' or part.kind not in ('Quader','Zylinder') or any(f.kind=='rotate' for f in part.features):
                raise ValueError('Diese Kante ist nur messbar. Direkte Maßänderung gibt es für vollständige Grundkanten eines ungedrehten Quaders bzw. die Zylinderhöhe.')
            direction=edge.tangentAt();coords=[abs(direction.x),abs(direction.y),abs(direction.z)];axis=max(range(3),key=lambda i:coords[i])
            if coords[axis]<.999 or (part.kind=='Zylinder' and axis!=2) or abs(edge.Length()-part.dimensions[axis])>1e-4:
                raise ValueError('Diese Kante entspricht keinem unveränderten Grundmaß. Bitte Grundmaße links bearbeiten.')
            dialog=ValueDialog('Kantenmaß ändern','Neue Länge (mm)',edge.Length(),parent=self)
            if dialog.exec()==QDialog.DialogCode.Accepted:
                dims=list(part.dimensions);dims[axis]=dialog.value.value();self.document.resize(row,dims);self.refresh([row])
        except Exception as exc:self.error(exc)

    def record_measurement(self):
        try:
            row=self.one_row()
            if not self.measure_selection:raise ValueError('Eine Kante oder im Modus Messen zwei Kanten auswählen.')
            self.document.measure(row,self.measure_selection[0],self.measure_selection[1] if len(self.measure_selection)>1 else None)
            self.refresh([row]);self.statusBar().showMessage('Messwert zur Zeichnung hinzugefügt. Zeichnung öffnen, um ihn zu sehen.')
        except Exception as exc:self.error(exc)

    def drag_part(self):
        try:
            row=self.one_row();part=self.parts[row];bb=exact_box(part.shape)
            origin=((bb.xmin+bb.xmax)/2,(bb.ymin+bb.ymax)/2,(bb.zmin+bb.zmax)/2)
            anchor=part.position;token=object();self.drag_session=token
            self.viewer.clear_box_widgets()
            def changed(box,widget):
                widget.ScalingEnabledOff()
                delta=tuple(a-b for a,b in zip(box.center,origin))
                if self.drag_session is token and sum(v*v for v in delta)>1e-10:
                    def commit():
                        if self.drag_session is token:
                            try:
                                self.document.position(row,tuple(a+b for a,b in zip(anchor,delta)));self.refresh([row])
                            except Exception as exc:self.error(exc)
                    QTimer.singleShot(0,commit)
            self.viewer.add_box_widget(changed,bounds=(bb.xmin,bb.xmax,bb.ymin,bb.ymax,bb.zmin,bb.zmax),factor=1.,rotation_enabled=False,pass_widget=True,interaction_event='end',color='#d6851e')
            self.statusBar().showMessage('Verschieberahmen mit linker Maustaste ziehen und loslassen. Nur Verschieben; ein Rückgängig-Schritt.')
        except Exception as exc:self.error(exc)

    def combine_parts(self,cut=False):
        try:
            rows=self.selected_rows()
            if len(rows)<2:raise ValueError('Mindestens zwei Körper mit Strg auswählen. Beim Abziehen ist der erste in der Liste der Zielkörper.')
            self.document.combine(rows,cut);self.refresh([len(self.parts)-1],reset=True)
        except Exception as exc:self.error(exc)

    def delete_parts(self):
        rows=self.selected_rows()
        if rows:self.document.delete(rows);self.refresh([])

    def open_feature_history(self):
        try:
            from feature_history import FeatureHistoryDialog
            FeatureHistoryDialog(self,self.one_row()).exec()
        except Exception as exc:self.error(exc)

    def open_catalogue(self):
        try:
            from feature_dialogs import CatalogueDialog
            dialog=CatalogueDialog(self)
            if dialog.exec()==QDialog.DialogCode.Accepted:self.append_part(dialog.part())
        except Exception as exc:self.error(exc)

    def open_assistant(self):
        from assistant_dialog import AssistantDialog
        AssistantDialog(self).exec()

    def state_signature(self):
        return tuple((p.name,p.kind,p.dimensions,p.position,repr(p.features),p.measurements,id(p.shape)) for p in self.parts)

    def allow_document_close(self):
        if self.test_mode or self.state_signature()==self.saved_signature:return True
        dialog=QMessageBox(self);dialog.setWindowTitle('Ungespeicherte Änderungen')
        dialog.setText('Projekt mit Maßen und Bearbeitungsschritten vor dem Schließen speichern?')
        save=dialog.addButton('Projekt speichern',QMessageBox.ButtonRole.AcceptRole)
        discard=dialog.addButton('Ohne Speichern',QMessageBox.ButtonRole.DestructiveRole)
        dialog.addButton('Abbrechen',QMessageBox.ButtonRole.RejectRole);dialog.exec()
        return self.save_project() if dialog.clickedButton() is save else dialog.clickedButton() is discard

    def closeEvent(self,event):
        from PySide6.QtCore import QThread
        if any(thread.isRunning() for thread in self.findChildren(QThread)):
            QMessageBox.information(self,'Vorgang läuft','Bitte laufenden Download oder KI-Vorgang zuerst beenden.');event.ignore();return
        if self.allow_document_close():event.accept()
        else:event.ignore()

    def save_project(self):
        path,_=QFileDialog.getSaveFileName(self,'Projekt speichern','','Precision CAD (*.pcad)')
        if path:
            try:
                from projects import save_project
                save_project(self.parts,Path(path).with_suffix('.pcad'));self.saved_signature=self.state_signature()
                self.setWindowTitle('Precision CAD – Windows-Testversion 0.5')
                self.statusBar().showMessage('Projekt mit Grundmaßen und Bearbeitungsschritten gespeichert.');return True
            except Exception as exc:self.error(exc)
        return False

    def open_example(self):
        if not self.allow_document_close():return
        try:
            from projects import load_project
            root=Path(sys.executable).parent if getattr(sys,"frozen",False) else Path(__file__).resolve().parents[1]
            parts=load_project(root/"examples"/"Bohrplatte.pcad")
            self.document.replace_parts(parts);self.saved_signature=self.state_signature();self.refresh([0],reset=True)
        except Exception as exc:self.error(exc)

    def open_project(self):
        if not self.allow_document_close():return
        path,_=QFileDialog.getOpenFileName(self,'Projekt öffnen','','Precision CAD (*.pcad)')
        if path:
            try:
                from projects import load_project
                parts=load_project(path);self.document.replace_parts(parts);self.saved_signature=self.state_signature();self.refresh([0] if parts else [],reset=True)
            except Exception as exc:self.error(exc)

    def open_updates(self):
        from update_dialog import UpdateDialog
        UpdateDialog(self).exec()

    def open_drawing(self):
        rows = self.selected_rows()
        row = rows[0] if len(rows) == 1 else -1
        if row < 0:
            QMessageBox.information(self, "Zeichnung", "Bitte zuerst ein Bauteil auswählen.")
            return
        try:
            from drawing_dialog import DrawingDialog
            def resize_from_drawing(dimensions):
                self.document.resize(row,dimensions);self.refresh([row]);return self.parts[row]
            def measurement_from_drawing(first,second):
                self.document.measure(row,first,second);self.refresh([row]);return self.parts[row]
            DrawingDialog(self.parts[row], self, on_resize=resize_from_drawing, on_measurement=measurement_from_drawing).exec()
        except Exception as exc:
            QMessageBox.critical(self, "Zeichnung", str(exc))

    def open_step(self):
        path, _ = QFileDialog.getOpenFileName(self, "STEP öffnen", "", "STEP (*.step *.stp)")
        if not path:
            return
        try:
            self.append_part(read_step(path))
        except Exception as exc:
            QMessageBox.critical(self, "Importfehler", str(exc))

    def save_step(self):
        if not self.parts:
            QMessageBox.information(self, "Keine Bauteile", "Bitte zuerst ein Bauteil erstellen.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "STEP speichern", "modell.step", "STEP (*.step)")
        if not path:
            return
        try:
            path = str(Path(path).with_suffix(".step"))
            write_step(self.parts, path)
            QMessageBox.information(self, "Gespeichert", path)
        except Exception as exc:
            QMessageBox.critical(self, "Exportfehler", str(exc))

def main():
    app = QApplication(sys.argv)
    if "--smoke-test" in sys.argv:
        from PySide6.QtCore import QTimer
        window = MainWindow()
        window.show()
        def check():
            import tempfile
            try:
                from update_dialog import UpdateDialog
                update_dialog = UpdateDialog(window)
                assert update_dialog.button.text() == "Auf Updates prüfen"
                update_dialog.close()
                window.add_box()
                window.add_cylinder()
                window.sizes[0].setValue(12)
                window.resize_selected()
                window.positions[0].setValue(8)
                window.positions[2].setValue(10)
                window.position_selected()
                assert window.parts[1].position == (8, 0, 10)
                window.undo()
                assert window.parts[1].position == (0, 0, 0)
                window.redo()
                assert window.parts[1].position == (8, 0, 10)
                window.items.item(0).setSelected(True)
                window.deltas[1].setValue(5)
                window.move_selected()
                assert window.parts[0].position == (0, 5, 0)
                assert window.parts[1].position == (8, 5, 10)
                window.undo()
                assert window.parts[0].position == (0, 0, 0)
                window.redo()
                window.items.item(0).setSelected(False)
                window.sizes[2].setValue(25)
                window.resize_selected()
                assert window.parts[1].position == (8, 5, 10)
                print('Smoke: selecting faces and making a real bore',flush=True)
                from feature_dialogs import HoleDialog,CatalogueDialog
                from feature_history import FeatureHistoryDialog,HoleEditDialog
                window.pick_mode.setCurrentIndex(1)
                shape=window.parts[0].shape
                face=max(range(len(shape.Faces())),key=lambda i:shape.Faces()[i].Center().z)
                point=shape.Faces()[face].Center().toTuple()
                window.apply_pick((0,'face',face),point)
                assert window.entity==(0,'face',face)
                hole=HoleDialog(window.parts[0],face,point,window);hole.diameter.setValue(6)
                window.document.feature(0,hole.feature());window.refresh([0])
                assert window.parts[0].shape.Volume()<30000
                edge=next(i for i,e in enumerate(window.parts[0].shape.Edges()) if e.geomType()=='LINE')
                window.document.feature(0,Feature('fillet',((edge,),1.5)));window.refresh([0])
                editor=HoleEditDialog(window.parts[0].features[0],window);editor.diameter.setValue(8)
                window.document.change_feature(0,0,editor.feature());window.refresh([0])
                history=FeatureHistoryDialog(window,0);assert history.items.count()==2;history.close()
                standard=CatalogueDialog(window);window.append_part(standard.part())
                assert 'M10' in window.parts[-1].name
                print('Smoke: parametric drawing and mouse move',flush=True)
                from drawing_dialog import DrawingDialog
                from PySide6.QtWidgets import QInputDialog
                def resize_document(dims):
                    window.document.resize(0,dims);window.refresh([0]);return window.parts[0]
                def measure_document(a,b):
                    window.document.measure(0,a,b);window.refresh([0]);return window.parts[0]
                drawing=DrawingDialog(window.parts[0],window,on_resize=resize_document,on_measurement=measure_document)
                old_input=QInputDialog.getDouble
                QInputDialog.getDouble=lambda *args,**kwargs:(60.,True)
                try:
                    from PySide6.QtTest import QTest
                    from PySide6.QtCore import QPoint
                    drawing.show();QApplication.processEvents()
                    rect=next(rect for rect,axis in drawing.preview.targets if axis==0 and rect.x()>=580)
                    scale,ox,oy=drawing.preview.transform();center=rect.center()
                    QTest.mouseClick(drawing.preview,Qt.MouseButton.LeftButton,pos=QPoint(round(ox+center.x()*scale),round(oy+center.y()*scale)))
                finally:QInputDialog.getDouble=old_input
                print("Drawing edit result",window.parts[0].dimensions,len(window.parts[0].features),flush=True)
                assert window.parts[0].dimensions[0]==60 and len(window.parts[0].features)==2
                drawing.add_measurement(0,None)
                assert window.parts[0].measurements
                drawing.show();QApplication.processEvents()
                from PySide6.QtTest import QTest
                from PySide6.QtCore import QPoint
                drawing.measure_mode.setChecked(True)
                candidates=[points for _,points in drawing.preview.paths if len(points)==2 and abs(points[0][0]-points[1][0])<1e-5 and abs(points[0][1]-points[1][1])>20]
                assert len(candidates)>=2
                for points in (min(candidates,key=lambda p:p[0][0]),max(candidates,key=lambda p:p[0][0])):
                    x=(points[0][0]+points[1][0])/2;y=(points[0][1]+points[1][1])/2
                    scale,ox,oy=drawing.preview.transform()
                    QTest.mouseClick(drawing.preview,Qt.MouseButton.LeftButton,pos=QPoint(round(ox+x*scale),round(oy+y*scale)))
                assert len(window.parts[0].measurements)==2
                drawing.close()
                window.items.clearSelection();window.items.item(0).setSelected(True)
                original=window.parts[0].position
                window.drag_part()
                from vtkmodules.vtkCommonTransforms import vtkTransform
                widget=window.viewer.widgets.box_widgets[-1];transform=vtkTransform();transform.Translate(5,0,0)
                widget.SetTransform(transform);widget.InvokeEvent('EndInteractionEvent');QApplication.processEvents()
                assert abs(window.parts[0].position[0]-original[0]-5)<1e-5
                window.undo();assert window.parts[0].position==original
                from assistant_dialog import AssistantDialog
                assistant=AssistantDialog(window);assistant.prompt.setPlainText('Quader 10 20 30');assistant.prepare()
                assert assistant.candidate is not None and len(window.parts)==3
                assistant.reject()
                print('Smoke: native project round trip',flush=True)
                with tempfile.TemporaryDirectory() as folder:
                    from projects import save_project,load_project
                    project=Path(folder)/'smoke.pcad';save_project(window.parts,project)
                    loaded=load_project(project)
                    assert len(loaded)==3 and len(loaded[0].features)==2
                    window.document.replace_parts(loaded);window.refresh([0])
                    path = Path(folder) / "smoke.step"
                    write_step(window.parts, path)
                    assert read_step(path).shape.isValid()
                    from drawing_dialog import DrawingDialog, write_pdf
                    drawing = DrawingDialog(window.parts[0], window)
                    assert b"svg" in drawing.svg
                    write_pdf(drawing.svg, Path(folder) / "drawing.pdf")
                    assert (Path(folder) / "drawing.pdf").stat().st_size > 1000
                window.open_example()
                assert len(window.parts)==1 and len(window.parts[0].features)==6
                window.findChildren(QTabWidget)[0].setCurrentIndex(1)
                window.viewer.camera.azimuth += 30
                window.viewer.render()
                window.viewer.screenshot(str(Path.cwd() / "smoke.png"))
                window.grab().save(str(Path.cwd() / "smoke-ui.png"))
                window.viewer.close()
                window.close()
                app.exit(0)
            except Exception:
                import traceback
                traceback.print_exc()
                app.exit(1)
        QTimer.singleShot(1500, check)
        return app.exec()
    window = MainWindow()
    window.show()
    result = app.exec()
    window.viewer.close()
    return result

if __name__ == "__main__":
    sys.exit(main())
