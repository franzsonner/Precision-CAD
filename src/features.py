"""Validated BREP operations and a small, explicitly simplified metric catalogue."""
from dataclasses import dataclass
import math
import cadquery as cq


@dataclass(frozen=True)
class Feature:
    kind: str
    args: tuple
    topology: tuple = ()


# Nominal diameter: coarse pitch, width across flats, head height, nut height.
METRIC = {3: (.5, 5.5, 2, 2.4), 4: (.7, 7, 2.8, 3.2), 5: (.8, 8, 3.5, 4.7),
          6: (1, 10, 4, 5.2), 8: (1.25, 13, 5.3, 6.8), 10: (1.5, 16, 6.4, 8.4),
          12: (1.75, 18, 7.5, 10.8), 16: (2, 24, 10, 14.8)}


def positive(value, name='Maß', maximum=100000):
    if not math.isfinite(value) or not 0 < value <= maximum:
        raise ValueError(f'{name} muss größer als 0 und höchstens {maximum} sein.')
    return value


def vector(values):
    if len(values) != 3 or not all(math.isfinite(v) and abs(v) <= 100000 for v in values):
        raise ValueError('Ungültiger Vektor.')
    return cq.Vector(*values)


def unit(values):
    v = vector(values)
    if v.Length < 1e-9:
        raise ValueError('Richtungsvektor darf nicht null sein.')
    return v.normalized()


def drilling_direction(normal, tilt, azimuth):
    if not math.isfinite(tilt) or not 0 <= tilt <= 85 or not math.isfinite(azimuth):
        raise ValueError('Bohrungsneigung muss zwischen 0 und 85° liegen.')
    n = unit(normal)
    ref = cq.Vector(0, 0, 1) if abs(n.z) < .9 else cq.Vector(1, 0, 0)
    u = n.cross(ref).normalized()
    v = n.cross(u).normalized()
    t, a = math.radians(tilt), math.radians(azimuth)
    return (n.multiply(-math.cos(t)) + u.multiply(math.sin(t)*math.cos(a)) + v.multiply(math.sin(t)*math.sin(a))).toTuple()


def valid(shape):
    if not shape.isValid() or not shape.Solids() or shape.Volume() <= 1e-7:
        raise ValueError('Bearbeitung erzeugt keinen gültigen Volumenkörper.')
    return shape


def apply_feature(shape, feature):
    kind, args = feature.kind, feature.args
    if kind in ("fillet","chamfer","draft") and feature.topology and tuple(feature.topology)!=(len(shape.Faces()),len(shape.Edges())):
        raise ValueError("Eine vorherige Änderung hat die Flächen-/Kantenstruktur geändert. Betroffenen Schritt und nachfolgende Schritte entfernen und neu auswählen.")
    if kind == 'hole':
        point, direction, diameter, depth, through, counter, head_d, head_depth, thread = args
        p, d = vector(point), unit(direction)
        radius = positive(diameter, 'Durchmesser') / 2
        length = exact_box(shape).DiagonalLength * 3 + 1 if through else positive(depth, 'Bohrtiefe')
        vertex=cq.Vertex.makeVertex(*p.toTuple())
        planes=[(f.distance(vertex),f.normalAt()) for f in shape.Faces() if f.geomType()=='PLANE']
        if not planes:raise ValueError('Ebene Startfläche fehlt.')
        nearest=min(distance for distance,_ in planes)
        normal=min((n for distance,n in planes if distance<=nearest+1e-5),key=lambda n:n.dot(d))
        cosine=-normal.dot(d)
        if cosine<1e-4:raise ValueError('Die Bohrachse muss in den Körper zeigen, nicht entlang oder aus der Startfläche.')
        tangent=math.sqrt(max(0,1-cosine*cosine))/cosine
        # Extend the complete cutting profile outside the entry plane. A fixed
        # epsilon clips half of an inclined bore with the cutter's own end cap.
        margin=radius*tangent+.2
        origin = p - d.multiply(margin)
        tool = cq.Solid.makeCylinder(radius, length + margin, origin, d)
        if counter != 'none':
            if positive(head_d, 'Senkdurchmesser') <= diameter:
                raise ValueError('Senkdurchmesser muss größer als die Bohrung sein.')
            if counter == 'counterbore':
                h = positive(head_depth, 'Senktiefe')
                head_margin=head_d/2*tangent+.2
                extra = cq.Solid.makeCylinder(head_d / 2,h+head_margin,p-d.multiply(head_margin),d)
            elif counter == 'countersink':
                if not math.isfinite(head_depth) or not 10 <= head_depth <= 170:
                    raise ValueError('Senkwinkel muss zwischen 10 und 170° liegen.')
                h = (head_d-diameter)/2/math.tan(math.radians(head_depth/2))
                head_margin=head_d/2*tangent+.2
                extra = cq.Solid.makeCone(head_d/2+head_margin*math.tan(math.radians(head_depth/2)),radius,h+head_margin,p-d.multiply(head_margin),d)
            else:
                raise ValueError('Unbekannte Senkung.')
            if not through and h > depth:
                raise ValueError('Senkung ist tiefer als die Sackbohrung.')
            tool = tool.fuse(extra)
        result = valid(shape.cut(tool).clean())
        if shape.Volume() - result.Volume() < 1e-6:
            raise ValueError('Die Bohrung trifft den Körper nicht.')
        return result
    if kind in ('fillet', 'chamfer'):
        indices, value = args
        positive(value, 'Radius / Fasenbreite')
        edges = shape.Edges()
        if not indices or any(not isinstance(i, int) or not 0 <= i < len(edges) for i in indices):
            raise ValueError('Kantenauswahl ist nicht mehr gültig.')
        if len(shape.Solids()) != 1:
            raise ValueError('Bitte einen einzelnen Volumenkörper bearbeiten.')
        selected = [edges[i] for i in indices]
        solid = shape.Solids()[0]
        return valid(solid.fillet(value, selected) if kind == 'fillet' else solid.chamfer(value, None, selected))
    if kind == 'draft':
        from OCP.BRepOffsetAPI import BRepOffsetAPI_DraftAngle
        from OCP.gp import gp_Dir, gp_Pln, gp_Pnt
        index, axis, angle = args
        if axis not in (0, 1, 2) or not math.isfinite(angle) or not .01 <= abs(angle) <= 60:
            raise ValueError('Flächenneigung: Achse X/Y/Z und Winkel ±0,01 bis ±60° wählen.')
        faces = shape.Faces()
        if not 0 <= index < len(faces) or faces[index].geomType() != 'PLANE':
            raise ValueError('Bitte eine ebene Seitenfläche auswählen.')
        direction = [0., 0., 0.]; direction[axis] = 1.
        bb = exact_box(shape)
        point = [0., 0., 0.]; point[axis] = (bb.xmin, bb.ymin, bb.zmin)[axis]
        draft = BRepOffsetAPI_DraftAngle(shape.wrapped)
        draft.Add(faces[index].wrapped, gp_Dir(*direction), math.radians(angle), gp_Pln(gp_Pnt(*point), gp_Dir(*direction)))
        if not draft.AddDone():
            raise ValueError('Fläche lässt sich um diese Achse nicht neigen. Andere Zugrichtung wählen.')
        draft.Build()
        if not draft.IsDone():
            raise ValueError('Neigung konnte nicht erzeugt werden.')
        return valid(cq.Shape.cast(draft.Shape()))
    if kind == 'rotate':
        axis, angle = args
        if axis not in (0, 1, 2) or not math.isfinite(angle) or abs(angle) > 360:
            raise ValueError('Drehung: Achse X/Y/Z und Winkel bis ±360° wählen.')
        direction = [0., 0., 0.]; direction[axis] = 1.
        return valid(shape.rotate((0, 0, 0), direction, angle))
    raise ValueError('Unbekannte Bearbeitungsfunktion.')


def catalogue(kind, diameter, length=30, pitch=None):
    if diameter not in METRIC or kind not in ('bolt', 'nut', 'washer'):
        raise ValueError('Kataloggröße nicht vorhanden.')
    coarse, flats, head, nut = METRIC[diameter]
    pitch = coarse if pitch is None else positive(pitch, 'Gewindesteigung', diameter/2)
    if kind == 'bolt':
        positive(length, 'Schraubenlänge', 1000)
        shank = cq.Workplane('XY').circle(diameter/2).extrude(length).val()
        cap = cq.Workplane('XY').polygon(6, flats/math.cos(math.pi/6)).extrude(-head).val()
        shape = shank.fuse(cap).clean()
        name = f'Sechskantschraube M{diameter}×{pitch:g}×{length:g} (vereinfacht)'
    elif kind == 'nut':
        shape = cq.Workplane('XY').polygon(6, flats/math.cos(math.pi/6)).circle(diameter/2).extrude(nut).val()
        name = f'Sechskantmutter M{diameter}×{pitch:g} (vereinfacht)'
    else:
        inner,outer,thickness={3:(3.2,7,.5),4:(4.3,9,.8),5:(5.3,10,1),6:(6.4,12,1.6),8:(8.4,16,1.6),10:(10.5,20,2),12:(13,24,2.5),16:(17,30,3)}[diameter]
        shape = cq.Workplane('XY').circle(outer/2).circle(inner/2).extrude(thickness).val()
        name = f'Scheibe für M{diameter} (vereinfacht)'
    return name, valid(shape)


def edge_measure(shape, first, second=None):
    edges = shape.Edges()
    if first < 0 or first >= len(edges) or (second is not None and not 0 <= second < len(edges)):
        raise ValueError('Kante nicht mehr vorhanden.')
    a = edges[first]
    if second is None:
        return a.Length(), None
    b = edges[second]
    angle = None
    if a.geomType() == b.geomType() == 'LINE':
        dot = max(-1., min(1., abs(a.tangentAt().dot(b.tangentAt()))))
        angle = math.degrees(math.acos(dot))
    return a.distance(b), angle


def measure_points(shape, first, second=None):
    edges=shape.Edges();a=edges[first]
    value,angle=edge_measure(shape,first,second)
    if second is None:
        return value,angle,a.startPoint().toTuple(),a.endPoint().toTuple()
    from OCP.BRepExtrema import BRepExtrema_DistShapeShape
    distance=BRepExtrema_DistShapeShape(a.wrapped,edges[second].wrapped)
    distance.Perform()
    if not distance.IsDone() or not distance.NbSolution():raise ValueError('Abstand nicht berechenbar.')
    p,q=distance.PointOnShape1(1),distance.PointOnShape2(1)
    return value,angle,(p.X(),p.Y(),p.Z()),(q.X(),q.Y(),q.Z())


def exact_box(shape):
    """Bounds of analytic geometry, independent of viewport triangulation caches."""
    from OCP.Bnd import Bnd_Box
    from OCP.BRepBndLib import BRepBndLib
    box=Bnd_Box()
    BRepBndLib.AddOptimal_s(shape.wrapped,box,False,False)
    return cq.BoundBox(box)
