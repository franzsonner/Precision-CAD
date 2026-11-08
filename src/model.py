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

    @classmethod
    def create(cls, kind, dimensions):
        return cls(kind, primitive(kind, dimensions), kind, tuple(dimensions))

    def resize(self, dimensions):
        shape = primitive(self.kind, dimensions)
        self.shape, self.dimensions = shape, tuple(dimensions)


def read_step(path):
    shapes = cq.importers.importStep(str(path)).vals()
    if not shapes:
        raise ValueError("Die STEP-Datei enthält keine Geometrie.")
    return Part(Path(path).stem, cq.Compound.makeCompound(shapes))


def write_step(parts, path):
    if not parts:
        raise ValueError("Keine Bauteile vorhanden.")
    cq.exporters.export(cq.Compound.makeCompound([p.shape for p in parts]), str(path), exportType="STEP")
