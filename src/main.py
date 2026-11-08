"""Precision CAD - early independent desktop prototype (not yet Windows-tested)."""
import sys
from pathlib import Path
import cadquery as cq
import pyvista as pv
from pyvistaqt import QtInteractor
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QDoubleSpinBox, QLabel, QFileDialog, QMessageBox, QListWidget
)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Precision CAD – Prototyp 0.1")
        self.resize(1100, 720)
        self.parts = []
        root = QWidget()
        self.setCentralWidget(root)
        layout = QHBoxLayout(root)
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
            ("Quader erstellen", self.add_box),
            ("Zylinder erstellen", self.add_cylinder),
            ("STEP öffnen", self.open_step),
            ("STEP exportieren", self.save_step),
            ("Projekt speichern (STEP)", self.save_step),
        ]:
            button = QPushButton(title)
            button.clicked.connect(fn)
            controls.addWidget(button)
        self.items = QListWidget()
        controls.addWidget(QLabel("Bauteile"))
        controls.addWidget(self.items)
        controls.addStretch()
        layout.addWidget(sidebar, 1)
        self.viewer = QtInteractor(root)
        layout.addWidget(self.viewer, 4)
        self.viewer.set_background("#f3f6fa")
        self.viewer.add_axes()

    def values(self):
        return [f.value() for f in self.sizes]

    def add_box(self):
        x, y, z = self.values()
        self.append_part(cq.Workplane("XY").box(x, y, z).val(), "Quader")

    def add_cylinder(self):
        radius, _, height = self.values()
        self.append_part(cq.Workplane("XY").circle(radius).extrude(height).val(), "Zylinder")

    def append_part(self, shape, name):
        self.parts.append(shape)
        self.items.addItem(f"{name} {len(self.parts)}")
        self.redraw()

    def redraw(self):
        self.viewer.clear()
        self.viewer.add_axes()
        for shape in self.parts:
            vertices, triangles = shape.tessellate(0.5)
            if not vertices or not triangles:
                continue
            points = [[v.x, v.y, v.z] for v in vertices]
            faces = []
            for tri in triangles:
                faces.extend([3, *tri])
            mesh = pv.PolyData(points, faces)
            self.viewer.add_mesh(mesh, show_edges=True, color="#9ebfe3")
        self.viewer.reset_camera()

    def open_step(self):
        path, _ = QFileDialog.getOpenFileName(self, "STEP öffnen", "", "STEP (*.step *.stp)")
        if not path:
            return
        try:
            imported = cq.importers.importStep(path).val()
            self.append_part(imported, Path(path).stem)
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
            compound = cq.Compound.makeCompound(self.parts)
            cq.exporters.export(compound, path, exportType="STEP")
            QMessageBox.information(self, "Gespeichert", path)
        except Exception as exc:
            QMessageBox.critical(self, "Exportfehler", str(exc))

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
