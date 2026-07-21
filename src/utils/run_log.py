"""Append-only per-method run history (RUNS.md), separate from a single run's own config.md.

A run's README/report describe that one run in isolation. RUNS.md answers a
different question - "how does this run differ from the previous ones, and
why" - across every run (tuning sweep or production) that ever wrote into a
given method folder. Never overwritten, never atomic (a log, not a primary
artifact - same tier as reports/logs, see docs/dev/design_patterns.md).
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


def append_run_log_entry(
    runs_md_path: Path,
    session_name: str,
    now: datetime,
    run_type: str,
    params_summary: dict,
    output_dir: Path,
    run_notes: str | None,
    session_description_extra: str | None = None,
) -> None:
    """Append one entry to runs_md_path, creating it (with a title) if absent.

    run_type distinguishes a fine-tuning sweep from a production run in the
    same log, without splitting them into separate files - seeing both in
    one chronological history is the point (e.g. "s2 used the params the
    20-07 tuning sweep in this same file found best").
    """
    import re
    
    # Extract session number (e.g. s1 -> 1, umap_s2.1_p50 -> 2.1)
    # We look for `s` followed by digits (and optional decimal) that is followed by either `_` or end of string.
    # We also ensure it's preceded by `_` or is at the beginning of the string to avoid matching `pas1`.
    match = re.search(r'(?:^|_)s(\d+(?:\.\d+)?)(?:_|$)', session_name)
    session_num = match.group(1) if match else "1"
    session_header = f"## Session {session_num}"
    
    # Format: ### <session_name> - <date>
    entry_lines = [
        f"### {session_name} — {now.strftime('%d-%m-%y %H:%M')}",
        "",
        f"Params: {json.dumps(params_summary)}",
        f"Output: {output_dir}"
    ]
    if run_notes:
        entry_lines.append(f"Note: {run_notes}")
    entry_lines.append("")
    new_entry = "\n".join(entry_lines)

    runs_md_path.parent.mkdir(parents=True, exist_ok=True)
    
    if not runs_md_path.is_file():
        file_content = f"# Run history — {runs_md_path.parent.name}\n\n"
    else:
        file_content = runs_md_path.read_text()

    if session_header not in file_content:
        # If we are in results/, fetch session description from data/derived/*/SESSIONS.md
        # We can find it by looking for the first SESSIONS.md in data/derived/ that has this session
        session_desc = ""
        
        # Try to find an existing session description from any data/derived/*/SESSIONS.md
        for sessions_md in Path("data/derived").rglob("SESSIONS.md"):
            if sessions_md.is_file():
                content = sessions_md.read_text()
                lm_match = re.search(rf'^{session_header}\n(.*?)(?=^### |^## Session |\Z)', content, flags=re.MULTILINE | re.DOTALL)
                if lm_match:
                    session_desc = lm_match.group(1).strip()
                    break
        
        if session_description_extra:
            if session_desc:
                session_desc += f"\n{session_description_extra}"
            else:
                session_desc = session_description_extra
                
        file_content += f"\n{session_header}\n{session_desc}\n\n"
    
    # Insert new_entry at the end of the `## Session N` block
    pattern = rf'^{session_header}.*?(?=^## Session |\Z)'
    match = re.search(pattern, file_content, flags=re.MULTILINE | re.DOTALL)
    if match:
        section_text = match.group(0).rstrip()
        new_section_text = section_text + "\n\n" + new_entry + "\n"
        file_content = file_content[:match.start()] + new_section_text + file_content[match.end():]
    else:
        file_content += new_entry
        
    runs_md_path.write_text(file_content)
