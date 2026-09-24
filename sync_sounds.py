"""Short, asynchronous Windows notification sounds; no extra dependencies."""
from pathlib import Path
import ctypes
import os

try:
    import winsound
except ImportError:
    winsound = None

SOUNDS = {"start": "sync_start.mp3", "press_again": "dock_prompt.mp3", "connected": "connected.wav", "complete": "complete.wav"}


def play(event):
    if winsound is None:
        return
    try:
        path = Path(__file__).parent / "sounds" / SOUNDS[event]
        if os.name == 'nt':
            send = ctypes.windll.winmm.mciSendStringW
            send('close ic35_dock_prompt', None, 0, None)
            if path.suffix == '.mp3':
                winsound.PlaySound(None, 0)
                if send(f'open "{path}" type mpegvideo alias ic35_dock_prompt', None, 0, None) == 0:
                    send('play ic35_dock_prompt from 0', None, 0, None)
                return
        winsound.PlaySound(str(path), winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT)
    except (OSError, RuntimeError, KeyError):
        # Audio must never interrupt the backup or the synchronization.
        pass
