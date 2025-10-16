import smtplib
import mimetypes
from email.message import EmailMessage
from pathlib import Path

# Gmail SMTP 서버 및 포트 번호
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587  # STARTTLS 사용 포트

SENDER_EMAIL = 'yealkki38@gmail.com'  # 보내는 사람 (본인 Gmail 주소)
SENDER_PASSWORD = ''          # Gmail 앱 비밀번호
RECEIVER_EMAIL = 'poochin74@naver.com' # 받는 사람 주소


EMAIL_SUBJECT = '웹 크롤링 방식을 이용한 정기 메일 확인 테스트'
EMAIL_BODY = """
안녕하세요. 이 메일은 Python 스크립트를 사용하여 Gmail SMTP 서버를 통해
자동으로 전송된 테스트 메일입니다.

지속적인 연결이 어려운 환경에서, 정기적인 메일 확인이 가능한지 테스트합니다.
하루에 한 번 또는 두 번 크롤링하여 회신 여부를 확인할 수 있을지 기대됩니다.

회신이 오는지 확인해 주시면 감사하겠습니다!
"""
# 첨부 파일 경로
ATTACHMENT_FILE = 'C:\Coddyssey_Repository2\week5\summer.jpg'


def send_email_with_attachment():
    """
    Gmail SMTP 서버에 로그인하여 메일 본문과 첨부 파일을 전송합니다.
    
    SMTP 통신 및 파일 처리 과정에서 발생할 수 있는 예외를 처리합니다.
    """
    try:
        # EmailMessage 객체 생성
        msg = EmailMessage()
        msg['Subject'] = EMAIL_SUBJECT
        msg['From'] = SENDER_EMAIL
        msg['To'] = RECEIVER_EMAIL
        msg.set_content(EMAIL_BODY)

        # 첨부 파일 처리 (보너스 과제)
        attachment_path = Path(ATTACHMENT_FILE)
        if attachment_path.exists() and attachment_path.is_file():
            # 파일의 MIME 타입 추측
            ctype, encoding = mimetypes.guess_type(attachment_path)
            if ctype is None or encoding is not None:
                # 추측 실패 시 기본값 사용
                ctype = 'application/octet-stream'

            maintype, subtype = ctype.split('/', 1)

            with open(attachment_path, 'rb') as fp:
                msg.add_attachment(
                    fp.read(),
                    maintype = maintype,
                    subtype = subtype,
                    filename = attachment_path.name
                )
            print(f'정보: 파일이 성공적으로 첨부되었습니다: {attachment_path.name}')
        else:
            print(f'경고: 첨부 파일 ({ATTACHMENT_FILE})을 찾을 수 없습니다. 첨부 없이 본문만 전송합니다.')

        # SMTP 서버 연결 및 로그인
        print(f'정보: {SMTP_SERVER}:{SMTP_PORT} 서버에 연결을 시작합니다...')
        
        # smtplib.SMTP 객체 생성 및 TLS 암호화 시작 (587 포트 사용)
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            print('정보: TLS 암호화 연결 설정 완료.')
            
            # 로그인
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            print('정보: Gmail 계정에 성공적으로 로그인했습니다.')

            # 메일 전송
            server.send_message(msg)
            print('성공: 메일 전송이 완료되었습니다!')

    except smtplib.SMTPAuthenticationError:
        print('오류: SMTP 인증에 실패했습니다.')
        print('  -> 앱 비밀번호(App Password)가 올바른지 확인해 주세요.')
        print('  -> 또는 SENDER_EMAIL과 SENDER_PASSWORD가 정확한지 확인해 주세요.')
    except smtplib.SMTPConnectError:
        print('오류: SMTP 서버 연결에 실패했습니다.')
        print('  -> 네트워크 연결 상태 또는 서버 주소를 확인해 주세요.')
    except TimeoutError:
        print('오류: 연결 시간이 초과되었습니다.')
        print('  -> 방화벽 설정 등을 확인해 주세요.')
    except Exception as e:
        print(f'치명적 오류: 메일 전송 중 예상치 못한 오류가 발생했습니다. ({e})')


if __name__ == '__main__':
    send_email_with_attachment()
