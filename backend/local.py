"""Loopback-only HTTP adapter. The application handler is identical to Lambda's."""
import json
import os
import secrets
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from http.cookies import SimpleCookie
from types import SimpleNamespace
from urllib.parse import urlsplit

os.environ['LOCAL_DEV'] = '1'
os.environ.setdefault('LINK_SECRET', secrets.token_hex(32))
from .app import handler

SESSIONS = set()
ORIGINS = {'http://127.0.0.1:5173', 'http://localhost:5173', 'http://127.0.0.1:7171'}

class LocalHandler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def handle_request(self):
        if self.headers.get('Host') not in {'127.0.0.1:7171', 'localhost:7171', '127.0.0.1:5173', 'localhost:5173'}:
            self.send_error(403); return
        if self.command == 'POST' and self.headers.get('Origin') not in ORIGINS:
            self.send_error(403); return
        try:
            size = int(self.headers.get('Content-Length', 0))
            if not 0 <= size <= 16384:
                self.send_error(413); return
            raw = self.rfile.read(size).decode('utf-8') if size else None
        except (ValueError, UnicodeDecodeError):
            self.send_error(400); return
        cookie = SimpleCookie(self.headers.get('Cookie', ''))
        session = cookie.get('ks_session')
        identifier = session.value if session and session.value in SESSIONS else secrets.token_hex(24)
        SESSIONS.add(identifier)
        path = urlsplit(self.path).path
        event = {'version': '2.0', 'routeKey': f'{self.command} /local', 'rawPath': path, 'rawQueryString': '',
                 'headers': {k.lower(): v for k, v in self.headers.items()}, 'body': raw, 'isBase64Encoded': False,
                 'requestContext': {'stage': '$default', 'requestId': str(uuid.uuid4()), 'http': {'method': self.command, 'path': path},
                 'authorizer': {'jwt': {'claims': {'sub': identifier, 'token_use': 'access'}}}}}
        result = handler(event, SimpleNamespace(aws_request_id=event['requestContext']['requestId']))
        self.send_response(result['statusCode'])
        for k, v in result.get('headers', {}).items(): self.send_header(k, v)
        self.send_header('Set-Cookie', f'ks_session={identifier}; HttpOnly; SameSite=Strict; Path=/')
        self.end_headers()
        self.wfile.write(result.get('body', '').encode())

    do_GET = handle_request
    do_POST = handle_request

if __name__ == '__main__':
    print('KabadiSetu local API at http://127.0.0.1:7171. Local sessions are not Cognito.')
    ThreadingHTTPServer(('127.0.0.1', 7171), LocalHandler).serve_forever()
