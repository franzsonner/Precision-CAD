"""Exact BREP geometry; millimetres. No GUI dependencies."""
from dataclasses import dataclass
import math
from pathlib import Path
import cadquery as cq


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

    @classmethod
    def create(cls, kind, dimensions):
        return cls(kind, primitive(kind, dimensions), kind, tuple(dimensions))

    def resize(self, dimensions):
        shape = primitive(self.kind, dimensions).translate(self.position)
        self.shape, self.dimensions = shape, tuple(dimensions)

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
