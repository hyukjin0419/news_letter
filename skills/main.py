import os
import sys
import json
import re
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
ARCHIVE_DIR = "../archive"
ARCHIVE_INDEX = "../archive/index.html"


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


def save_archive(html: str, date: str, stories: list) -> None:
    """발송한 HTML을 archive/ 폴더에 저장 + index.html 자동 업데이트"""
    os.makedirs(ARCHIVE_DIR, exist_ok=True)

    # 1. HTML 파일 저장
    path = os.path.join(ARCHIVE_DIR, f"{date}.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  ✅ 아카이브 저장 완료 → archive/{date}.html")

    # 2. index.html의 archives 배열 업데이트
    if not os.path.exists(ARCHIVE_INDEX):
        print(f"  ⚠️  archive/index.html 없음, 목록 업데이트 스킵")
        return

    # 대표 제목 (첫 번째 기사 헤드라인)
    first_title = stories[0].get("title", "")[:40] if stories else ""
    title_display = f"{first_title} 외 {len(stories)-1}건" if len(stories) > 1 else first_title

    new_entry = f'      {{ date: "{date}", title: "{title_display}" }},'

    with open(ARCHIVE_INDEX, "r", encoding="utf-8") as f:
        content = f.read()

    # archives 배열 안에 새 항목 추가
    updated = content.replace(
    "    const archives = [",
    f"    const archives = [\n{new_entry}"
)

    with open(ARCHIVE_INDEX, "w", encoding="utf-8") as f:
        f.write(updated)

    print(f"  ✅ 아카이브 목록 업데이트 완료 → {date}")


def load_latest_archive() -> str | None:
    """아카이브에서 가장 최근 HTML 파일 로드"""
    if not os.path.exists(ARCHIVE_DIR):
        print("  ❌ archive/ 폴더가 없어요. 먼저 python main.py 로 한 번 실행해주세요.")
        return None

    files = sorted([f for f in os.listdir(ARCHIVE_DIR) if f.endswith(".html") and f != "index.html"])
    if not files:
        print("  ❌ 아카이브에 저장된 파일이 없어요. 먼저 python main.py 로 한 번 실행해주세요.")
        return None

    latest = files[-1]
    path = os.path.join(ARCHIVE_DIR, latest)
    with open(path, "r", encoding="utf-8") as f:
        html = f.read()

    print(f"  ✅ 아카이브 로드 완료 → archive/{latest}")
    return html


def send_to_all(subscribers: list[str], subject: str, html: str) -> None:
    """전체 구독자에게 발송"""
    print(f"\n🚀 {len(subscribers)}명에게 발송 중...")
    success, fail = 0, 0
    for email in subscribers:
        if send_email(email, subject, html):
            print(f"  ✅ {email}")
            success += 1
        else:
            fail += 1
    print(f"\n{'═' * 50}")
    print(f"✅ 완료 — 성공: {success}명 | 실패: {fail}명")
    print(f"{'═' * 50}\n")


def main():
    today = datetime.now().strftime("%Y-%m-%d")
    is_test = "--test" in sys.argv

    if is_test:
        print(f"\n🧪 [테스트 모드] 아카이브 최신 파일로 발송 ({today})\n")
    else:
        print(f"\n🌊 FIRSTWAVE 뉴스레터 파이프라인 시작 ({today})\n")

    # 0단계: 구독자 먼저 확인
    print("📋 [0] 구독자 확인 중...")
    subscribers = get_subscribers()
    if not subscribers:
        print("⚠️  구독자가 없어 파이프라인을 중단합니다.")
        return

    if is_test:
        # 테스트 모드: 아카이브 최신 파일 로드 후 발송
        print("\n📂 [1] 아카이브 로드 중...")
        final_html = load_latest_archive()
        if not final_html:
            return
        subject = f"[테스트] 🌊 FIRSTWAVE · {today} 기술 브리핑"
        send_to_all(subscribers, subject, final_html)

    else:
        # 실제 모드: 전체 파이프라인 실행
        print("\n🔎 [1] 기사 수집 중...")
        stories = fetch_top_tech_news(limit=3)
        if not stories:
            print("❌ 수집된 기사가 없습니다.")
            return

        print("\n🤖 [2] Gemini 분석 중...")
        analyzed = deep_analyze_tech(stories)

        print("\n✍️  [3] Claude 작문 중...")
        final_html = write_newsletter(analyzed)
        if not final_html:
            print("❌ 뉴스레터 생성 실패")
            return

        # 아카이브 저장 + index.html 업데이트
        save_archive(final_html, today, stories)

        subject = f"🌊 FIRSTWAVE · {today} 기술 브리핑"
        send_to_all(subscribers, subject, final_html)


if __name__ == "__main__":
    main()