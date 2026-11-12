"""Build a self-contained Windows folder app without credentials or runtime data."""
import importlib.metadata
from pathlib import Path
import shutil
import subprocess
import sys
import tkinter
import _tkinter

ROOT = Path(__file__).resolve().parents[1]
subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-q'], cwd=ROOT, check=True)
PYROOT = Path(sys.base_prefix)
TKLIB = Path(tkinter.__file__).parent
TKBIN = Path(_tkinter.__file__)
subprocess.run([sys.executable, str(ROOT / 'scripts/build_addon.py')], check=True)
licenses = ROOT / 'build-licenses'
licenses.mkdir(exist_ok=True)
for dist in importlib.metadata.distributions():
    for file in dist.files or []:
        if any(word in file.name.lower() for word in ('license', 'copying', 'notice')):
            source = Path(dist.locate_file(file))
            if source.is_file():
                target = licenses / dist.metadata['Name'] / str(file).replace('..', '_')
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, target)
for name, source in [('Python-LICENSE.txt', Path(sys.base_prefix) / 'LICENSE.txt'),
                     ('Tcl-license.terms', Path(sys.base_prefix) / 'tcl/tcl8.6/license.terms'),
                     ('Tk-license.terms', Path(sys.base_prefix) / 'tcl/tk8.6/license.terms')]:
    if source.is_file(): shutil.copyfile(source, licenses / name)
with (ROOT / 'build-requirements.txt').open('w') as out:
    subprocess.run([sys.executable, '-m', 'pip', 'freeze'], stdout=out, check=True)
subprocess.run([sys.executable, '-m', 'PyInstaller', '--noconfirm', '--clean', '--onedir', '--windowed',
               '--contents-directory', '_internal',
               '--paths', str(TKLIB.parent),
               '--hidden-import=tkinter', '--hidden-import=_tkinter',
               '--add-data', f'{TKLIB};tkinter',
               '--add-binary', f'{TKBIN};.',
               '--add-binary', f'{TKBIN.parent / "tk86t.dll"};.',
               '--add-data', f'{PYROOT / "tcl"};tcl',
               '--name', 'IC35Thunderbird', '--add-data', f'{ROOT / "sounds"};sounds',
               '--collect-all', 'radicale', '--collect-all', 'tzdata', '--collect-all', 'passlib',
               '--copy-metadata', 'libpass', '--recursive-copy-metadata', 'radicale',
               str(ROOT / 'desktop_entry.py')], cwd=ROOT, check=True)
bundle = ROOT / 'dist/IC35Thunderbird'
if not (bundle / '_internal').is_dir():
    raise RuntimeError('Onedir runtime folder missing')
subprocess.run([sys.executable, str(ROOT / 'scripts/smoke_windows.py'),
                str(bundle / 'IC35Thunderbird.exe')], cwd=ROOT, check=True, timeout=120)
