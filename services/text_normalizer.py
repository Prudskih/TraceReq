
from __future__ import annotations

def normalize_text(value: str, lower: bool = True) -> str:
    """Убирает лишние пробелы и приводит текст к нижнему регистру."""
    normalized = " ".join((value or "").strip().split())
    return normalized.lower() if lower else normalized