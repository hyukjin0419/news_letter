import requests
import trafilatura

def fetch_top_tech_news(limit=3):
    """최신 기술 뉴스 수집 및 본문 추출"""
    print("🔎 [Skill: Fetcher] 뉴스 수집 시작...")
    try:
        top_ids = requests.get(
            "https://hacker-news.firebaseio.com/v0/topstories.json",
            timeout=10
        ).json()
    except Exception as e:
        print(f"❌ HN 목록 가져오기 실패: {e}")
        return []

    stories = []
    candidate_ids = iter(top_ids)

    while len(stories) < limit:
        try:
            i = next(candidate_ids)
        except StopIteration:
            break

        try:
            s = requests.get(
                f"https://hacker-news.firebaseio.com/v0/item/{i}.json",
                timeout=10
            ).json()
            url = s.get('url')
            if not url:
                continue  # Ask HN / Show HN 등 본문 없는 게시물 스킵

            downloaded = trafilatura.fetch_url(url)
            content = trafilatura.extract(downloaded) or ""
            if not content:
                continue  # 본문 추출 실패 시 스킵

            stories.append({
                "title": s.get('title'),
                "score": s.get('score', 0),
                "comments": s.get('descendants', 0),
                "link_content": content
            })
            print(f"  ✅ ({len(stories)}/{limit}) {s.get('title')}")
        except Exception as e:
            print(f"  ⚠️ 기사 {i}번 건너뜀: {e}")
            continue

    return stories
