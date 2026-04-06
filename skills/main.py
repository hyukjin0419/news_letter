import os
import smtplib
import gspread
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials

from fetcher01 import fetch_top_tech_news
from analyzer import deep_analyze_tech
from writer import write_newsletter

load_dotenv()

GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
SHEETS_ID = "1OX65Jlt51Ub7pZdN9RlAJd9Bz7ilxs86KfZk_e3fUUk"
CREDENTIALS_FILE = "../credentials.json"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]


def get_subscribers() -> list[str]:
    """Google Sheets에서 구독자 이메일 목록 가져오기"""
    try:
        creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
        gc = gspread.authorize(creds)
        sheet = gc.open_by_key(SHEETS_ID).sheet1
        records = sheet.get_all_records()
        emails = [r["email"] for r in records if r.get("email")]
        print(f"  ✅ 구독자 {len(emails)}명 확인")
        return emails
    except Exception as e:
        print(f"  ❌ Sheets 로드 실패: {e}")
        return []


def send_email(to_email: str, subject: str, html: str) -> bool:
    """Gmail SMTP로 이메일 발송"""
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"FIRSTWAVE <{GMAIL_USER}>"
        msg["To"] = to_email
        msg.attach(MIMEText(html, "html", "utf-8"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_USER, to_email, msg.as_string())
        return True
    except Exception as e:
        print(f"  ❌ 발송 실패 ({to_email}): {e}")
        return False


def save_archive(html: str, date: str) -> None:
    """발송한 HTML을 archive/ 폴더에 날짜별로 저장"""
    archive_dir = "../archive"
    os.makedirs(archive_dir, exist_ok=True)
    path = os.path.join(archive_dir, f"{date}.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  ✅ 아카이브 저장 완료 → archive/{date}.html")


def main():
    today = datetime.now().strftime("%Y-%m-%d")
    print(f"\n🌊 FIRSTWAVE 뉴스레터 파이프라인 시작 ({today})\n")

    # 0단계: 구독자 먼저 확인 — 없으면 API 호출 없이 종료
    print("📋 [0/4] 구독자 확인 중...")
    subscribers = get_subscribers()
    if not subscribers:
        print("⚠️  구독자가 없어 파이프라인을 중단합니다. (토큰 절약)")
        return

    # 1단계: 기사 수집
    print("\n🔎 [1/4] 기사 수집 중...")
    stories = fetch_top_tech_news(limit=3)
    if not stories:
        print("❌ 수집된 기사가 없습니다.")
        return

    # 2단계: Gemini 분석
    print("\n🤖 [2/4] Gemini 분석 중...")
    analyzed = deep_analyze_tech(stories)

    # 3단계: Claude 작문 + HTML 생성
    print("\n✍️  [3/4] Claude 작문 중...")
    final_html = write_newsletter(analyzed)
    if not final_html:
        print("❌ 뉴스레터 생성 실패")
        return

    # 4단계: 아카이브 저장
    save_archive(final_html, today)

    # 5단계: 전체 발송
    subject = f"🌊 FIRSTWAVE · {today} 기술 브리핑"
    print(f"\n🚀 [4/4] {len(subscribers)}명에게 발송 중...")

    success, fail = 0, 0
    for email in subscribers:
        if send_email(email, subject, final_html):
            print(f"  ✅ {email}")
            success += 1
        else:
            fail += 1

    print(f"\n{'═' * 50}")
    print(f"✅ 완료 — 성공: {success}명 | 실패: {fail}명")
    print(f"{'═' * 50}\n")


if __name__ == "__main__":
    main()