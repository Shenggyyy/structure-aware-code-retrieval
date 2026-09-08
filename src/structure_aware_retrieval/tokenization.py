"""Shared, versioned lexical preprocessing for code and queries."""

import re

TOKENIZER_VERSION = 1
WORDS = re.compile(r"[^\W_]+(?:_[^\W_]+)*", re.UNICODE)
PARTS = re.compile(r"_+|(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])")


def tokenize_code(text: str) -> list[str]:
    """Keep complete identifiers and their components without stemming/stopwords."""
    tokens: list[str] = []
    for word in WORDS.findall(text):
        tokens.append(word.casefold())
        parts = PARTS.split(word)
        if len(parts) > 1:
            tokens.extend(part.casefold() for part in parts if part)
    return tokens
