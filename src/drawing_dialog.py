"""Drawing preview and vector SVG/PDF export."""
from pathlib import Path
from PySide6.QtCore import QByteArray, QRectF, Qt, Signal, QPointF
from PySide6.QtGui import QPainter, QPolygonF, QColor, QPen, QPdfWriter, QPageSize, QPageLayout
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog, QMessageBox, QWidget, QInputDialog, QLabel, QCheckBox
from drawing import sheet_svg, editable_axis, NS
import xml.etree.ElementTree as ET


class DrawingPreview(QWidget):
    axis_clicked=Signal(int)
    edges_clicked=Signal(int,int)
    first_edge=Signal(int)
    measure_mode=False
    chosen=None
    def load(self,svg):
        self.chosen=None;self.paths=[]
        self.svg=svg;self.renderer=QSvgRenderer(QByteArray(svg));self.targets=[]
        for text in ET.fromstring(svg).iter(f'{{{NS}}}text'):
            if 'data-axis' in text.attrib:
                x,y=float(text.get('x')),float(text.get('y'))
                middle=text.get('text-anchor')=='middle'
                width=max(70,len(text.text or '')*9)
                self.targets.append((QRectF(x-width/2 if middle else x,y-20,width,26),int(text.get('data-axis'))))
        for path in ET.fromstring(svg).iter(f'{{{NS}}}polyline'):
            if 'data-edge' in path.attrib:
                points=[tuple(map(float,p.split(','))) for p in path.get('points').split()]
                self.paths.append((int(path.get('data-edge')),points))
        self.update()
    def transform(self):
        scale=min(self.width()/1122,self.height()/794)
        return scale,(self.width()-1122*scale)/2,(self.height()-794*scale)/2
    def paintEvent(self,event):
        if not hasattr(self,'renderer'):return
        painter=QPainter(self);painter.fillRect(self.rect(),Qt.GlobalColor.white)
        scale,x,y=self.transform();self.renderer.render(painter,QRectF(x,y,1122*scale,794*scale))
        if self.chosen is not None:
            painter.translate(x,y);painter.scale(scale,scale);painter.setPen(QPen(QColor('#cc3366'),2/max(scale,.01)))
            for index,points in self.paths:
                if index==self.chosen:painter.drawPolyline(QPolygonF([QPointF(a,b) for a,b in points]))
        painter.end()
    def mousePressEvent(self,event):
        scale,x,y=self.transform()
        if scale<=0:return
        point=event.position();px,py=(point.x()-x)/scale,(point.y()-y)/scale
        if self.measure_mode:
            import math
            best=None
            for index,points in self.paths:
                for a,b in zip(points,points[1:]):
                    dx,dy=b[0]-a[0],b[1]-a[1];den=dx*dx+dy*dy
                    t=max(0,min(1,((px-a[0])*dx+(py-a[1])*dy)/den)) if den>1e-15 else 0
                    distance=math.hypot(px-a[0]-t*dx,py-a[1]-t*dy)
                    if best is None or distance<best[0]:best=(distance,index)
            if best and best[0]*scale<=8:
                if self.chosen is None:
                    self.chosen=best[1];self.first_edge.emit(self.chosen);self.update()
                else:
                    first=self.chosen;self.chosen=None;self.edges_clicked.emit(first,best[1]);self.update()
            return
        for rect,axis in self.targets:
            if rect.contains(px,py):self.axis_clicked.emit(axis);break


class DrawingDialog(QDialog):
    def __init__(self, part, parent=None, on_resize=None, on_measurement=None):
        super().__init__(parent)
        self.setWindowTitle('Zeichnung – A4-Übersichtsblatt')
        self.resize(1000, 780)
        self.part,self.on_resize,self.on_measurement=part,on_resize,on_measurement
        self.svg = sheet_svg(part).encode('utf-8')
        layout = QVBoxLayout(self)
        self.preview = DrawingPreview()
        self.preview.load(self.svg)
        self.preview.axis_clicked.connect(self.edit_dimension)
        self.preview.edges_clicked.connect(self.add_measurement)
        layout.addWidget(self.preview, 1)
        self.measure_mode=QCheckBox("Im Blatt zwei Kanten anklicken → exakten 3D-Mindestabstand bemaßen")
        self.measure_mode.setEnabled(on_measurement is not None)
        self.measure_mode.toggled.connect(self.set_measure_mode)
        layout.addWidget(self.measure_mode)
        self.status=QLabel("Blaue Grundmaße können direkt bearbeitet werden.")
        self.status.setWordWrap(True);layout.addWidget(self.status)
        self.preview.first_edge.connect(lambda i:self.status.setText(f"Kante {i+1} gewählt; zweite Kante anklicken. Überlagerte Projektionskanten ggf. im 3D-Fenster auswählen."))
        label=QLabel("Blaue Grundmaße anklicken zum Ändern. Messwerte entstehen über Prüfen → Maß in Zeichnung im Hauptfenster.")
        label.setWordWrap(True);layout.addWidget(label)
        buttons = QHBoxLayout()
        for label, suffix in [('SVG speichern', 'svg'), ('PDF speichern', 'pdf')]:
            button = QPushButton(label)
            button.clicked.connect(lambda checked=False, ext=suffix: self.save(ext))
            buttons.addWidget(button)
        layout.addLayout(buttons)

    def set_measure_mode(self,on):
        self.preview.measure_mode=on;self.preview.chosen=None;self.preview.update()
        self.status.setText('Zwei Kanten anklicken. Gemessen wird der 3D-Mindestabstand, nicht der Abstand auf dem Papier.' if on else 'Blaue Grundmaße können direkt bearbeitet werden.')

    def add_measurement(self,first,second):
        if not self.on_measurement:return
        try:
            self.part=self.on_measurement(first,None if first==second else second)
            self.svg=sheet_svg(self.part).encode('utf-8');self.preview.load(self.svg)
            self.status.setText('Messwert zum Blatt hinzugefügt. Neue Auswahl möglich.')
        except Exception as exc:QMessageBox.warning(self,'Messung',str(exc))

    def edit_dimension(self,axis):
        if not self.on_resize or not editable_axis(self.part,axis):return
        old=self.part.dimensions[axis] if self.part.kind=='Quader' or axis==2 else self.part.dimensions[0]*2
        value,ok=QInputDialog.getDouble(self,'Zeichnungsmaß ändern','Neues Grundmaß (mm)',old,.1,100000,3)
        if ok:
            try:
                dims=list(self.part.dimensions)
                if self.part.kind=='Zylinder' and axis!=2:dims[0]=value/2
                else:dims[axis]=value
                self.part=self.on_resize(dims)
                self.svg=sheet_svg(self.part).encode('utf-8');self.preview.load(self.svg)
            except Exception as exc:QMessageBox.warning(self,'Maßänderung nicht übernommen',str(exc))

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
