"""Drawing preview and vector SVG/PDF export."""
from pathlib import Path
from PySide6.QtCore import QByteArray, QRectF
from PySide6.QtGui import QPainter, QPdfWriter, QPageSize, QPageLayout
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog, QMessageBox
from drawing import sheet_svg


class DrawingDialog(QDialog):
    def __init__(self, part, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Zeichnung – A4-Übersichtsblatt')
        self.resize(1000, 780)
        self.svg = sheet_svg(part).encode('utf-8')
        layout = QVBoxLayout(self)
        preview = QSvgWidget()
        preview.load(QByteArray(self.svg))
        layout.addWidget(preview, 1)
        buttons = QHBoxLayout()
        for label, suffix in [('SVG speichern', 'svg'), ('PDF speichern', 'pdf')]:
            button = QPushButton(label)
            button.clicked.connect(lambda checked=False, ext=suffix: self.save(ext))
            buttons.addWidget(button)
        layout.addLayout(buttons)

    def save(self, suffix):
        path, _ = QFileDialog.getSaveFileName(self, 'Zeichnung speichern', f'zeichnung.{suffix}', f'{suffix.upper()} (*.{suffix})')
        if not path:
            return
        try:
            path = str(Path(path).with_suffix('.' + suffix))
            if suffix == 'svg':
                Path(path).write_bytes(self.svg)
            else:
                write_pdf(self.svg, path)
        except Exception as exc:
            QMessageBox.critical(self, 'Zeichnungsexport', str(exc))


def write_pdf(svg, path):
    writer = QPdfWriter(str(path))
    writer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
    writer.setPageOrientation(QPageLayout.Orientation.Landscape)
    painter = QPainter(writer)
    if not painter.isActive():
        raise OSError('PDF konnte nicht angelegt werden.')
    try:
        renderer = QSvgRenderer(QByteArray(svg))
        if not renderer.isValid():
            raise ValueError('Ungültige Zeichnung.')
        renderer.render(painter, QRectF(0, 0, writer.width(), writer.height()))
    finally:
        painter.end()
