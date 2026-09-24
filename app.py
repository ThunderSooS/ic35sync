"""Thunderbird-only desktop application. No cloud accounts or OAuth."""
import json
import math
import os
from pathlib import Path
import queue
import socket
import subprocess
import sys
import threading
import time
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import serial
from serial.tools import list_ports
import bridge
import dav_sync
import ic35_protocol as proto
import manager_protocol as manager
import private_storage
import sync_sounds
import thunderbird_rpc
import thunderbird_calendar

VERSION = '3.4.0a11'
ROOT = Path(os.environ.get('IC35_TB_DATA_DIR') or Path(os.environ.get('APPDATA', Path.home())) / 'IC35ThunderbirdAlpha')
PORT = 5233
BASE = f'http://127.0.0.1:{PORT}'


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        ROOT.mkdir(parents=True, exist_ok=True)
        self.title(f'IC35 Sync Beta · {VERSION}')
        self.geometry('900x840')
        self.minsize(820, 720)
        self.messages = queue.Queue()
        self.busy = False
        self.server = None
        self.server_log = None
        self.broker = None
        self.angle = 0
        self.prompt_timer = None
        self.start_sound_until = 0
        settings = ROOT / 'settings.json'
        config = json.loads(settings.read_text()) if settings.exists() else {}
        self.saved_calendars = config.get('calendars', {})
        self.calendar_ids = {'Lokale IC35-Sammlung': ''}
        self.port = tk.StringVar(value=config.get('port', ''))
        self.zone = tk.StringVar(value=config.get('zone', 'Europe/Berlin'))
        self.stage = tk.StringVar(value='Bereit · Thunderbird vor dem Geräteabgleich synchronisieren')
        self.server_status = tk.StringVar(value='Lokaler Thunderbird-Dienst gestoppt')
        ttk.Label(self, text='Siemens IC35 ↔ Thunderbird', font=('Segoe UI', 21)).pack(pady=(16, 5))
        ttk.Label(self, text='Kontakte · Kalender · Aufgaben — lokal auf deinem PC').pack()
        row = ttk.Frame(self, padding=12); row.pack()
        ttk.Label(row, text='Dock-Anschluss:').pack(side='left')
        self.ports = ttk.Combobox(row, textvariable=self.port, width=12, values=[x.device for x in list_ports.comports()])
        self.ports.pack(side='left', padx=8)
        ttk.Label(row, text='IC35-Zeitzone:').pack(side='left')
        self.zone_entry = ttk.Entry(row, textvariable=self.zone, width=22); self.zone_entry.pack(side='left', padx=8)
        choices = ttk.Frame(self, padding=6); choices.pack(fill='x', padx=22)
        self.calendar_vars, self.calendar_boxes = {}, {}
        for kind, label in [('events', 'Termine aus:'), ('tasks', 'Aufgaben aus:')]:
            line = ttk.Frame(choices); line.pack(fill='x', pady=3)
            ttk.Label(line, text=label, width=16).pack(side='left')
            saved = self.saved_calendars.get(kind, '')
            title = ('Gespeicherter Thunderbird-Kalender [' + saved + ']') if saved else 'Lokale IC35-Sammlung'
            self.calendar_ids[title] = saved
            var = tk.StringVar(value=title)
            box = ttk.Combobox(line, textvariable=var, state='readonly', width=66)
            self.calendar_vars[kind], self.calendar_boxes[kind] = var, box
            box.configure(width=66, values=[title, 'Lokale IC35-Sammlung'] if saved else ['Lokale IC35-Sammlung'])
            box.pack(side='left', fill='x', expand=True)
        actions = ttk.Frame(choices); actions.pack(pady=5)
        self.pair_btn = ttk.Button(actions, text='Thunderbird-Add-on koppeln', command=self.pair_addon); self.pair_btn.pack(side='left', padx=4)
        self.refresh_btn = ttk.Button(actions, text='Kalender aus Thunderbird laden', command=self.load_calendars); self.refresh_btn.pack(side='left', padx=4)
        self.canvas = tk.Canvas(self, width=84, height=84, highlightthickness=0)
        self.canvas.pack()
        self.arrows = [self.canvas.create_line(0, 0, 1, 1, width=5, fill=c, arrow=tk.LAST,
                         arrowshape=(12, 14, 6), smooth=True) for c in ('#1664a5', '#39a3bb')]
        self.draw()
        self.sync_btn = ttk.Button(self, text='ALLES MIT THUNDERBIRD SYNCHRONISIEREN', command=lambda: self.launch(False))
        self.sync_btn.pack(ipady=9, pady=6)
        ttk.Label(self, textvariable=self.stage, wraplength=800, font=('Segoe UI', 11)).pack(pady=8)
        tools = ttk.Frame(self, padding=8); tools.pack(fill='x')
        self.backup_btn = ttk.Button(tools, text='Nur Vollbackup', command=lambda: self.launch(True)); self.backup_btn.pack(side='left', padx=4)
        ttk.Button(tools, text='Thunderbird einrichten', command=self.setup_help).pack(side='left', padx=4)
        ttk.Button(tools, text='Geschützte Datei exportieren', command=self.export_file).pack(side='left', padx=4)
        ttk.Button(tools, text='Datenordner', command=lambda: os.startfile(ROOT)).pack(side='left', padx=4)
        ttk.Label(self, textvariable=self.server_status).pack()
        self.log_text = tk.Text(self, wrap='word', height=18, font=('Consolas', 9))
        self.log_text.pack(fill='both', expand=True, padx=16, pady=12)
        self.protocol('WM_DELETE_WINDOW', self.close)
        self.after(100, self.drain)
        self.after(400, self.start_server_ui)

    def draw(self):
        for item, offset in zip(self.arrows, (10, 190)):
            points = []
            for index in range(29):
                radians = math.radians(self.angle + offset + 155 * index / 28)
                points.extend((42 + 29 * math.cos(radians), 42 + 29 * math.sin(radians)))
            self.canvas.coords(item, *points)
        if self.busy:
            self.angle = (self.angle + 6) % 360
            self.after(45, self.draw)

    def emit(self, kind, value):
        self.messages.put((kind, value))

    def drain(self):
        try:
            while True:
                kind, value = self.messages.get_nowait()
                if kind == 'log':
                    self.log_text.insert('end', f'[{datetime.now():%H:%M:%S}] {value}\n')
                    self.log_text.see('end')
                elif kind == 'stage':
                    self.stage.set(value)
                elif kind == 'sound':
                    if value == 'start':
                        self.start_sound_until = time.monotonic() + 2.5
                        sync_sounds.play(value)
                    elif value == 'press_again':
                        delay = max(0, int((self.start_sound_until - time.monotonic()) * 1000))
                        self.prompt_timer = self.after(delay, lambda: sync_sounds.play('press_again'))
                    else:
                        if self.prompt_timer is not None:
                            self.after_cancel(self.prompt_timer)
                            self.prompt_timer = None
                        sync_sounds.play(value)
                elif kind == 'calendars':
                    self.show_calendars(value)
                    self.refresh_btn.configure(state='normal')
                elif kind == 'calendar_error':
                    self.refresh_btn.configure(state='normal')
                    messagebox.showerror('Thunderbird-Verbindung', value)
                elif kind in ('done', 'error'):
                    if self.prompt_timer is not None:
                        self.after_cancel(self.prompt_timer)
                        self.prompt_timer = None
                    self.busy = False
                    for widget in (self.sync_btn, self.backup_btn, self.ports, self.zone_entry):
                        widget.configure(state='normal')
                    for widget in self.calendar_boxes.values():
                        widget.configure(state='readonly')
                    self.pair_btn.configure(state='normal'); self.refresh_btn.configure(state='normal')
                    self.stage.set('✓ Abgeschlossen' if kind == 'done' else 'Abgleich angehalten')
                    if kind == 'done':
                        sync_sounds.play('complete')
                        messagebox.showinfo('IC35 · Thunderbird', value)
                    else:
                        messagebox.showerror('Abgleich angehalten', value)
        except queue.Empty:
            pass
        self.after(100, self.drain)

    def start_server_ui(self):
        try:
            self.start_server()
            if (ROOT / 'addon_pairing.dpapi').exists():
                self.get_broker()
            self.server_status.set('Lokaler Thunderbird-Dienst läuft · App geöffnet lassen')
        except Exception as exc:
            self.server_status.set(str(exc))

    def get_broker(self):
        if self.broker is None:
            self.broker = thunderbird_rpc.Broker(ROOT)
        return self.broker

    def pair_addon(self):
        try:
            broker = self.get_broker()
            self.clipboard_clear(); self.clipboard_append(broker.pairing['token'])
            messagebox.showinfo('Thunderbird-Add-on koppeln',
                'Der Kopplungscode wurde in die Zwischenablage kopiert.\n\n'
                '1. In Thunderbird → Add-ons und Themes → Zahnrad → Add-on aus Datei installieren.\n'
                '2. IC35-Thunderbird-Bridge-3.4.0a9.xpi auswählen.\n'
                '3. In den Add-on-Einstellungen den Code einfügen und „Verbinden“ drücken.\n'
                '4. Hier „Kalender aus Thunderbird laden“ anklicken und „twitch“ bei Terminen auswählen.\n\n'
                'Die XPI-Datei liegt neben der installierten EXE. Thunderbird geöffnet lassen.')
        except Exception as exc:
            messagebox.showerror('Kopplung', str(exc))

    def load_calendars(self):
        try:
            broker = self.get_broker()
        except Exception as exc:
            messagebox.showerror('Thunderbird-Verbindung', str(exc)); return
        self.refresh_btn.configure(state='disabled')
        def load():
            try:
                self.emit('calendars', broker.call('list', timeout=20))
            except Exception as exc:
                self.emit('calendar_error', str(exc))
        threading.Thread(target=load, daemon=True).start()

    def show_calendars(self, response):
        current = {k: self.calendar_ids.get(v.get(), '') for k, v in self.calendar_vars.items()}
        self.calendar_ids = {'Lokale IC35-Sammlung': ''}
        for kind, box in self.calendar_boxes.items():
            labels = ['Lokale IC35-Sammlung']
            selected = None
            for info in response['calendars']:
                if not info[kind] or info['disabled'] or info['readOnly'] or info['type'] not in ('storage', 'caldav'):
                    continue
                label = f'{info["name"]} · Thunderbird [{info["id"][:8]}]'
                labels.append(label); self.calendar_ids[label] = info['id']
                if info['id'] == current[kind]: selected = label
            if current[kind] and selected is None:
                selected = 'Nicht verfügbar [' + current[kind] + ']'
                labels.append(selected); self.calendar_ids[selected] = current[kind]
            box.configure(values=labels)
            self.calendar_vars[kind].set(selected or labels[0])
        self.emit('log', 'Thunderbird ' + response['version'] + ': Kalender geladen. Gewünschtes Ziel bei „Termine aus“ auswählen.')

    def start_server(self):
        if self.server is not None and self.server.poll() is None:
            return
        with socket.socket() as probe:
            if probe.connect_ex(('127.0.0.1', PORT)) == 0:
                raise RuntimeError('Port 5233 ist belegt. Andere Thunderbird-Alpha schließen.')
        if (ROOT / 'thunderbird_state.dpapi').exists() or any((ROOT / 'sync_states').glob('*/thunderbird_state.dpapi')):
            for name in ('calendar', 'addressbook'):
                if not (ROOT / 'radicale' / 'collection-root' / 'ic35' / name / '.Radicale.props').exists():
                    raise RuntimeError('Lokale Sammlung fehlt bei vorhandenem Sync-State. Abgleich zum Schutz der Gerätedaten gesperrt.')
        bridge.ensure_radicale_storage(ROOT / 'radicale')
        command = [sys.executable]
        if getattr(sys, 'frozen', False):
            command += ['--radicale']
        else:
            command += [str(Path(__file__).with_name('radicale_windows_launcher.py'))]
        command += ['--config', '', '--storage-filesystem-folder', str(ROOT / 'radicale'),
                    '--storage-type', 'multifilesystem', '--auth-type', 'none', '--server-hosts', f'127.0.0.1:{PORT}']
        self.server_log = (ROOT / 'radicale_start.log').open('w', encoding='utf-8')
        self.server = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=self.server_log,
            stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NO_WINDOW)
        for _ in range(100):
            with socket.socket() as probe:
                if probe.connect_ex(('127.0.0.1', PORT)) == 0:
                    return
            if self.server.poll() is not None:
                break
            time.sleep(.1)
        self.stop_server()
        raise RuntimeError('Lokaler Dienst konnte nicht gestartet werden; radicale_start.log im Datenordner prüfen')

    def setup_help(self):
        self.start_server_ui()
        messagebox.showinfo('Thunderbird einrichten',
            'Bestehenden Kalender wie „twitch“ nutzen:\n'
            '„Thunderbird-Add-on koppeln“ → Add-on installieren → Kalender laden → bei Terminen auswählen.\n'
            'Thunderbird übernimmt weiterhin dessen Server-/Handy-Synchronisation.\n\n'
            'Für Kontakte und alternativ lokale Termine/Aufgaben:\n\n'
            'Adressbuch → Neues Adressbuch → CardDAV-Adressbuch hinzufügen:\n'
            f'Benutzername: ic35\nAdresse: {BASE}/ic35/addressbook/\n\n'
            'Kalender → Neuer Kalender → Im Netzwerk → CalDAV:\n'
            f'Benutzername: ic35\nAdresse: {BASE}/ic35/calendar/\n'
            'Dieser Kalender enthält auch die Aufgaben. Falls Thunderbird nach einem Passwort fragt: ic35.\n'
            'Dies ist nur der lokale Dienst, kein Internet-Konto.\n\n'
            'Die App geöffnet lassen. Thunderbird vor und nach jedem Geräteabgleich synchronisieren.\n'
            'Nur Einträge in diesen Sammlungen werden abgeglichen.\n'
            'Beim ersten Geräteabgleich werden vorhandene IC35-Inhalte übernommen.')

    def export_file(self):
        source = filedialog.askopenfilename(initialdir=ROOT, title='Geschützte Datei auswählen')
        if not source:
            return
        try:
            data = private_storage.decode(Path(source).read_bytes())
            target = filedialog.asksaveasfilename(title='Unverschlüsselte Kopie speichern', initialfile=Path(source).name.removesuffix('.dpapi'))
            if target:
                with Path(target).open('xb') as stream:
                    stream.write(data)
                messagebox.showinfo('Export', 'Unverschlüsselte Kopie gespeichert.')
        except Exception as exc:
            messagebox.showerror('Export', str(exc))

    def launch(self, backup):
        if self.busy:
            return
        if str(self.refresh_btn['state']) == 'disabled':
            messagebox.showinfo('Kalender werden geladen', 'Bitte kurz warten, bis die Kalenderliste geladen ist.'); return
        port, zone = self.port.get().strip(), self.zone.get().strip()
        if not port:
            messagebox.showerror('Dock-Anschluss', 'Bitte COM-Anschluss auswählen.'); return
        try:
            ZoneInfo(zone)
            self.start_server()
            selections = {kind: self.calendar_ids[var.get()] for kind, var in self.calendar_vars.items()}
            if any(selections.values()) and not backup:
                self.get_broker()
        except Exception as exc:
            messagebox.showerror('Vorbereitung', str(exc)); return
        (ROOT / 'settings.json').write_text(json.dumps({'port': port, 'zone': zone, 'calendars': selections}), encoding='utf-8')
        self.busy = True
        for widget in (self.sync_btn, self.backup_btn, self.ports, self.zone_entry):
            widget.configure(state='disabled')
        for widget in (*self.calendar_boxes.values(), self.pair_btn, self.refresh_btn):
            widget.configure(state='disabled')
        self.draw()
        self.log_text.delete('1.0', 'end')
        threading.Thread(target=self.worker, args=(port, zone, backup, selections), daemon=True).start()

    def worker(self, port, zone, backup, selections):
        import msvcrt
        ser, lock = None, None
        log = lambda message='': self.emit('log', message)
        try:
            lock = (ROOT / 'sync.lock').open('a+b')
            if lock.tell() == 0:
                lock.write(b'0'); lock.flush()
            lock.seek(0)
            msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
            stamp = datetime.now().strftime('%Y%m%d_%H%M%S') + '_' + uuid.uuid4().hex[:6]
            protected_log = private_storage.Log(ROOT / 'logs' / f'{stamp}.log.dpapi')
            def log(message=''):
                protected_log.append(message)
                self.emit('log', message)
            self.emit('sound', 'start')
            self.emit('stage', '1/3 · Lokalen Thunderbird-Abgleich vorbereiten …')
            dav = dav_sync.DAV(BASE, zone)
            state_root = ROOT
            if any(selections.values()) and not backup:
                dav = thunderbird_calendar.Calendars(dav, self.broker, selections)
            if not backup:
                dav.snapshot()  # Verify availability before prompting for the dock.
                if isinstance(dav, thunderbird_calendar.Calendars):
                    state_root = ROOT / 'sync_states' / dav.state_key()
                journals = [ROOT / 'pending.dpapi', *(ROOT / 'sync_states').glob('*/pending.dpapi')]
                if any(path.exists() and path.parent != state_root for path in journals):
                    raise RuntimeError('Für eine andere Kalenderauswahl ist ein Abgleich unterbrochen. Zuerst die vorherige Auswahl wiederherstellen und diesen Vorgang abschließen.')
            self.emit('stage', '2/3 · Bitte jetzt die Taste am IC35-Dock drücken')
            self.emit('sound', 'press_again')
            ser = serial.Serial(port=port, baudrate=115200, bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_TWO, timeout=.1,
                write_timeout=.75, xonxoff=False, rtscts=False, dsrdtr=False)
            ser.rts = False; ser.dtr = True
            ser.reset_input_buffer(); ser.reset_output_buffer()
            if backup:
                manager.manager_connect(ser, log)
            else:
                proto.PORT, proto.log = port, log
                if not proto.do_welcome_and_reopen(ser):
                    raise RuntimeError('Dock-Verbindung fehlgeschlagen')
            self.emit('sound', 'connected')
            self.emit('stage', '2/3 · ✓ Dock-Tastendruck erkannt · Daten werden gelesen …')
            if backup:
                path = ROOT / 'backups' / f'database_{stamp}.org.dpapi'
                path.parent.mkdir(parents=True, exist_ok=True)
                manager.backup_database(ser, path, log, protected=True)
                manager.manager_disconnect(ser, log)
                message = f'Vollbackup gespeichert:\n{path}'
            else:
                identity = proto.identify(ser)
                if not identity or not proto.power_request(ser):
                    raise RuntimeError('IC35 nicht initialisiert')
                auth = proto.authenticate_once(ser, '')
                if auth is None or auth[:2] != b'\x01\x01':
                    raise RuntimeError('IC35-Anmeldung fehlgeschlagen')
                proto.read_sync_info(ser)
                proto.DATABASES = list(dav_sync.model.DB.values())
                proto.EXPORTFILE = ROOT / 'exports' / f'{stamp}.json.dpapi'
                proto.EXPORTFILE.parent.mkdir(parents=True, exist_ok=True)
                export = proto.read_and_export_databases(ser, identity)
                self.emit('stage', '3/3 · Kontakte, Kalender und Aufgaben abgleichen …')
                result = dav_sync.Sync(state_root, identity, dav, dav_sync.Device(ser), log).run(export)
                private_storage.write_json(ROOT / 'reports' / f'{stamp}.dpapi', result)
                proto.disconnect(ser)
                stats = result['stats']
                message = (f'IC35 angelegt/aktualisiert: {stats["write_device"]}\n'
                           f'Thunderbird angelegt/aktualisiert: {stats["write_remote"]}\n'
                           f'Gelöscht auf IC35/Thunderbird: {stats["delete_device"]}/{stats["delete_remote"]}\n'
                           f'Übersprungen: {len(result["skipped"])} (siehe Protokoll)\n\n'
                           'Jetzt in Thunderbird synchronisieren, um die Änderungen abzurufen.')
            log('Vorgang erfolgreich abgeschlossen.')
            self.emit('done', message)
        except Exception as exc:
            try:
                log(f'Abbruch: {exc}')
            except Exception:
                self.emit('log', f'Abbruch: {exc} (Protokollspeicherung fehlgeschlagen)')
            self.emit('error', str(exc))
        finally:
            if ser is not None:
                ser.close()
            if lock is not None:
                lock.close()

    def stop_server(self):
        if self.server is not None and self.server.poll() is None:
            if getattr(sys, 'frozen', False):
                subprocess.run(['taskkill', '/PID', str(self.server.pid), '/T', '/F'],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                               creationflags=subprocess.CREATE_NO_WINDOW)
            else:
                self.server.terminate()
            try:
                self.server.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.server.kill()
        if self.server_log:
            self.server_log.close()
            self.server_log = None
        self.server = None

    def close(self):
        if self.busy:
            messagebox.showinfo('Abgleich läuft', 'Bitte den laufenden Gerätezugriff abwarten.')
            return
        self.stop_server()
        if self.broker:
            self.broker.close()
        self.destroy()


if __name__ == '__main__':
    App().mainloop()
