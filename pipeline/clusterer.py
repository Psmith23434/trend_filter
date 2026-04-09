"""Cluster embedded signals into trend groups."""
import uuid
from typing import List
import numpy as np
from sklearn.cluster import DBSCAN
from pipeline.models import RawSignal, TrendCluster


def cluster_signals(
    signals: List[RawSignal],
    eps: float = 0.25,
    min_samples: int = 2,
) -> List[TrendCluster]:
    """DBSCAN clustering on signal embeddings. Returns one TrendCluster per group."""
    if not signals or not signals[0].embedding:
        raise ValueError("Signals must be embedded before clustering.")

    vectors = np.array([s.embedding for s in signals])
    # Cosine distance: normalize then euclidean
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    vectors = vectors / np.clip(norms, 1e-8, None)

    labels = DBSCAN(eps=eps, min_samples=min_samples, metric="euclidean").fit_predict(vectors)

    clusters: dict[int, List[RawSignal]] = {}
    for label, signal in zip(labels, signals):
        if label == -1:
            continue  # noise
        clusters.setdefault(label, []).append(signal)

    result = []
    for label, group in clusters.items():
        rep = max(group, key=lambda s: s.engagement)
        sources = list({s.source for s in group})
        result.append(TrendCluster(
            id=str(uuid.uuid4()),
            signals=group,
            representative_title=rep.title,
            keywords=[],  # filled by scorer
            sources=sources,
        ))
    return result
