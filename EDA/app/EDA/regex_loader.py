# app/EDA/regex_loader.py
from __future__ import annotations
from typing import Dict, List, Set
import re
import yaml  # pip install pyyaml


class RegexConfig:
    def __init__(
        self,
        patterns: Dict[str, re.Pattern],
        order: List[str],
        macro_map: Dict[str, str],
        violent_set: Set[str],
    ):
        self.patterns = patterns
        self.order = order
        self.macro_map = macro_map
        self.violent_set = violent_set


def load_regex_config(path: str) -> RegexConfig:
    with open(path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    for required in ("patterns", "order", "macro_map", "violent_set"):
        if required not in cfg:
            raise ValueError(f"regex config missing '{required}'")

    raw_patterns = cfg["patterns"]
    if not isinstance(raw_patterns, dict) or not raw_patterns:
        raise ValueError("'patterns' must be a non-empty dict")

    patterns: Dict[str, re.Pattern] = {}
    for key, lst in raw_patterns.items():
        if isinstance(lst, str):
            lst = [lst]
        if not isinstance(lst, list) or not lst:
            raise ValueError(f"'patterns.{key}' must be list or string")
        union = "|".join(f"(?:{pat})" for pat in lst)
        patterns[key] = re.compile(union, re.IGNORECASE)

    order = list(cfg["order"])
    macro_map = dict(cfg["macro_map"])
    violent_set = set(cfg["violent_set"])

    for k in order:
        if k not in patterns:
            raise ValueError(f"'order' contains key with no pattern: {k}")

    return RegexConfig(
        patterns=patterns, order=order, macro_map=macro_map, violent_set=violent_set
    )
