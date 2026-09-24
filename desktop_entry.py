"""Desktop application, private local DAV subprocess, isolated offline checks."""
import os
import sys

# Keep Tkinter visible to PyInstaller.  The GUI is imported only in the
# normal desktop branch, so static analysis otherwise omits it from the EXE.
import tkinter

if '--package-check' in sys.argv:
    def _error(kind, value, trace):
        import traceback
        from pathlib import Path
        Path(sys.argv[-1] + '.error').write_text(''.join(traceback.format_exception(kind, value, trace)), encoding='utf-8')
        os._exit(1)
    sys.excepthook = _error

if __name__ == '__main__':
    if sys.stdout is None:
        sys.stdout = open(os.devnull, 'w')
    if sys.stderr is None:
        sys.stderr = open(os.devnull, 'w')
    if '--radicale' in sys.argv:
        sys.argv.remove('--radicale')
        from radicale_windows_launcher import run
        run()
    elif '--package-check' in sys.argv:
        import json
        import tempfile
        from pathlib import Path
        import private_storage
        import sync_sounds
        import thunderbird_rpc
        import radicale.storage.multifilesystem
        import radicale.auth.none
        import radicale.rights.owner_only
        import radicale.web.internal
        from zoneinfo import ZoneInfo
        with tempfile.TemporaryDirectory() as tmp:
            os.environ['IC35_TB_DATA_DIR'] = tmp
            from app import App, VERSION
            app = App()
            app.withdraw()
            app.update_idletasks()
            app.close()
            test = Path(tmp) / 'check.dpapi'
            private_storage.write_json(test, {'synthetic': 'test'})
            assert private_storage.read_json(test) == {'synthetic': 'test'}
            assert b'synthetic' not in test.read_bytes()
            broker = thunderbird_rpc.Broker(tmp, port=0)
            try:
                assert len(broker.pairing['token']) == 43
                assert private_storage.read_json(Path(tmp) / 'addon_pairing.dpapi')['token'] == broker.pairing['token']
            finally:
                broker.close()
            ZoneInfo('Europe/Berlin')
            for name in sync_sounds.SOUNDS.values():
                assert (Path(sync_sounds.__file__).parent / 'sounds' / name).is_file()
        Path(sys.argv[-1]).write_text(json.dumps({'package_check': 'ok', 'version': VERSION, 'ui': 'ok', 'DPAPI': 'ok', 'sounds': 'present', 'addon_broker': 'ok'}), encoding='utf-8')
    else:
        from app import App
        App().mainloop()
