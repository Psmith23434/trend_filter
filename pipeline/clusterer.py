"""Cluster embedded signals into trend groups.

Tuning via .env:
  CLUSTER_EPS=0.40          # cosine similarity threshold (default 0.35)
                            # higher → more (looser) clusters
                            # lower  → fewer (tighter) clusters
  CLUSTER_MIN_SAMPLES=2     # min articles per cluster (default 2, minimum useful value)
"""
import os
import uuid
from typing import List
import numpy as np
from sklearn.cluster import DBSCAN
from pipeline.models import RawSignal, TrendCluster


def _float_env(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, "").strip())
    except (ValueError, AttributeError):
        return default


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, "").strip())
    except (ValueError, AttributeError):
        return default


def cluster_signals(
    signals: List[RawSignal],
    eps: float | None = None,
    min_samples: int | None = None,
) -> List[TrendCluster]:
    """DBSCAN clustering on signal embeddings. Returns one TrendCluster per group."""
    if not signals or not signals[0].embedding:
        raise ValueError("Signals must be embedded before clustering.")

    # Prefer explicit args; fall back to .env; fall back to sensible defaults
    eps         = eps         if eps         is not None else _float_env("CLUSTER_EPS",         0.35)
    min_samples = min_samples if min_samples is not None else _int_env(  "CLUSTER_MIN_SAMPLES", 2)

    vectors = np.array([s.embedding for s in signals])
    # Cosine distance via normalised euclidean
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    vectors = vectors / np.clip(norms, 1e-8, None)

    labels = DBSCAN(eps=eps, min_samples=min_samples, metric="euclidean").fit_predict(vectors)

    clusters: dict[int, List[RawSignal]] = {}
    for label, signal in zip(labels, signals):
        if label == -1:
            continue  # noise — not similar enough to any cluster
        clusters.setdefault(label, []).append(signal)

    result = []
    for label, group in clusters.items():
        rep = max(group, key=lambda s: s.engagement)
        sources = list({s.source for s in group})
        result.append(TrendCluster(
            id=str(uuid.uuid4()),
            signals=group,
            representative_title=rep.title,
            keywords=[],
            sources=sources,
        ))
    return result
