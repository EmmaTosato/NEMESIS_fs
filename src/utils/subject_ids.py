"""Subject-ID naming convention: `sub-<DISEASE><SITE>[HC]<NUM>`, and the group
('ST' | 'HC' | 'PD' | 'GM') it encodes.

The one place that parses a subject id - every layer that discovers subjects
from the filesystem (features, metadata, scripts) reuses `group_of` instead of
re-deriving the regex. See docs/guides/datasets.md ("Naming dei soggetti") for
why the site list is closed.
"""

from __future__ import annotations

import re

KNOWN_GROUPS = ("ST", "HC", "PD", "GM")

# Every site code seen across the in-scope datasets' real subject IDs -
# deliberately a closed, explicit list, not `[A-Z]+?` free-form matching.
KNOWN_SITES = ("UNIPD", "UKLFR", "UCLUK", "UKE")
_SITE_ALTERNATION = "|".join(sorted(KNOWN_SITES, key=len, reverse=True))
_SUBJECT_RE = re.compile(rf"^sub-(?P<disease>ST|PD|GM)(?P<site>{_SITE_ALTERNATION})(?P<hc>HC)?(?P<num>\d+)$")


def group_of(subject_id: str) -> str:
    """Group of a subject_id ('ST' | 'HC' | 'PD' | 'GM'), from its naming.

    Raises ValueError both for a malformed subject_id and for one whose site
    code isn't in KNOWN_SITES - a genuinely new site must be added by a human,
    never inferred.
    """
    match = _SUBJECT_RE.match(subject_id)
    if match is None:
        raise ValueError(f"subject_id does not match expected naming: {subject_id!r}")
    return "HC" if match.group("hc") else match.group("disease")
