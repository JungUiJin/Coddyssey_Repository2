import sys
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

NAVER_ID = "poochin74"
NAVER_PW = ""

LOGIN_URL = "https://nid.naver.com/nidlogin.login?mode=form&url=https://www.naver.com/"
MAIL_URL = "https://mail.naver.com/"

def build_driver(headless: bool = False) -> webdriver.Chrome:
    opts = Options()
    if headless:
        opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--lang=ko-KR")
    opts.add_argument("--window-size=1200,900")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts)

def wait_css(drv, css, timeout):
    return WebDriverWait(drv, timeout).until(EC.presence_of_element_located((By.CSS_SELECTOR, css)))

# 캡차 수동 해결 유도
def maybe_wait_for_captcha(driver, timeout=180):
    suspicious_keywords = ["자동입력 방지", "로봇", "captcha", "봇이 아님", "자동 로그인 방지"]
    page_source = driver.page_source
    if any(word in page_source for word in suspicious_keywords):
        print("\n⚠️  캡차가 감지되었습니다. 브라우저에서 직접 인증을 진행해주세요.")
        print(f"⏳ {timeout}초 동안 대기합니다...")
        # timeout 초 동안 사용자가 직접 캡차를 풀 때까지 대기
        WebDriverWait(driver, timeout).until_not(
            lambda d: any(word in d.page_source for word in suspicious_keywords)
        )
        print("✅ 캡차가 해제된 것으로 보입니다. 자동화 재개합니다.")

def main():
    driver = build_driver(headless=False)  # 서버/CI에서 쓸 땐 True 권장
    try:
        opts = Options()
        opts.add_experimental_option('excludeSwitches', ['enable-logging'])  # 윈도우에서 콘솔 경고 숨김
        driver.get(LOGIN_URL)

        # 로그인 입력 필드 대기
        id_box = wait_css(driver, "input#id", timeout=12)
        pw_box = wait_css(driver, "input#pw", timeou3t=12)

        id_box.clear()
        id_box.send_keys(NAVER_ID)
        pw_box.clear()
        pw_box.send_keys(NAVER_PW)
        pw_box.send_keys(Keys.RETURN)

        # 캡차가 걸렸는지 체크 → 있으면 사용자에게 안내 후 대기
        maybe_wait_for_captcha(driver, timeout=180)

        # 로그인 성공 대기
        WebDriverWait(driver, 15).until(
            lambda d: "naver.com" in d.current_url.lower() and "nidlogin" not in d.current_url.lower()
        )
        print("[성공] 현재 URL:", driver.current_url)

        # 로그인 성공 확인 후 요소 추출
        driver.get("https://www.naver.com/")

        nickname = wait_css(driver, "span.MyView-module__nickname___fcxwI", timeout=10).text
        email = wait_css(driver, "div.MyView-module__desc_email___JwAKa", timeout=10).text

        print(f"닉네임: {nickname}")
        print(f"이메일: {email}")
        
        # 📧 메일 페이지로 이동
        driver.get(MAIL_URL)
        
        # 메일 목록이 로딩될 때까지 대기
        WebDriverWait(driver, 15).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a.mail_title_link span.text"))
        )

        # 메일 제목 수집
        mail_titles = driver.find_elements(By.CSS_SELECTOR, "a.mail_title_link span.text")

        print("\n📨 받은 메일 제목 목록:")
        for i, t in enumerate(mail_titles, start=1):
            print(f"{i}. {t.text}")

    finally:
        driver.quit()

if __name__ == "__main__":
    main()
