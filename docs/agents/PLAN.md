# PLAN — 단계별 개발 로드맵

> [GOAL.md](GOAL.md) 달성을 위한 실행 계획. 진행 상태는 [STATUS.md](STATUS.md), 검증은 [TEST.md](TEST.md) 참조.
> 기존 기능 중심 스프린트 계획은 [../IMPLEMENTATION_PROMPT_PLAN.md](../IMPLEMENTATION_PROMPT_PLAN.md)와 정합.

## 정합 매핑 (3-에이전트 ↔ 기존 코드)
| 에이전트 | 기존 자산 | 보강 필요 |
|---|---|---|
| ③ 전략 | `features/screener` (거래량/상한가 작동), `services/chart/condition_schema.py` (스키마만) | CAN SLIM, 지표(Pandas), DSL 평가엔진, 인과분석 |
| ② 시장판단 | `features/news`, `features/reports` (Naver+정형보고서 작동) | Trafilatura 본문추출, 타임라인, 메가내러티브 종합 |
| ① 모니터링 | `features/monitor`(스텁), `services/telegram`(NotImplemented) | APScheduler, 마감 리포트 파이프라인, 텔레그램 실구현 |

## Phase 0 — 문서·검증 골격 + 베이스라인 ✅ (소)
- `docs/agents/{GOAL,PLAN,STATUS,TEST}.md` 생성
- 기존 `pytest` 베이스라인 확인(회귀 가드 고정)
- **완료기준**: 문서 4종 + 기존 테스트 그린

## Phase 1 — 🧠 메가 내러티브 맥락 저장소 (백본) ★최우선 (중)
- ORM 테이블 4종: `market_digest`, `event_calendar`, `group_map`, `narrative_memory`
- 코어 도메인 모델 + 리포지토리 4종
- `services/context/ContextService`: 종목/날짜 기준 다차원 맥락 조립 + 프롬프트 주입 텍스트 생성
- **완료기준**: read/write + 프롬프트 주입 단위테스트 통과

## Phase 2 — 📊 전략 에이전트 고도화 ✅ (중~대)
- `services/chart/indicators.py` (MA/RSI/거래량변화율 — 순수 Pandas)
- `services/chart/evaluator.py` (기존 `condition_schema` DSL 평가)
- `features/strategy/`: CAN SLIM 정량 필터 + 인과관계 분석(가격이벤트 ↔ 뉴스 ↔ 맥락)
- LLM 추상화에 `generate_structured(schema)` 추가(인과/브리핑 공용)
- **완료기준**: 지표·DSL·CAN SLIM 단위테스트, 인과 리포트 JSON 스키마 검증 → **그린**

## Phase 3 — 📰 시장 판단 에이전트 ✅ (중)
- Trafilatura 본문추출 활성화(`services/news/extractor.py` + `rss_adapter` 구현 + requirements)
- 타임라인 프로파일(장전/장중/마감) 오케스트레이션
- 메가 내러티브 종합 시황 브리핑(Phase1 맥락 주입)
- **완료기준**: 타임라인별 브리핑 생성, 본문추출 mock 테스트 → **그린**

## Phase 4 — 🛰️ 모니터링 에이전트 + 자동화 ✅ (대)
- `services/scheduler/` APScheduler 인프로세스(FastAPI lifespan, `SCHEDULER_ENABLED` opt-in), 낮/밤 교대 잡
- 장마감 후 일일 리포트(Gemini) → 종합시황을 Phase1 저장소에 역기록(루프 닫기)
- Telegram adapter 실구현(timeout/retry) + 중복발송 방지
- **완료기준**: 스케줄 발화·텔레그램 발송 mock 테스트, 마감→저장→익일주입 E2E → **그린**

## Phase 5 — 마감: Claude 자리 예약 + 통합검증 ✅ (소~중)
- LLM factory `anthropic` 자리 예약(기본 비활성, Gemini 유지)
- API 라우트 3종 + 프론트 api.ts 최소 연결
- 3대 에이전트 통합 E2E(mock), uv 환경 구성, 문서 최종 갱신
- **완료기준**: 통합 루프 E2E 그린, `uv run pytest` 59 passed

## 진행 규칙
- 매 Phase: adapter-mock 단위테스트 우선 → 최소구현 → `pytest` → STATUS 갱신.
- 외부 API 실호출은 테스트에서 금지(전부 mock).
- 승인 게이트: Phase 0~1 연속 자율 실행 후 보고. 이후 Phase는 보고 시 재확인.
