import json
import re
from datetime import datetime
from litellm import completion

WRITER_MODEL = "anthropic/claude-sonnet-4-6"
LOGO_URL = "https://raw.githubusercontent.com/hyukjin0419/news_letter/main/assets/logo.svg"
ARCHIVE_BASE_URL = "https://hyukjin0419.github.io/news_letter/archive"


HTML_TEMPLATE = """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
  <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>FIRSTWAVE · {date}</title>
</head>
<body style="margin:0;padding:0;background-color:#f0f0ee;font-family:Arial,sans-serif;-webkit-text-size-adjust:100%;-ms-text-size-adjust:100%;word-break:keep-all;">

  <div style="background-color:#f0f0ee;padding:36px 16px;">
    <div style="max-width:560px;margin:0 auto;width:100%;">

      <!-- ===== HEADER ===== -->
      <div style="background-color:#ffffff;border:1px solid #e0e0dc;border-radius:12px;padding:32px 36px 28px;margin-bottom:10px;">

        <!-- H-LOGO + H-DATE -->
        <div style="display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:20px;">
          <img src="{logo_url}" width="130" height="44" alt="FIRSTWAVE" style="display:block;border:0;" />
          <span style="font-size:11px;color:#aaaaaa;font-family:Arial,sans-serif;padding-top:4px;">{date}</span>
        </div>

        <!-- H-DIVIDER -->
        <div style="height:1px;background-color:#efefeb;margin-bottom:20px;">&nbsp;</div>

        <!-- H-TITLE -->
        <p style="margin:0 0 10px 0;font-size:24px;font-weight:700;color:#0a0a0a;line-height:1.3;letter-spacing:-0.02em;font-family:Arial,sans-serif;word-break:keep-all;">오늘의 기술 첫 번째 파도,<br/>가장 먼저 전해드려요</p>

        <!-- H-SUB -->
        <p style="margin:0;font-size:13px;color:#999999;font-family:Arial,sans-serif;">매일 오전 8시 &middot; HN 상위 3개 엄선</p>

      </div>

      <!-- ===== CARDS ===== -->
      {news_blocks}

      <!-- ===== FOOTER ===== -->
      <div style="background-color:#ffffff;border:1px solid #e0e0dc;border-radius:12px;padding:18px 36px;">
        <div style="display:flex;align-items:center;justify-content:space-between;">
          <span style="font-size:11px;color:#bbbbbb;font-family:Arial,sans-serif;">FIRSTWAVE &middot; 매일 오전 8시 발신</span>
          <span style="font-size:11px;color:#0a0a0a;font-weight:700;font-family:Arial,sans-serif;">&#9679; 오늘 발행</span>
        </div>
      </div>

    </div>
  </div>

</body>
</html>"""


CARD_TEMPLATE = """
      <!-- CARD -->
      <div style="background-color:#ffffff;border:1px solid #e0e0dc;border-radius:12px;padding:28px 36px;margin-bottom:10px;word-break:keep-all;">

        <!-- C-BADGE + C-META -->
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:14px;">
          <span style="font-size:11px;font-weight:700;color:#ffffff;background-color:#0a0a0a;letter-spacing:0.08em;font-family:Arial,sans-serif;padding:4px 10px;border-radius:4px;">WAVE {wave_num}</span>
          <span style="font-size:11px;color:#bbbbbb;font-family:Arial,sans-serif;">{score} pts &middot; {comments} comments</span>
        </div>

        <!-- C-TITLE -->
        <p style="margin:0 0 18px 0;font-size:17px;font-weight:700;color:#0a0a0a;line-height:1.45;letter-spacing:-0.01em;font-family:Arial,sans-serif;word-break:keep-all;">{headline}</p>

        <!-- C-DIVIDER -->
        <div style="height:1px;background-color:#f0f0ec;margin-bottom:18px;">&nbsp;</div>

        <!-- C-POINTS -->
        <div style="margin-bottom:20px;">
          {points_rows}
        </div>

        <!-- C-INSIGHT -->
        <div style="background-color:#f7f7f5;border-left:3px solid #0a0a0a;padding:16px 18px;border-radius:0 8px 8px 0;">
          <p style="margin:0 0 6px 0;font-size:12px;font-weight:700;color:#0a0a0a;letter-spacing:0.06em;font-family:Arial,sans-serif;">우리가 챙겨갈 점</p>
          <div style="height:1px;background-color:#e8e8e4;margin-bottom:8px;">&nbsp;</div>
          <p style="margin:0;font-size:13px;color:#555555;line-height:1.7;font-family:Arial,sans-serif;word-break:keep-all;">{insight}</p>
        </div>

      </div>"""


POINT_ROW_TEMPLATE = """
          <div style="display:flex;align-items:flex-start;padding:8px 0;border-bottom:1px solid #f5f5f3;">
            <span style="font-size:14px;color:#0a0a0a;margin-right:10px;margin-top:1px;flex-shrink:0;line-height:1.6;">&#8226;</span>
            <p style="margin:0;font-size:13px;color:#333333;line-height:1.7;font-family:Arial,sans-serif;word-break:keep-all;">{point_text}</p>
          </div>"""


def _build_points_rows(body_html: str) -> str:
    items = re.findall(r'<li>(.*?)</li>', body_html, re.DOTALL)
    rows = ""
    for i, item in enumerate(items):
        item = re.sub(r'[\U00010000-\U0010ffff]|[\u2600-\u27BF]', '', item)
        item = re.sub(
            r'<code>(.*?)</code>',
            r'<span style="background-color:#f0f0ee;color:#0a0a0a;font-size:11px;padding:2px 6px;border-radius:3px;font-family:Courier New,monospace;font-weight:700;">\1</span>',
            item
        )
        # 마지막 포인트는 border-bottom 없애기
        row = POINT_ROW_TEMPLATE.format(point_text=item.strip())
        if i == len(items) - 1:
            row = row.replace("border-bottom:1px solid #f5f5f3;", "border-bottom:none;")
        rows += row
    return rows


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
        today = datetime.now().strftime("%Y-%m-%d")

        blocks_html = ""
        for i, b in enumerate(data.get('blocks', [])):
            s = valid[i]
            blocks_html += CARD_TEMPLATE.format(
                wave_num=str(i + 1).zfill(2),
                score=s['score'],
                comments=s['comments'],
                headline=b['headline'],
                points_rows=_build_points_rows(b['body']),
                insight=b['insight'],
            )

        html = HTML_TEMPLATE.format(
            date=today,
            news_blocks=blocks_html,
            logo_url=LOGO_URL,
        )
        print(f"  ✅ FIRSTWAVE 이메일 HTML 생성 완료 ({len(html)}자)")
        return html

    except Exception as e:
        print(f"  ❌ [Writer] 작문 실패: {e}")
        return None