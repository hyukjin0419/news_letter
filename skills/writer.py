import json
import re
from datetime import datetime
from litellm import completion

WRITER_MODEL = "anthropic/claude-sonnet-4-6"

HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{ font-family: 'Pretendard', -apple-system, sans-serif; line-height: 1.6; color: #334155; background-color: #f8fafc; margin: 0; padding: 20px; }}
    .container {{ max-width: 600px; margin: 0 auto; }}

    /* HEADER */
    .header {{ text-align: center; padding: 32px 0 24px; }}
    .logo-text {{ font-size: 13px; font-weight: 800; letter-spacing: 0.12em; color: #000; display: block; margin-bottom: 4px; }}
    .header-title {{ font-size: 26px; font-weight: 800; color: #0f172a; margin: 8px 0 4px; }}
    .header-sub {{ font-size: 13px; color: #94a3b8; }}
    .header-date {{ font-size: 12px; color: #cbd5e1; margin-top: 4px; }}

    /* CARD */
    .card {{ background: #ffffff; border: 1px solid #e2e8f0; border-radius: 16px; padding: 25px; margin-bottom: 20px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.07); }}
    .tag {{ background: #eef2ff; color: #4f46e5; padding: 4px 10px; border-radius: 6px; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; }}
    .card-title {{ color: #0f172a; margin: 12px 0 8px; font-size: 19px; font-weight: 700; letter-spacing: -0.025em; line-height: 1.35; }}
    .meta {{ font-size: 12px; color: #94a3b8; margin-bottom: 16px; }}

    /* POINTS */
    .summary-list {{ margin: 16px 0; padding-left: 20px; color: #475569; }}
    .summary-list li {{ margin-bottom: 10px; font-size: 14px; line-height: 1.6; }}
    code {{ background: #f1f5f9; color: #2563eb; padding: 2px 5px; border-radius: 4px; font-family: ui-monospace, monospace; font-size: 0.88em; }}

    /* INSIGHT */
    .insight-box {{ background: #f8fafc; border-left: 4px solid #6366f1; padding: 16px 18px; border-radius: 0 10px 10px 0; margin-top: 18px; }}
    .insight-title {{ font-weight: 800; color: #4338ca; font-size: 11px; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 6px; display: block; }}
    .insight-text {{ font-size: 13px; color: #475569; line-height: 1.65; }}

    /* FOOTER */
    footer {{ text-align: center; color: #cbd5e1; font-size: 12px; margin-top: 32px; padding-bottom: 40px; line-height: 1.8; }}
  </style>
</head>
<body>
  <div class="container">

    <!-- HEADER -->
    <div class="header">
      <span class="logo-text">FIRSTWAVE</span>
      <div class="header-title">오늘의 기술 첫 번째 파도</div>
      <div class="header-sub">매일 오전 8시 · HN 상위 3개 엄선</div>
      <div class="header-date">{date}</div>
    </div>

    <!-- CARDS -->
    {news_blocks}

    <!-- FOOTER -->
    <footer>
      FIRSTWAVE · 매일 오전 8시 발신
    </footer>

  </div>
</body>
</html>"""

CARD_TEMPLATE = """
    <div class="card">
      <span class="tag">WAVE {wave_num}</span>
      <h2 class="card-title">{headline}</h2>
      <div class="meta">{score} pts &nbsp;·&nbsp; {comments} comments</div>
      <ul class="summary-list">
        {points}
      </ul>
      <div class="insight-box">
        <span class="insight-title">우리가 챙겨갈 점</span>
        <div class="insight-text">{insight}</div>
      </div>
    </div>"""


def _build_points(body_html: str) -> str:
    """<li> 항목 파싱 + 이모지 제거"""
    items = re.findall(r'<li>(.*?)</li>', body_html, re.DOTALL)
    result = ""
    for item in items:
        item = re.sub(r'[\U00010000-\U0010ffff]|[\u2600-\u27BF]', '', item)
        result += f"<li>{item.strip()}</li>\n"
    return result


def write_newsletter(stories: list) -> str | None:
    valid = [s for s in stories if s.get('deep_summary')]
    if not valid:
        print("❌ [Writer] 분석된 기사가 없어 작문을 건너뜁니다.")
        return None

    print(f"✍️  [Writer] Claude가 {len(valid)}개 기사 뉴스레터 작성 중...")

    payload = [
        {
            "title": s["title"],
            "score": s["score"],
            "comments": s["comments"],
            "analysis": s["deep_summary"],
        }
        for s in valid
    ]

    prompt = f"""
너는 토스의 UX 라이팅 가이드라인을 완벽히 숙지한 10년 차 시니어 소프트웨어 엔지니어이자,
동료 개발자들에게 인사이트를 전하는 다정한 뉴스레터 작가야.
Gemini가 분석한 내용을 바탕으로, 한국 개발자들이 출근길에 가볍게 읽으면서도
"와, 이건 진짜 내 업무에 도움 되겠다"라고 느낄 만한 뉴스레터를 써줘.

[토스 스타일 라이팅 가이드라인]
1. 쉬운 단어: 어려운 한자어 대신 대화하듯 쉬운 우리말을 써줘.
2. 명확한 가치: "이 기술이 나왔다"가 아니라 "이 기술로 업무가 이렇게 편해진다"는 가치 중심으로.
3. 리듬감 있는 문체: 짧고 간결하게, '~해요', '~죠', '~까요' 해요체를 써줘.
4. 솔직함과 위트: 엔지니어 고충에 공감하며 가벼운 위트를 섞어줘.

[주의사항]
- 이모티콘, 이모지, 특수문자(🔥✅❌💡 등)는 절대 사용하지 마.
- 텍스트와 <code> 태그만 사용해.

[콘텐츠 구성 규칙]
1. headline: 호기심 자극형 제목 (이모지 없이 텍스트만)
2. body: 핵심 3가지 <li> 포인트, 기술 용어는 <code> 태그로 강조
3. insight: 동료에게 해주는 진심 어린 조언 (이모지 없이 텍스트만)

[출력 형식] JSON만 출력, 다른 텍스트 없이:
{{
  "blocks": [
    {{
      "headline": "제목",
      "body": "<li>요약1</li><li>요약2</li><li>요약3</li>",
      "insight": "조언"
    }}
  ]
}}

데이터: {json.dumps(payload, ensure_ascii=False)}"""

    try:
        response = completion(
            model=WRITER_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=3000,
        )

        raw = response.choices[0].message.content
        print(f"  ✅ Claude 응답 수신 ({len(raw)}자)")

        json_match = re.search(r'\{.*\}', raw, re.DOTALL)
        if not json_match:
            raise ValueError("응답에서 JSON 구조를 찾을 수 없습니다.")

        data = json.loads(json_match.group())
        today = datetime.now().strftime("%Y.%m.%d")

        blocks_html = ""
        for i, b in enumerate(data.get('blocks', [])):
            s = valid[i]
            blocks_html += CARD_TEMPLATE.format(
                wave_num=str(i + 1).zfill(2),
                score=s['score'],
                comments=s['comments'],
                headline=b['headline'],
                points=_build_points(b['body']),
                insight=b['insight'],
            )

        html = HTML_TEMPLATE.format(date=today, news_blocks=blocks_html)
        print(f"  ✅ FIRSTWAVE HTML 생성 완료 ({len(html)}자)")
        return html

    except Exception as e:
        print(f"  ❌ [Writer] 작문 실패: {e}")
        return None
