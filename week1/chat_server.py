#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
멀티스레드 TCP 채팅 서버
요구사항:
- 다중 클라이언트 동시 접속 지원
- 접속 시 전체 공지: "~님이 입장하셨습니다."
- '/종료' 입력 시 연결 종료
- 모든 메시지는 '사용자> 메시지' 형태로 브로드캐스트
- 보너스: 귓속말 기능('/w 닉네임 메시지' 또는 '/귓속말 닉네임 메시지')
- 외부 라이브러리 사용 금지 (표준 라이브러리의 socket, threading만 사용)
- PEP8 스타일 및 과제의 문자열/공백 규칙 준수
"""
from __future__ import annotations

import socket
import threading
from typing import Dict, Tuple


ENCODING = 'utf-8'
BUFFER_SIZE = 4096


class ChatServer:
    def __init__(self, host: str = '127.0.0.1', port: int = 50007) -> None:
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.clients_lock = threading.Lock()
        # sockets -> nickname
        self.clients: Dict[socket.socket, str] = {}

    def start(self) -> None:
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()
        print(f'서버 시작: {self.host}:{self.port} (Ctrl+C로 종료)')

        try:
            while True:
                client_socket, addr = self.server_socket.accept()
                threading.Thread(
                    target=self._handle_client,
                    args=(client_socket, addr),
                    daemon=True
                ).start()
        except KeyboardInterrupt:
            print('\n서버 종료 중...')
        finally:
            self._shutdown()

    def _handle_client(self, client_socket: socket.socket, addr: Tuple[str, int]) -> None:
        nickname = ''
        try:
            # 최초 수신: 닉네임
            nickname = self._recv_text(client_socket).strip()
            if not nickname:
                client_socket.close()
                return

            with self.clients_lock:
                self.clients[client_socket] = nickname

            self._broadcast_system(f'{nickname}님이 입장하셨습니다.')

            # 메시지 루프
            while True:
                data = self._recv_text(client_socket)
                if not data:
                    break
                msg = data.strip()

                # 종료 명령
                if msg == '/종료':
                    self._send_text(client_socket, '서버> 연결을 종료합니다. 안녕히 가세요.')
                    break

                # 귓속말: '/w 닉 메시지' 또는 '/귓속말 닉 메시지'
                if msg.startswith('/w ') or msg.startswith('/귓속말 '):
                    self._handle_whisper(nickname, msg, client_socket)
                    continue

                # 일반 브로드캐스트
                self._broadcast_chat(nickname, msg)

        except (ConnectionResetError, ConnectionAbortedError):
            pass
        finally:
            # 정리
            with self.clients_lock:
                existed = client_socket in self.clients
                if existed:
                    nickname = self.clients.pop(client_socket)
            try:
                client_socket.close()
            except Exception:
                pass
            if nickname:
                self._broadcast_system(f'{nickname}님이 퇴장하셨습니다.')

    def _handle_whisper(self, sender: str, raw: str, client_socket: socket.socket) -> None:
        # 구문 파싱: /w 닉 메시지  또는  /귓속말 닉 메시지
        parts = raw.split(' ', 2)
        if len(parts) < 3:
            self._send_text(client_socket, '서버> 사용법: /w 닉네임 메시지')
            return
        _, target_name, body = parts
        target_sock = self._find_socket_by_name(target_name)
        if not target_sock:
            self._send_text(client_socket, f'서버> 대상 닉네임을 찾을 수 없습니다: {target_name}')
            return

        # 보낸 사람, 받는 사람 모두에게 알림
        self._send_text(target_sock, f'(귓속말) {sender}> {body}')
        if target_sock is not client_socket:
            self._send_text(client_socket, f'(귓속말 보냄) {sender} -> {target_name}> {body}')

    def _find_socket_by_name(self, name: str) -> socket.socket | None:
        with self.clients_lock:
            for sock, nick in self.clients.items():
                if nick == name:
                    return sock
        return None

    def _broadcast_chat(self, nickname: str, message: str) -> None:
        text = f'{nickname}> {message}'
        self._broadcast(text)

    def _broadcast_system(self, message: str) -> None:
        text = f'서버> {message}'
        self._broadcast(text)

    def _broadcast(self, text: str) -> None:
        with self.clients_lock:
            dead = []
            for sock in self.clients:
                try:
                    self._send_text(sock, text)
                except Exception:
                    dead.append(sock)
            for sock in dead:
                # 클라이언트 소켓 정리
                nick = self.clients.pop(sock, None)
                try:
                    sock.close()
                except Exception:
                    pass
                if nick:
                    # 정리 중 퇴장 공지 (이미 호출될 수 있으므로 생략 가능)
                    pass

    def _send_text(self, sock: socket.socket, text: str) -> None:
        sock.sendall((text + '\n').encode(ENCODING))

    def _recv_text(self, sock: socket.socket) -> str:
        data = sock.recv(BUFFER_SIZE)
        if not data:
            return ''
        return data.decode(ENCODING)

    def _shutdown(self) -> None:
        with self.clients_lock:
            for sock in list(self.clients.keys()):
                try:
                    self._send_text(sock, '서버> 서버가 종료됩니다. 연결을 닫습니다.')
                except Exception:
                    pass
                try:
                    sock.close()
                except Exception:
                    pass
            self.clients.clear()
        try:
            self.server_socket.close()
        except Exception:
            pass


def main() -> None:
    server = ChatServer(host='127.0.0.1', port=50007)
    server.start()


if __name__ == '__main__':
    main()
