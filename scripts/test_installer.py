"""Install, verify the entire onedir runtime, smoke-test and uninstall in isolation."""
from pathlib import Path
import hashlib
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
setup = ROOT / '.installer-test/Isolated-Test-Setup.exe'
bundle = ROOT / 'dist/IC35Thunderbird'
expected = {path.relative_to(bundle): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in bundle.rglob('*') if path.is_file()}
assert Path('IC35Thunderbird.exe') in expected
assert any(path.parts[0] == '_internal' for path in expected)
with tempfile.TemporaryDirectory(prefix='ic35-install-check-') as tmp:
    target = Path(tmp) / 'app'
    subprocess.run([str(setup), '/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART', '/NOICONS',
                    '/TASKS=', f'/DIR={target}'], check=True, timeout=60)
    try:
        assert (target / 'licenses/pyserial/LICENSE.txt').exists()
        assert (target / 'README.en.md').exists()
        assert (target / 'IC35-Thunderbird-Bridge-3.4.0b5.xpi').exists()
        assert (target / '_internal').is_dir()
        for relative, digest in expected.items():
            installed = target / relative
            assert installed.is_file(), f'Missing installed runtime file: {relative}'
            assert hashlib.sha256(installed.read_bytes()).hexdigest() == digest, f'Installed file differs: {relative}'
        subprocess.run([sys.executable, str(ROOT / 'scripts/smoke_windows.py'),
                        str(target / 'IC35Thunderbird.exe')], check=True, timeout=120)
    finally:
        subprocess.run([str(target / 'unins000.exe'), '/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART'],
                       check=True, timeout=60)
    assert not (target / 'IC35Thunderbird.exe').exists()
    assert not (target / '_internal').exists()
print('Installer: complete onedir runtime hashes, installed EXE/DAV, uninstall OK')
