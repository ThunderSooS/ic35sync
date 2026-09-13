"""Resolve the publisher's Desktop OAuth configuration without a file dialog."""
import json
from pathlib import Path


def credentials_path(app_dir, data_dir):
    # Retain the client used by existing preview installations and their tokens.
    previous = Path(data_dir) / 'google_credentials.json'
    return previous if previous.is_file() else Path(app_dir) / 'google_oauth_client.json'


def require_client(path):
    path = Path(path)
    if not path.is_file():
        raise RuntimeError(
            'Die Google-Anmeldung ist in diesem Programmpaket noch nicht eingerichtet. '
            'Der Herausgeber muss die Desktop-OAuth-Konfiguration mitliefern. '
            'Als Nutzer musst du keine JSON-Datei erstellen oder auswählen.')
    config = json.loads(path.read_text(encoding='utf-8'))
    client = config.get('installed', {})
    if not all(client.get(key) for key in ('client_id', 'client_secret', 'auth_uri', 'token_uri')):
        raise ValueError('Ungültige Google-App-Konfiguration: Ein Desktop-OAuth-Client wird benötigt.')
    if client['auth_uri'] != 'https://accounts.google.com/o/oauth2/auth' or client['token_uri'] != 'https://oauth2.googleapis.com/token':
        raise ValueError('Die Google-App-Konfiguration enthält unerwartete Anmeldeadressen.')
    return path
