# FIRSTWAVE

> 기술의 파도가 본격적으로 덮쳐오기 전, 첫 파도를 읽고 준비해요.

매일 오전 8시, Hacker News 상위 기사를 AI가 분석해 핵심만 전달하는 한국 개발자 뉴스레터 서비스예요.

**[구독하기 →](https://hyukjin0419.github.io/news_letter/subscribe.html)**

---

## 어떻게 작동하나요?

```
HN 상위 기사 수집 (fetcher)
    ↓
Gemini로 기사 분석 (analyzer)
    ↓
Claude로 한국어 작문 (writer)
    ↓
구독자 전체 발송 (mailer)
    ↓
아카이브 저장 (archive)
```

매일 오전 8시, GitHub Actions가 자동으로 실행해요.

---

## 스택

| 역할 | 기술 |
|------|------|
| 기사 수집 | Hacker News API + trafilatura |
| 분석 | Google Gemini |
| 작문 | Anthropic Claude |
| 발송 | Gmail SMTP |
| 구독자 관리 | Google Sheets + Apps Script |
| 웹 | GitHub Pages |
| 자동화 | GitHub Actions |

---

## 프로젝트 구조

```
news_letter/
├── docs/                    # GitHub Pages
│   ├── index.html
│   ├── subscribe.html
│   ├── unsubscribe.html
│   ├── privacy.html
│   ├── terms_and_policy.html
│   ├── assets/
│   │   └── logo.svg
│   └── archive/
│       ├── index.html
│       ├── archive.json
│       └── sent_urls.json
├── skills/                  # 파이프라인
│   ├── fetcher01.py         # HN 기사 수집
│   ├── analyzer.py          # Gemini 분석
│   ├── writer.py            # Claude 작문 + HTML
│   ├── mailer.py            # Gmail 발송
│   ├── archive.py           # 아카이브 관리
│   ├── sheets.py            # 구독자 관리
│   ├── main.py              # 전체 파이프라인
│   └── main_single.py       # 단독 발송
└── .github/
    └── workflows/
        └── newsletter.yml   # 자동화
```