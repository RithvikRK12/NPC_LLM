"""Semantic embeddings from local Ollama; never substitute lexical hashes."""
from __future__ import annotations

import httpx
import numpy as np

from app.config.settings import get_settings


class EmbeddingUnavailable(RuntimeError):
    pass


class EmbeddingService:
    def __init__(self):
        self.settings = get_settings()
        self.dimensions = self.settings.embedding_dimensions
        # Bump revision whenever weights or preprocessing change, even for the same tag.
        self.model_key = f'ollama:{self.settings.embedding_model}:{self.settings.embedding_revision}:{self.dimensions}'

    def embed_many(self, texts: list[str], *, query: bool = False,
                   timeout_seconds: float | None = None) -> list[list[float]]:
        if not texts:
            return []
        prefix = 'search_query: ' if query else 'search_document: '
        # Nomic requires task prefixes; other Ollama models receive plain text.
        inputs = [prefix + t if self.settings.embedding_model.startswith('nomic-embed-text') else t for t in texts]
        timeout = self.settings.embedding_timeout_seconds
        if timeout_seconds is not None:
            if type(timeout_seconds) not in {int, float} or timeout_seconds <= 0:
                raise ValueError('embedding timeout must be positive')
            timeout = min(timeout, float(timeout_seconds))
        try:
            response = httpx.post(
                self.settings.embedding_base_url.rstrip('/') + '/api/embed',
                json={'model': self.settings.embedding_model, 'input': inputs, 'truncate': False},
                timeout=httpx.Timeout(timeout, connect=min(3.0, timeout)),
            )
            if response.status_code == 404:
                # Distinguish absent weights from an unsupported endpoint without
                # hiding other transport/server errors or substituting vectors.
                try:
                    error = response.json().get('error', '')
                except (ValueError, AttributeError):
                    error = ''
                if isinstance(error, str) and 'model' in error and 'not found' in error:
                    raise EmbeddingUnavailable(
                        f'Configured Ollama embedding model {self.settings.embedding_model!r} is not installed. '
                        'Install it on the configured embedding server; no substitute vectors were created.'
                    )
            response.raise_for_status()
            vectors = np.asarray(response.json()['embeddings'], dtype='float32')
            if vectors.shape != (len(texts), self.dimensions) or not np.isfinite(vectors).all():
                raise ValueError('Unexpected embedding dimensions or non-finite values')
            norms = np.linalg.norm(vectors, axis=1, keepdims=True)
            if np.any(norms <= 0):
                raise ValueError('Zero embedding vector')
            return (vectors / norms).tolist()
        except (httpx.HTTPError, ValueError, KeyError, TypeError) as exc:
            raise EmbeddingUnavailable(f'Semantic embedding failed for {self.model_key}: {exc}') from exc

    def embed(self, text: str, *, query: bool = False,
              timeout_seconds: float | None = None) -> list[float]:
        return self.embed_many([text], query=query, timeout_seconds=timeout_seconds)[0]
