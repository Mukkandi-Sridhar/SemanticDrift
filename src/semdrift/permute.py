"""Generate reproducible tool orders shared across experiment conditions."""

import random
from typing import Any

from .data import digest


def perm(repeat_r: int, seed: int, names: list[str]) -> list[str]:
    order = list(names)
    random.Random(f"{seed}:{repeat_r}").shuffle(order)
    return order


def permutations(k: int, seed: int, names: list[str]) -> list[dict[str, Any]]:
    return [
        {
            "repeat": r,
            "permutation_id": digest(perm(r, seed, names)),
            "tool_order": perm(r, seed, names),
        }
        for r in range(k)
    ]
