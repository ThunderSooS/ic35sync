"""Make an upload bundle preserving the remotely edited website documents."""
import zipfile
from check_release import ROOT, release_files, check

check()
paths = [p for p in release_files() if 'docs' not in p.relative_to(ROOT).parts]
paths.append(ROOT / 'docs/TASKS_UNDATED_FIX.md')
paths.append(ROOT / 'docs/LOCAL_DATA_PROTECTION.md')
paths.append(ROOT / 'docs/PRIVACY.md')
output = ROOT / 'dist/IC35-Sync-3.3.0a4-GitHub-Update.zip'
with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_STORED, allowZip64=False) as z:
    for p in paths:
        z.write(p, p.relative_to(ROOT).as_posix())
with zipfile.ZipFile(output) as z:
    assert z.testzip() is None
    assert all(z.read(p.relative_to(ROOT).as_posix()) == p.read_bytes() for p in paths)
print(output)
