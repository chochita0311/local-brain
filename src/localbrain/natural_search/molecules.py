"""Original character spans, structural boundaries and bounded input context."""

import bisect
import re
from dataclasses import dataclass

from .source import digest

SPLITTER_VERSION = "structural-spans-v1"
BREAKS = re.compile(r"\n\s*\n|\n(?=#{1,6} |[-*] |\d+[.)] )|(?<=[.!?。！？])\s+")


@dataclass(frozen=True)
class Profile:
    target: int = 512
    dimension: int = 512
    overlap: int = 0
    cutoff: float = 0.45

    def __post_init__(self):
        if self.target not in (256, 512, 768) or self.dimension not in (512, 1024):
            raise ValueError("INVALID_SEARCH_PROFILE")
        if self.overlap not in (0, 64) or not 0 <= self.cutoff <= 1:
            raise ValueError("INVALID_SEARCH_PROFILE")

    def index_contract(self):
        return {"splitter": SPLITTER_VERSION, "target": self.target, "dimension": self.dimension,
                "overlap": self.overlap, "body_max": 768, "context_max": 128, "input_max": 1024}


def tokens(tokenizer, text):
    return tokenizer.encode(text, add_special_tokens=False, verbose=False)


def bounded_context(tokenizer, text, limit=128):
    """Context-only excerpt; the body is never sent through this function."""
    if len(tokens(tokenizer, text)) <= limit:
        return text, False
    low, high = 0, len(text)
    while low < high:
        middle = (low + high + 1) // 2
        if len(tokens(tokenizer, text[:middle])) <= limit:
            low = middle
        else:
            high = middle - 1
    return text[:low], True


def split_spans(text, tokenizer, profile):
    """Cover every character, preserving Unicode and preferring structural endings."""
    encoded = tokenizer(text, add_special_tokens=False, return_offsets_mapping=True, truncation=False, verbose=False)
    offsets = encoded["offset_mapping"]
    if not offsets:
        if text:
            yield 0, len(text)
        return
    starts = [pair[0] for pair in offsets]
    breaks = [match.end() for match in BREAKS.finditer(text)]
    start = 0
    while start < len(text):
        index = bisect.bisect_left(starts, start)
        if len(offsets) - index <= profile.target:
            end = len(text)
        else:
            desired = offsets[min(index + profile.target, len(offsets) - 1)][0]
            ceiling = offsets[min(index + 768, len(offsets) - 1)][0]
            candidates = breaks[bisect.bisect_right(breaks, start):bisect.bisect_right(breaks, ceiling)]
            # Do not make tiny fragments merely because a paragraph starts early.
            floor = offsets[min(index + profile.target // 2, len(offsets) - 1)][0]
            candidates = [value for value in candidates if value >= floor]
            end = min(candidates, key=lambda value: abs(value - desired)) if candidates else desired
            end = max(start + 1, end)
        # Retokenizing after a Unicode/structural boundary can change token count.
        while len(tokens(tokenizer, text[start:end])) > 768:
            end = start + max(1, (end - start) // 2)
        yield start, end
        if end == len(text):
            break
        if profile.overlap:
            end_index = bisect.bisect_left(starts, end)
            overlap_start = offsets[max(index + 1, end_index - profile.overlap)][0]
            start = max(start + 1, min(end, overlap_start))
        else:
            start = end


def molecularize(source, tokenizer, profile):
    ordinal, previous_request = 0, None
    contexts = {}
    for block in source.blocks:
        text = block["text"]
        context_event = previous_request["id"] if block["role"] == "assistant" and previous_request else None
        if context_event not in contexts:
            prefix = "Title: " + source.title
            if context_event is not None:
                prefix += "\nPrevious request: " + previous_request["text"]
            contexts[context_event] = bounded_context(tokenizer, prefix)
        prefix, limited = contexts[context_event]
        for start, end in split_spans(text, tokenizer, profile):
            body = text[start:end]
            actual = prefix + "\n\n" + body
            if len(tokenizer.encode(actual, add_special_tokens=True)) > 1024:
                raise ValueError("MOLECULE_INPUT_TOO_LONG")
            locator = {"block_id": block["id"], "role": block["role"], "start": start, "end": end,
                       "line_start": text.count("\n", 0, start) + 1,
                       "line_end": text.count("\n", 0, end) + 1,
                       "context_event": context_event, "context_limited": limited}
            yield {"ordinal": ordinal, "text": body, "context": prefix, "input": actual,
                   "input_hash": digest(actual), "body_hash": digest(body), "locator": locator}
            ordinal += 1
        if block["role"] == "user":
            previous_request = block
