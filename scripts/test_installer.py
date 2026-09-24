"""Install, smoke-test and uninstall in an isolated folder; never launch the app normally."""
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
setup = ROOT / '.installer-test/Isolated-Test-Setup.exe'
# Compile installer.iss with /DBuildTest=1 first. Its separate AppId preserves installed releases.
with tempfile.TemporaryDirectory(prefix='ic35-install-check-') as tmp:
    target = Path(tmp) / 'app'
    subprocess.run([str(setup), '/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART', '/NOICONS',
                    '/TASKS=', f'/DIR={target}'], check=True, timeout=60)
    try:
        assert (target / 'licenses/pyserial/LICENSE.txt').exists()
        assert (target / 'README.en.md').exists()
        assert (target / 'IC35-Thunderbird-Bridge-3.4.0a9.xpi').exists()
        subprocess.run([sys.executable, str(ROOT / 'scripts/smoke_windows.py'),
                        str(target / 'IC35Thunderbird.exe')], check=True, timeout=90)
    finally:
        subprocess.run([str(target / 'unins000.exe'), '/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART'],
                       check=True, timeout=60)
    assert not (target / 'IC35Thunderbird.exe').exists()
print('Installer: isolated install, installed EXE/DAV, uninstall OK')
