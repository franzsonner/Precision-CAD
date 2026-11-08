import math
import pytest
from model import Part, read_step, write_step


def test_resize():
    box = Part.create("Quader", (10, 20, 30))
    assert box.shape.Volume() == pytest.approx(6000)
    box.resize((5, 6, 7))
    assert box.shape.Volume() == pytest.approx(210)
    cylinder = Part.create("Zylinder", (3, 1, 10))
    cylinder.resize((4, 1, 20))
    assert cylinder.shape.Volume() == pytest.approx(math.pi * 16 * 20)


def test_step_multiple_solids(tmp_path):
    parts = [Part.create("Quader", (10, 20, 30)), Part.create("Zylinder", (3, 1, 10))]
    path = tmp_path / "körper.step"
    write_step(parts, path)
    imported = read_step(path)
    assert len(imported.shape.Solids()) == 2
    assert imported.shape.isValid()
    assert imported.shape.Volume() == pytest.approx(sum(p.shape.Volume() for p in parts))
    with pytest.raises(ValueError):
        imported.resize((1, 2, 3))


@pytest.mark.parametrize('value', [0, -1, float('nan'), float('inf'), 100001])
def test_invalid_dimensions(value):
    part = Part.create("Quader", (1, 2, 3))
    with pytest.raises(ValueError):
        part.resize((value, 2, 3))
    assert part.shape.Volume() == pytest.approx(6)


def test_errors(tmp_path):
    with pytest.raises(ValueError):
        write_step([], tmp_path / 'empty.step')
    path = tmp_path / 'broken.step'
    path.write_text('invalid STEP')
    with pytest.raises(Exception):
        read_step(path)
