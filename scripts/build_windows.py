"""Build the Windows EXE with an explicit Desktop OAuth client, never runtime data."""
import argparse
import importlib.metadata
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from google_app_setup import require_client

parser = argparse.ArgumentParser()
parser.add_argument('desktop_client')
args = parser.parse_args()
client = require_client(args.desktop_client).resolve()
import json
data = json.loads(client.read_text(encoding='utf-8'))
assert set(data) == {'installed'}
assert data['installed']['project_id'] == 'ic35sync'
allowed = {'client_id', 'project_id', 'auth_uri', 'token_uri',
           'auth_provider_x509_cert_url', 'client_secret', 'redirect_uris'}
assert not set(data['installed']) - allowed
stage = ROOT / 'build-client'
stage.mkdir(exist_ok=True)
(stage / 'google_oauth_client.json').write_text(json.dumps(data), encoding='utf-8')
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
python_license = Path(sys.base_prefix) / 'LICENSE.txt'
if python_license.is_file():
    shutil.copyfile(python_license, licenses / 'Python-LICENSE.txt')
tk_license = Path(sys.base_prefix) / 'tcl/tk8.6/license.terms'
if tk_license.is_file():
    shutil.copyfile(tk_license, licenses / 'TclTk-license.terms')
subprocess.run([sys.executable, '-m', 'pip', 'freeze'], stdout=(ROOT / 'build-requirements.txt').open('w'), check=True)
command = [sys.executable, '-m', 'PyInstaller', '--noconfirm', '--clean',
           '--onefile', '--windowed', '--name', 'IC35Sync',
           '--add-data', f'{ROOT / "sounds"};sounds',
           '--add-data', f'{stage / "google_oauth_client.json"};.',
           '--collect-all', 'radicale', '--collect-all', 'googleapiclient',
           '--collect-all', 'tzdata', '--collect-all', 'passlib',
           '--copy-metadata', 'libpass', '--recursive-copy-metadata', 'radicale',
           str(ROOT / 'desktop_entry.py')]
subprocess.run(command, cwd=ROOT, check=True)
