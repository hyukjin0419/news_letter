import re
import json
import os
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

SKIP_DOMAINS = [
    "arxiv.org",
    "youtube.com",
    "twitter.com",
    "x.com",
    "reddit.com",
    "linkedin.com",
    "docs.google.com",
]

MIN_CONTENT_LENGTH = 200
CANDIDATE_POOL = 30

README_MAX_LENGTH = 15000
ARTICLE_MAX_LENGTH = 5000
ARTICLE_HEAD_LENGTH = 4000
ARTICLE_TAIL_LENGTH = 1000

SENT_URLS_FILE = "../archive/sent_urls.json"


def load_sent_urls() -> set:
    """이미 발송한 URL 목록 로드"""
    if not os.path.exists(SENT_URLS_FILE):
        return set()
    try:
        with open(SENT_URLS_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    except Exception:
        return set()


def is_good_candidate(story: dict, sent_urls: set) -> bool:
    """크롤링 전, 메타데이터만으로 좋은 기사인지 판단"""
    if not story or story.get('type') != 'story':
        return False

    if story.get('dead') or story.get('deleted'):
        return False

    url = story.get('url', '')

    if not url:
        return False

    if any(domain in url.lower() for domain in SKIP_DOMAINS):
        return False

    if story.get('score', 0) < 50:
        return False

    # 이미 발송한 URL 스킵
    if url in sent_urls:
        print(f"  ⏭️ 중복 스킵: {story.get('title', '')[:50]}")
        return False

    return True


def fetch_github_readme(url: str) -> str:
    try:
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


def process_story(item_id: int, sent_urls: set) -> dict | None:
    """개별 아이템 조회 및 크롤링"""
    try:
        s = requests.get(
            f"https://hacker-news.firebaseio.com/v0/item/{item_id}.json",
            timeout=5
        ).json()

        if not is_good_candidate(s, sent_urls):
            if s.get('url') not in sent_urls:
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
    HN 상위 기사 중 중복 제외하고 limit개 반환.
    - 이미 발송한 URL은 스킵
    - 풀 30개에서 limit개 채울 때까지 계속 시도
    """
    print(f"🔎 [Fetcher] HN 상위 기사 수집 중 (목표: {limit}개)...")

    sent_urls = load_sent_urls()
    if sent_urls:
        print(f"  📋 이미 발송한 URL {len(sent_urls)}개 제외")

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

        result = process_story(item_id, sent_urls)
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