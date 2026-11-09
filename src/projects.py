"""Versioned, atomic project files. Geometry is BREP, parameters are JSON."""
from dataclasses import asdict
import io
import json
import os
from pathlib import Path
import tempfile
import zipfile
import cadquery as cq
from model import Part, primitive, checked_position
from features import Feature, apply_feature, valid


def save_project(parts, path):
    path = Path(path)
    if len(parts)>1000:raise ValueError("Maximal 1000 Bauteile in dieser Testversion.")
    fd, temporary = tempfile.mkstemp(prefix='.pcad-', suffix='.tmp', dir=path.parent)
    os.close(fd)
    try:
        records = []
        with zipfile.ZipFile(temporary, 'w', zipfile.ZIP_DEFLATED) as z:
            for i, part in enumerate(parts):
                record = {'name': part.name, 'kind': part.kind, 'dimensions': part.dimensions,
                          'position': part.position, 'features': [asdict(f) for f in part.features],
                          'measurements': part.measurements}
                if part.kind is None:
                    base = part.base_shape or part.shape.translate(tuple(-v for v in part.position))
                    stream = io.BytesIO()
                    if not base.exportBrep(stream):
                        raise ValueError('BREP konnte nicht gespeichert werden.')
                    z.writestr(f'base-{i}.brep', stream.getvalue())
                records.append(record)
            z.writestr('project.json', json.dumps({'version': 1, 'parts': records}, ensure_ascii=False))
        with zipfile.ZipFile(temporary) as check:
            if sum(f.file_size for f in check.infolist())>100*1024*1024:
                raise ValueError("Projekt überschreitet die Formatgrenze von 100 MB unkomprimiert.")
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def load_project(path):
    result = []
    with zipfile.ZipFile(path) as z:
        if sum(f.file_size for f in z.infolist()) > 100 * 1024 * 1024:
            raise ValueError('Projekt ist für diese Testversion zu groß.')
        data = json.loads(z.read('project.json'))
        if data.get('version') != 1 or len(data['parts']) > 1000:
            raise ValueError('Unbekanntes oder zu großes Projektformat.')
        for i, record in enumerate(data['parts']):
            kind = record['kind']
            dims = tuple(record['dimensions']) if record['dimensions'] is not None else None
            base = primitive(kind, dims) if kind is not None else valid(cq.Shape.importBrep(io.BytesIO(z.read(f'base-{i}.brep'))))
            def freeze(value):return tuple(freeze(v) for v in value) if isinstance(value,list) else value
            features = tuple(Feature(f['kind'], freeze(f['args']),tuple(f.get('topology',()))) for f in record['features'])
            if len(features) > 200:
                raise ValueError('Zu viele Bearbeitungsschritte.')
            shape = base
            for feature in features:
                shape = apply_feature(shape, feature)
            position = checked_position(record['position'])
            measurements = tuple(tuple(m) for m in record.get('measurements', []))
            result.append(Part(str(record['name']), shape.translate(position), kind, dims, position,
                               features, base if kind is None else None, measurements))
    return result
