"""Include original installed package notices and exact version/source metadata."""
from importlib.metadata import distributions
from pathlib import Path
import json
import shutil

out = Path('dist/Precision-CAD/licenses')
out.mkdir(parents=True, exist_ok=True)
inventory = []
for dist in distributions():
    name = dist.metadata['Name']
    target = out / name
    target.mkdir(exist_ok=True)
    (target / 'METADATA.txt').write_text(dist.read_text('METADATA') or dist.read_text('PKG-INFO') or '', encoding='utf-8')
    for entry in dist.files or []:
        if any(word in str(entry).lower() for word in ('license', 'copying', 'copyright', 'notice')):
            source = Path(dist.locate_file(entry))
            if source.is_file():
                # Preserve hierarchy: multiple bundled libraries can have the same filename.
                relative = Path(*[p for p in entry.parts if p not in ('..', '.')])
                dest = target / relative
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, dest)
    inventory.append({'name': name, 'version': dist.version,
                      'license': dist.metadata.get('License-Expression') or dist.metadata.get('License'),
                      'sources': dist.metadata.get_all('Project-URL') or [dist.metadata.get('Home-page')]})
(out / 'inventory.json').write_text(json.dumps(inventory, indent=2), encoding='utf-8')
for file in ('LICENSE', 'THIRD_PARTY.md', 'README.md', 'requirements.txt'):
    shutil.copy2(file, out.parent / file)

# The bundled interpreter also retains its original PSF license.
import sys
for location in (Path(sys.base_prefix) / 'LICENSE.txt', Path(sys.base_prefix) / 'lib' / f'python{sys.version_info.major}.{sys.version_info.minor}' / 'LICENSE.txt'):
    if location.exists():
        shutil.copy2(location, out / 'PYTHON-LICENSE.txt')
        break
else:
    raise RuntimeError('Python license not found')

shutil.copytree('third_party', out / 'additional-notices', dirs_exist_ok=True)
