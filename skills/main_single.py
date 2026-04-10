import sys
from datetime import datetime
from dotenv import load_dotenv
import os

from fetcher import fetch_top_tech_news
from analyzer import deep_analyze_tech
from writer import write_newsletter
from mailer import send_email
from archive import save_newsletter, load_latest_html

load_dotenv()

MY_EMAIL = os.getenv("MY_EMAIL")


def main():
    today = datetime.now().strftime("%Y-%m-%d")
    is_test = "--test" in sys.argv
    is_preview = "--preview" in sys.argv

    if is_test:
        print(f"\n🧪 [테스트 모드] 아카이브 최신 파일로 발송 ({today})\n")
    elif is_preview:
        print(f"\n👀 [미리보기 모드] 생성 + 저장만 ({today})\n")
    else:
        print(f"\n🌊 FIRSTWAVE 파이프라인 시작 ({today})\n")

    # 테스트 모드
    if is_test:
        print("📂 [1] 아카이브 로드 중...")
        final_html = load_latest_html()
        if not final_html:
            return
        subject = f"[테스트] 🌊 FIRSTWAVE · {today} 기술 브리핑"
        personalized_html = final_html.replace('__EMAIL__', MY_EMAIL)
        send_email(MY_EMAIL, subject, personalized_html)
        print(f"  ✅ {MY_EMAIL} 발송 완료")
        return

    # 실제/미리보기 모드
    print("\n🔎 [1] 기사 수집 중...")
    stories = fetch_top_tech_news(limit=3)
    if not stories:
        print("❌ 수집된 기사가 없습니다.")
        return

    print("\n🤖 [2] Gemini 분석 중...")
    analyzed = deep_analyze_tech(stories)

    print("\n✍️  [3] Claude 작문 중...")
    final_html = write_newsletter(analyzed)
    if not final_html:
        print("❌ 뉴스레터 생성 실패")
        return

    print("\n💾 [4] 아카이브 저장 중...")
    save_newsletter(final_html, today, stories)

    if is_preview:
        print("\n👀 미리보기 저장 완료. 발송은 python main_single.py 로 실행하세요.")
        return

    subject = f"🌊 FIRSTWAVE · {today} 기술 브리핑"
    personalized_html = final_html.replace('__EMAIL__', MY_EMAIL)
    if send_email(MY_EMAIL, subject, personalized_html):
        print(f"\n✅ 발송 완료 → {MY_EMAIL}")
    else:
        print(f"\n❌ 발송 실패 → {MY_EMAIL}")


if __name__ == "__main__":
    main()