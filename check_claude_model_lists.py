import os
import requests
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()
api_key = os.getenv("ANTHROPIC_API_KEY")

# Anthropic API 모델 목록 엔드포인트
url = "https://api.anthropic.com/v1/models"
headers = {
    "x-api-key": api_key,
    "anthropic-version": "2023-06-01"  # API 버전 헤더
}

print("📡 Anthropic 서버에서 모델 목록을 불러오는 중...")

try:
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        models = response.json().get('data', [])
        print("\n✅ 사용 가능한 Claude 모델 목록:")
        for m in models:
            print(f"- {m['id']}")
            
        print("\n💡 위 목록 중 하나를 v1.py의 model='anthropic/모델명' 자리에 넣으세요.")
    else:
        print(f"\n❌ 에러 발생: {response.status_code}")
        print(f"메시지: {response.text}")

except Exception as e:
    print(f"\n❌ 연결 실패: {e}")