# TEST — 검증 매트릭스

> 원칙(CLAUDE.md §4, PLAN.md): adapter-mock 우선, 외부 API 실호출 금지, 단계별 인수기준 충족 시에만 🟢.

## 실행 방법
> `python`/`py`는 Windows Store 스텁이라 작동하지 않는다. **uv**(권장) 또는 `python3` 사용.
```bash
cd app/backend
uv sync                 # 환경 구성(타 PC 재현, uv.lock 사용)
uv run pytest -q        # 전체 테스트
uv run pytest tests/test_integration_loop.py -v   # 특정 모듈
```
대안(pip): `./.venv/Scripts/python.exe -m pytest -q`
> ✅ 최근 실행(2026-06-20, `python -m pytest`): `64 passed`.
> ✅ Frontend 최근 실행(2026-06-20, `npm run build`): 성공.

## 테스트 인벤토리
| 파일 | 대상 | 상태 |
|---|---|---|
| `tests/test_screener_normalizer.py` | 거래량 필터/병합 | 기존 🟢(작성됨) |
| `tests/test_trading_calendar.py` | 거래일 범위 | 기존 🟢 |
| `tests/test_llm_provider.py` | provider factory/검증 | 기존 🟢 |
| `tests/test_context_repository.py` | 맥락 저장소 CRUD (6) | Phase1 🟢 |
| `tests/test_context_service.py` | 맥락 조립/프롬프트 주입 (4) | Phase1 🟢 |
| `tests/test_chart_indicators.py` | 지표(순수 Pandas) (5) | Phase2 🟢 |
| `tests/test_chart_evaluator.py` | DSL 평가/검증 (5) | Phase2 🟢 |
| `tests/test_canslim.py` | CAN SLIM 정량필터 (3) | Phase2 🟢 |
| `tests/test_causality.py` | 인과분석 오케스트레이션 (2, fake LLM) | Phase2 🟢 |
| `tests/test_news_extractor.py` | Trafilatura 추출기 (6, 주입) | Phase3 🟢 |
| `tests/test_rss_adapter.py` | RSS 어댑터 (3, 주입) | Phase3 🟢 |
| `tests/test_briefing.py` | 타임라인 브리핑 (3, fake LLM) | Phase3 🟢 |
| `tests/test_telegram_adapter.py` | 텔레그램 dedupe/발송/에러 (5, fake client) | Phase4 🟢 |
| `tests/test_scheduler.py` | 낮/밤 잡 등록 (2) | Phase4 🟢 |
| `tests/test_monitor_pipeline.py` | 마감 리포트→역기록→발송 (2, fake) | Phase4 🟢 |
| `tests/test_integration_loop.py` | 모니터링→익일 브리핑 루프 E2E (1, fake) | Phase5 🟢 |

## 단계별 인수기준
### Phase 0
- [x] `docs/agents/` 4종 문서 존재
- [x] 기존 테스트 그린 (11 passed)

### Phase 1 — 맥락 저장소
- [x] 4종 테이블 upsert/조회 round-trip 통과
- [x] `event_calendar` 날짜 범위 조회 정확
- [x] `group_map` 종목→그룹/테마 역인덱스 조회
- [x] `ContextService.build_context()`가 종목+날짜로 일정·그룹·최근 시황을 조립
- [x] `ContextService.to_prompt_block()`가 결정적(deterministic) 텍스트 생성

### Phase 2 — 전략 에이전트
- [x] 지표(MA5/20/60, RSI14, 등락률, 거래량변화율) 순수 Pandas 산출
- [x] DSL 평가엔진: 허용 지표/연산자만, 미허용 지표 거부(보안), indicator vs indicator 비교
- [x] CAN SLIM 정량 필터(추세/신고가/거래량/모멘텀), 펀더멘털 항목 pending 분리
- [x] 인과분석: 정량+맥락+뉴스 프롬프트 조립, COMPOSITE 리포트 저장, LLM 주입형
- [x] LLM 추상화 `generate_structured` 추가 후 기존 `generate_news_price_report` 회귀 그린

### Phase 3 — 시장 판단 에이전트
- [x] Trafilatura 추출기: 주입형, 실패 시 None(예외 비전파), max_chars 절단
- [x] RSS 어댑터: 날짜 필터/중복 제거/본문 enrich, feedparser 지연 import
- [x] 타임라인 프로파일(장전/장중/마감) 관점 분기
- [x] 브리핑: 시장 전반 맥락(stock_code=None) 주입, MarketBriefingJson 구조화 출력

### Phase 4 — 모니터링 에이전트
- [x] Telegram: dedupe(TTL), not_configured 처리, timeout/retry, fake client 검증
- [x] APScheduler 낮(KR_DAY 15:40 월-금)/밤(US_NIGHT 06:30 화-토) 잡 등록
- [x] 일일 마감 리포트: 특징주 로그→Gemini→MarketDigest **맥락저장소 역기록**→텔레그램
- [x] main.py lifespan에서 `SCHEDULER_ENABLED` opt-in 기동

### Phase 5 — 고급 LLM 슬롯 + 통합
- [x] legacy anthropic 슬롯을 Gemini 3.5 Flash 고급 모드로 매핑, factory/health/테스트 정합
- [x] OpenRouter provider mock 테스트, role별 모델 선택, JSON Schema request body 검증
- [x] API 라우트 3종(strategy/briefing/monitor) OpenAPI 등록 확인
- [x] **통합 E2E**: 모니터링이 쓴 6/18 digest가 6/19 브리핑 맥락에 주입됨(루프 확인)
- [x] uv 환경(`uv sync`/`uv run pytest`)로 타 PC 재현 검증

## Mock 전략
- KIS/Naver/Telegram/Gemini: httpx/SDK 클라이언트를 `monkeypatch` 또는 주입형 fake로 대체.
- DB: 인메모리 SQLite(`sqlite:///:memory:`) 세션 픽스처 사용.
