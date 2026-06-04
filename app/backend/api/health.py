"""Health check endpoint."""



from fastapi import APIRouter



from config import get_settings

from services.kis.adapter import get_kis_adapter

from services.kis.auth_status import check_kis_status

from services.llm.adapter import get_llm_provider

from storage.db import engine



router = APIRouter()





def _llm_missing_env(settings) -> list[str]:

    provider = (settings.llm_provider or "openai").lower().strip()

    if provider == "google":

        if not settings.google_api_key:

            return ["GOOGLE_API_KEY"]

        return []

    if not settings.openai_api_key:

        return ["OPENAI_API_KEY"]

    return []





@router.get("/health")

async def health():

    settings = get_settings()

    kis_status = check_kis_status()

    adapter = get_kis_adapter()

    kis_smoke = (

        await adapter.smoke_test()

        if adapter.is_available

        else {

            "status": "not_configured",

            "message": kis_status.get("message", ""),

        }

    )



    llm = get_llm_provider()

    llm_missing = _llm_missing_env(settings)



    db_ok = False

    try:

        with engine.connect() as conn:

            from sqlalchemy import text



            conn.execute(text("SELECT 1"))

            db_ok = True

    except Exception:

        db_ok = False



    missing_env = []

    if not settings.naver_client_id or not settings.naver_client_secret:

        missing_env.append("NAVER_CLIENT_ID/SECRET")

    missing_env.extend(llm_missing)



    return {

        "status": "ok" if db_ok else "degraded",

        "app_env": settings.app_env,

        "database": "ok" if db_ok else "error",

        "kis": {**kis_status, "smoke": kis_smoke},

        "news_provider": settings.news_provider,

        "news_configured": bool(

            settings.naver_client_id and settings.naver_client_secret

        ),

        "llm": {

            "provider": llm.provider_name,

            "configured": llm.is_configured,

            "model": llm.model_name,

        },

        "llm_configured": llm.is_configured,

        "missing_optional_env": missing_env,

    }

