#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
멀티스레드 TCP 채팅 클라이언트
요구사항 지원:
- '/종료' 입력 시 연결 종료
- 귓속말: '/w 닉네임 메시지' 또는 '/귓속말 닉네임 메시지'
- 외부 라이브러리 사용 금지
"""
from __future__ import annotations

import socket
import threading
import sys


ENCODING = 'utf-8'
BUFFER_SIZE = 4096


def receiver_loop(sock: socket.socket) -> None:
    try:
        while True:
            data = sock.recv(BUFFER_SIZE)
            if not data:
                print('서버와의 연결이 종료되었습니다.')
                break
            text = data.decode(ENCODING)
            # 수신 데이터는 그대로 출력
            sys.stdout.write(text)
            sys.stdout.flush()
    except (ConnectionResetError, OSError):
        pass
    finally:
        try:
            sock.close()
        except Exception:
            pass


def main() -> None:
    host = '127.0.0.1'
    port = 50007

    print('닉네임을 입력하세요: ', end='')
    nickname = input().strip()
    if not nickname:
        print('닉네임이 필요합니다. 프로그램을 종료합니다.')
        return

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))

    # 최초에 닉네임 전송
    sock.sendall((nickname + '\n').encode(ENCODING))

    print("안내: '/종료' 로 종료, '/w 닉네임 메시지' 로 귓속말.")
    print('메시지를 입력하세요.')

    t = threading.Thread(target=receiver_loop, args=(sock,), daemon=True)
    t.start()

    try:
        while True:
            try:
                line = input()
            except EOFError:
                line = '/종료'
            if not line:
                continue

            sock.sendall((line + '\n').encode(ENCODING))
            if line.strip() == '/종료':
                break
    finally:
        try:
            sock.close()
        except Exception:
            pass


if __name__ == '__main__':
    main()
