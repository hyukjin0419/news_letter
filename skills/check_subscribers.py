"""
check_subscribers.py — 구독자 목록 확인용
Google Sheets 연동 테스트 및 구독자 목록을 출력합니다.

실행: python check_subscribers.py
"""
import gspread
from google.oauth2.service_account import Credentials

SHEETS_ID = "1OX65Jlt51Ub7pZdN9RlAJd9Bz7ilxs86KfZk_e3fUUk"
CREDENTIALS_FILE = "../credentials.json"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

if __name__ == "__main__":
    print("📋 Google Sheets 구독자 확인 중...\n")

    try:
        creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
        gc = gspread.authorize(creds)
        sheet = gc.open_by_key(SHEETS_ID).sheet1
        records = sheet.get_all_records()

        emails = [r["email"] for r in records if r.get("email")]

        if not emails:
            print("⚠️  구독자가 없습니다.")
            print("   Google Sheets에 이메일을 추가해주세요.")
        else:
            print(f"✅ 총 구독자: {len(emails)}명\n")
            for i, email in enumerate(emails, 1):
                print(f"  {i}. {email}")

    except Exception as e:
        print(f"❌ 연결 실패: {e}")
        print("\n확인사항:")
        print("  1. credentials.json 위치가 ../credentials.json 인지 확인")
        print("  2. Google Sheets에 서비스 계정 이메일이 공유되어 있는지 확인")
        print("  3. Sheets 첫 번째 행에 'email' 헤더가 있는지 확인")