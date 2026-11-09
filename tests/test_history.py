import pytest
from model import Document, Part, read_step, write_step


def make_document():
    doc = Document()
    doc.add(Part.create('Quader', (50, 30, 20)))
    doc.add(Part.create('Zylinder', (4, 1, 15)))
    return doc


def test_cylinder_on_box_resize_and_history():
    doc = make_document()
    doc.position(1, (12, 5, 10))
    assert doc.parts[1].shape.BoundingBox().zmin == pytest.approx(10)
    doc.resize(1, (6, 1, 25))
    assert doc.parts[1].position == (12, 5, 10)
    assert doc.parts[1].shape.BoundingBox().zmax == pytest.approx(35)
    doc.undo()
    assert doc.parts[1].dimensions == (4, 1, 15)
    assert doc.parts[1].position == (12, 5, 10)
    doc.undo()
    assert doc.parts[1].position == (0, 0, 0)
    doc.redo(); doc.redo()
    assert doc.parts[1].shape.BoundingBox().zmax == pytest.approx(35)


def test_group_move_is_one_undo_and_keeps_relative_position(tmp_path):
    doc = make_document()
    doc.position(1, (12, 5, 10))
    doc.translate([0, 1], (-3, 9, 2))
    assert doc.parts[0].position == (-3, 9, 2)
    assert doc.parts[1].position == (9, 14, 12)
    doc.undo()
    assert [p.position for p in doc.parts] == [(0, 0, 0), (12, 5, 10)]
    doc.redo()
    path = tmp_path / 'positioniert.step'
    write_step(doc.parts, path)
    imported = read_step(path)
    assert imported.shape.BoundingBox().zmax == pytest.approx(27)
    assert len(imported.shape.Solids()) == 2
    doc = Document()
    doc.add(imported)
    doc.position(0, (0, 0, 3))
    assert doc.parts[0].shape.BoundingBox().zmax == pytest.approx(30)
    doc.undo()
    assert doc.parts[0].shape.BoundingBox().zmax == pytest.approx(27)
    doc.undo()
    assert doc.parts == []


def test_failed_group_move_is_atomic_and_new_edit_clears_redo():
    doc = make_document()
    doc.position(1, (100000, 0, 0))
    before = len(doc.undo_stack)
    with pytest.raises(ValueError):
        doc.translate([0, 1], (1, 0, 0))
    assert [p.position for p in doc.parts] == [(0, 0, 0), (100000, 0, 0)]
    assert len(doc.undo_stack) == before
    doc.undo()
    assert doc.redo_stack
    with pytest.raises(ValueError):
        doc.resize(0, (-1, 2, 3))
    assert doc.redo_stack
    doc.position(0, (1, 2, 3))
    assert not doc.redo_stack


def test_add_undo_redo_and_history_limit():
    doc = Document()
    doc.undo(); doc.redo()
    doc.add(Part.create('Quader', (1, 2, 3)))
    doc.undo()
    assert not doc.parts
    doc.redo()
    for x in range(105):
        doc.position(0, (x, 0, 0))
    assert len(doc.undo_stack) == 100
