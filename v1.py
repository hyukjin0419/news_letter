import requests
from litellm import completion
import os
from dotenv import load_dotenv

load_dotenv()

os.environ["ANTHROPIC_API_KEY"] = os.getenv("ANTHROPIC_API_KEY")
os.environ["GEMINI_API_KEY"] = os.getenv("GEMINI_API_KEY")

def fetch_hn_top_stories(limit=5):
    '''Hacker News API에서 실시간 인기 기사 추출'''
    printf(f"🔎 Hacker News에서 상위 {limit}개의 기사 추출 중...")
    try:
        response = requests.get("https://hacker-news.firebaseio.com/v0/topstories.json")
        if response.status_code == 200:
            stories = response.json()
            return stories[:limit]
        else:
            print(f"❌ Hacker News API 요청 실패: {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return []

import os
import requests
from litellm import completion
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

def fetch_hn_top_stories(limit=5):
    """Hacker News API에서 실시간 인기 기사 추출"""
    print(f"🔎 Hacker News에서 상위 {limit}개 기사를 가져오는 중...")
    top_ids_url = "https://hacker-news.firebaseio.com/v0/topstories.json"
    ids = requests.get(top_ids_url).json()[:limit]
    
    stories = []
    for s_id in ids:
        item = requests.get(f"https://hacker-news.firebaseio.com/v0/item/{s_id}.json").json()
        if 'url' in item:
            stories.append({"title": item['title'], "url": item['url']})
    return stories

def run_ai_pipeline(stories):
    # 1. 컨텍스트 구성
    context = "\n".join([f"- {s['title']} ({s['url']})" for s in stories])

    # 2. [Research Phase] Gemini로 핵심 기술 분석 (비용 효율적)
    print("🤖 Gemini가 기술적 맥락을 분석하고 있습니다...")
    research_prompt = f"""
    아래 뉴스 기사들을 분석해서 개발자에게 중요한 기술적 키워드와 핵심 내용을 추출해줘.
    기사 목록:
    {context}
    """
    
    research_response = completion(
        model="gemini/gemini-3-flash-preview",
        messages=[{"role": "user", "content": research_prompt}]
    )
    analysis_result = research_response.choices[0].message.content

    # 3. [Editing Phase] Claude로 뉴스레터 집필 (고퀄리티 문장)
    print("✍️ Claude가 뉴스레터를 작성하고 있습니다...")
    writing_prompt = f"""
    너는 10년 차 시니어 소프트웨어 엔지니어이자 인기 기술 뉴스레터 작가야.
    Gemini의 분석 내용을 바탕으로 한국 개발자들이 열광할 만한 위트 있고 통찰력 있는 뉴스레터를 써줘.
    
    [분석 내용]:
    {analysis_result}
    
    [가이드라인]:
    - 말투는 친근하면서도 전문적이어야 함 (예: ~네요, ~입니다).
    - 각 뉴스마다 '엔지니어의 시각'에서 본 짧은 코멘트를 추가할 것.
    - 마지막엔 '오늘의 한 줄 요약'을 포함할 것.
    """

    newsletter_response = completion(
        model="anthropic/claude-sonnet-4-6",
        messages=[{"role": "user", "content": writing_prompt}]
    )
    
    return newsletter_response.choices[0].message.content

if __name__ == "__main__":
    try:
        stories = fetch_hn_top_stories(5)
        newsletter_content = run_ai_pipeline(stories)
        
        print("\n" + "="*60)
        print("🚀 생성된 뉴스레터 본문")
        print("="*60 + "\n")
        print(newsletter_content)
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")