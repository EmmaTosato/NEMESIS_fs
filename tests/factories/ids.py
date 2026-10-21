"""ID di soggetto sintetici nel formato reale (`sub-<gruppo><SITO><nnnn>`, vedi `src/utils/subject_ids.py`)."""

from __future__ import annotations

DEFAULT_SITE = "UNIPD"


def subject_id(index: int, site: str = DEFAULT_SITE, group: str = "ST") -> str:
    """`sub-STUNIPD0003`; `group="HC"` dà un controllo sano (`sub-STUNIPDHC0003` nel formato reale)."""
    if group == "ST":
        return f"sub-ST{site}{index:04d}"
    if group == "HC":
        return f"sub-ST{site}HC{index:04d}"
    raise ValueError(f"gruppo sconosciuto {group!r}: attesi 'ST' o 'HC'")


def subject_ids(n: int, site: str = DEFAULT_SITE) -> list[str]:
    return [subject_id(i, site) for i in range(n)]
