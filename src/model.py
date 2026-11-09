"""Exact BREP geometry; millimetres. No GUI dependencies."""
from dataclasses import dataclass
import math
from pathlib import Path
import cadquery as cq
from features import Feature, apply_feature, valid


def primitive(kind, dimensions):
    x, y, z = dimensions
    if not all(math.isfinite(v) and 0.1 <= v <= 100000 for v in dimensions):
        raise ValueError("Maße müssen zwischen 0,1 und 100000 mm liegen.")
    if kind == "Quader":
        return cq.Workplane("XY").box(x, y, z).val()
    if kind == "Zylinder":
        return cq.Workplane("XY").circle(x).extrude(z).val()
    raise ValueError("Importierte Körper besitzen keine editierbaren Grundmaße.")


@dataclass
class Part:
    name: str
    shape: cq.Shape
    kind: str | None = None
    dimensions: tuple | None = None
    position: tuple = (0.0, 0.0, 0.0)
    features: tuple = ()
    base_shape: cq.Shape | None = None
    measurements: tuple = ()

    @classmethod
    def create(cls, kind, dimensions):
        return cls(kind, primitive(kind, dimensions), kind, tuple(dimensions))

    def resize(self, dimensions):
        shape = primitive(self.kind, dimensions)
        for feature in self.features:
            shape = apply_feature(shape, feature)
        self.shape, self.dimensions = shape.translate(self.position), tuple(dimensions)
        self.measurements = ()

    def add_feature(self, feature):
        if len(self.features)>=200:raise ValueError("Maximal 200 Bearbeitungsschritte pro Körper in dieser Testversion.")
        local = self.shape.translate(tuple(-v for v in self.position))
        if feature.kind in ("fillet","chamfer","draft") and not feature.topology:
            from dataclasses import replace
            feature=replace(feature,topology=(len(local.Faces()),len(local.Edges())))
        result = apply_feature(local, feature)
        base = self.base_shape
        if self.kind is None and base is None:
            base = local
        self.shape = result.translate(self.position)
        self.features = (*self.features, feature)
        self.base_shape = base
        self.measurements = ()

    def change_features(self, features):
        base = primitive(self.kind,self.dimensions) if self.kind is not None else self.base_shape
        if base is None:
            base = self.shape.translate(tuple(-v for v in self.position))
        shape = base
        for feature in features:
            shape = apply_feature(shape,feature)
        self.shape = shape.translate(self.position)
        self.features = tuple(features)
        self.base_shape = base if self.kind is None else self.base_shape
        self.measurements = ()

    def set_position(self, position):
        position = checked_position(position)
        delta = tuple(a - b for a, b in zip(position, self.position))
        self.shape = self.shape.translate(delta)
        self.position = position


def read_step(path):
    shapes = cq.importers.importStep(str(path)).vals()
    if not shapes:
        raise ValueError("Die STEP-Datei enthält keine Geometrie.")
    return Part(Path(path).stem, cq.Compound.makeCompound(shapes))


def write_step(parts, path):
    if not parts:
        raise ValueError("Keine Bauteile vorhanden.")
    cq.exporters.export(cq.Compound.makeCompound([p.shape for p in parts]), str(path), exportType="STEP")


class Document:
    """Bounded, transactional edit history. Shapes are replaced, never mutated."""
    def __init__(self):
        self.parts = []
        self.undo_stack = []
        self.redo_stack = []

    def _edit(self, operation):
        from dataclasses import replace
        before = [replace(p) for p in self.parts]
        after = [replace(p) for p in self.parts]
        operation(after)
        self.undo_stack.append(before)
        self.undo_stack = self.undo_stack[-100:]
        self.redo_stack.clear()
        self.parts = after

    def add(self, part):
        self._edit(lambda parts: parts.append(part))

    def resize(self, row, dimensions):
        self._edit(lambda parts: parts[row].resize(dimensions))

    def feature(self, row, feature):
        self._edit(lambda parts: parts[row].add_feature(feature))

    def change_feature(self,row,index,feature):
        def edit(parts):
            from dataclasses import replace
            features=list(parts[row].features);features[index]=replace(feature,topology=features[index].topology)
            parts[row].change_features(features)
        self._edit(edit)

    def truncate_features(self,row,index):
        self._edit(lambda parts:parts[row].change_features(parts[row].features[:index]))

    def measure(self, row, first, second=None):
        from features import edge_measure
        edge_measure(self.parts[row].shape, first, second)
        def record(parts):
            parts[row].measurements = (*parts[row].measurements, (first, second))[-5:]
        self._edit(record)

    def combine(self, rows, cut=False):
        rows = sorted(set(rows))
        if len(rows) < 2:
            raise ValueError('Mindestens zwei Bauteile auswählen.')
        def operation(parts):
            shape = parts[rows[0]].shape
            before = shape.Volume()
            for row in rows[1:]:
                shape = shape.cut(parts[row].shape) if cut else shape.fuse(parts[row].shape)
            shape = valid(shape.clean())
            if cut and abs(shape.Volume()-before) < 1e-6:
                raise ValueError('Die Werkzeugkörper schneiden den Zielkörper nicht.')
            combined = Part('Differenz' if cut else 'Vereinigt', shape, base_shape=shape)
            parts[:] = [p for i, p in enumerate(parts) if i not in rows] + [combined]
        self._edit(operation)

    def delete(self, rows):
        rows = set(rows)
        self._edit(lambda parts: parts.__setitem__(slice(None), [p for i, p in enumerate(parts) if i not in rows]))

    def replace_part(self, row, part):
        valid(part.shape)
        self._edit(lambda parts: parts.__setitem__(row, part))

    def replace_parts(self, parts):
        self._edit(lambda target: target.__setitem__(slice(None), parts))

    def position(self, row, position):
        self._edit(lambda parts: parts[row].set_position(position))

    def translate(self, rows, delta):
        delta = checked_position(delta)
        rows = sorted(set(rows))
        if not rows:
            raise ValueError('Bitte mindestens ein Bauteil auswählen.')
        def move(parts):
            for row in rows:
                parts[row].set_position(tuple(a + b for a, b in zip(parts[row].position, delta)))
        self._edit(move)

    def undo(self):
        if self.undo_stack:
            self.redo_stack.append(self.parts)
            self.parts = self.undo_stack.pop()

    def redo(self):
        if self.redo_stack:
            self.undo_stack.append(self.parts)
            self.parts = self.redo_stack.pop()


def checked_position(position):
    position = tuple(position)
    if len(position) != 3 or not all(math.isfinite(v) and abs(v) <= 100000 for v in position):
        raise ValueError('Positionen müssen zwischen −100000 und 100000 mm liegen.')
    return position
