import os
import requests
import resend
import trafilatura
import json
import re
from dotenv import load_dotenv
from litellm import completion

# 1. 환경 변수 로드
load_dotenv()
resend.api_key = os.getenv("RESEND_API_KEY")

# --- [고정 HTML 템플릿] ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: 'Pretendard', -apple-system, sans-serif; line-height: 1.6; color: #334155; background-color: #f8fafc; margin: 0; padding: 20px; }}
        .container {{ max-width: 600px; margin: 0 auto; }}
        .card {{ background: #ffffff; border: 1px solid #e2e8f0; border-radius: 16px; padding: 25px; margin-bottom: 25px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }}
        .tag {{ background: #eef2ff; color: #4f46e5; padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: 700; text-transform: uppercase; }}
        h1 {{ color: #1e293b; font-size: 28px; text-align: center; margin-bottom: 30px; }}
        h2 {{ color: #0f172a; margin: 15px 0 10px 0; font-size: 20px; letter-spacing: -0.025em; }}
        .meta {{ font-size: 13px; color: #64748b; margin-bottom: 16px; display: flex; gap: 10px; }}
        .summary-list {{ margin: 16px 0; padding-left: 20px; color: #475569; }}
        .summary-list li {{ margin-bottom: 10px; }}
        .insight-box {{ background: #f1f5f9; border-left: 5px solid #6366f1; padding: 20px; border-radius: 0 12px 12px 0; margin-top: 20px; }}
        .insight-title {{ font-weight: 800; color: #4338ca; font-size: 13px; text-transform: uppercase; margin-bottom: 5px; display: block; }}
        code {{ background: #f1f5f9; color: #2563eb; padding: 2px 4px; border-radius: 4px; font-family: ui-monospace, monospace; font-size: 0.9em; }}
        footer {{ text-align: center; color: #9ca3af; font-size: 12px; margin-top: 40px; padding-bottom: 40px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 Dev Digest: 시니어의 한 수</h1>
        {news_blocks}
        <footer>
            본 뉴스레터는 AI에 의해 자동 생성되었습니다. <br>
            출근길 3분 브리핑 영상은 <b>노션 페이지</b>에서 확인하세요!
        </footer>
    </div>
</body>
</html>
"""

def fetch_enriched_hn_data(limit=3):
    """[정보 수집] 기사 본문 전체를 긁어와 할루시네이션을 방지합니다."""
    print(f"🔎 HN 기사 및 본문 수집 중 (최대 {limit}개)...")
    try:
        top_ids = requests.get("https://hacker-news.firebaseio.com/v0/topstories.json").json()[:limit]
    except Exception as e:
        print(f"❌ HN ID 가져오기 실패: {e}")
        return []
    
    enriched_stories = []
    for i in top_ids:
        try:
            s = requests.get(f"https://hacker-news.firebaseio.com/v0/item/{i}.json").json()
            url = s.get('url')
            content = ""
            if url:
                downloaded = trafilatura.fetch_url(url)
                # [수정] None 방지 및 데이터 무결성 확보
                content = trafilatura.extract(downloaded) or ""
            
            enriched_stories.append({
                "title": s.get('title'),
                "score": s.get('score', 0),
                "comments": s.get('descendants', 0),
                # 30,000자로 확장하여 기사 전체 문맥 파악
                "link_content": content[:30000] if content else "본문 내용 없음"
            })
        except Exception as e:
            print(f"⚠️ 기사 {i}번 처리 중 건너뜀: {e}")
            continue
            
    return enriched_stories

def process_data_pipeline(stories):
    """[정보 재활용 및 생성] Gemini 분석 -> Claude 작문 흐름"""
    if not stories:
        return None

    # 1. Gemini: 본문 정밀 분석 (Claude에게 보낼 데이터 정제)
    print("🤖 Gemini: 전체 본문 읽고 팩트 요약 중...")
    for s in stories:
        res = completion(
            model="gemini/gemini-2.5-flash",
            messages=[{"content": f"이 기술 기사 본문을 사실에 근거해 상세히 요약해줘. 할루시네이션 주의:\n{s['link_content']}", "role": "user"}]
        )
        s['deep_summary'] = res.choices[0].message.content

    # 2. Claude: 정제된 데이터를 바탕으로 위트 있는 작문 (JSON 응답)
    print("✍️ Claude: 가독성 중심의 뉴스레터 데이터 생성 중...")
    # v6_final.py 내의 Claude 프롬프트 부분 수정
    prompt = f"""
    너는 토스의 UX 라이팅 가이드라인을 완벽히 숙지한 10년 차 시니어 소프트웨어 엔지니어이자, 
    동료 개발자들에게 인사이트를 전하는 다정한 뉴스레터 작가야.

    Gemini가 분석한 내용을 바탕으로, 한국 개발자들이 출근길에 가볍게 읽으면서도 
    "와, 이건 진짜 내 업무에 도움 되겠다"라고 느낄 만한 뉴스레터를 써줘.

    [토스 스타일 라이팅 가이드라인]
    1. **쉬운 단어:** 어려운 한자어나 딱딱한 업계 용어 대신, 대화하듯 쉬운 우리말을 써줘.
    2. **명확한 가치:** "이 기술이 나왔다"가 아니라 "이 기술로 우리 삶(업무)이 이렇게 편해진다"는 가치 중심으로 말해줘.
    3. **리듬감 있는 문체:** 문장은 짧고 간결하게, 말투는 '~해요', '~죠', '~까요'와 같이 친근한 '해요체'를 사용해줘.
    4. **솔직함과 위트:** 엔지니어로서 겪는 고충에 공감하며, 가벼운 농담이나 위트를 섞어줘.

    [콘텐츠 구성 규칙]
    1. **Headline:** 클릭하고 싶게 만드는 호기심 자극형 제목 (예: "그 코드가 유출된 진짜 이유", "35만 년 버틴 네안데르탈인의 생존 비결")
    2. **Body:** Gemini 요약본을 바탕으로 핵심만 3가지 불렛포인트(<li>)로 작성해. 반드시 <code>태그로 기술 용어를 강조해.
    3. **Insight:** 'Senior Insight' 대신 **'우리가 챙겨갈 점'**이라는 제목을 쓰고, 동료에게 해주는 진심 어린 조언을 담아줘.

    [출력 형식]
    결과는 반드시 아래 JSON 구조로만 출력해:
    {{
    "blocks": [
        {{ 
        "headline": "제목", 
        "body": "<li>요약1</li><li>요약2</li><li>요약3</li>", 
        "insight": "다정한 조언" 
        }}
    ]
    }}

데이터: {json.dumps(stories, ensure_ascii=False)}"""
    



    response = completion(
        model="anthropic/claude-sonnet-4-6",
        messages=[{"content": prompt, "role": "user"}]
    )
    
    # 3. JSON 파싱 보안 강화 (정규표현식 사용)
    try:
        raw_output = response.choices[0].message.content
        json_match = re.search(r'\{.*\}', raw_output, re.DOTALL)
        if not json_match:
            raise ValueError("응답에서 JSON 구조를 찾을 수 없습니다.")
        
        data = json.loads(json_match.group())
        
        # 템플릿에 데이터 주입
        blocks_html = ""
        for i, b in enumerate(data.get('blocks', [])):
            s = stories[i]
            blocks_html += f"""
            <div class="card">
                <span class="tag">ISSUE {i+1}</span>
                <h2>{b['headline']}</h2>
                <div class="meta">👍 {s['score']} points | 💬 {s['comments']} comments</div>
                <div class="summary-list">{b['body']}</div>
                <div class="insight-box">
                    <span class="insight-title">💡 Senior Insight</span>
                    {b['insight']}
                </div>
            </div>
            """
        return HTML_TEMPLATE.format(news_blocks=blocks_html)

    except Exception as e:
        print(f"❌ 데이터 매핑/파싱 실패: {e}")
        return None

def main():
    # 1. 수집
    stories = fetch_enriched_hn_data(limit=3)
    if not stories:
        print("❌ 수집된 기사가 없습니다.")
        return

    # 2. 분석 및 HTML 생성
    final_html = process_data_pipeline(stories)
    
    # 3. [최종 검증] 에러가 없을 때만 발송
    if final_html and "데이터 처리 오류" not in final_html:
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