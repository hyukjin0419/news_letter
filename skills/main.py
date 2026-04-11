import sys
from datetime import datetime, timezone, timedelta

from fetcher import fetch_top_tech_news
from analyzer import deep_analyze_tech
from writer import write_newsletter
from sheets import get_subscribers
from mailer import send_to_all
from archive import save_newsletter, load_latest_html


def main():
    KST = timezone(timedelta(hours=9))
    today = datetime.now(KST).strftime("%Y-%m-%d")
    is_test = "--test" in sys.argv
    is_preview = "--preview" in sys.argv

    if is_test:
        print(f"\n🧪 [테스트 모드] 아카이브 최신 파일로 발송 ({today})\n")
    elif is_preview:
        print(f"\n👀 [미리보기 모드] 생성 + 저장만, 발송 없음 ({today})\n")
    else:
        print(f"\n🌊 FIRSTWAVE 파이프라인 시작 ({today})\n")

    # 0단계: 구독자 확인 (테스트/미리보기 제외)
    if not is_preview:
        print("📋 [0] 구독자 확인 중...")
        subscribers = get_subscribers()
        if not subscribers:
            print("⚠️  구독자가 없어 파이프라인을 중단합니다.")
            return
    else:
        subscribers = []

    # 테스트 모드: 아카이브 최신 파일로 발송
    if is_test:
        print("\n📂 [1] 아카이브 로드 중...")
        final_html = load_latest_html()
        if not final_html:
            return
        subject = f"[테스트] 🌊 FIRSTWAVE · {today} 기술 브리핑"
        success, fail = send_to_all(subscribers, subject, final_html)
        print(f"\n{'═' * 50}")
        print(f"✅ 완료 — 성공: {success}명 | 실패: {fail}명")
        print(f"{'═' * 50}\n")
        return

    # 실제/미리보기 모드: 전체 파이프라인
    print("\n🔎 [1] 기사 수집 중...")
    stories = fetch_top_tech_news(limit=3)
    if not stories:
        print("❌ 수집된 기사가 없습니다.")
        return

    print("\n🤖 [2] Gemini 분석 중...")
    analyzed = deep_analyze_tech(stories)

    print("\n✍️  [3] Claude 작문 중...")
    final_html, headlines = write_newsletter(analyzed)
    if not final_html:
        print("❌ 뉴스레터 생성 실패")
        return

    print("\n💾 [4] 아카이브 저장 중...")
    save_newsletter(final_html, today, stories, headlines)

    # 미리보기 모드는 발송 없이 종료
    if is_preview:
        print("\n👀 미리보기 저장 완료. 발송은 python main.py 로 실행하세요.")
        return

    # 발송
    subject = f"🌊 FIRSTWAVE · {today} 기술 브리핑"
    success, fail = send_to_all(subscribers, subject, final_html)

    print(f"\n{'═' * 50}")
    print(f"✅ 완료 — 성공: {success}명 | 실패: {fail}명")
    print(f"{'═' * 50}\n")


if __name__ == "__main__":
    main()