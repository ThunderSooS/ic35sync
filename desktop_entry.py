"""Frozen desktop entry point and private CardDAV subprocess mode."""
import os
import sys

if '--package-check' in sys.argv:
    def _check_error(kind, value, trace):
        import traceback
        from pathlib import Path
        Path(sys.argv[-1] + '.error').write_text(
            ''.join(traceback.format_exception(kind, value, trace)), encoding='utf-8')
        os._exit(1)
    sys.excepthook = _check_error

if __name__ == '__main__':
    if '--radicale' in sys.argv:
        sys.argv.remove('--radicale')
        from radicale_windows_launcher import run
        run()
    elif '--package-check' in sys.argv:
        # Explicit offline check: no user settings, network or device access.
        import json
        from pathlib import Path
        import tkinter as tk
        import serial
        import google_auth_oauthlib.flow
        from googleapiclient.discovery import build
        from google.auth.credentials import AnonymousCredentials
        import radicale_windows_launcher
        import radicale.storage.multifilesystem_nolock
        import radicale.auth.none
        import radicale.rights.owner_only
        import radicale.web.internal
        import sync_sounds
        import google_app_setup
        root = tk.Tk()
        root.withdraw()
        root.update()
        root.destroy()
        base = Path(__file__).resolve().parent
        google_app_setup.require_client(base / 'google_oauth_client.json')
        for name in sync_sounds.SOUNDS.values():
            assert (base / 'sounds' / name).is_file()
        for api, version in [('calendar', 'v3'), ('tasks', 'v1')]:
            build(api, version, credentials=AnonymousCredentials(), static_discovery=True)
        Path(sys.argv[-1]).write_text(json.dumps({'package_check': 'ok'}), encoding='utf-8')
    else:
        # Windowed Python has no stdout/stderr; libraries may still write to them.
        if sys.stdout is None:
            sys.stdout = open(os.devnull, 'w')
        if sys.stderr is None:
            sys.stderr = open(os.devnull, 'w')
        from IC35_Thunderbird_Sync import App
        App().mainloop()
