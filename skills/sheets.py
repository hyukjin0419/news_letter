import gspread
from google.oauth2.service_account import Credentials

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