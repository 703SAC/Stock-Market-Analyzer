# Stock Market Analyzer 설정 가이드

## 1. Python 백엔드

```bash
cd app/backend
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

헬스 확인: http://localhost:8000/api/health

### `WinError 10013` (포트 8000)

대부분 **8000 포트를 다른 프로세스가 이미 쓰는 경우**입니다.

```powershell
netstat -ano | findstr ":8000"
# LISTENING 옆 PID 확인 후 종료
Stop-Process -Id <PID> -Force
```

또는 다른 포트로 실행:

```powershell
uvicorn main:app --reload --port 8001
```

프론트 `.env.local`의 `NEXT_PUBLIC_API_URL`도 같은 포트로 맞춥니다.

## 2. KIS Open API (한국투자증권)

1. `~/KIS/config/kis_devlp.yaml` 에 앱키·시크릿·계좌 정보를 설정합니다.
2. `open-trading-api/examples_user` 샘플과 동일한 경로를 사용합니다. **원본 `open-trading-api`는 수정하지 마세요.**
3. 백엔드는 KIS 샘플 `kis_auth`를 **수정하지 않고**, 토큰 발급·저장·`changeTREnv`만 직접 호출합니다 (`kis_auth.auth()`는 실패해도 예외 없이 종료됩니다).
4. `.env`에 `KIS_CONFIG_PATH=~/KIS/config/kis_devlp.yaml` (선택)
5. 토큰 파일: `~/KIS/config/KISprodYYYYMMDD` (실전), `KISvpsYYYYMMDD` (모의) — **prod/vps는 파일을 나눕니다.**
6. 모의투자만 쓸 경우 `.env`에 `KIS_SVR=vps`, yaml에 `paper_app` / `paper_sec` / `my_paper_stock`
7. **모의(vps)에서는 `chk-holiday`(휴장일) API가 없습니다.** 스크리너 거래일은 월~금으로 잡고, 공휴일까지 정확히 쓰려면 `KIS_SVR=prod` 또는 수동 보정이 필요합니다.

### `Get Authentification token fail!`

`kis_auth`는 **`~/KIS/config/kis_devlp.yaml`** 만 읽습니다. (`.env`의 `KIS_CONFIG_PATH`가 있으면 백엔드가 동일 파일을 다시 로드합니다.)

| 원인 | 확인 |
|------|------|
| 실전/모의 키 불일치 | 실전 앱키 → `KIS_SVR=prod`, 모의 앱키 → `KIS_SVR=vps` |
| yaml 값 비어 있음 | `my_app`, `my_sec` (또는 `paper_app`, `paper_sec`)에 발급받은 키 입력 |
| placeholder 그대로 | `"앱키"` 같은 예시 문자열이면 안 됨 |
| API 미승인/오타 | 한국투자 Open API 포털에서 앱키 상태 확인 |
| 1분에 1회 제한 (`EGW00133`) | 토큰을 연속 발급하지 말고 1분 후 재시도. 오래된 `KIS20260531` 단일 파일은 삭제 후 `KISvps…` / `KISprod…` 사용 |
| `OPSQ0002` 없는 서비스 코드 + `chk-holiday` | **vps(모의) 미지원** — 정상. 백엔드는 월~금 달력으로 대체합니다 |

`/api/health`의 `kis.smoke`에 `status_code`, `message`, `error_code`, `token_file`이 표시됩니다 (비밀값 없음).

`kis-ai-extensions`의 `setup_check.py` 항목을 참고해 다음을 점검합니다.

- Python 3.11+
- `kis_devlp.yaml` 존재
- 토큰 파일 (`~/KIS/config/KISYYYYMMDD`)
- 민감정보는 로그·API 응답에 노출하지 않음

## 3. Naver 검색 API (뉴스)

1. [Naver Developers](https://developers.naver.com/)에서 애플리케이션 등록
2. 검색 API 사용 설정
3. 워크스페이스 루트 `.env`에 `NAVER_CLIENT_ID`, `NAVER_CLIENT_SECRET` 설정 (백엔드가 이 파일을 읽음)
4. Naver Developers 앱에서 **검색 API** 사용 설정

### Naver `401 Unauthorized`

| 원인 | 조치 |
|------|------|
| Client ID/Secret 오타·빈 값 | [Naver Developers](https://developers.naver.com/)에서 앱 키 재확인 |
| ID와 Secret 뒤바뀜 | `NAVER_CLIENT_ID` = Client ID, `NAVER_CLIENT_SECRET` = Client Secret |
| 검색 API 미등록 | 애플리케이션 → API 설정 → **검색** 활성화 |
| `.env` 위치 | `Stock Market Analyzer/.env` (프론트 `.env.local` 아님) |

401이면 스택 대신 API가 `401`과 안내 메시지를 반환합니다.

## 4. LLM 보고서 (OpenAI 또는 Google AI Studio)

`LLM_PROVIDER`로 사용할 서비스를 하나만 선택합니다.

### OpenAI (기본)

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
LLM_MODEL=gpt-4o-mini
```

`LLM_MODEL`을 비우면 `gpt-4o-mini`가 기본값입니다.

### Google AI Studio (Gemini)

1. [Google AI Studio](https://aistudio.google.com/apikey)에서 API 키 발급
2. `.env` 설정:

```env
LLM_PROVIDER=google
GOOGLE_API_KEY=your_aistudio_api_key
LLM_MODEL=gemini-2.0-flash
```

`LLM_MODEL`을 비우면 `gemini-2.0-flash`가 기본값입니다.

OpenAI 키와 Google 키를 **둘 다 넣어도** 실제로 쓰는 쪽은 `LLM_PROVIDER` 하나뿐입니다.

`/api/health`의 `llm` 필드에서 `provider`, `configured`, `model`을 확인할 수 있습니다.

## 5. Next.js 프론트엔드

```bash
cd app/frontend
npm install
npm run dev
```

**주의:** `npm audit fix --force`는 실행하지 마세요. Next.js가 9.x/16.x로 바뀌며 React 18과 충돌합니다.  
로컬 개발용 경고는 무시해도 됩니다. 문제 시 `node_modules`와 `package-lock.json` 삭제 후 `npm install`만 다시 하세요.

`.env.local`:

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 6. 보안

- API 키는 백엔드 `.env`에만 둡니다.
- 프론트엔드에 KIS/LLM/Naver 키를 넣지 않습니다.
- `kis-ai-extensions` secret guard / prod guard 개념을 CI·에이전트 규칙에 반영하세요.
