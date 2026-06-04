# Stock Market Analyzer

한국 주식 시장 분석 MVP — 거래량/상한가 스크리너, Naver 뉴스, LLM 정형 보고서.

## 구조

- `open-trading-api/` — KIS 샘플 (수정 금지)
- `kis-ai-extensions/` — 개발 보조 플러그인 (런타임 import 금지)
- `app/backend/` — FastAPI
- `app/frontend/` — Next.js

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
