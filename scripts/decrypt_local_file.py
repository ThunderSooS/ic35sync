"""Explicit export for recovery/support; never overwrites an existing file."""
import argparse
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import private_storage

parser = argparse.ArgumentParser(description='IC35-Datei unter demselben Windows-Konto entschlüsseln.')
parser.add_argument('source')
parser.add_argument('destination')
args = parser.parse_args()
data = private_storage.decode(Path(args.source).read_bytes())
with Path(args.destination).open('xb') as stream:
    stream.write(data)
print('Klartextdatei erstellt. Sie kann persönliche Daten enthalten.')
