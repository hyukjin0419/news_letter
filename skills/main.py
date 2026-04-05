import os
import resend
from fetcher01 import fetch_top_tech_news
from analyzer import deep_analyze_tech
from writer import write_newsletter

resend.api_key = os.getenv("RESEND_API_KEY")


def main():
    # 1단계: 기사 수집
    stories = fetch_top_tech_news(limit=3)
    if not stories:
        print("❌ 수집된 기사가 없습니다.")
        return

    # 2단계: Gemini 분석
    analyzed = deep_analyze_tech(stories)

    # 3단계: Claude 작문 + HTML 생성
    final_html = write_newsletter(analyzed)

    # 4단계: 검증 후 발송
    if final_html:
        print("🚀 모든 검증 완료. 이메일을 발송합니다.")
        try:
            resend.Emails.send({
                "from": "DevDigest <onboarding@resend.dev>",
                "to": [os.getenv("MY_EMAIL")],
                "subject": "🔥 오늘 아침, 시니어 개발자의 기술 브리핑",
                "html": final_html,
            })
            print("✅ 뉴스레터 발송이 완료되었습니다!")
        except Exception as e:
            print(f"❌ 이메일 전송 API 오류: {e}")
    else:
        print("⚠️ 데이터 처리 중 오류가 감지되어 발송을 중단했습니다.")


if __name__ == "__main__":
    main()
