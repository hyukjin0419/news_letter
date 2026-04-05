import json
import re
from datetime import datetime
from litellm import completion

WRITER_MODEL = "anthropic/claude-sonnet-4-6"

# ─────────────────────────────────────────
# 로고 정의
# ─────────────────────────────────────────

LOGO_EMAIL = """<img src="https://raw.githubusercontent.com/hyukjin0419/news_letter/main/assets/logo.svg"
     width="120" height="50" alt="FIRSTWAVE" style="display:block;" />"""

LOGO_PREVIEW = """<img src="https://raw.githubusercontent.com/hyukjin0419/news_letter/main/assets/logo.svg"
     width="120" height="50" alt="FIRSTWAVE" style="display:block;" />"""


# ─────────────────────────────────────────
# HTML 템플릿
# ─────────────────────────────────────────

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>FIRSTWAVE · {date}</title>
</head>
<body style="margin:0;padding:0;background-color:#f5f5f5;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif;">

<table width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color:#f5f5f5;">
  <tr>
    <td align="center" style="padding:32px 16px;">
      <table width="600" cellpadding="0" cellspacing="0" border="0" style="max-width:600px;width:100%;">

        <!-- HEADER -->
        <tr>
          <td style="background-color:#ffffff;border:1px solid #e5e5e5;border-radius:12px;padding:28px 28px 22px;">
            <table width="100%" cellpadding="0" cellspacing="0" border="0">
              <tr>
                <td>
                  <!-- H-LOGO -->
                  {logo}
                </td>
                <td align="right" valign="top">
                  <!-- H-DATE -->
                  <span style="font-size:11px;color:#999999;">{date}</span>
                </td>
              </tr>
            </table>
            <!-- H-DIVIDER -->
            <div style="height:1px;background-color:#f0f0f0;margin:16px 0;"></div>
            <!-- H-TITLE -->
            <p style="margin:0 0 8px 0;font-size:22px;font-weight:600;color:#000000;line-height:1.35;">오늘의 기술 첫 번째 파도,<br>가장 먼저 전해드려요</p>
            <!-- H-SUB -->
            <p style="margin:0;font-size:13px;color:#666666;">매일 오전 8시 &middot; HN 상위 3개 엄선</p>
          </td>
        </tr>

        <tr><td style="height:10px;"></td></tr>

        <!-- CARDS -->
        {news_blocks}

        <!-- FOOTER -->
        <tr>
          <td style="background-color:#ffffff;border:1px solid #e5e5e5;border-radius:12px;padding:16px 28px;">
            <table width="100%" cellpadding="0" cellspacing="0" border="0">
              <tr>
                <!-- F-TEXT -->
                <td><span style="font-size:11px;color:#999999;">FIRSTWAVE &middot; 매일 오전 8시 발신</span></td>
                <!-- F-LIVE -->
                <td align="right">
                  <span style="display:inline-block;width:6px;height:6px;background-color:#000000;border-radius:50%;vertical-align:middle;margin-right:5px;"></span>
                  <span style="font-size:11px;color:#000000;font-weight:500;vertical-align:middle;">오늘 발행</span>
                </td>
              </tr>
            </table>
          </td>
        </tr>

      </table>
    </td>
  </tr>
</table>
</body>
</html>"""

CARD_TEMPLATE = """
        <tr>
          <td style="background-color:#ffffff;border:1px solid #e5e5e5;border-radius:12px;padding:22px 28px;">
            <!-- C-BADGE + C-META -->
            <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-bottom:12px;">
              <tr>
                <td><span style="font-size:11px;font-weight:600;color:#000000;letter-spacing:0.06em;">WAVE {wave_num}</span></td>
                <td align="right">
                  <span style="font-size:11px;color:#999999;">{score} pts</span>
                  <span style="font-size:11px;color:#cccccc;margin:0 4px;">&middot;</span>
                  <span style="font-size:11px;color:#999999;">{comments} comments</span>
                </td>
              </tr>
            </table>
            <!-- C-TITLE -->
            <p style="margin:0 0 14px 0;font-size:16px;font-weight:600;color:#000000;line-height:1.45;">{headline}</p>
            <!-- C-DIVIDER -->
            <div style="height:1px;background-color:#f0f0f0;margin-bottom:14px;"></div>
            <!-- C-POINTS -->
            <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-bottom:16px;">
              {points_rows}
            </table>
            <!-- C-INSIGHT -->
            <table width="100%" cellpadding="0" cellspacing="0" border="0">
              <tr>
                <td style="background-color:#fafafa;border:1px solid #eaeaea;border-radius:8px;padding:14px 16px;">
                  <!-- C-INSIGHT-LABEL -->
                  <p style="margin:0 0 5px 0;font-size:11px;font-weight:600;color:#000000;">우리가 챙겨갈 점</p>
                  <!-- C-INSIGHT-TEXT -->
                  <p style="margin:0;font-size:12px;color:#666666;line-height:1.65;">{insight}</p>
                </td>
              </tr>
            </table>
          </td>
        </tr>
        <tr><td style="height:10px;"></td></tr>"""

POINT_ROW_TEMPLATE = """
              <tr>
                <td width="16" valign="top" style="padding-top:10px;">
                  <!-- C-POINT-DASH -->
                  <div style="width:10px;height:1px;background-color:#dddddd;"></div>
                </td>
                <td style="padding:4px 0 4px 4px;font-size:13px;color:#444444;line-height:1.6;">{point_text}</td>
              </tr>"""


def _build_points_rows(body_html: str) -> str:
    items = re.findall(r'<li>(.*?)</li>', body_html, re.DOTALL)
    rows = ""
    for item in items:
        item = re.sub(r'[\U00010000-\U0010ffff]|[\u2600-\u27BF]', '', item)
        item = re.sub(
            r'<code>(.*?)</code>',
            r'<span style="background-color:#f5f5f5;color:#000000;font-size:11px;padding:1px 5px;border-radius:3px;border:1px solid #e5e5e5;font-family:Courier New,monospace;">\1</span>',
            item
        )
        rows += POINT_ROW_TEMPLATE.format(point_text=item.strip())
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
        today = datetime.now().strftime("%Y.%m.%d")

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
            logo=LOGO_EMAIL,
        )
        print(f"  ✅ FIRSTWAVE 이메일 HTML 생성 완료 ({len(html)}자)")
        return html

    except Exception as e:
        print(f"  ❌ [Writer] 작문 실패: {e}")
        return None
