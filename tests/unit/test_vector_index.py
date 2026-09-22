"""Tests del encoder ligero y del índice cosine."""

from app.rag.embeddings import HashEncoder
from app.rag.vector_index import InMemoryVectorIndex


def test_hash_encoder_is_deterministic():
    encoder = HashEncoder(dimension=32)
    first = encoder.encode_one("cáncer de pulmón estadio IA")
    second = encoder.encode_one("cáncer de pulmón estadio IA")
    assert first == second
    assert len(first) == 32
    assert abs(sum(value * value for value in first) - 1.0) < 1e-6


def test_vector_index_ranks_overlapping_text_first():
    encoder = HashEncoder(dimension=64)
    index = InMemoryVectorIndex()
    texts = [
        "resección quirúrgica en estadio IA de cáncer de pulmón",
        "receta de cocina con pollo y verduras",
    ]
    index.add(
        ids=["medical", "noise"],
        texts=texts,
        embeddings=encoder.encode(texts),
        metadatas=[{"source": "nccn"}, {"source": "other"}],
    )

    hits = index.query(
        encoder.encode_one("tratamiento quirúrgico estadio IA pulmón"),
        top_k=2,
    )
    assert hits[0]["id"] == "medical"
    assert hits[0]["distance"] <= hits[1]["distance"]


def test_build_encoder_hash_backend():
    from types import SimpleNamespace

    from app.rag.embeddings import HashEncoder, build_encoder

    encoder = build_encoder(
        SimpleNamespace(embedding_backend="hash", embedding_dimension=16)
    )
    assert isinstance(encoder, HashEncoder)
    assert encoder.dimension == 16


def test_fastembed_encoder_uses_onnx_stub(monkeypatch, tmp_path):
    import sys
    from types import ModuleType

    import numpy as np

    from app.rag.embeddings import FastEmbedEncoder, build_encoder

    fake = ModuleType("fastembed")

    class TextEmbedding:
        def __init__(self, model_name, cache_dir):
            self.model_name = model_name
            self.cache_dir = cache_dir

        def embed(self, texts):
            return [np.array([1.0, 0.0, 0.0, 0.0], dtype=float) for _ in texts]

    fake.TextEmbedding = TextEmbedding
    monkeypatch.setitem(sys.modules, "fastembed", fake)

    encoder = FastEmbedEncoder("stub-model", str(tmp_path), dimension=4)
    vector = encoder.encode_one("cáncer de pulmón")
    assert vector == [1.0, 0.0, 0.0, 0.0]

    built = build_encoder(
        type("S", (), {
            "embedding_backend": "fastembed",
            "embedding_model": "stub-model",
            "embedding_cache_dir": str(tmp_path),
            "embedding_dimension": 4,
        })()
    )
    assert built.encode(["hola"])[0] == [1.0, 0.0, 0.0, 0.0]


def test_vector_index_edge_cases():
    encoder = HashEncoder(dimension=16)
    index = InMemoryVectorIndex()
    index.add(["a"], ["tumor pulmonar"], encoder.encode(["tumor pulmonar"]), [{"source": "a"}])
    index.add(["a"], ["tumor pulmonar estadio IA"], encoder.encode(["tumor pulmonar estadio IA"]))
    index.clear()
    assert index.count == 0
    assert index.query([0.0] * 16, top_k=3) == []
    assert index.query(encoder.encode_one("x"), top_k=0) == []
