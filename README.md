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

### Backend — uv (권장, 타 PC 재현성)

[uv](https://docs.astral.sh/uv/)는 `requires-python`을 보고 인터프리터를 자동 선택/설치하고
`uv.lock`으로 동일 환경을 재현한다.

```bash
cd app/backend
uv sync                              # .venv 생성 + 잠긴 의존성 설치
uv run pytest -q                     # 테스트
uv run uvicorn main:app --reload --port 8000
```

### Backend — pip (대안)

```bash
cd app/backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

> ⚠️ 일부 Windows에서는 `python`이 Microsoft Store 스텁이라 동작하지 않는다. 이때는 `python3` 또는 uv 사용.

### Frontend

```bash
cd app/frontend
npm install
npm run dev
```

## 3대 에이전트 / 아키텍처

에이전트 시스템 설계·진행·검증 문서는 [docs/agents/](docs/agents/) 참조
([GOAL](docs/agents/GOAL.md) · [PLAN](docs/agents/PLAN.md) · [STATUS](docs/agents/STATUS.md) · [TEST](docs/agents/TEST.md)).

자세한 설정: [docs/setup.md](docs/setup.md)

`.env.example`을 복사해 `.env`를 만드세요.

## API

- `GET /api/health`
- `GET /api/screener/events`
- `GET /api/news/search`
- `POST /api/reports/news-price`
- `POST /api/strategy/causality` — 전략: 상한가/거래량 인과분석(CAN SLIM+맥락)
- `POST /api/briefing` — 시장판단: 타임라인별 메가 내러티브 브리핑
- `POST /api/monitor/daily-report` — 모니터링: 장마감 일일 리포트→맥락 역기록→텔레그램
