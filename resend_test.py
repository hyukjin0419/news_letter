import os
import resend
from dotenv import load_dotenv

# .env 파일을 로드합니다.
load_dotenv()

# os.environ으로 환경 변수를 가져옵니다.
resend.api_key = os.getenv("RESEND_API_KEY")

params = {
    "from": "onboarding@resend.dev",
    "to": "redtruth0419@gmail.com",
    "subject": "Hello World",
    "html": "<strong>It works!</strong>",
}

email = resend.Emails.send(params)
print(email)