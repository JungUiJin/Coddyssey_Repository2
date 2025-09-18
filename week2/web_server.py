#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import datetime
import http.server
import json
import os
import socketserver
import threading
import urllib.error
import urllib.request
from typing import Dict, Tuple

HOST = '0.0.0.0'
PORT = 8080
WEB_ROOT = os.path.dirname(os.path.abspath(__file__))

REQUEST_LOCK = threading.Lock()
REQUEST_TOTAL = 0
REQUESTS_PER_IP: Dict[str, int] = {}
LAST_ACCESS_AT: Dict[str, str] = {}

def get_client_ip(handler: http.server.BaseHTTPRequestHandler) -> str:
    fwd = handler.headers.get('X-Forwarded-For')
    if fwd:
        return fwd.split(',')[0].strip()
    return handler.client_address[0]

def geo_lookup(ip: str, timeout: float = 1.5) -> str:
    if ip.startswith('127.') or ip.startswith('10.') or ip.startswith('192.168.') or ip.startswith('172.16.'):
        return ''
    url = f'http://ip-api.com/json/{ip}?fields=status,country,regionName,city,query'
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            if data.get('status') == 'success':
                country = data.get('country') or ''
                region = data.get('regionName') or ''
                city = data.get('city') or ''
                return ', '.join([p for p in (city, region, country) if p])
    except (urllib.error.URLError, TimeoutError, ValueError):
        return ''
    return ''

class SimpleHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args) -> None:
        return

    def _log_access(self) -> Tuple[str, str]:
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ip = get_client_ip(self)
        with REQUEST_LOCK:
            global REQUEST_TOTAL
            REQUEST_TOTAL += 1
            REQUESTS_PER_IP[ip] = REQUESTS_PER_IP.get(ip, 0) + 1
            LAST_ACCESS_AT[ip] = now
        print(f'[접속] {now} | IP: {ip} | {self.command} {self.path}')
        threading.Thread(target=self._maybe_print_geo, args=(ip,), daemon=True).start()
        return now, ip

    def _maybe_print_geo(self, ip: str) -> None:
        where = geo_lookup(ip)
        if where:
            print(f'  └ 위치 추정: {ip} ≈ {where}')

    def do_GET(self) -> None:
        self._log_access()
        if self.path == '/stats':
            self._serve_stats()
            return
        if self.path in ('/', '/index.html'):
            self._serve_index()
            return
        try:
            super().do_GET()
        except BrokenPipeError:
            pass

    def _serve_index(self) -> None:
        index_path = os.path.join(WEB_ROOT, 'index.html')
        if not os.path.exists(index_path):
            self.send_response(404)
            self.send_header('Content-Type', 'text/plain; charset=utf-8')
            self.end_headers()
            self.wfile.write(b'index.html not found')
            return
        with open(index_path, 'rb') as f:
            body = f.read()
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        try:
            self.wfile.write(body)
        except BrokenPipeError:
            pass

    def _serve_stats(self) -> None:
        with REQUEST_LOCK:
            total = REQUEST_TOTAL
            per_ip = dict(REQUESTS_PER_IP)
            last_at = dict(LAST_ACCESS_AT)
        rows = []
        for ip, cnt in sorted(per_ip.items(), key=lambda kv: (-kv[1], kv[0])):
            rows.append(f'<tr><td>{ip}</td><td>{cnt}</td><td>{last_at.get(ip, "")}</td></tr>')
        table_html = '\n'.join(rows) if rows else '<tr><td colspan="3">No data</td></tr>'
        html_tpl = """<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>요청 통계</title>
  <style>
    body {{ font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; margin: 2rem; }}
    h1 {{ margin-bottom: 0.25rem; }}
    .meta {{ color: #555; margin-bottom: 1rem; }}
    table {{ border-collapse: collapse; width: 100%; max-width: 800px; }}
    th, td {{ border: 1px solid #ccc; padding: 8px 10px; text-align: left; }}
    th {{ background: #f6f6f6; }}
    code {{ background: #f3f3f3; padding: 2px 4px; border-radius: 4px; }}
  </style>
</head>
<body>
  <h1>요청 통계</h1>
  <div class="meta">총 요청 수: <strong>{total}</strong></div>
  <table>
    <thead><tr><th>IP</th><th>요청 수</th><th>마지막 접속 시간</th></tr></thead>
    <tbody>
      {rows}
    </tbody>
  </table>
  <p><a href="/">← 홈으로</a></p>
</body>
</html>"""
        html = html_tpl.format(total=total, rows=table_html)
        body = html.encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        try:
            self.wfile.write(body)
        except BrokenPipeError:
            pass

def run_server() -> None:
    os.chdir(WEB_ROOT)
    handler = SimpleHandler
    with socketserver.ThreadingTCPServer((HOST, PORT), handler) as httpd:
        print(f'HTTP 서버 시작: http://127.0.0.1:{PORT}  (Ctrl+C로 종료)')
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print('\n서버 종료 중...')
        finally:
            httpd.shutdown()

if __name__ == '__main__':
    run_server()
