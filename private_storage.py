"""Windows current-user DPAPI storage. No plaintext fallback on failure."""
import base64
import ctypes
from ctypes import wintypes
import json
import os
from pathlib import Path
import tempfile

MAGIC = b'IC35-DPAPI-1\n'
LOG_MAGIC = b'IC35-DPAPI-LOG-1\n'


def _crypt(data, decrypt=False):
    if os.name != 'nt':
        raise RuntimeError('Geschützte Speicherung benötigt Windows DPAPI.')
    class Blob(ctypes.Structure):
        _fields_ = [('size', wintypes.DWORD), ('data', ctypes.POINTER(ctypes.c_ubyte))]
    buffer = ctypes.create_string_buffer(data)
    source = Blob(len(data), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ubyte)))
    output = Blob()
    crypt = ctypes.WinDLL('crypt32', use_last_error=True)
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    fn = crypt.CryptUnprotectData if decrypt else crypt.CryptProtectData
    fn.argtypes = [ctypes.POINTER(Blob), ctypes.c_void_p, ctypes.POINTER(Blob),
                   ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(Blob)]
    fn.restype = wintypes.BOOL
    kernel.LocalFree.argtypes = [ctypes.c_void_p]
    kernel.LocalFree.restype = ctypes.c_void_p
    if not fn(ctypes.byref(source), None, None, None, None, 1, ctypes.byref(output)):
        raise OSError('Windows konnte die geschützten Daten nicht lesen/schreiben '
                      '(Windows-Konto, Dateiintegrität oder DPAPI prüfen).')
    try:
        return ctypes.string_at(output.data, output.size)
    finally:
        kernel.LocalFree(output.data)


def decode(raw):
    if raw.startswith(LOG_MAGIC):
        lines = raw[len(LOG_MAGIC):].splitlines(keepends=True)
        if any(not line.endswith(b'\n') for line in lines):
            raise ValueError('Unvollständiges geschütztes Protokoll.')
        return b''.join(_crypt(base64.b64decode(line.strip(), validate=True), True) for line in lines)
    if not raw.startswith(MAGIC):
        raise ValueError('Keine unterstützte geschützte IC35-Datei.')
    return _crypt(raw[len(MAGIC):], True)


def write_bytes(path, data):
    path = Path(path)
    encrypted = MAGIC + _crypt(data)
    if decode(encrypted) != data:
        raise OSError('DPAPI-Kontrolllesen fehlgeschlagen.')
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=path.name + '.', suffix='.tmp', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(encrypted)
            stream.flush()
            os.fsync(stream.fileno())
        if decode(Path(tmp).read_bytes()) != data:
            raise OSError('Datei-Kontrolllesen fehlgeschlagen.')
        os.replace(tmp, path)
    finally:
        Path(tmp).unlink(missing_ok=True)


def write_json(path, obj):
    write_bytes(path, json.dumps(obj, ensure_ascii=False, indent=2).encode('utf-8'))


def read_json(path, migrate=False):
    path = Path(path)
    raw = path.read_bytes()
    protected = raw.startswith(MAGIC)
    obj = json.loads((decode(raw) if protected else raw).decode('utf-8'))
    if migrate and not protected:
        write_json(path, obj)
    return obj


class Log:
    def __init__(self, path):
        self.path = Path(path)
        # Fail before starting a device operation if DPAPI is unavailable.
        _crypt(b'IC35 log initialization')
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open('xb') as stream:
            stream.write(LOG_MAGIC)

    def append(self, message):
        raw = (str(message) + '\n').encode('utf-8')
        line = base64.b64encode(_crypt(raw)) + b'\n'
        with self.path.open('ab') as stream:
            stream.write(line)
