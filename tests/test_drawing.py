import xml.etree.ElementTree as ET
import pytest
from model import Part
from drawing import sheet_svg, NS


@pytest.mark.parametrize('kind', ['Quader', 'Zylinder'])
def test_orthographic_drawing(kind):
    part = Part.create(kind, (10, 20, 30))
    part.name = '<Bauteil & Test>'
    svg = sheet_svg(part)
    root = ET.fromstring(svg)
    assert root.attrib['width'] == '297mm'
    assert len([g for g in root.findall(f'{{{NS}}}g') if 'data-view' in g.attrib]) == 3
    assert len(root.findall(f'.//{{{NS}}}path')) > 0
    text = ''.join(root.itertext())
    assert '<Bauteil & Test>' in text
    assert '30.000 mm' in text
    assert 'Maßstab variabel' in text
    if kind == 'Zylinder':
        assert 'Durchmesser: 20.000 mm' in text
