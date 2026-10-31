"""Strict local embeddings: one input, one vector, with foreground priority."""

import copy
import threading
from contextlib import contextmanager

from localbrain.models.installation import model_root
from localbrain.models.embedding import LocalEncoder

QUERY_INSTRUCTION = ("Instruct: Given a search query, retrieve relevant passages from work sessions "
                     "and documents that answer the query.\nQuery: ")


class SearchEncoder(LocalEncoder):
    def __init__(self, config, profile, *, device="auto", batch_size=8):
        super().__init__(model_root("embedding", config.data_dir) / "model.json", device=device,
                         dimension=profile.dimension, max_tokens=1024, batch_size=batch_size)
        self.contract.update(profile.index_contract())
        self.contract["token_windows"] = "one-molecule-one-vector-v1"
        self.contract["query_instruction"] = QUERY_INSTRUCTION
        self.contract["dtype"] = "float32"
        self._condition = threading.Condition()
        self._busy = False
        self._queries = 0
        self._splitter_tokenizer = None

    @contextmanager
    def turn(self, query=False):
        with self._condition:
            if query:
                self._queries += 1
            try:
                while self._busy or (not query and self._queries):
                    self._condition.wait()
                self._busy = True
            finally:
                if query:
                    self._queries -= 1
        try:
            yield
        finally:
            with self._condition:
                self._busy = False
                self._condition.notify_all()

    @property
    def tokenizer(self):
        with self.turn():
            self._load()
            if self._splitter_tokenizer is None:
                # Fast tokenizers mutate padding/truncation state during encode.
                # Molecularization may run beside a foreground model query.
                self._splitter_tokenizer = copy.deepcopy(self.model.tokenizer)
        return self._splitter_tokenizer

    def encode(self, texts, *, query=False):
        import numpy as np
        with self.turn(query):
            self._load()
            inputs = [QUERY_INSTRUCTION + text if query else text for text in texts]
            for text in inputs:
                if len(self.model.tokenizer.encode(text, add_special_tokens=True)) > self.max_tokens:
                    raise ValueError("SEARCH_INPUT_TOO_LONG")
            vectors = self.model.encode(inputs, batch_size=self.batch_size, prompt="",
                                        convert_to_numpy=True, normalize_embeddings=True,
                                        show_progress_bar=False)
            if self.device == "mps":
                import torch
                torch.mps.synchronize()
            return np.asarray(vectors, dtype=np.float32)
