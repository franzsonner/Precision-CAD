"""Bundle LGPL source archives alongside binaries; fail rather than omit sources."""
import hashlib
import json
import zipfile
from pathlib import Path
from urllib.request import urlopen
from importlib.metadata import version

out = Path('dist/Precision-CAD/sources')
out.mkdir(parents=True, exist_ok=True)
qt = version('PySide6')
occt = '.'.join(version('cadquery-ocp').split('.')[:3]).replace('.', '_')
archives = {
    'libraw.zip': 'https://github.com/LibRaw/LibRaw/archive/refs/tags/0.21.5.zip',
    'freeimage.zip': 'https://downloads.sourceforge.net/project/freeimage/Source%20Distribution/3.18.0/FreeImage3180.zip',
    'ocp-build-system.zip': 'https://github.com/CadQuery/ocp-build-system/archive/refs/tags/v7.9.3.1.1.zip',
    'qtsvg.zip': f'https://github.com/qt/qtsvg/archive/refs/tags/v{qt}.zip',
    'qtbase.zip': f'https://github.com/qt/qtbase/archive/refs/tags/v{qt}.zip',
    'pyside-setup.zip': f'https://github.com/pyside/pyside-setup/archive/refs/tags/v{qt}.zip',
    'occt.zip': f'https://github.com/Open-Cascade-SAS/OCCT/archive/refs/tags/V{occt}.zip',
}
manifest = []
for name, url in archives.items():
    dest = out / name
    if not dest.exists() or not zipfile.is_zipfile(dest):
        with urlopen(url, timeout=120) as response, dest.open('wb') as file:
            while block := response.read(1024 * 1024):
                file.write(block)
    if not zipfile.is_zipfile(dest):
        raise ValueError(f'Invalid source archive: {url}')
    digest = hashlib.file_digest(dest.open('rb'), 'sha256').hexdigest()
    manifest.append({'file': name, 'url': url, 'sha256': digest})
(out / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
