"""Build an explicit Desktop-client test bundle; never include user tokens."""
import argparse
import hashlib
import json
import sys
import zipfile
from check_release import ROOT, release_files, check

sys.path.insert(0, str(ROOT))
from google_app_setup import require_client

parser = argparse.ArgumentParser()
parser.add_argument('desktop_client')
args = parser.parse_args()
check()
path = require_client(args.desktop_client)
data = json.loads(path.read_text(encoding='utf-8'))
if set(data) != {'installed'}:
    raise ValueError('Expected only a Desktop installed-client configuration.')
client = data['installed']
allowed = {'client_id', 'project_id', 'auth_uri', 'token_uri',
           'auth_provider_x509_cert_url', 'client_secret', 'redirect_uris'}
if set(client) - allowed:
    raise ValueError('Unexpected fields in Desktop configuration.')
if client.get('project_id') != 'ic35sync':
    raise ValueError('Expected the ic35sync project.')
payload = json.dumps({'installed': client}, indent=2).encode('utf-8')
files = {'ic35-sync/' + p.relative_to(ROOT).as_posix(): p.read_bytes()
         for p in release_files()}
files['ic35-sync/google_oauth_client.json'] = payload
files['ic35-sync/LOGIN_TEST.txt'] = (
    'Google-Anmeldung eingerichtet (3.3.0a6). Windows-DPAPI-Schutz aktiviert.\r\n'
    'Persoenliches Extra: Sprachhinweis bei Aufforderung zum Druecken der Docktaste.\r\n'
    'install.bat einmal starten, danach start.bat und Google verbinden.\r\n'
    'Kalender und Aufgaben haben getrennte Freigaben.\r\n'
    'Dieses Testpaket enthaelt den Desktop-App-Client, keine Nutzer-Tokens.\r\n'
    'Die Google-Datenzugriffspruefung ist noch nicht abgeschlossen.\r\n'
    'Datenordner: %APPDATA%\\IC35SyncPreview.\r\n'
    'Anmeldung zuerst testen; Gesamtsync schreibt Daten in beide Richtungen.\r\n'
).encode('utf-8')
output = ROOT / 'dist' / 'IC35-Sync-3.3.0a6-Google-Login-Test.zip'
output.parent.mkdir(exist_ok=True)
with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_STORED, allowZip64=False) as z:
    for name, contents in sorted(files.items()):
        info = zipfile.ZipInfo(name, (2026, 9, 9, 0, 0, 0))
        info.create_system = 0
        info.external_attr = 0x20
        z.writestr(info, contents)
with zipfile.ZipFile(output) as z:
    assert z.testzip() is None
    assert set(z.namelist()) == set(files)
    for name, contents in files.items():
        assert z.read(name) == contents
digest = hashlib.sha256(output.read_bytes()).hexdigest()
output.with_suffix('.zip.sha256').write_text(digest + '  ' + output.name + '\n', encoding='ascii')
print('Desktop configuration validated; no user tokens included.')
print(output)
print('ZIP readback passed; SHA256 ' + digest)
