import re
import requests
import trafilatura
from trafilatura.settings import use_config

# 브라우저처럼 보이게 해서 봇 차단 우회
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

# trafilatura도 동일한 User-Agent 사용
TRAFILATURA_CONFIG = use_config()
TRAFILATURA_CONFIG.set("DEFAULT", "USER_AGENT", HEADERS['User-Agent'])

# 크롤링 품질이 낮거나 본문 추출이 안되는 도메인
# github.com은 전용 처리로 대응하므로 제외
SKIP_DOMAINS = [
    "arxiv.org",
    "youtube.com",
    "twitter.com",
    "x.com",
    "reddit.com",
    "linkedin.com",
    "docs.google.com",
]

MIN_CONTENT_LENGTH = 200   # 본문 최소 길이 기준
CANDIDATE_POOL = 30        # 후보 기사 수 (넉넉하게)

# GitHub README: 중간에 핵심 내용(설치법, API 등)이 있어서 넉넉하게
README_MAX_LENGTH = 15000

# 일반 기사: Head + Tail 전략 (중간은 세부사항/광고 노이즈가 많음)
ARTICLE_MAX_LENGTH = 5000
ARTICLE_HEAD_LENGTH = 4000  # 앞부분 (핵심 내용)
ARTICLE_TAIL_LENGTH = 1000  # 뒷부분 (결론/전망)


def is_good_candidate(story: dict) -> bool:
    """크롤링 전, 메타데이터만으로 좋은 기사인지 판단"""
    if not story or story.get('type') != 'story':
        return False  # comment, job, poll 등 제외

    if story.get('dead') or story.get('deleted'):
        return False  # 삭제/차단된 글 제외

    url = story.get('url', '')

    if not url:
        return False  # Ask HN, Show HN 등 url 없는 경우

    if any(domain in url.lower() for domain in SKIP_DOMAINS):
        return False  # 크롤링 품질 낮은 도메인 제거

    if story.get('score', 0) < 50:
        return False  # 점수 너무 낮은 기사 제거

    return True


def fetch_github_readme(url: str) -> str:
    """
    GitHub 저장소 URL에서 README.md를 직접 가져옴.
    - raw.githubusercontent.com으로 직접 접근 (JS 렌더링 불필요)
    - main → master 순으로 브랜치 시도
    - 너무 길면 앞부분만 (설치법, 사용법 등 핵심이 앞에 있음)
    """
    try:
        # github.com/owner/repo 또는 github.com/owner/repo/tree/branch/... 형태 파싱
        match = re.match(r'https?://github\.com/([^/]+)/([^/?\s#]+)', url)
        if not match:
            print(f"  ⚠️ GitHub URL 파싱 실패: {url}")
            return ""

        owner, repo = match.group(1), match.group(2)

        for branch in ['main', 'master']:
            raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/README.md"
            res = requests.get(raw_url, headers=HEADERS, timeout=10)

            if res.status_code == 200:
                readme = res.text

                # README가 너무 길면 앞부분만 사용 (핵심 설명이 앞에 집중)
                if len(readme) > README_MAX_LENGTH:
                    readme = readme[:README_MAX_LENGTH] + "\n\n[...이하 생략...]"

                print(f"  📄 GitHub README 수집 완료 ({owner}/{repo}, {len(readme)}자)")
                return readme

        print(f"  ⚠️ README를 찾을 수 없음 ({owner}/{repo})")
        return ""

    except Exception as e:
        print(f"  ⚠️ GitHub 크롤링 실패 ({url}): {e}")
        return ""


def crawl_content(url: str) -> str:
    """
    url 타입에 따라 적절한 방식으로 본문 추출.
    - GitHub: README.md 직접 수집
    - 일반 기사: trafilatura (Head 4000 + Tail 1000 전략)
    """
    if "github.com" in url:
        return fetch_github_readme(url)

    try:
        downloaded = trafilatura.fetch_url(url, config=TRAFILATURA_CONFIG)
        raw_text = trafilatura.extract(downloaded) or ""

        if len(raw_text) > ARTICLE_MAX_LENGTH:
            head = raw_text[:ARTICLE_HEAD_LENGTH]
            tail = raw_text[-ARTICLE_TAIL_LENGTH:]
            return f"{head}\n\n[...중략...]\n\n{tail}"

        return raw_text

    except Exception as e:
        print(f"  ⚠️ 크롤링 실패 ({url}): {e}")
        return ""


def process_story(item_id: int) -> dict | None:
    """개별 아이템 조회 및 크롤링 (병렬 처리용)"""
    try:
        s = requests.get(
            f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json",
            timeout=5
        ).json()

        if not is_good_candidate(s):
            print(f"  ⏭️ 스킵: {s.get('title', '')[:50]}")
            return None

        url = s.get('url')
        print(f"  🌐 크롤링: {url}")
        content = crawl_content(url)

        if len(content) < MIN_CONTENT_LENGTH:
            print(f"  ⏭️ 본문 부족 ({len(content)}자), 스킵")
            return None

        return {
            "title": s.get('title'),
            "url": url,
            "score": s.get('score', 0),
            "comments": s.get('descendants', 0),
            "link_content": content,
        }

    except Exception as e:
        print(f"  ⚠️ 처리 실패 ({item_id}): {e}")
        return None


def fetch_top_tech_news(limit=3) -> list:
    """
    HN 상위 기사 중 품질 좋은 기사만 골라 limit개 반환.
    - 순차 처리로 HN 순위 보장
    - 풀 30개 중 limit개 채워지면 중단
    - 사전 필터링 + 본문 품질 검증으로 안정성 확보
    """
    print(f"🔎 [Fetcher] HN 상위 기사 수집 중 (목표: {limit}개)...")

    try:
        top_ids = requests.get(
            "https://hacker-news.firebaseio.com/v0/topstories.json"
        ).json()[:CANDIDATE_POOL]
    except Exception as e:
        print(f"❌ HN API 오류: {e}")
        return []

    stories = []

    for item_id in top_ids:
        if len(stories) >= limit:
            break

        result = process_story(item_id)
        if result:
            stories.append(result)
            print(f"  ✅ 수집 완료 ({len(stories)}/{limit}): {result['title'][:50]}")

    if len(stories) < limit:
        print(f"⚠️ 목표 {limit}개 중 {len(stories)}개만 수집됨 (후보 풀 부족)")

    return stories


if __name__ == "__main__":
    results = fetch_top_tech_news(limit=3)
    print(f"\n📦 최종 수집: {len(results)}개")
    for r in results:
        print(f"  - [{r['score']}점] {r['title']}")
        print(f"    본문 {len(r['link_content'])}자 | {r['url']}")
