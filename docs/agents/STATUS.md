# STATUS — 살아있는 구현 상태표

> 범례: 🟢 작동/검증 · 🟡 부분 · 🔴 미구현/스텁. 갱신일은 작업 시점 기준.
> 최종 갱신: 2026-06-19 (Phase 0~5 완료)

## 환경
| 항목 | 상태 | 비고 |
|---|---|---|
| Python 런타임 | 🟢 | `python3` = 3.14.6. `python`/`py`는 Windows Store 스텁이라 작동 안 함 |
| uv 환경 | 🟢 | `app/backend/pyproject.toml` + `uv.lock`(1916줄, 크로스플랫폼). `uv sync`/`uv run pytest`로 타 PC 재현 |
| 검증 venv | 🟢 | `app/backend/.venv` = uv 관리(gitignore 대상) |
| 테스트 결과 | 🟢 | `66 passed`, 2026-06-20 `uv run pytest` 실행 |
| 프론트 빌드 | 🟢 | node v24/npm11, `npm run build` 성공(11 routes, strict 타입체크 통과) |
| FastAPI 앱 | 🟢 | `create_app()` 정상, 에이전트 3종 + context API OpenAPI 등록 확인 |
| SQLite/SQLAlchemy | 🟢 | `storage/db.py` 작동 |

## 컴포넌트
| 영역 | 컴포넌트 | 상태 | 위치 | 비고 |
|---|---|---|---|---|
| 백본 | 맥락 저장소 ORM 4종 | 🟢 | `storage/models.py` | Phase 1 추가 |
| 백본 | 맥락 리포지토리 4종 | 🟢 | `storage/repositories/context.py` | Phase 1 |
| 백본 | ContextService | 🟢 | `services/context/service.py` | Phase 1, 프롬프트 주입 |
| ③ 전략 | 거래량/상한가 스크리너 | 🟢 | `features/screener` | 기존 작동 |
| ③ 전략 | CAN SLIM 정량 필터 | 🟢 | `features/strategy/canslim.py` | Phase2, 순수 Pandas. 펀더멘털(C/A/N/I)은 DART 전까지 pending |
| ③ 전략 | 지표(Pandas)/DSL 평가엔진 | 🟢 | `services/chart/{indicators,evaluator}.py` | Phase2 |
| ③ 전략 | 인과관계 분석 | 🟢 | `features/strategy/causality.py` | Phase2, 맥락 주입 |
| ② 시장판단 | Naver 뉴스 검색 | 🟢 | `services/news/naver_adapter.py` | 기존 작동 |
| ② 시장판단 | 정형 보고서(뉴스+가격) | 🟢 | `features/reports` | 기존 작동 |
| ② 시장판단 | Trafilatura 본문추출 | 🟢 | `services/news/extractor.py`, `rss_adapter.py` | Phase3, lazy import |
| ② 시장판단 | 타임라인/메가내러티브 브리핑 | 🟢 | `features/briefing/` | Phase3, 장전/장중/마감 |
| ① 모니터링 | APScheduler 낮/밤 교대 | 🟢 | `services/scheduler/` | Phase4, 인프로세스. `SCHEDULER_ENABLED`로 opt-in |
| ① 모니터링 | 일일 마감 리포트 파이프라인 | 🟢 | `features/monitor/service.py` | Phase4, **종합시황을 맥락저장소에 역기록(루프 닫음)** |
| ① 모니터링 | Telegram 발송 | 🟢 | `services/telegram/adapter.py` | Phase4, httpx+timeout/retry+dedupe |
| LLM | 구조화 출력 추상화 | 🟢 | `services/llm/base.py` | Phase2, `generate_structured(schema)` |
| LLM | Gemini provider | 🟢 | `services/llm/google_provider.py` | 메인(무료) |
| LLM | OpenAI provider | 🟢 | `services/llm/openai_provider.py` | |
| LLM | Claude(anthropic) provider | 🟢 | `services/llm/anthropic_provider.py` | Phase5, opt-in 자리(기본 비활성) |
| API | 에이전트 라우트 3종 | 🟢 | `api/{strategy,briefing,monitor}.py` | Phase5 |
| API | 맥락 저장소 읽기/시드 | 🟢 | `api/context.py` | FE연동, GET 4종 + 시드 POST 4종 |
| Frontend | 에이전트 페이지 4종 | 🟢 | `app/frontend/app/{strategy,briefing,monitor,context}` | 전략/브리핑/모니터링/맥락뷰어 |
| Frontend | 공통 컴포넌트 | 🟢 | `app/frontend/components/` | ReportView·CanSlimPanel·RawJsonToggle·ConfidenceBadge |
| Frontend | 품질검증 UI | 🟢 | (각 페이지) | confidence·sources·원본JSON 토글 |

## Phase 진행
| Phase | 상태 | 비고 |
|---|---|---|
| 0 문서·베이스라인 | 🟢 완료 | 문서 4종 + 기존 11 테스트 그린 |
| 1 맥락 저장소 | 🟢 완료 | 코드+테스트 10개 그린 |
| 2 전략 에이전트 | 🟢 완료 | 지표/평가/CAN SLIM/인과 + LLM 추상화, 테스트 그린 |
| 3 시장판단 에이전트 | 🟢 완료 | 추출기/RSS/타임라인 브리핑, 테스트 그린 |
| 4 모니터링+자동화 | 🟢 완료 | APScheduler·텔레그램·마감리포트→역기록, 테스트 그린 |
| 5 Claude 자리예약+통합 | 🟢 완료 | anthropic 자리, API 라우트, 통합 E2E(루프), uv 환경 |
