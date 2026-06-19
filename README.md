# Stock Market Analyzer

한국 주식 시장 분석 MVP — 거래량/상한가 스크리너, Naver 뉴스, LLM 정형 보고서.

## 구조

- `open-trading-api/` — KIS 샘플 (수정 금지)
- `kis-ai-extensions/` — 개발 보조 플러그인 (런타임 import 금지)
- `app/backend/` — FastAPI
- `app/frontend/` — Next.js

## Agent Guidelines

- `CLAUDE.md` — Claude/LLM 공통 작업 원칙 (Karpathy 4원칙 + 프로젝트 제약)
- `CLAUDE.ko.md` — 위 원칙의 한국어 버전
- `.cursor/rules/karpathy-guidelines.mdc` — Cursor 프로젝트 규칙(always apply)
- `skills/karpathy-guidelines/SKILL.md` — 재사용 가능한 스킬 문서
- `CURSOR.md` — Cursor에서의 적용 방법
- `CURSOR.ko.md` — Cursor 적용 방법 한국어 안내

## 작업 템플릿

- `docs/backend-task-template.md` — 백엔드 작업 체크리스트 템플릿
- `docs/frontend-task-template.md` — 프론트엔드 작업 체크리스트 템플릿
- `.github/pull_request_template.md` — PR 작성 시 4원칙 검증 체크리스트

## 빠른 시작

```bash
# Backend
cd app/backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Frontend
cd app/frontend
npm install
npm run dev
```

자세한 설정: [docs/setup.md](docs/setup.md)

`.env.example`을 복사해 `.env`를 만드세요.

## API

- `GET /api/health`
- `GET /api/screener/events`
- `GET /api/news/search`
- `POST /api/reports/news-price`
