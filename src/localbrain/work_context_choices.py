"""Finite model answer codes, not a semantic validator or free-text repair."""

import re

from .work_reconstruction import require

VERSION = "work-context-choice-trie.v1"
SEMANTIC_VERSION = "work-context-semantic-choice-trie.v1"
MAX_OPTIONS = 128
MAX_CODE_TOKENS = 8


def validate_codes(codes, *, max_code_chars=8):
    require(type(max_code_chars) is int and max_code_chars in {8, 32}, "INVALID_CHOICES")
    require(isinstance(codes, list) and 1 <= len(codes) <= MAX_OPTIONS
            and all(isinstance(code, str) and re.fullmatch(r"[A-Za-z0-9_-]{1,%d}" % max_code_chars, code)
                    for code in codes), "INVALID_CHOICES")
    require(len(codes) == len(set(codes)), "INVALID_CHOICES")


class ChoiceTrie:
    def __init__(self, encoded, eos, *, max_code_chars=8):
        require(isinstance(encoded, dict), "INVALID_CHOICES")
        validate_codes(list(encoded), max_code_chars=max_code_chars)
        require(eos and all(type(token) is int for token in eos), "INVALID_CHOICES")
        self.eos = set(eos)
        self.root = {}
        self.max_output = 1
        for code, tokens in encoded.items():
            require(isinstance(tokens, (list, tuple)) and 1 <= len(tokens) <= MAX_CODE_TOKENS
                    and all(type(token) is int and token >= 0 and token not in self.eos
                            for token in tokens), "INVALID_CHOICES")
            node = self.root
            for token in tokens:
                node = node.setdefault(token, {})
            require(None not in node, "INVALID_CHOICES")
            node[None] = code
            self.max_output = max(self.max_output, len(tokens) + 1)

    def node(self, prefix):
        node = self.root
        for token in prefix:
            require(type(token) is int and token in node, "INVALID_CHOICE_OUTPUT")
            node = node[token]
        return node

    def allowed(self, prefix):
        node = self.node(prefix)
        return sorted({token for token in node if token is not None}
                      | (self.eos if None in node else set()))

    def answer(self, tokens):
        require(tokens and tokens[-1] in self.eos, "OUTPUT_TRUNCATED")
        node = self.node(tokens[:-1])
        require(None in node, "INVALID_CHOICE_OUTPUT")
        return node[None]
