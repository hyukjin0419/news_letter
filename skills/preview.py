"""
preview.py — API 호출 없이 디자인 확인용
더미 데이터로 newsletter_preview.html 생성 후 브라우저로 자동으로 열어줍니다.

실행: python preview.py
"""
import os
import webbrowser
from datetime import datetime
from writer import HTML_TEMPLATE, CARD_TEMPLATE, _build_points

DUMMY_BLOCKS = [
    {
        "wave_num": "01",
        "score": 289,
        "comments": 142,
        "headline": "Go의 nil을 없애버린 언어가 등장했어요",
        "body": (
            "<li>Hindley-Milner 타입 시스템으로 <code>nil</code>을 컴파일 타임에 완전 차단해요</li>"
            "<li>Go 패키지 그대로 <code>import \"go:fmt\"</code> 사용 가능, 결과물도 Go 코드예요</li>"
            "<li>문법은 Rust — <code>match</code>, <code>Result&lt;T,E&gt;</code>, 기본 불변 변수까지</li>"
        ),
        "insight": "nil 때문에 새벽에 슬랙 알림 받아본 적 있으신가요. Lisette의 접근법이 Go 생태계에서 자리잡는지 지켜볼 만해요.",
    },
    {
        "wave_num": "02",
        "score": 156,
        "comments": 89,
        "headline": "독일 정부가 모바일 앱 보안을 이렇게 검증해요",
        "body": (
            "<li>Android는 <code>KeyAttestation</code> + <code>PlayIntegrity</code>로 기기 무결성 검증해요</li>"
            "<li>iOS는 <code>AppAttest</code>로 Secure Enclave 기반 앱 서명을 확인해요</li>"
            "<li><code>RASP</code>로 런타임에도 지속적으로 앱 무결성을 모니터링해요</li>"
        ),
        "insight": "금융/공공 앱 개발한다면 이 아키텍처 참고할 만해요. 국내 전자서명 서비스에도 비슷한 흐름이 올 수 있어요.",
    },
    {
        "wave_num": "03",
        "score": 198,
        "comments": 64,
        "headline": "Screen Studio 대신 쓸 수 있는 무료 오픈소스 등장했어요",
        "body": (
            "<li><code>Electron</code> + <code>React</code> + <code>PixiJS</code> 스택으로 만든 화면 녹화 편집 툴이에요</li>"
            "<li>자동/수동 줌, 모션 블러, 어노테이션 등 핵심 기능은 다 있어요</li>"
            "<li>MIT 라이선스로 개인·상업용 모두 무료, 수정·배포도 자유로워요</li>"
        ),
        "insight": "Screen Studio가 비싸서 망설이고 계셨다면 한번 써볼 만해요. 베타라 버그가 있을 수 있으니 중요한 녹화엔 백업 준비해두세요.",
    },
]

if __name__ == "__main__":
    today = datetime.now().strftime("%Y.%m.%d")

    blocks_html = ""
    for b in DUMMY_BLOCKS:
        blocks_html += CARD_TEMPLATE.format(
            wave_num=b["wave_num"],
            score=b["score"],
            comments=b["comments"],
            headline=b["headline"],
            points=_build_points(b["body"]),
            insight=b["insight"],
        )

    html = HTML_TEMPLATE.format(date=today, news_blocks=blocks_html)

    output_path = "newsletter_preview.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"✅ 미리보기 생성 완료 → {output_path}")
    print("🌐 브라우저로 열게요...")
    webbrowser.open(f"file://{os.path.abspath(output_path)}")