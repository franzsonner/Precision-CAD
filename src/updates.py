"""Public GitHub release updates, installed beside existing versions."""
import hashlib
import json
import os
from pathlib import Path, PureWindowsPath
import re
import stat
import sys
import tempfile
from urllib.request import Request, urlopen
import zipfile

REPOSITORY = 'franzsonner/Precision-CAD'
API = f'https://api.github.com/repos/{REPOSITORY}/releases/latest'
ASSET = 'Precision-CAD-Windows-x64.zip'
MAX_DOWNLOAD = 1500 * 1024 * 1024


def current_build():
    root = Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path(__file__).resolve().parents[1]
    try:
        build = json.loads((root / 'build-info.json').read_text(encoding='utf-8'))
        if not isinstance(build, dict) or not isinstance(build.get('number'), int):
            return {'tag': '', 'number': 0}
        return build
    except (OSError, ValueError):
        return {'tag': '', 'number': 0}


def request(url):
    return urlopen(Request(url, headers={'User-Agent': 'Precision-CAD-Updater', 'Accept': 'application/vnd.github+json'}), timeout=60)


def latest_release():
    with request(API) as response:
        release = json.loads(response.read(1024 * 1024))
    if release.get('draft') or release.get('prerelease'):
        raise ValueError('Kein freigegebener Testbuild verfügbar.')
    tag = release.get('tag_name', '')
    if not re.fullmatch(r'test-\d+', tag):
        raise ValueError('Unbekannte Versionskennung auf GitHub.')
    return release


def is_newer(release, build=None):
    build = current_build() if build is None else build
    tag = release['tag_name']
    return int(tag.removeprefix('test-')) > int(build.get('number', 0))


def asset_url(release, name):
    asset = next((a for a in release.get('assets', []) if a.get('name') == name), None)
    if not asset:
        raise ValueError(f'Datei fehlt im GitHub-Release: {name}')
    url = asset.get('browser_download_url', '')
    prefix = f'https://github.com/{REPOSITORY}/releases/download/{release["tag_name"]}/'
    if not url.startswith(prefix) or '/' in url[len(prefix):]:
        raise ValueError('Ungültige Download-Adresse.')
    return url


def extract_checked(archive, destination):
    with zipfile.ZipFile(archive) as z:
        entries = z.infolist()
        if len(entries) > 30000 or sum(e.file_size for e in entries) > 4 * 1024 ** 3:
            raise ValueError('Update-Archiv ist zu groß.')
        for entry in entries:
            name = entry.filename.replace('\\', '/')
            path = PureWindowsPath(name)
            reserved = {'CON', 'PRN', 'AUX', 'NUL'} | {f'{prefix}{n}' for prefix in ('COM', 'LPT') for n in range(1, 10)}
            invalid = any(p.endswith((' ', '.')) or p.split('.')[0].upper() in reserved for p in path.parts if p != '.')
            if invalid or path.drive or path.root or '..' in path.parts or ':' in name or stat.S_ISLNK(entry.external_attr >> 16):
                raise ValueError('Unsicherer Pfad im Update-Archiv.')
        for entry in entries:
            z.extract(entry, destination)
    if not (Path(destination) / 'Precision-CAD.exe').is_file():
        raise ValueError('Das Update enthält keine Precision-CAD.exe.')


def install_release(release, versions, progress=lambda text: None):
    tag = release['tag_name']
    if not re.fullmatch(r'test-\d+', tag):
        raise ValueError('Ungültige Versionskennung.')
    url = asset_url(release, ASSET)
    checksum_url = asset_url(release, ASSET + '.sha256')
    progress('Prüfsumme von GitHub laden …')
    with request(checksum_url) as response:
        checksum_parts = response.read(4096).decode('ascii').split()
        expected = checksum_parts[0].lower() if checksum_parts else ''
    if not re.fullmatch('[0-9a-f]{64}', expected):
        raise ValueError('Ungültige SHA-256-Prüfsumme.')
    versions = Path(versions)
    versions.mkdir(parents=True, exist_ok=True)
    target = versions / tag
    # Never overwrite a running or previously installed version.
    if target.exists():
        info = json.loads((target / 'build-info.json').read_text(encoding='utf-8'))
        if info.get('tag') == tag and (target / 'Precision-CAD.exe').is_file():
            return target / 'Precision-CAD.exe'
        raise ValueError('Der Versionsordner existiert bereits und wird nicht überschrieben.')
    with tempfile.TemporaryDirectory(prefix='.update-', dir=versions) as folder:
        archive = Path(folder) / 'update.zip'
        digest = hashlib.sha256()
        size = 0
        with request(url) as response, archive.open('wb') as output:
            while block := response.read(1024 * 1024):
                size += len(block)
                if size > MAX_DOWNLOAD:
                    raise ValueError('Der Download ist zu groß.')
                output.write(block)
                digest.update(block)
                progress(f'Update von GitHub laden: {size // (1024 * 1024)} MB …')
        if digest.hexdigest() != expected:
            raise ValueError('Prüfsumme stimmt nicht überein. Update wurde verworfen.')
        progress('Update prüfen und entpacken …')
        staged = Path(folder) / 'app'
        staged.mkdir()
        extract_checked(archive, staged)
        info = json.loads((staged / 'build-info.json').read_text(encoding='utf-8'))
        if info.get('tag') != tag:
            raise ValueError('Versionskennung im Archiv stimmt nicht mit dem Release überein.')
        progress("Installation abschließen …")
        staged.rename(target)
    return target / 'Precision-CAD.exe'
