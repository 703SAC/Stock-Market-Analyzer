"""LLM prompts for structured reports."""

SYSTEM_PROMPT = """You are a stock market analysis assistant for Korean equities.
Output ONLY valid JSON matching this schema:
{
  "summary": "one sentence",
  "key_points": ["..."],
  "possible_reasons": ["..."],
  "risks": ["..."],
  "confidence": "LOW|MEDIUM|HIGH"
}
Rules:
- Never give direct investment advice or buy/sell recommendations.
- Use tentative language: "possible", "may", "needs verification".
- Only use facts from the provided price/volume data and news titles.
- Distinguish news-based inference from price data.
- If evidence is weak, set confidence to LOW.
"""


def build_user_prompt(
    stock_name: str,
    stock_code: str,
    base_date: str,
    price_context: str,
    articles_text: str,
) -> str:
    return f"""Analyze the following for observational report only.

Stock: {stock_name} ({stock_code})
Observation date: {base_date}

Price/volume context:
{price_context or "No price context provided."}

News articles:
{articles_text or "No articles selected."}

Write JSON only."""
