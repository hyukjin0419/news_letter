import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
response = requests.get(url)

if response.status_code == 200:
    models = response.json().get('models', [])
    print("✅ 사용 가능한 Gemini 모델 목록:")
    for m in models:
        # 'models/' 접두사를 떼고 출력
        name = m['name'].replace('models/', '')
        print(f"- {name}")
else:
    print(f"❌ 에러 발생: {response.status_code}, {response.text}")