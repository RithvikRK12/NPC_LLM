"""Bounded cache of immutable, transaction-versioned FAISS HNSW indexes."""
from collections import OrderedDict
from dataclasses import dataclass
from threading import RLock

import faiss
import numpy as np


@dataclass
class CandidateIndex:
    ids: list[int]
    index: object

    @classmethod
    def build(cls, rows, dimensions):
        ids, vectors = [], []
        for memory_id, vector in rows:
            try:
                value = np.asarray(vector, dtype='float32')
            except (TypeError, ValueError):
                continue
            if value.shape != (dimensions,) or not np.isfinite(value).all() or np.linalg.norm(value) <= 0:
                continue
            ids.append(memory_id)
            vectors.append(value)
        index = faiss.IndexHNSWFlat(dimensions, 32, faiss.METRIC_INNER_PRODUCT)
        index.hnsw.efConstruction = 100
        index.hnsw.efSearch = 100
        if vectors:
            matrix = np.ascontiguousarray(vectors, dtype='float32')
            faiss.normalize_L2(matrix)
            index.add(matrix)
        return cls(ids, index)

    def search(self, vector, count):
        if not self.ids:
            return []
        matrix = np.ascontiguousarray([vector], dtype='float32')
        faiss.normalize_L2(matrix)
        scores, positions = self.index.search(matrix, min(count, len(self.ids)))
        return [(self.ids[int(pos)], float(score)) for pos, score in zip(positions[0], scores[0]) if pos >= 0]


_cache = OrderedDict()
_lock = RLock()


def cached_index(key, build):
    with _lock:
        if key in _cache:
            _cache.move_to_end(key)
            return _cache[key]
    value = build()
    with _lock:
        _cache[key] = value
        _cache.move_to_end(key)
        while len(_cache) > 32:
            _cache.popitem(last=False)
    return value
