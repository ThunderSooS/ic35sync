from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
FILES = ('manifest.json', 'schema.json', 'api.js', 'background.js', 'options.html', 'options.js')
target = ROOT / 'release/IC35-Thunderbird-Bridge-3.4.0a9.xpi'
target.parent.mkdir(exist_ok=True)
with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as archive:
    for name in FILES:
        archive.write(ROOT / 'addon' / name, name)
    archive.write(ROOT / 'LICENSE', 'LICENSE')
with zipfile.ZipFile(target) as archive:
    assert archive.testzip() is None
print(target.name)
