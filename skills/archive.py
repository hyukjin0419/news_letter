import os
import json

ARCHIVE_DIR = "../docs/archive"
ARCHIVE_JSON = "../docs/archive/archive.json"
SENT_URLS_FILE = "../docs/archive/sent_urls.json"


def save_newsletter(html: str, date: str, stories: list) -> None:
    """발송한 HTML 저장 + archive.json + sent_urls.json 업데이트"""
    os.makedirs(ARCHIVE_DIR, exist_ok=True)

    # 1. HTML 파일 저장
    html_path = os.path.join(ARCHIVE_DIR, f"{date}.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  ✅ HTML 저장 완료 → archive/{date}.html")

    # 2. archive.json 업데이트
    first_title = stories[0].get("title", "") if stories else ""
    title_display = f"{first_title[:40]}{'...' if len(first_title) > 40 else ''} 외 {len(stories)-1}건" if len(stories) > 1 else first_title[:40]
    new_entry = {"date": date, "title": title_display}

    archives = _load_json(ARCHIVE_JSON, default=[])
    archives = [a for a in archives if a["date"] != date]  # 중복 날짜 방지
    archives.append(new_entry)
    archives.sort(key=lambda x: x["date"], reverse=True)

    _save_json(ARCHIVE_JSON, archives)
    print(f"  ✅ archive.json 업데이트 완료 ({len(archives)}개)")

    # 3. sent_urls.json 업데이트
    new_urls = [s["url"] for s in stories if s.get("url")]
    sent_urls = _load_json(SENT_URLS_FILE, default=[])
    sent_urls = list(set(sent_urls + new_urls))  # 중복 제거

    _save_json(SENT_URLS_FILE, sent_urls)
    print(f"  ✅ sent_urls.json 업데이트 완료 (총 {len(sent_urls)}개 URL)")


def load_latest_html() -> str | None:
    """아카이브에서 가장 최근 HTML 파일 로드 (테스트용)"""
    if not os.path.exists(ARCHIVE_DIR):
        print("  ❌ archive/ 폴더가 없어요. 먼저 python main.py 로 실행해주세요.")
        return None

    files = sorted([
        f for f in os.listdir(ARCHIVE_DIR)
        if f.endswith(".html") and f != "index.html"
    ])

    if not files:
        print("  ❌ 저장된 뉴스레터가 없어요. 먼저 python main.py 로 실행해주세요.")
        return None

    latest = files[-1]
    with open(os.path.join(ARCHIVE_DIR, latest), "r", encoding="utf-8") as f:
        html = f.read()

    print(f"  ✅ 아카이브 로드 완료 → archive/{latest}")
    return html


def _load_json(path: str, default) -> list:
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def _save_json(path: str, data) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)