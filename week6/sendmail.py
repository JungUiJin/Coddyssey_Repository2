import smtplib
import csv
from email.message import EmailMessage
from pathlib import Path
import mimetypes # mimetypes를 전역으로 import 하여 함수 내에서 import를 제거함

# [1] SMTP 및 인증 정보 (네이버 설정)
SMTP_SERVER = 'smtp.naver.com' # 네이버 SMTP 서버
SMTP_PORT = 587                # STARTTLS 사용 포트 (네이버도 587)

SENDER_EMAIL = 'poochin74@naver.com'   # 보내는 사람 (본인 네이버 주소)
SENDER_PASSWORD = '' # 네이버 '앱 비밀번호'

# [2] 메일 내용 설정
EMAIL_SUBJECT = 'Dr. Han의 희망 메시지 - HTML 형식 테스트'

# HTML 형식의 메일 본문 (내용 생략 - 원본과 동일)
HTML_BODY = """
<html>
<head>
    <style>
        .container {
            font-family: Arial, sans-serif;
            border: 1px solid #ddd;
            padding: 20px;
            max-width: 600px;
            margin: 0 auto;
        }
        .header {
            background-color: #f2f2f2;
            padding: 10px;
            text-align: center;
        }
        .message {
            margin-top: 20px;
            line-height: 1.6;
        }
        .footer {
            margin-top: 30px;
            font-size: 0.8em;
            color: #777;
            text-align: right;
        }
    </style>
</head>
<body>
    <div class='container'>
        <div class='header'>
            <h2>화성에서 온 희망 메일</h2>
        </div>
        <div class='message'>
            <p>
                Dr. Han!!, we received your message, but we couldn't understand the situation, so we all froze, and we don't even know how much we cried after hugging each other. We are so grateful that you are alive, and we will do our best too. Just in case your condition is not good, we are sending this message in English.
            </p>
            <p>
                **한송희 박사님의 생존 소식에 모두가 감동했습니다.** 박사님을 구출하기 위한 가장 효과적인 메시지 전달 방안을 마련하는 것이 급선무입니다. 이 메일은 그 테스트의 일환입니다.
            </p>
        </div>
        <div class='footer'>
            <p>From: Dr. Han's Support Team</p>
        </div>
    </div>
</body>
</html>
"""

# 첨부 파일 경로 (이전 코드에서 사용된 경로 유지)
ATTACHMENT_FILE = 'C:\\Coddyssey_Repository2\\week5\\summer.jpg' # 실제 파일 경로로 수정 필요

# [3] CSV 파일 처리 및 메일 전송 함수
def get_recipient_list(csv_file_name='C:\\Coddyssey_Repository2\\week6\\mail_target_list.csv'):
    """
    CSV 파일에서 수신자 이름과 이메일 주소를 읽어 리스트로 반환합니다.
    (기존 코드와 동일)
    """
    recipients = []
    try:
        # 파일 인코딩(UTF-8)과 newline=''을 사용하여 CSV 파일을 안전하게 읽음
        with open(csv_file_name, 'r', newline = '', encoding = 'utf-8') as file:
            reader = csv.reader(file)
            header = next(reader) # 헤더 행 건너뛰기
            print(f'정보: CSV 파일 헤더: {header}')
            for row in reader:
                if len(row) >= 2:
                    name, email = row[0].strip(), row[1].strip()
                    if '@' in email: # 간단한 이메일 형식 확인
                        recipients.append((name, email))
        
        print(f'정보: 총 {len(recipients)}명의 수신자 정보를 읽었습니다.')
        return recipients

    except FileNotFoundError:
        print(f'오류: CSV 파일 ({csv_file_name})을 찾을 수 없습니다. 메일을 전송할 수 없습니다.')
        return []
    except Exception as e:
        print(f'치명적 오류: CSV 파일 처리 중 예상치 못한 오류 발생. ({e})')
        return []


def add_attachment_to_msg(msg, file_path):
    """첨부 파일을 EmailMessage 객체에 추가하는 내부 로직 (재사용을 위해 분리)"""
    attachment_path = Path(file_path)
    if attachment_path.exists() and attachment_path.is_file():
        ctype, encoding = mimetypes.guess_type(attachment_path)
        if ctype is None or encoding is not None:
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
        return True
    else:
        print(f'경고: 첨부 파일 ({ATTACHMENT_FILE})을 찾을 수 없습니다. 첨부 없이 본문만 전송합니다.')
        return False


def send_html_email_to_multiple_recipients(recipients):
    """
    한번의 연결로 일괄 전송
    """
    if not recipients:
        print('경고: 유효한 수신자가 없으므로 일괄 메일 전송을 건너뜁니다.')
        return

    receiver_emails = [email for name, email in recipients]
    
    print('\n--- [일괄 전송 시작] ---')

    try:
        msg = EmailMessage()
        msg['Subject'] = EMAIL_SUBJECT
        msg['From'] = SENDER_EMAIL
        msg['To'] = ', '.join(receiver_emails) # 일괄 전송을 위해 모든 수신자 목록을 'To'에 넣음
        msg.add_alternative(HTML_BODY, subtype = 'html')
        
        add_attachment_to_msg(msg, ATTACHMENT_FILE)

        print(f'정보: {SMTP_SERVER}:{SMTP_PORT} 서버에 연결을 시작합니다...')
        
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            print('정보: TLS 암호화 연결 설정 완료.')
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            print('정보: 네이버 계정에 성공적으로 로그인했습니다.')

            server.send_message(msg)
            
            print(f'성공: 총 {len(receiver_emails)}명의 수신자에게 일괄 메일 전송이 완료되었습니다!')

    except smtplib.SMTPAuthenticationError:
        print('오류: SMTP 인증에 실패했습니다. (방법 1)')
        print('  -> 네이버 **앱 비밀번호** 또는 로그인 설정(POP3/SMTP)을 확인해 주세요.')
    except Exception as e:
        print(f'치명적 오류: 일괄 메일 전송 중 예상치 못한 오류가 발생했습니다. ({e})')
    print('--------------------------------\n')


def send_html_email_one_by_one(recipients):
    """
    반복문으로 개별 전송
    """
    if not recipients:
        print('경고: 유효한 수신자가 없으므로 개별 메일 전송을 건너뜁니다.')
        return

    print('\n--- [개별 반복 전송 시작] ---')

    try:
        print(f'정보: {SMTP_SERVER}:{SMTP_PORT} 서버에 연결을 시작합니다...')
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            print('정보: TLS 암호화 연결 설정 완료.')
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            print('정보: 네이버 계정에 성공적으로 로그인했습니다.')

            success_count = 0
            
            for name, email in recipients:
                print(f'정보: 수신자 {name} ({email})에게 개별 메일 전송 시도...')

                # 매번 새로운 EmailMessage 객체 생성 및 수신자 설정
                msg = EmailMessage()
                msg['Subject'] = EMAIL_SUBJECT
                msg['From'] = SENDER_EMAIL
                # **핵심 수정: 수신자를 1명만 설정**
                msg['To'] = email 
                msg.add_alternative(HTML_BODY, subtype = 'html')

                # 첨부 파일 추가
                add_attachment_to_msg(msg, ATTACHMENT_FILE)

                # 메일 전송
                server.send_message(msg)
                success_count += 1
                print(f'성공: {name}에게 개별 메일 전송 완료.')
                
            print(f'성공: 총 {success_count}명에게 개별 메일 전송을 완료했습니다!')

    except smtplib.SMTPAuthenticationError:
        print('오류: SMTP 인증에 실패했습니다. (방법 2)')
        print('  -> 네이버 **앱 비밀번호** 또는 로그인 설정(POP3/SMTP)을 확인해 주세요.')
    except Exception as e:
        print(f'치명적 오류: 개별 메일 전송 중 예상치 못한 오류가 발생했습니다. ({e})')
    print('-------------------------------------\n')


# ====================================================================
# [4] 메인 실행
# ====================================================================

if __name__ == '__main__':
    # 1. CSV 파일에서 수신자 목록 읽기
    recipients = get_recipient_list()
    
    # 2. 메일 전송 시도 (두 가지 방법 중 선택하여 테스트 가능)

    # **일괄 전송 시도**
    send_html_email_to_multiple_recipients(recipients)
    
    # **개별 반복 시도**
    # send_html_email_one_by_one(recipients)