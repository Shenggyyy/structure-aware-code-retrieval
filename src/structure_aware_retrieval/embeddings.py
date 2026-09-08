"""Pinned CPU encoding and snapshot-bound, non-pickle vector artifacts."""

import hashlib
import json
import os
import tempfile
import time
from importlib.metadata import version
from pathlib import Path
from typing import Protocol

import numpy as np

from structure_aware_retrieval.indexing import LoadedIndex
from structure_aware_retrieval.models import stable_id

MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"
MODEL_REVISION = "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"
MODEL_SPEC = {
    "id": MODEL_ID,
    "revision": MODEL_REVISION,
    "dimensions": 384,
    "max_seq_length": 256,
    "normalize": True,
    "dtype": "float32",
    "device": "cpu",
    "threads": 4,
    "batch_size": 32,
    "query_prompt": "",
    "document_prompt": "",
    "text_policy": "path-qualified_name-signature-code-v1",
}


class Encoder(Protocol):
    spec: dict

    def encode(self, texts: list[str]) -> np.ndarray: ...

    def token_lengths(self, texts: list[str]) -> list[int]: ...


class SentenceEncoder:
    """Network is allowed only by the explicit prepare-model command."""

    def __init__(self, cache: Path, *, download: bool = False) -> None:
        try:
            import torch
            from sentence_transformers import SentenceTransformer
        except ImportError as error:
            raise ValueError(
                "Dense dependencies missing; run uv sync --locked --extra dense"
            ) from error
        torch.set_num_threads(MODEL_SPEC["threads"])
        torch.manual_seed(0)
        torch.use_deterministic_algorithms(True)
        try:
            self.model = SentenceTransformer(
                MODEL_ID,
                revision=MODEL_REVISION,
                cache_folder=str(cache),
                local_files_only=not download,
                trust_remote_code=False,
                device="cpu",
                model_kwargs={"use_safetensors": True},
            )
        except (OSError, ValueError) as error:
            raise ValueError(
                "Pinned model unavailable; run sacr prepare-model --cache PATH first. "
                f"Details: {error}"
            ) from error
        self.model.max_seq_length = MODEL_SPEC["max_seq_length"]
        self.model.eval()
        self.spec = {
            **MODEL_SPEC,
            "packages": {
                name: version(name)
                for name in ("sentence-transformers", "transformers", "torch", "tokenizers")
            },
        }
        if self.model.get_embedding_dimension() != self.spec["dimensions"]:
            raise ValueError("Unexpected embedding dimension for pinned model")

    def encode(self, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.empty((0, self.spec["dimensions"]), dtype=np.float32)
        return np.asarray(
            self.model.encode(
                texts,
                batch_size=self.spec["batch_size"],
                prompt="",
                normalize_embeddings=True,
                convert_to_numpy=True,
                show_progress_bar=False,
            ),
            dtype=np.float32,
        )

    def token_lengths(self, texts: list[str]) -> list[int]:
        # Count before truncation, including special tokens. No padding is included.
        return (
            [
                len(row)
                for row in self.model.tokenizer(
                    texts, truncation=False, padding=False, verbose=False
                )["input_ids"]
            ]
            if texts
            else []
        )


def canonical_texts(index: LoadedIndex) -> list[str]:
    return [
        "\n".join([chunk.path, symbol.qualified_name, symbol.signature, chunk.text])
        for chunk in index.chunks
        for symbol in [index.symbols[chunk.symbol_id]]
    ]


def _binding(index: LoadedIndex, spec: dict) -> dict:
    return {
        "schema_version": 1,
        "snapshot_id": index.metadata["snapshot_id"],
        "chunk_ids": [chunk.id for chunk in index.chunks],
        "text_hash": stable_id(canonical_texts(index)),
        "encoder": spec,
    }


def validate_vectors(vectors: np.ndarray, rows: int, dimensions: int) -> None:
    if vectors.dtype != np.float32 or vectors.shape != (rows, dimensions):
        raise ValueError("Vector dtype or shape mismatch")
    if not np.isfinite(vectors).all():
        raise ValueError("Vectors must be finite")
    if rows and not np.allclose(np.linalg.norm(vectors, axis=1), 1, atol=1e-5):
        raise ValueError("Vectors must be L2 normalized and nonzero")


def build_vectors(index: LoadedIndex, encoder: Encoder, output: Path) -> dict:
    if output.exists() or output.is_symlink():
        raise FileExistsError(f"Vector output already exists: {output}; choose a new file")
    start = time.perf_counter()
    texts = canonical_texts(index)
    lengths = encoder.token_lengths(texts)
    vectors = encoder.encode(texts)
    validate_vectors(vectors, len(texts), encoder.spec["dimensions"])
    metadata = {
        "binding": _binding(index, encoder.spec),
        "vector_hash": hashlib.sha256(vectors.tobytes()).hexdigest(),
        "build_seconds": time.perf_counter() - start,
        "vector_bytes": vectors.nbytes,
        "documents": len(texts),
        "truncated_documents": sum(n > encoder.spec["max_seq_length"] for n in lengths),
        "max_document_tokens": max(lengths, default=0),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=output.parent, suffix=".npz", delete=False) as handle:
            temporary = Path(handle.name)
            np.savez_compressed(
                handle,
                vectors=vectors,
                metadata=np.frombuffer(json.dumps(metadata).encode("utf-8"), dtype=np.uint8),
            )
        # A hard link publishes without replacing a concurrent output, on Windows and POSIX.
        os.link(temporary, output)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return metadata


def load_vectors(path: Path, index: LoadedIndex, spec: dict) -> tuple[np.ndarray, dict]:
    with np.load(path, allow_pickle=False) as archive:
        if set(archive.files) != {"vectors", "metadata"}:
            raise ValueError("Invalid vector archive fields")
        metadata = json.loads(archive["metadata"].tobytes().decode("utf-8"))
        vectors = archive["vectors"]
    if metadata.get("binding") != _binding(index, spec):
        raise ValueError(
            "Vector cache mismatch: snapshot, chunks, text, model or dependencies changed"
        )
    validate_vectors(vectors, len(index.chunks), spec["dimensions"])
    if hashlib.sha256(vectors.tobytes()).hexdigest() != metadata.get("vector_hash"):
        raise ValueError("Vector checksum mismatch")
    return vectors, metadata
