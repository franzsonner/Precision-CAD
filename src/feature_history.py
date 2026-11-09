import math
from PySide6.QtWidgets import (QDialog,QVBoxLayout,QHBoxLayout,QListWidget,QPushButton,QMessageBox,QComboBox,QCheckBox,QLineEdit)
from features import Feature
from feature_dialogs import FormDialog,ValueDialog,AngleDialog,number

LABELS={'hole':'Bohrung / Senkung','fillet':'Radius','chamfer':'Fase','draft':'Flächenneigung','rotate':'Drehen'}


class HoleEditDialog(FormDialog):
    def __init__(self,feature,parent):
        super().__init__('Bohrungsschritt bearbeiten',parent)
        point,direction,diameter,depth,through,counter,head,head_depth,thread=feature.args
        self.point=[number(v,-100000) for v in point]
        for axis,field in zip('XYZ',self.point):self.form.addRow('Eintritt '+axis+' relativ zum Bauteil',field)
        self.tilt=number(math.degrees(math.acos(max(-1,min(1,-direction[2])))),0,180)
        self.azimuth=number(math.degrees(math.atan2(direction[1],direction[0])),-360,360)
        self.form.addRow('Neigung gegen globale −Z-Richtung (°)',self.tilt);self.form.addRow('Azimut um Z (°)',self.azimuth)
        self.diameter=number(diameter);self.depth=number(depth);self.through=QCheckBox('Durch alles');self.through.setChecked(through)
        self.counter=QComboBox();self.counter.addItems(['Keine','Zylindersenkung','Kegelsenkung']);self.counter.setCurrentIndex(('none','counterbore','countersink').index(counter))
        self.head=number(head);self.head_depth=number(head_depth);self.thread=QLineEdit(thread)
        for label,field in [('Durchmesser (mm)',self.diameter),('Tiefe (mm)',self.depth),('',self.through),('Senkung',self.counter),('Senkdurchmesser (mm)',self.head),('Senktiefe (mm) / Senkwinkel (°)',self.head_depth),('Gewindebezeichnung (nur Kennzeichnung)',self.thread)]:self.form.addRow(label,field)
        self.finish('Ändert den bestehenden Schritt und berechnet alle nachfolgenden Schritte neu. Hier bezieht sich die Winkelangabe auf globale Achsen, nicht auf die ursprüngliche Fläche. Bei einem Kernloch Durchmesser und Gewindebezeichnung gemeinsam passend ändern.')
    def feature(self):
        t,a=math.radians(self.tilt.value()),math.radians(self.azimuth.value())
        direction=(math.sin(t)*math.cos(a),math.sin(t)*math.sin(a),-math.cos(t))
        return Feature('hole',(tuple(f.value() for f in self.point),direction,self.diameter.value(),self.depth.value(),self.through.isChecked(),('none','counterbore','countersink')[self.counter.currentIndex()],self.head.value(),self.head_depth.value(),self.thread.text()[:80]))


class FeatureHistoryDialog(QDialog):
    def __init__(self,main,row):
        super().__init__(main);self.main=main;self.row=row
        self.setWindowTitle('Bearbeitungsschritte – parametrischer Aufbau');self.resize(560,400)
        layout=QVBoxLayout(self);self.items=QListWidget();layout.addWidget(self.items)
        bar=QHBoxLayout();layout.addLayout(bar)
        for title,fn in [('Schritt bearbeiten',self.edit),('Ab hier entfernen',self.remove)]:
            button=QPushButton(title);button.clicked.connect(fn);bar.addWidget(button)
        self.reload()
    def reload(self):
        self.items.clear()
        for i,f in enumerate(self.main.parts[self.row].features):
            details=f'⌀{f.args[2]:g}' if f.kind=='hole' else str(f.args[-1])
            self.items.addItem(f'{i+1}. {LABELS[f.kind]}: {details}')
        if self.items.count():self.items.setCurrentRow(self.items.count()-1)
    def edit(self):
        index=self.items.currentRow()
        if index<0:return
        try:
            feature=self.main.parts[self.row].features[index]
            if feature.kind=='hole':
                dialog=HoleEditDialog(feature,self)
                if dialog.exec()!=QDialog.DialogCode.Accepted:return
                updated=dialog.feature()
            elif feature.kind in ('fillet','chamfer'):
                dialog=ValueDialog(LABELS[feature.kind],'Radius / Fasenbreite (mm)',feature.args[1],parent=self)
                if dialog.exec()!=QDialog.DialogCode.Accepted:return
                updated=Feature(feature.kind,(feature.args[0],dialog.value.value()))
            else:
                dialog=AngleDialog(LABELS[feature.kind],feature.kind=='draft',self)
                dialog.axis.setCurrentIndex(feature.args[-2]);dialog.angle.setValue(feature.args[-1])
                if dialog.exec()!=QDialog.DialogCode.Accepted:return
                updated=Feature(feature.kind,(feature.args[0],dialog.axis.currentIndex(),dialog.angle.value()) if feature.kind=='draft' else (dialog.axis.currentIndex(),dialog.angle.value()))
            self.main.document.change_feature(self.row,index,updated);self.main.refresh([self.row]);self.reload()
        except Exception as exc:self.main.error(exc)
    def remove(self):
        index=self.items.currentRow()
        if index<0:return
        if QMessageBox.question(self,'Schritte entfernen','Ausgewählten und alle nachfolgenden Schritte entfernen? Rückgängig ist möglich.')==QMessageBox.StandardButton.Yes:
            try:self.main.document.truncate_features(self.row,index);self.main.refresh([self.row]);self.reload()
            except Exception as exc:self.main.error(exc)
