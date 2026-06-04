# Stock Market Analyzer 구현 프롬프트용 계획서

이 문서는 다른 Codex/LLM 프롬프트에 그대로 넘겨 실제 구현을 시킬 수 있도록 만든 실행 계획이다. 목표는 `open-trading-api`를 직접 고치지 않고, submodule처럼 읽어 쓰는 외부 재료로 두며, 내 분석 앱의 코드 패턴을 처음부터 확장 가능하게 잡는 것이다.

## 0. 최종 방향

추천 구조는 다음과 같다.

- `open-trading-api/`: 한국투자증권 Open API 샘플 코드. 가능하면 수정하지 않는다.
- `kis-ai-extensions/`: KIS Open API를 AI agent가 안전하게 쓰도록 돕는 플러그인/스킬/명령 모음. 앱 런타임에 직접 의존하기보다는 개발 자동화, 인증 점검, 안전 규칙, 향후 전략/백테스트 기능 참고 자료로 활용한다.
- `app/backend/`: FastAPI 기반 분석 API 서버.
- `app/frontend/`: Next.js 기반 웹 UI.
- `app/backend/services/`: 외부 API와 비즈니스 로직을 감싸는 서비스 계층.
- `app/backend/features/`: 기능 단위 orchestration. 예: `screener`, `news`, `dart`, `chart`, `monitor`.
- `app/backend/storage/`: SQLite 또는 PostgreSQL 저장소.
- `app/backend/jobs/`: 장중 모니터링, 예약 수집, 알림 같은 백그라운드 작업.

비유하면 `open-trading-api`는 공구함이고, `app/`은 실제 작업대다. 공구함 자체를 개조하지 않고, 작업대에서 공구를 꺼내 쓰는 방식으로 만든다.

### 0.1 kis-ai-extensions 검토 결과

`kis-ai-extensions`는 주식 데이터 조회용 도메인 라이브러리라기보다, `open-trading-api`를 AI coding agent가 안전하게 다루도록 돕는 개발 보조 플러그인이다.

확인된 구성:

- `agents/codex`, `agents/claude`, `agents/cursor`, `agents/gemini`: AI agent별 설정, 명령, 스킬, 규칙.
- `shared/scripts/auth.py`, `do_auth.py`, `setup_check.py`, `api_client.py`: KIS 인증 상태 확인, 인증 실행, 환경 진단, 계좌/보유종목/지수 조회 스크립트.
- `shared/skills/kis-strategy-builder`, `kis-backtester`, `kis-order-executor`: 전략 설계, 백테스트, 주문 실행용 agent skill.
- `shared/hooks/*guard*`: appkey, appsecret, token 노출 방지와 실전 주문 보호 목적의 훅 템플릿.
- `package.json`: `@koreainvestment/kis-quant-plugin` 형태의 npm CLI 패키지.

활용 판단:

| 구분 | 판단 | 이유 |
| --- | --- | --- |
| 앱 런타임 의존성 | 보류 | 웹 앱의 screener/news/DART/chart 기능을 직접 제공하는 Python 패키지는 아니다. |
| 개발 보조 도구 | 활용 | 인증 확인, 환경 진단, agent 안전 규칙, 스킬 문서는 구현 프롬프트 품질을 높인다. |
| 향후 전략/백테스트 기능 | 활용 후보 | `kis-strategy-builder`, `kis-backtester` 스킬과 MCP 흐름은 차트 조건식/전략 검증 기능과 맞닿아 있다. |
| 실전 주문 자동화 | MVP 제외 | 현재 목표는 분석/보고서/알림이며 주문 실행은 안전 요구사항이 크므로 별도 단계로 둔다. |

따라서 `kis-ai-extensions`도 submodule처럼 보관하되, `app/backend`에서 직접 import하는 핵심 의존성으로 삼지 않는다. 대신 개발 agent에게 `/kis-setup`, `/auth`, 안전 규칙, strategy/backtest 스킬을 참고시키는 방식으로 사용한다.

## 1. 코드 패턴 원칙

### 1.1 외부 API는 무조건 Adapter로 감싼다

직접 `open-trading-api` 함수를 UI 라우터에서 호출하지 않는다.

나쁜 예:

```python
# router에서 바로 외부 샘플 함수 호출
df = volume_rank(...)
```

좋은 예:

```python
# router -> feature service -> adapter -> open-trading-api
result = screener_service.find_unusual_stocks(request)
```

권장 계층:

```text
frontend page
  -> backend router
    -> feature service
      -> adapter/service
        -> external API
```

이렇게 해야 나중에 DART, 증권사 리포트, Telegram, LLM, 다른 데이터 공급자를 붙여도 패턴이 무너지지 않는다.

### 1.2 기능별 폴더는 "입력, 처리, 출력"이 보이게 만든다

예시:

```text
app/backend/features/screener/
  schemas.py       # Request/Response 모델
  service.py       # 기능 흐름 조립
  normalizer.py    # DataFrame/API 응답을 내부 표준 모델로 변환
  prompts.py       # LLM 프롬프트가 있다면 여기에 배치
```

### 1.3 외부 API별 Adapter를 분리한다

```text
app/backend/services/
  kis/
    adapter.py
    models.py
    rate_limit.py
  news/
    adapter.py
    models.py
  dart/
    adapter.py
    parser.py
    models.py
  llm/
    adapter.py
    prompts.py
    schemas.py
  telegram/
    adapter.py
```

### 1.4 kis-ai-extensions는 개발 보조 계층으로 둔다

`kis-ai-extensions/shared/scripts`의 인증/진단 스크립트는 앱 내부 서비스의 정식 구현체로 복사하지 않는다. 대신 다음 용도로만 쓴다.

- 개발 시작 전 환경 점검: `setup_check.py`의 체크 항목을 참고해 `docs/setup.md`와 `/api/health` 진단 항목을 설계한다.
- 인증 상태 확인: `auth.py`, `do_auth.py`의 민감정보 비노출 패턴을 `services/kis/auth_status.py` 구현에 참고한다.
- 안전 규칙: secret guard, prod guard, trade log 개념을 우리 프로젝트의 agent 지시문과 CI secret scan에 반영한다.
- 전략/백테스트 확장: `kis-strategy-builder`, `kis-backtester` skill의 YAML/조건식 규칙을 차트 조건식 DSL과 향후 백테스트 기능 설계에 참고한다.

앱 런타임에서 직접 필요한 KIS 데이터 조회는 여전히 `services/kis/adapter.py`가 담당한다.

각 adapter는 외부 API의 지저분한 응답을 내부에서 쓰기 쉬운 모델로 바꿔서 돌려준다.

### 1.5 데이터 모델은 처음부터 표준화한다

기능이 늘어도 공통으로 쓰는 모델은 하나로 유지한다.

```python
class StockIdentity(BaseModel):
    code: str
    name: str | None = None
    market: str | None = None

class TradingDayStockEvent(BaseModel):
    trade_date: date
    stock: StockIdentity
    event_type: Literal["HIGH_VOLUME", "UPPER_LIMIT", "CONDITION_MATCH"]
    price: int | None = None
    change_rate: float | None = None
    volume: int | None = None
    source: str

class ArticleItem(BaseModel):
    title: str
    url: str
    publisher: str | None = None
    published_at: datetime | None = None
    summary: str | None = None

class AnalysisReport(BaseModel):
    stock: StockIdentity
    base_date: date
    report_type: Literal["NEWS_PRICE", "DART_PRICE", "CHART", "COMPOSITE"]
    key_points: list[str]
    possible_reasons: list[str]
    risks: list[str]
    confidence: Literal["LOW", "MEDIUM", "HIGH"]
    sources: list[str]
```

### 1.6 LLM 출력은 반드시 JSON Schema로 받는다

LLM은 문장으로 길게 쓰게 두지 않는다. 아래처럼 정해진 구조만 받는다.

```json
{
  "summary": "한 문장 요약",
  "key_points": ["핵심 근거 1", "핵심 근거 2"],
  "possible_reasons": ["가능한 이유"],
  "risks": ["주의점"],
  "confidence": "LOW|MEDIUM|HIGH"
}
```

분석 문구에는 항상 다음 원칙을 적용한다.

- 투자 조언처럼 단정하지 않는다.
- "가능성이 있다", "확인 필요" 표현을 쓴다.
- 근거 데이터가 없는 내용은 쓰지 않는다.
- 출처가 기사인지, DART인지, 가격 데이터인지 구분한다.

## 2. 현재 요구 기능 구현 계획

### 기능 A. 날짜별 거래량 1000만 주 이상 / 상한가 종목 표

사용 후보:

- `open-trading-api/examples_user/domestic_stock/domestic_stock_functions.py`
- `volume_rank`: 거래량 순위 조회
- `capture_uplowprice`: 상한가/하한가 포착
- `chk_holiday`: 국내 휴장일 조회
- `inquire_daily_itemchartprice`: 개별 종목 일봉 확인

구현 흐름:

1. 사용자가 단일 거래일 또는 기간을 입력한다.
2. `TradingCalendarService`가 실제 거래일 목록으로 바꾼다.
3. 각 거래일마다 `KisMarketAdapter.get_volume_rank()`를 호출한다.
4. 거래량이 10,000,000 이상인 종목만 필터링한다.
5. 각 거래일마다 `KisMarketAdapter.get_upper_limit_stocks()`를 호출한다.
6. 두 결과를 `TradingDayStockEvent`로 표준화한다.
7. 같은 종목이 두 조건을 동시에 만족하면 태그를 병합한다.
8. 결과를 DB에 캐시하고 웹 표로 보여준다.

API 설계:

```text
GET /api/screener/events?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD&min_volume=10000000
GET /api/screener/events/{event_id}
```

UI:

- 날짜 선택: 단일일/기간
- 필터: 거래량 기준, 상한가 포함 여부
- 표: 날짜, 종목명, 종목코드, 조건, 거래량, 등락률, 종가
- 액션: 기사 검색, LLM 분석, CSV 다운로드

### 기능 B. 종목별 기사 검색

사용 후보:

- Naver Search API
- Google Custom Search API
- RSS 기반 검색
- `httpx`, `feedparser`, `trafilatura`

구현 흐름:

1. 종목명과 종목코드를 받는다.
2. 기준일과 전날을 검색 범위로 잡는다.
3. 검색어는 `"{종목명} 주가"`, `"{종목명} 실적"`, `"{종목명} 공시"`처럼 여러 개를 만든다.
4. URL 기준으로 중복을 제거한다.
5. 제목, 언론사, 게시일, 링크, 요약을 저장한다.
6. 기사 원문 수집이 가능한 경우에만 본문을 추출한다.

API 설계:

```text
GET /api/news/search?stock_code=005930&base_date=YYYY-MM-DD
POST /api/news/refresh
```

UI:

- 종목별 기사 목록
- 기준일/전일 탭
- 제목, 언론사, 시간, 링크
- LLM에 포함할 기사 선택 체크박스

### 기능 C. LLM 기반 짧은 정형 보고서

사용 후보:

- `openai` Python SDK 또는 선택한 LLM SDK
- `pydantic` JSON 검증

구현 흐름:

1. 가격/거래량 이벤트, 기사 목록, 필요하면 일봉 데이터를 모은다.
2. LLM 프롬프트에 "정형 보고서만 작성" 규칙을 넣는다.
3. JSON Schema로 응답을 받는다.
4. 응답 검증 실패 시 1회 재시도한다.
5. DB에 보고서를 저장한다.
6. UI에서는 짧은 카드형 보고서로 보여준다.

API 설계:

```text
POST /api/reports/news-price
GET /api/reports/{report_id}
```

보고서 예시:

```text
종목: 삼성전자(005930)
관찰일: 2026-05-29
움직임: 거래량 1,250만 주, 전일 대비 +7.2%
가능한 이유: 반도체 업황 개선 기사와 기관 수급 기대가 함께 관찰됨
주의점: 기사 기반 추정이며 다음 거래일 거래량 지속 여부 확인 필요
```

## 3. 추가 기능 확장 계획

아래 기능들은 지금 아키텍처에 같이 반영한다. 다만 실제 구현 스프린트는 난이도와 API 선택에 따라 나눈다.

### 추가 기능 1. DART 보고서 섹션 조회 + 종합 분석

난이도: 중간

이유:

- DART API 연동 자체는 어렵지 않다.
- 어려운 부분은 사업보고서/분기보고서의 HTML 또는 XML에서 "관심 섹션"을 안정적으로 찾는 일이다.
- 회사명과 종목코드를 DART의 `corp_code`로 매핑해야 한다.

필요 API 후보:

- OpenDART 기업개황
- OpenDART 공시검색
- OpenDART 공시서류 원본파일
- OpenDART 고유번호 목록

권장 구현 범위:

Sprint 1차에서는 "공시 목록 조회 + 원문 링크/파일 저장"까지만 한다.
Sprint 2차에서 "관심 섹션 추출"을 붙인다.
Sprint 3차에서 "주가 + 기사 + DART + 리서치 리포트 종합 LLM 분석"으로 확장한다.

관심 섹션 예시:

- 사업의 내용
- 주요 제품 및 서비스
- 매출 및 수주상황
- 위험요소
- 연구개발
- 재무에 관한 사항

폴더:

```text
app/backend/services/dart/
  adapter.py          # OpenDART API 호출
  corp_code.py        # 종목코드 -> corp_code 매핑
  parser.py           # 보고서 원문 파싱
  section_finder.py   # 관심 섹션 추출
  models.py

app/backend/features/dart_report/
  service.py
  schemas.py
  prompts.py
```

API 설계:

```text
GET /api/dart/companies/{stock_code}
GET /api/dart/filings?stock_code=005930&from=YYYY-MM-DD&to=YYYY-MM-DD
GET /api/dart/filings/{rcept_no}/sections
POST /api/reports/composite
```

UI:

- 종목 입력
- 공시 목록
- 보고서 선택
- 관심 섹션 체크박스
- 섹션 본문 보기
- 종합 분석 버튼

구체화가 더 필요한 것:

- 관심 섹션 목록을 사용자가 직접 고를지, 기본 프리셋을 둘지 결정
- 증권사 리서치 리포트 API 공급자 결정
- 원문 저장 정책 결정

판단:

- 아키텍처에는 지금 포함한다.
- 실제 구현은 핵심 기능 A/B/C 이후 별도 스프린트로 진행한다.

### 추가 기능 2. 차트 분석 + 조건식 검색 + LLM 조건식 생성

난이도: 중간에서 높음

이유:

- 일봉 데이터 조회는 어렵지 않다.
- 사용자가 쉽게 조건식을 입력하게 만드는 DSL 설계가 중요하다.
- LLM이 만든 조건식은 반드시 검증하고 샌드박스에서 실행해야 한다.

사용 후보:

- KIS 일봉 API: `inquire_daily_itemchartprice`
- 기존 `strategy_builder/core/indicators.py`
- `pandas`, `numpy`
- 조건식 파서: `lark` 또는 제한된 JSON DSL

권장 조건식 방식:

처음에는 Python 문자열을 직접 실행하지 않는다. JSON DSL을 쓴다.

예시:

```json
{
  "all": [
    {"indicator": "volume", "op": ">", "value": 10000000},
    {"indicator": "close", "op": ">", "indicator_right": "ma20"},
    {"indicator": "rsi14", "op": "<", "value": 70}
  ]
}
```

나중에 사람이 쓰기 쉬운 문법을 추가한다.

```text
volume > 10000000 AND close > ma20 AND rsi14 < 70
```

LLM 조건식 생성 흐름:

1. 사용자가 자연어로 말한다. 예: "거래량이 갑자기 늘고 20일선 위로 올라온 종목 찾아줘"
2. LLM이 JSON DSL을 생성한다.
3. 서버가 DSL을 스키마로 검증한다.
4. 허용된 지표와 연산자만 실행한다.
5. 조건식 결과를 표와 차트에 표시한다.

폴더:

```text
app/backend/services/chart/
  data.py             # 일봉/분봉 조회
  indicators.py       # 이동평균, RSI, 거래량 변화율
  condition_schema.py # JSON DSL 스키마
  evaluator.py        # 조건식 실행

app/backend/features/chart_search/
  service.py
  schemas.py
  prompts.py          # 자연어 -> 조건식 프롬프트
```

API 설계:

```text
GET /api/charts/{stock_code}/daily?days=240
POST /api/chart-search/evaluate
POST /api/chart-search/generate-condition
```

UI:

- 종목 입력
- 기간 선택
- 조건식 빌더
- 자연어로 조건식 만들기
- 결과 차트
- 조건 만족 날짜 표시

구체화가 더 필요한 것:

- 검색 대상: 전체 코스피/코스닥인지, 관심 종목 목록인지
- 데이터 주기: 일봉만 할지, 분봉까지 할지
- 지표 목록: MVP에서 지원할 지표 범위

판단:

- 기반 설계는 지금 포함한다.
- 전체 시장 검색은 API 호출량이 많으므로 MVP에서는 관심 종목 또는 스크리너 결과 종목만 대상으로 시작한다.

### 추가 기능 3. 실시간 시장 모니터링 + Telegram 알림

난이도: 중간에서 높음

이유:

- Telegram 알림 전송은 쉽다.
- 장중 실시간 데이터 수신, 조건식 평가, 중복 알림 방지가 핵심이다.
- 한국투자증권 WebSocket 인증과 연결 안정성 관리가 필요하다.

사용 후보:

- `open-trading-api/examples_user/domestic_stock/domestic_stock_functions_ws.py`
- `open-trading-api/strategy_builder/core/websocket_manager.py`
- Telegram Bot API `sendMessage`
- `asyncio`, `websockets`, `apscheduler` 또는 FastAPI lifespan task

구현 흐름:

1. 사용자가 감시할 종목 목록과 조건식을 저장한다.
2. 장 시작 전에 WebSocket 구독을 시작한다.
3. 실시간 체결/호가 데이터를 내부 이벤트로 변환한다.
4. 조건식을 평가한다.
5. 조건 만족 시 Telegram으로 알림을 보낸다.
6. 같은 조건은 일정 시간 동안 다시 보내지 않는다.
7. 장 종료 후 연결을 정리한다.

폴더:

```text
app/backend/services/realtime/
  kis_ws.py
  event_bus.py
  monitor_engine.py
  dedupe.py

app/backend/services/telegram/
  adapter.py

app/backend/features/monitor/
  service.py
  schemas.py
```

API 설계:

```text
GET /api/monitors
POST /api/monitors
PATCH /api/monitors/{monitor_id}
DELETE /api/monitors/{monitor_id}
POST /api/monitors/{monitor_id}/test-alert
```

UI:

- 감시 조건 목록
- 종목 선택
- 조건식 선택
- Telegram 테스트 발송
- 알림 로그
- 활성/비활성 토글

구체화가 더 필요한 것:

- 실시간 조건식은 현재가 기준인지, 분봉 완성 기준인지
- 알림 빈도 제한 기준
- 감시 종목 수 제한
- 장중 서버를 계속 켜둘 환경

판단:

- Telegram adapter와 monitor 데이터 모델은 미리 설계한다.
- 실제 실시간 WebSocket 모니터링은 차트 조건식 엔진이 안정된 뒤 진행한다.

## 4. 스프린트 계획

### Sprint 0. 프로젝트 뼈대와 패턴 확정

목표:

- submodule 방식 확정
- FastAPI/Next.js 앱 생성
- 공통 모델, adapter 패턴, 에러 처리, 환경 변수 구조 확정

작업:

- `app/backend`, `app/frontend` 생성
- `services/kis/adapter.py` 생성
- `features/screener` 생성
- `kis-ai-extensions`의 `/kis-setup`, `/auth`, secret/prod guard 개념을 개발 체크리스트에 반영
- `.env.example` 작성
- API 키는 절대 코드에 넣지 않기

완료 기준:

- `/api/health` 응답
- KIS 인증 설정 가이드 문서화
- adapter를 통한 샘플 API 1개 호출 가능

### Sprint 1. 거래량/상한가 스크리너

목표:

- 날짜/기간 입력으로 거래량 1000만 주 이상 종목과 상한가 종목을 표로 조회

작업:

- 거래일 계산
- `volume_rank` adapter
- `capture_uplowprice` adapter
- 결과 표준화
- SQLite 캐시
- CSV 다운로드

완료 기준:

- 하루 조회 가능
- 기간 조회 가능
- 거래량/상한가 태그 표시

### Sprint 2. 웹 UI 1차

목표:

- 브라우저에서 스크리너를 실제로 사용 가능하게 만들기

작업:

- 날짜 선택 UI
- 결과 테이블
- 조건 필터
- 로딩/에러 상태
- 종목 상세 패널

완료 기준:

- 사용자가 날짜를 넣고 결과를 볼 수 있음
- 결과에서 기사 검색으로 넘어갈 수 있음

### Sprint 3. 기사 검색

목표:

- 스크리너 결과 종목 또는 직접 입력 종목의 기준일/전일 기사 조회

작업:

- News adapter
- 중복 제거
- 날짜 필터
- 기사 선택 UI
- 기사 캐시

완료 기준:

- 종목별 기사 목록 표시
- LLM 분석에 넣을 기사 선택 가능

### Sprint 4. LLM 뉴스/가격 분석 보고서

목표:

- 주가 움직임과 기사 기반 정형 보고서 생성

작업:

- LLM adapter
- JSON Schema 응답 검증
- 뉴스+가격 프롬프트
- 보고서 저장
- 보고서 카드 UI

완료 기준:

- 종목 1개에 대해 짧은 보고서 생성
- 근거 기사 링크 표시

### Sprint 5. DART 1차

목표:

- 종목별 DART 공시 목록과 보고서 원문 접근 준비

작업:

- OpenDART API 키 설정
- corp_code 매핑
- 공시 목록 조회
- 보고서 원문 파일 저장
- 웹에서 공시 목록 표시

완료 기준:

- 종목코드로 최근 사업/분기/반기보고서 목록 조회
- 원문 링크 또는 원문 파일 접근 가능

### Sprint 6. DART 섹션 추출 + 종합 보고서

목표:

- 관심 섹션만 웹에서 보고, LLM 종합 분석에 포함

작업:

- 보고서 파서
- 관심 섹션 추출
- 섹션 선택 UI
- DART+가격+뉴스 종합 프롬프트

완료 기준:

- 사용자가 관심 섹션을 고를 수 있음
- 섹션 기반 종합 보고서 생성

### Sprint 7. 차트 조건식 MVP

목표:

- 일봉 데이터 기반 조건식 검색

작업:

- 차트 데이터 adapter
- 기본 지표: MA, RSI, 거래량 변화율, 등락률
- JSON DSL
- 조건식 evaluator
- 조건 만족 날짜 표시

완료 기준:

- 지정 종목에 대해 조건식 평가 가능
- 차트에서 만족 날짜 확인 가능

### Sprint 8. LLM 조건식 생성

목표:

- 자연어로 조건식을 만들고 검증

작업:

- 자연어 -> JSON DSL 프롬프트
- DSL 검증
- 미리보기/수정 UI
- 조건식 저장

완료 기준:

- "거래량이 늘고 20일선 위" 같은 자연어를 조건식으로 변환
- 변환된 조건식 실행 가능

### Sprint 9. 실시간 모니터링 + Telegram

목표:

- 장중 조건 만족 시 Telegram 알림

작업:

- Telegram adapter
- KIS WebSocket 연결
- monitor engine
- 중복 알림 방지
- 알림 로그

완료 기준:

- 테스트 알림 발송 가능
- 실시간 조건 만족 시 알림 발송

## 5. 개발자가 지켜야 할 구현 규칙

### 5.1 라우터는 얇게 유지한다

라우터는 request validation과 service 호출만 한다. 비즈니스 로직은 feature service에 둔다.

```python
@router.get("/events")
async def get_events(query: ScreenerQuery):
    return await screener_service.find_events(query)
```

### 5.2 pandas DataFrame은 service 밖으로 최대한 내보내지 않는다

외부 API adapter 안에서는 DataFrame을 써도 되지만, 라우터 응답은 Pydantic 모델 또는 dict/list로 변환한다.

### 5.3 모든 외부 호출은 timeout, retry, rate limit을 가진다

적용 대상:

- KIS REST
- KIS WebSocket 재연결
- News API
- DART API
- LLM API
- Telegram API

### 5.4 캐시 우선

같은 날짜, 같은 종목, 같은 기사, 같은 보고서는 DB 캐시를 먼저 확인한다.

캐시 키 예시:

```text
screener:{date}:{min_volume}
news:{stock_code}:{base_date}
dart:{stock_code}:{rcept_no}
report:{report_type}:{stock_code}:{base_date}:{source_hash}
```

### 5.5 테스트는 adapter mock 중심으로 작성한다

실제 외부 API를 테스트마다 호출하지 않는다.

테스트 대상:

- 거래일 범위 계산
- 거래량 필터링
- 상한가/거래량 결과 병합
- 기사 중복 제거
- LLM JSON 검증
- 조건식 evaluator
- Telegram 중복 알림 방지

## 6. 환경 변수 초안

```env
APP_ENV=local
DATABASE_URL=sqlite:///./data/analyzer.sqlite

KIS_CONFIG_PATH=~/KIS/config/kis_devlp.yaml

NEWS_PROVIDER=naver
NAVER_CLIENT_ID=
NAVER_CLIENT_SECRET=

OPENDART_API_KEY=

LLM_PROVIDER=openai
OPENAI_API_KEY=
LLM_MODEL=

TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
```

## 7. MVP에서 하지 말 것

초기 구현에서 피할 것:

- 전체 한국 시장 전 종목을 매일 무제한으로 조회
- 사용자가 입력한 Python 코드를 그대로 실행
- LLM 분석을 투자 추천처럼 표현
- API 키를 프론트엔드에 노출
- 원본 `open-trading-api` 파일을 대량 수정
- `kis-ai-extensions`를 앱 런타임 핵심 의존성으로 직접 import
- 실시간 모니터링을 조건식 엔진보다 먼저 구현

## 8. 다음 구현 프롬프트에 넣을 핵심 지시문

아래 문장을 실제 구현 프롬프트에 포함한다.

```text
open-trading-api는 외부 submodule처럼 취급하고 직접 수정하지 마라.
kis-ai-extensions는 앱 런타임 라이브러리가 아니라 AI agent용 개발 보조 플러그인으로 취급하라.
kis-ai-extensions의 setup/auth/secret guard/prod guard/strategy-backtest skill은 개발 체크리스트와 안전 규칙, 향후 백테스트 확장 설계에 참고하라.
app/backend와 app/frontend에 새 분석 앱을 만든다.
외부 API 호출은 services/*/adapter.py로 감싸고,
기능 흐름은 features/*/service.py에 둔다.
라우터는 얇게 유지하고, 응답은 Pydantic 모델로 표준화한다.
LLM 응답은 JSON Schema로 검증한다.
초기 MVP는 거래량/상한가 스크리너, 기사 검색, 뉴스+가격 정형 보고서까지 구현한다.
DART, 차트 조건식, 실시간 Telegram 모니터링은 같은 패턴으로 확장할 수 있게 폴더와 모델만 고려한다.
```

## 9. 외부 공식 문서 확인 대상

구현 직전에 아래 공식 문서를 최신 기준으로 확인한다.

- Korea Investment Open API: KIS 인증, 국내주식 REST, 국내주식 WebSocket
- OpenDART: 공시검색, 공시서류 원본파일, 고유번호 목록
- Telegram Bot API: `sendMessage`
- 선택한 LLM provider의 JSON/structured output 방식
