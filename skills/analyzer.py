import json
from litellm import completion

ANALYZER_MODEL = "gemini/gemini-2.5-flash"


def _parse_json_response(raw: str) -> dict | None:
    try:
        clean = raw.strip()

        # 마크다운 코드블록 제거
        if "```json" in clean:
            clean = clean.split("```json")[1].split("```")[0].strip()
        elif "```" in clean:
            clean = clean.split("```")[1].split("```")[0].strip()

        # { } 블록만 추출
        start = clean.find("{")
        end = clean.rfind("}") + 1
        if start == -1 or end == 0:
            print(f"  ⚠️ JSON 블록을 찾을 수 없음")
            print(f"  ⚠️ 원본 응답 (앞 200자): {raw[:200]}")
            return None

        return json.loads(clean[start:end])

    except json.JSONDecodeError as e:
        print(f"  ⚠️ JSON 파싱 실패: {e}")
        print(f"  ⚠️ 원본 응답 (앞 200자): {raw[:200]}")
        return None

def _log_result(index: int, total: int, title: str, result: dict) -> None:
    """분석 결과 콘솔 출력"""
    sep = "─" * 60
    print(f"\n{sep}")
    print(f"📊 [{index}/{total}] {title}")
    print(sep)
    print(f"  📌 Summary    : {result.get('summary', 'N/A')}")
    print(f"  🛠  Stack      : {', '.join(result.get('stack', []))}")
    print(f"  💡 Key Points :")
    for i, point in enumerate(result.get('key_points', []), 1):
        print(f"      {i}. {point}")
    print(f"  ⚠️  Risk       : {result.get('risk', 'N/A')}")
    print(sep)


def deep_analyze_tech(stories: list) -> list:
    """
    Gemini로 기사 본문을 분석해 구조화된 JSON을 추출합니다.
    결과는 deep_summary(dict) 필드에 저장되어 Claude 작문 단계로 전달됩니다.
    """
    total = len(stories)
    print(f"\n🤖 [Analyzer] Gemini가 {total}개 기사 분석 시작...\n")

    success, fail = 0, 0

    for i, s in enumerate(stories, 1):
        print(f"  🔍 [{i}/{total}] 분석 중: {s['title'][:40]}...")

        prompt = (
            f"Summarize this tech article based only on facts. No hallucination. "
            f"Respond only in this JSON format:\n"
            f'{{"summary": "...", "stack": ["..."], "key_points": ["...", "...", "..."], "risk": "..."}}\n\n'
            f"Article:\n{s['link_content']}"
        )

        try:
            res = completion(
                model=ANALYZER_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=3000,
            )

            raw = res.choices[0].message.content
            parsed = _parse_json_response(raw)

            if parsed:
                s['deep_summary'] = parsed
                _log_result(i, total, s['title'], parsed)
                success += 1
            else:
                s['deep_summary'] = None
                fail += 1

        except Exception as e:
            print(f"  ❌ [{i}/{total}] API 호출 실패: {e}")
            s['deep_summary'] = None
            fail += 1

    print(f"\n{'═' * 60}")
    print(f"✅ 분석 완료 — 성공: {success}개 | 실패: {fail}개 | 전체: {total}개")
    print(f"{'═' * 60}\n")

    return stories
