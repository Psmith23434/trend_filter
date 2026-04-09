"""CSV export helpers."""
import csv
import io
from typing import List

FIELDS = [
    "id", "created_at", "niche", "signal_type", "urgency", "score",
    "title", "label", "brief",
    "growth", "source_diversity", "commercial_intent", "novelty", "persistence",
    "signal_count_in_cluster", "sources", "keywords", "evidence_urls",
    "product_ideas", "action_plan",
]


def trends_to_csv(trends: List) -> str:
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=FIELDS, extrasaction="ignore")
    writer.writeheader()
    for t in trends:
        row = {f: getattr(t, f, "") for f in FIELDS}
        # Flatten list fields to pipe-separated strings
        for lf in ("sources", "keywords", "evidence_urls", "product_ideas", "action_plan"):
            val = row.get(lf) or []
            row[lf] = " | ".join(str(v) for v in val)
        writer.writerow(row)
    return buf.getvalue()
