"""Match source-established skill identifiers, without interpreting use wording."""

import re
from collections import defaultdict
from typing import Iterable, Set


class SkillReferenceMatcher:
    """A named reference is evidence of discussion, not proof of application."""

    def __init__(self, names: Iterable[str]):
        aliases = defaultdict(set)
        canonical = {}
        for name in names:
            canonical.setdefault(name.casefold(), name)
        for name in canonical.values():
            aliases[name.casefold()].add(name)
            if ":" in name:
                aliases[name.rsplit(":", 1)[-1].casefold()].add(name)
        self.aliases = {alias: next(iter(values)) for alias, values in aliases.items()
                        if len(values) == 1}
        # Identifier boundaries, not language-specific particles or use verbs.
        self.pattern = re.compile(
            r"(?<![A-Za-z0-9_:/-])\$?(" + "|".join(
                re.escape(alias) for alias in sorted(self.aliases, key=len, reverse=True)
            ) + r")(?![A-Za-z0-9_:/-])",
        ) if self.aliases else None

    def match(self, text: str) -> Set[str]:
        if self.pattern is None:
            return set()
        return {self.aliases[match.group(1)]
                for match in self.pattern.finditer(text.casefold())}
