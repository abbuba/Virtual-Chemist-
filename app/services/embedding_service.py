import hashlib
import math
import re

DIM = 384
_STOP = {"a", "an", "the", "and", "or", "of", "to", "in", "is", "it", "for", "with", "that", "as", "by", "on", "at", "from", "are", "be", "can", "its", "this", "into", "than"}


def _bucket(token: str) -> tuple[int, float]:
    h = hashlib.md5(token.encode()).digest()
    return int.from_bytes(h[:4], "big") % DIM, 1.0 if h[4] % 2 else -1.0


def embed_text(text: str) -> list[float]:
    """Turns text into a 384-number vector (hashing trick, no model download)."""
    return _hash_embed(text)


def _hash_embed(text: str) -> list[float]:
    """Turns text into a 384-number vector. Similar wording gives similar vectors.

    Words and 3-letter pieces are hashed into slots (the "hashing trick"), so
    "poison" also matches "poisonous". No model download or internet is needed.
    """
    vec = [0.0] * DIM
    for word in re.findall(r"[a-z0-9]+", text.lower()):
        if word in _STOP:
            continue
        slot, sign = _bucket("w:" + word)
        vec[slot] += 2.0 * sign
        padded = f"#{word}#"
        for i in range(len(padded) - 2):
            slot, sign = _bucket("t:" + padded[i:i + 3])
            vec[slot] += sign
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [round(v / norm, 6) for v in vec]


def molecule_text(formula, name, description, safety, uses) -> str:
    return f"{name}. {name}. {formula}. {description} {uses} {safety}"
