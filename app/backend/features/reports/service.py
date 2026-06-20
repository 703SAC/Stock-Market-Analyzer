"""Report generation orchestration."""

from sqlalchemy.orm import Session

from core.models import AnalysisReport, ArticleItem, StockIdentity
from features.reports.prompts import SYSTEM_PROMPT, build_user_prompt
from features.reports.schemas import NewsPriceReportRequest, NewsPriceReportResponse
from features.news.schemas import NewsSearchQuery
from features.news.service import news_service
from services.llm.adapter import llm_adapter
from storage.repositories import reports as report_repo


class ReportService:
    def __init__(self, llm=None):
        self._llm = llm

    async def create_news_price_report(
        self, db: Session, body: NewsPriceReportRequest
    ) -> NewsPriceReportResponse:
        news_query = NewsSearchQuery(
            stock_code=body.stock_code,
            stock_name=body.stock_name,
            base_date=body.base_date,
        )
        news_result = await news_service.search(db, news_query)
        selected = self._filter_articles(news_result.articles, body.article_ids)

        price_context = ""
        if body.screener_event:
            ev = body.screener_event
            price_context = (
                f"Event types: {', '.join(ev.event_types)}; "
                f"volume: {ev.volume}; change_rate: {ev.change_rate}; "
                f"price: {ev.price}"
            )

        articles_text = "\n".join(
            f"- {a.title} ({a.url})" for a in selected
        )
        user_prompt = build_user_prompt(
            body.stock_name or body.stock_code,
            body.stock_code,
            body.base_date.isoformat(),
            price_context,
            articles_text,
        )
        llm = self._llm or llm_adapter.for_role("pro")
        llm_result = await llm.generate_news_price_report(
            SYSTEM_PROMPT, user_prompt
        )

        report = AnalysisReport(
            stock=StockIdentity(
                code=body.stock_code,
                name=body.stock_name,
            ),
            base_date=body.base_date,
            report_type="NEWS_PRICE",
            summary=llm_result.summary,
            key_points=llm_result.key_points,
            possible_reasons=llm_result.possible_reasons,
            risks=llm_result.risks,
            confidence=llm_result.confidence,
            sources=["news", "price"] if body.screener_event else ["news"],
            article_urls=[a.url for a in selected],
        )
        saved = report_repo.save_report(db, report)
        return NewsPriceReportResponse(report=saved)

    async def get_report(self, db: Session, report_id: str) -> AnalysisReport | None:
        return report_repo.get_report(db, report_id)

    def _filter_articles(
        self, articles: list[ArticleItem], article_ids: list[str]
    ) -> list[ArticleItem]:
        if not article_ids:
            return articles[:5]
        id_set = set(article_ids)
        return [a for a in articles if a.id in id_set]


report_service = ReportService()
