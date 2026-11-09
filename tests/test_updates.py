import hashlib
import io
import json
import stat
import zipfile
from pathlib import Path
import pytest
import updates


def release():
    return {'tag_name': 'test-42', 'assets': [
        {'name': n, 'browser_download_url': f'https://github.com/franzsonner/Precision-CAD/releases/download/test-42/{n}'}
        for n in (updates.ASSET, updates.ASSET + '.sha256')]}


def archive(tag='test-42'):
    data = io.BytesIO()
    with zipfile.ZipFile(data, 'w') as z:
        z.writestr('Precision-CAD.exe', b'new executable')
        z.writestr('build-info.json', json.dumps({'tag': tag, 'number': 42}))
        z.writestr('licenses/LICENSE', 'Original license')
    return data.getvalue()


def fake_download(monkeypatch, data, checksum=None):
    digest = checksum or hashlib.sha256(data).hexdigest()
    def request(url):
        return io.BytesIO(digest.encode() if url.endswith('.sha256') else data)
    monkeypatch.setattr(updates, 'request', request)


def test_newer_release_and_no_downgrade():
    assert updates.is_newer(release(), {'number': 41})
    assert not updates.is_newer(release(), {'number': 42})
    assert not updates.is_newer(release(), {'number': 43})


def test_install_preserves_old_version_and_retains_notices(tmp_path, monkeypatch):
    old = tmp_path / 'test-41'
    old.mkdir()
    (old / 'Precision-CAD.exe').write_bytes(b'old executable')
    fake_download(monkeypatch, archive())
    progress = []
    exe = updates.install_release(release(), tmp_path, progress.append)
    assert exe.read_bytes() == b'new executable'
    assert (old / 'Precision-CAD.exe').read_bytes() == b'old executable'
    assert (exe.parent / 'licenses/LICENSE').read_text() == 'Original license'
    assert not list(tmp_path.glob('.update-*'))
    assert progress
    assert updates.install_release(release(), tmp_path) == exe


def test_corrupt_download_and_wrong_version_leave_no_install(tmp_path, monkeypatch):
    fake_download(monkeypatch, archive(), '0' * 64)
    with pytest.raises(ValueError, match='Prüfsumme'):
        updates.install_release(release(), tmp_path)
    assert not list(tmp_path.iterdir())
    fake_download(monkeypatch, archive('test-41'))
    with pytest.raises(ValueError, match='Versionskennung'):
        updates.install_release(release(), tmp_path)
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize('name', ['../escape', '..\\escape', 'C:/escape', '/escape', 'dir/../../escape', 'dir/.. /escape', 'NUL.txt', 'file:stream'])
def test_archive_rejects_windows_path_traversal_and_devices(tmp_path, name):
    data = io.BytesIO()
    with zipfile.ZipFile(data, 'w') as z:
        z.writestr('Precision-CAD.exe', 'exe')
        z.writestr(name, 'bad')
    data.seek(0)
    with pytest.raises(ValueError, match='Unsicherer Pfad'):
        updates.extract_checked(data, tmp_path)
    assert not list(tmp_path.iterdir())


def test_symlink_archive_rejected(tmp_path):
    data = io.BytesIO()
    with zipfile.ZipFile(data, 'w') as z:
        link = zipfile.ZipInfo('link')
        link.external_attr = (stat.S_IFLNK | 0o777) << 16
        z.writestr(link, '../escape')
    data.seek(0)
    with pytest.raises(ValueError):
        updates.extract_checked(data, tmp_path)


def test_download_cannot_use_another_repository():
    r = release()
    r['assets'][0]['browser_download_url'] = 'https://example.org/update.zip'
    with pytest.raises(ValueError, match='Download-Adresse'):
        updates.asset_url(r, updates.ASSET)


def test_cancelled_download_cleans_staging(tmp_path, monkeypatch):
    fake_download(monkeypatch, archive())
    def cancel(text):
        if 'MB' in text:
            raise RuntimeError('Update abgebrochen.')
    with pytest.raises(RuntimeError, match='abgebrochen'):
        updates.install_release(release(), tmp_path, cancel)
    assert not list(tmp_path.iterdir())
