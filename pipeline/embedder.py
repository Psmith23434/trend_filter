"""Embed signals using sentence-transformers."""
from typing import List
from pipeline.models import RawSignal

MODEL_NAME = "all-MiniLM-L6-v2"
_model = None


def get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def embed_signals(signals: List[RawSignal]) -> List[RawSignal]:
    """Add embedding vectors to each signal."""
    model = get_model()
    texts = [f"{s.title} {s.text}" for s in signals]
    embeddings = model.encode(texts, batch_size=32, show_progress_bar=True)
    for signal, emb in zip(signals, embeddings):
        signal.embedding = emb.tolist()
    return signals
