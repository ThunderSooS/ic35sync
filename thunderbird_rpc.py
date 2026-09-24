"""Authenticated loopback command broker. Thunderbird polls; websites cannot submit commands."""
import hmac
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import queue
import secrets
import threading
import time
import uuid
import private_storage

PORT = 5234
PROTOCOL = 1


class Broker:
    def __init__(self, root, port=PORT, pairing=None):
        self.path = Path(root) / 'addon_pairing.dpapi'
        self.pairing = pairing or (private_storage.read_json(self.path) if self.path.exists() else {'token': secrets.token_urlsafe(32), 'profile': None})
        if pairing is None and not self.path.exists():
            private_storage.write_json(self.path, self.pairing)
        self.jobs = queue.Queue()
        self.pending = {}
        self.lock = threading.RLock()
        self.call_lock = threading.Lock()
        self.last_seen = 0
        self.session = None
        self.version = ''
        self.test_pairing = pairing is not None
        broker = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass  # Never log headers, pairing codes or organizer payloads.

            def send(self, status, data):
                raw = json.dumps(data, ensure_ascii=False).encode('utf-8')
                self.send_response(status)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.send_header('Cache-Control', 'no-store')
                self.send_header('Content-Length', str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)

            def do_POST(self):
                try:
                    self.connection.settimeout(20)
                    length = int(self.headers.get('Content-Length', '0'))
                    if length <= 0 or length > 32 * 1024 * 1024:
                        return self.send(400, {'error': 'body'})
                    # Drain the bounded body before returning errors (Windows otherwise resets the socket).
                    raw = self.rfile.read(length)
                    origin = self.headers.get('Origin', '')
                    if origin and not origin.startswith('moz-extension://'):
                        return self.send(403, {'error': 'origin'})
                    if self.headers.get('Host') != f'127.0.0.1:{self.server.server_port}':
                        return self.send(403, {'error': 'host'})
                    supplied = self.headers.get('Authorization', '')
                    if not hmac.compare_digest(supplied, 'Bearer ' + broker.pairing['token']):
                        return self.send(403, {'error': 'pairing'})
                    if self.headers.get_content_type() != 'application/json':
                        return self.send(400, {'error': 'body'})
                    body = json.loads(raw)
                    if body.get('protocol') != PROTOCOL:
                        return self.send(409, {'error': 'protocol'})
                    profile, session = body.get('profile'), body.get('session')
                    if not isinstance(profile, str) or not isinstance(session, str) or not 8 <= len(profile) <= 100 or not 8 <= len(session) <= 100:
                        return self.send(400, {'error': 'identity'})
                    with broker.lock:
                        if broker.pairing['profile'] not in (None, profile):
                            # A valid secret proves this is a deliberate
                            # re-pair after an add-on/profile reset. Permit it
                            # only when no other session is active.
                            if broker.session is not None and time.monotonic() - broker.last_seen < 30:
                                return self.send(403, {'error': 'profile'})
                            broker.pairing['profile'] = profile
                            if not broker.test_pairing:
                                private_storage.write_json(broker.path, broker.pairing)
                        if broker.session not in (None, session) and time.monotonic() - broker.last_seen < 30:
                            return self.send(409, {'error': 'another_instance'})
                        if broker.pairing['profile'] is None:
                            broker.pairing['profile'] = profile
                            if not broker.test_pairing:
                                private_storage.write_json(broker.path, broker.pairing)
                        broker.session = session
                        broker.last_seen = time.monotonic()
                        broker.version = str(body.get('version', ''))[:40]
                    if self.path == '/poll':
                        until = time.monotonic() + 10
                        while time.monotonic() < until:
                            try:
                                job = broker.jobs.get(timeout=.25)
                            except queue.Empty:
                                continue
                            with broker.lock:
                                if job['id'] in broker.pending:
                                    return self.send(200, job)
                        return self.send(200, {'idle': True})
                    if self.path == '/result':
                        with broker.lock:
                            target = broker.pending.get(body.get('id'))
                            if target:
                                target['reply'] = body
                                target['event'].set()
                        return self.send(200, {'accepted': True})
                    return self.send(404, {'error': 'route'})
                except (BrokenPipeError, ConnectionResetError, TimeoutError):
                    pass
                except Exception:
                    try:
                        self.send(400, {'error': 'invalid_request'})
                    except OSError:
                        pass

        self.server = ThreadingHTTPServer(('127.0.0.1', port), Handler)
        self.server.daemon_threads = True
        self.port = self.server.server_port
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def call(self, method, params=None, timeout=100):
        if method not in ('list', 'snapshot', 'get', 'write', 'delete'):
            raise ValueError('Unknown calendar command')
        with self.call_lock:
            if time.monotonic() - self.last_seen > 25:
                raise RuntimeError('Thunderbird-Add-on nicht verbunden. Thunderbird öffnen und Kopplung prüfen.')
            identifier = uuid.uuid4().hex
            target = {'event': threading.Event()}
            with self.lock:
                self.pending[identifier] = target
            self.jobs.put({'id': identifier, 'method': method, 'params': params or {}})
            try:
                if not target['event'].wait(timeout):
                    raise RuntimeError('Thunderbird antwortet nicht rechtzeitig. Vorgang gestoppt; beim nächsten Lauf wird der Stand geprüft.')
                reply = target['reply']
                if not reply.get('ok'):
                    raise RuntimeError('Thunderbird: ' + str(reply.get('error', 'Kalenderzugriff fehlgeschlagen')))
                return reply['data']
            finally:
                with self.lock:
                    self.pending.pop(identifier, None)

    def close(self):
        self.server.shutdown()
        self.server.server_close()
