import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")


def send_email(to_email: str, subject: str, html: str) -> bool:
    """Gmail SMTP로 단일 이메일 발송"""
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


def send_to_all(subscribers: list[str], subject: str, html: str) -> tuple[int, int]:
    """전체 구독자에게 발송, (성공, 실패) 반환"""
    print(f"\n🚀 {len(subscribers)}명에게 발송 중...")
    success, fail = 0, 0
    for email in subscribers:
        if send_email(email, subject, html):
            print(f"  ✅ {email}")
            success += 1
        else:
            fail += 1
    return success, fail