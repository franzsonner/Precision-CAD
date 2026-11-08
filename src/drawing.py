"""A4 overview sheet: orthographic geometry and overall dimensions in mm."""
import xml.etree.ElementTree as ET
from cadquery.occ_impl.exporters.svg import getSVG

NS = 'http://www.w3.org/2000/svg'
ET.register_namespace('', NS)


def sheet_svg(part):
    root = ET.Element(f'{{{NS}}}svg', {'width': '297mm', 'height': '210mm', 'viewBox': '0 0 1122 794'})
    def text(x, y, value, size=16):
        node = ET.SubElement(root, f'{{{NS}}}text', {'x': str(x), 'y': str(y), 'font-size': str(size), 'font-family': 'Arial, sans-serif', 'fill': '#172334'})
        node.text = value
    ET.SubElement(root, f'{{{NS}}}rect', {'x': '20', 'y': '20', 'width': '1082', 'height': '754', 'fill': 'white', 'stroke': '#172334'})
    text(40, 55, f'Precision CAD – {part.name}', 23)
    text(40, 84, 'Technisches Übersichtsblatt · Orthogonale Ansichten · Maße in mm')
    # OCCT hidden-line removal provides true parallel projections, also for STEP.
    views = [('Vorne (Blick entlang −Y)', (0, -1, 0), 50, 135),
             ('Rechts (Blick entlang −X)', (1, 0, 0), 595, 135),
             ('Oben (Blick entlang −Z)', (0, 0, 1), 50, 425)]
    for label, direction, x, y in views:
        text(x, y - 12, label)
        # OCCT chooses a rotated default X axis for the front/side projector.
        # Rotate the input around the viewing axis so Z stays vertical on paper.
        shape = part.shape
        if direction == (0, -1, 0):
            shape = shape.rotate((0, 0, 0), (0, 1, 0), 90)
        elif direction == (1, 0, 0):
            shape = shape.rotate((0, 0, 0), (1, 0, 0), 90)
        svg = ET.fromstring(getSVG(shape, {
            'width': 450, 'height': 240, 'marginLeft': 45, 'marginTop': 25,
            'projectionDir': direction, 'showAxes': False, 'showHidden': True,
            'strokeColor': (20, 30, 40), 'hiddenColor': (130, 130, 130),
        }))
        group = ET.SubElement(root, f'{{{NS}}}g', {'transform': f'translate({x},{y})', 'data-view': label})
        group.extend(list(svg))
    bb = part.shape.BoundingBox()
    text(595, 445, 'Gesamtabmessungen (achsenparalleler Hüllkörper)', 17)
    for index, (label, value) in enumerate([('X / Länge', bb.xlen), ('Y / Breite', bb.ylen), ('Z / Höhe', bb.zlen)]):
        text(595, 480 + index * 28, f'{label}: {value:.3f} mm')
    if part.kind == 'Zylinder':
        text(595, 580, f'Durchmesser: {2 * part.dimensions[0]:.3f} mm')
    text(40, 712, 'Ansichten einzeln eingepasst · Maßstab variabel · Nicht vom Ausdruck abmessen', 14)
    text(40, 739, 'Testversion: keine normgerechte Fertigungszeichnung; Toleranzen und Einzelbemaßung fehlen.', 14)
    return ET.tostring(root, encoding='unicode')
