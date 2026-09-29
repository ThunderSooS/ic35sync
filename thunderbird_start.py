"""Start installed Thunderbird once, without changing its profile or lifetime."""
import csv
import ctypes
import os
from pathlib import Path
import shutil
import subprocess
import winreg


def running():
    session = ctypes.c_ulong()
    if not ctypes.windll.kernel32.ProcessIdToSessionId(os.getpid(), ctypes.byref(session)):
        raise OSError('Windows-Sitzung konnte nicht ermittelt werden')
    result = subprocess.run(
        ['tasklist.exe', '/FI', 'IMAGENAME eq thunderbird.exe', '/FI',
         f'SESSION eq {session.value}', '/FO', 'CSV', '/NH'],
        capture_output=True, text=True, errors='replace', timeout=10,
        creationflags=subprocess.CREATE_NO_WINDOW, check=True)
    return any(row and row[0].lower() == 'thunderbird.exe'
               for row in csv.reader(result.stdout.splitlines()))


def executable():
    for hive in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
        for view in (winreg.KEY_WOW64_64KEY, winreg.KEY_WOW64_32KEY):
            try:
                with winreg.OpenKey(hive, r'SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\thunderbird.exe',
                                    0, winreg.KEY_READ | view) as key:
                    path = Path(os.path.expandvars(winreg.QueryValueEx(key, None)[0]).strip('"'))
                    if path.is_file():
                        return path
            except OSError:
                pass
    for variable, suffix in [('ProgramFiles', 'Mozilla Thunderbird'),
                             ('ProgramFiles(x86)', 'Mozilla Thunderbird'),
                             ('LOCALAPPDATA', 'Programs/Mozilla Thunderbird')]:
        if os.environ.get(variable):
            path = Path(os.environ[variable]) / suffix / 'thunderbird.exe'
            if path.is_file():
                return path
    return shutil.which('thunderbird.exe')


def ensure_started(log):
    try:
        if running():
            log('Thunderbird läuft bereits.')
            return
        path = executable()
        if not path:
            log('Thunderbird nicht gefunden. Bitte Thunderbird manuell öffnen.')
            return
        # Recheck after discovery in case Thunderbird started in the meantime.
        if running():
            log('Thunderbird läuft bereits.')
            return
        subprocess.Popen([str(path)], close_fds=True)
        log('Thunderbird wurde gestartet. Die Add-on-Verbindung wird aufgebaut.')
    except (OSError, subprocess.SubprocessError) as exc:
        log(f'Thunderbird konnte nicht automatisch gestartet werden: {exc}. Bitte manuell öffnen.')
