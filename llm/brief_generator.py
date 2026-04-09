"""Generate trend briefs using a local Ollama model (default) or cloud LLM.

Set LLM_PROVIDER in .env:
  LLM_PROVIDER=ollama      (default, free, local)
  LLM_PROVIDER=openai      (requires OPENAI_API_KEY)
  LLM_PROVIDER=anthropic   (requires ANTHROPIC_API_KEY)
"""
import os
import json
import re
from pipeline.models import TrendCluster

SYSTEM_PROMPT = """You are a trend analyst for digital product creators.
Given a cluster of signals about a trending topic, output a structured brief.
Be concise, specific, and commercial. Avoid generic statements.
Always respond with valid JSON only — no extra text."""

USER_TEMPLATE = """Trend: {title}
Sources: {sources}
Top signals:
{signals}

Respond with this exact JSON structure:
{{
  "description": "2-sentence plain-language explanation of what this trend is.",
  "why_now": "1-2 sentences on why this is rising right now.",
  "product_ideas": ["idea 1", "idea 2", "idea 3"],
  "urgency": "low or medium or high"
}}"""


def generate_brief(cluster: TrendCluster) -> TrendCluster:
    provider = os.getenv("LLM_PROVIDER", "ollama").lower()
    signals_text = "\n".join(
        f"- [{s.source}] {s.title}" for s in cluster.signals[:5]
    )
    user_msg = USER_TEMPLATE.format(
        title=cluster.representative_title,
        sources=", ".join(cluster.sources),
        signals=signals_text,
    )
    try:
        raw = _call_llm(system=SYSTEM_PROMPT, user=user_msg, provider=provider)
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            data = json.loads(match.group())
            cluster.brief = data.get("description", "")
            cluster.product_ideas = data.get("product_ideas", [])
            cluster.urgency = data.get("urgency", "medium")
    except Exception as e:
        print(f"[BriefGenerator] Error ({provider}): {e}")
        cluster.brief = f"Trend: {cluster.representative_title}"
        cluster.urgency = "medium"
        cluster.product_ideas = []
    return cluster


def _call_llm(system: str, user: str, provider: str) -> str:
    if provider == "ollama":
        return _ollama(system, user)
    elif provider == "openai":
        return _openai(system, user)
    elif provider == "anthropic":
        return _anthropic(system, user)
    else:
        raise ValueError(f"Unknown LLM_PROVIDER: {provider}")


def _ollama(system: str, user: str) -> str:
    """Call local Ollama instance. Install: https://ollama.com — then run: ollama pull llama3"""
    import httpx
    model = os.getenv("OLLAMA_MODEL", "llama3")
    ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434/api/chat")
    payload = {
        "model": model,
        "stream": False,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }
    resp = httpx.post(ollama_url, json=payload, timeout=60)
    resp.raise_for_status()
    return resp.json()["message"]["content"]


def _openai(system: str, user: str) -> str:
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    resp = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.4,
    )
    return resp.choices[0].message.content


def _anthropic(system: str, user: str) -> str:
    import anthropic
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    msg = client.messages.create(
        model=os.getenv("ANTHROPIC_MODEL", "claude-3-haiku-20240307"),
        max_tokens=512,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return msg.content[0].text
