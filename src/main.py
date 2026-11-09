"""Precision CAD desktop test application."""
import os
os.environ.setdefault("QT_API", "pyside6")
import sys
from pathlib import Path
from model import Part, Document, read_step, write_step
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtCore import Qt
import pyvista as pv
from pyvistaqt import QtInteractor
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QDoubleSpinBox, QLabel, QFileDialog, QMessageBox, QListWidget, QTabWidget, QAbstractItemView, QScrollArea
)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Precision CAD – Windows-Testversion 0.4")
        self.resize(1100, 720)
        self.document = Document()
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
            ("Start", [("Quader", self.add_box), ("Zylinder", self.add_cylinder), ("STEP öffnen", self.open_step), ("STEP speichern", self.save_step)]),
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
                button = QPushButton(label)
                button.clicked.connect(callback)
                bar.addWidget(button)
            bar.addStretch()
            ribbon.addTab(tab, title)
        ribbon.setMaximumHeight(100)
        self.statusBar().showMessage("Bauteil auswählen → Maße ändern → Anwenden | Zeichnung: A4-Vorschau und PDF/SVG")
        sidebar = QWidget()
        controls = QVBoxLayout(sidebar)
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
        controls.addWidget(QLabel("Linke Maustaste: drehen\nMausrad: zoomen\nShift + linke Maustaste: verschieben"))
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
        if reset:
            self.viewer.reset_camera()

    def undo(self):
        self.document.undo()
        self.refresh()

    def redo(self):
        self.document.redo()
        self.refresh()

    def selection_changed(self):
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
        for index, part in enumerate(self.parts):
            vertices, triangles = part.shape.tessellate(0.1)
            if not vertices or not triangles:
                continue
            points = [[v.x, v.y, v.z] for v in vertices]
            faces = []
            for tri in triangles:
                faces.extend([3, *tri])
            mesh = pv.PolyData(points, faces)
            self.viewer.add_mesh(mesh, color="#f6b75d" if index in selected else "#9ebfe3", smooth_shading=True, split_sharp_edges=True)
            edges = mesh.extract_feature_edges(feature_angle=35, boundary_edges=True,
                                               non_manifold_edges=False, feature_edges=True, manifold_edges=False)
            if edges.n_points:
                self.viewer.add_mesh(edges, color="#31475f", line_width=1.5)
        if reset:
            self.viewer.reset_camera()

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
            DrawingDialog(self.parts[row], self).exec()
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
                with tempfile.TemporaryDirectory() as folder:
                    path = Path(folder) / "smoke.step"
                    write_step(window.parts, path)
                    assert read_step(path).shape.isValid()
                    from drawing_dialog import DrawingDialog, write_pdf
                    drawing = DrawingDialog(window.parts[0], window)
                    assert b"svg" in drawing.svg
                    write_pdf(drawing.svg, Path(folder) / "drawing.pdf")
                    assert (Path(folder) / "drawing.pdf").stat().st_size > 1000
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
