"""Generate trend briefs using an LLM."""
import os
from typing import Optional
from pipeline.models import TrendCluster

SYSTEM_PROMPT = """You are a trend analyst for digital product creators.
Given a cluster of signals about a trending topic, you output a structured brief.
Be concise, specific, and commercial. Avoid generic statements."""

USER_TEMPLATE = """Trend: {title}
Sources: {sources}
Top signals:
{signals}

Output a JSON object with these exact keys:
- description: 2-sentence plain-language explanation of what this trend is.
- why_now: 1-2 sentences on why this is rising right now.
- product_ideas: list of 3 concrete product/content ideas (strings).
- urgency: one of low | medium | high."""


def generate_brief(cluster: TrendCluster, provider: str = "openai") -> TrendCluster:
    signals_text = "\n".join(
        f"- [{s.source}] {s.title}" for s in cluster.signals[:5]
    )
    user_msg = USER_TEMPLATE.format(
        title=cluster.representative_title,
        sources=", ".join(cluster.sources),
        signals=signals_text,
    )

    raw = _call_llm(system=SYSTEM_PROMPT, user=user_msg, provider=provider)

    import json, re
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        try:
            data = json.loads(match.group())
            cluster.brief = data.get("description", "")
            cluster.product_ideas = data.get("product_ideas", [])
            cluster.urgency = data.get("urgency", "medium")
        except json.JSONDecodeError:
            cluster.brief = raw
    return cluster


def _call_llm(system: str, user: str, provider: str = "openai") -> str:
    if provider == "openai":
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.4,
        )
        return resp.choices[0].message.content
    elif provider == "anthropic":
        import anthropic
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        msg = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=512,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return msg.content[0].text
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")
