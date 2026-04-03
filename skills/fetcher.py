import requests
import trafilatura

def fetch_top_tech_news(limit=3):
    """최신 기술 뉴스 수집 및 본문 추출 (Head 4000 + Tail 1000 전략)"""
    print("🔎 [Skill: Fetcher] 뉴스 수집 시작...")
    try:
        # 8번 라인 오타 수정: limit 파라미터 적용
        top_ids = requests.get("https://hacker-news.firebaseio.com/v0/topstories.json").json()[:limit]
        stories = []
        
        for i in top_ids:
            s = requests.get(f"https://hacker-news.firebaseio.com/v0/item/{i}.json").json()
            url = s.get('url')
            content = ""
            
            if url:
                downloaded = trafilatura.fetch_url(url)
                raw_text = trafilatura.extract(downloaded) or ""
                
                # 🌟 지능적 문맥 다듬기 (Context Trimming)
                # 전체가 5,000자보다 길면 앞 4,000자(핵심)와 뒤 1,000자(결론)만 합칩니다.
                if len(raw_text) > 5000:
                    head = raw_text[:4000]
                    tail = raw_text[-1000:]
                    content = f"{head}\n\n[...중략: 세부 데이터 및 광고...] \n\n{tail}"
                else:
                    content = raw_text
            
            stories.append({
                "title": s.get('title'),
                "score": s.get('score', 0),
                "comments": s.get('descendants', 0),
                "link_content": content # 최적화된 본문 데이터
            })
            
        return stories
    except Exception as e:
        print(f"❌ Fetcher 오류: {e}")
        return []
