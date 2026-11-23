"""Parse the cloudflared changelog files.

The GitHub release bodies of cloudflared only list checksums. The actual
changes live in two files of the cloudflared repository:

* ``RELEASE_NOTES``: a section per version, a version line followed by
  ``- <date> <change>`` lines.
* ``CHANGES.md``: ``## <version>`` sections with breaking changes, notices
  and new features (only for some versions).
"""

from __future__ import annotations

import re
from typing import Any

RELEASE_NOTES_URL = (
    "https://raw.githubusercontent.com/cloudflare/cloudflared/{tag}/RELEASE_NOTES"
)
CHANGES_URL = "https://raw.githubusercontent.com/cloudflare/cloudflared/{tag}/CHANGES.md"
RELEASE_NOTES_PAGE_URL = (
    "https://github.com/cloudflare/cloudflared/blob/{tag}/RELEASE_NOTES"
)
CHANGES_PAGE_URL = "https://github.com/cloudflare/cloudflared/blob/{tag}/CHANGES.md"

# Keep only the most recent versions; older ones are not useful as update notes.
MAX_VERSIONS = 40

_VERSION_LINE_RE = re.compile(r"^(\d+\.\d+\.\d+)\s*$")
_ENTRY_RE = re.compile(r"^-\s+(?:\d{4}-\d{2}-\d{2}\s+)?(.*\S)\s*$")
_CHANGES_HEADING_RE = re.compile(r"^##\s+(\d+\.\d+\.\d+)\s*$")


def parse_version(version: Any) -> tuple[int, ...] | None:
    """Parse a cloudflared version like '2026.11.2' into a comparable tuple."""
    if not isinstance(version, str):
        return None
    parts = version.strip().lstrip("v").split(".")
    try:
        return tuple(int(part) for part in parts)
    except ValueError:
        return None


def parse_release_notes(text: str) -> dict[str, list[str]]:
    """Parse RELEASE_NOTES into {version: [change, ...]}, newest first."""
    notes: dict[str, list[str]] = {}
    current: list[str] | None = None
    for line in text.splitlines():
        if match := _VERSION_LINE_RE.match(line):
            if len(notes) >= MAX_VERSIONS:
                break
            current = notes.setdefault(match.group(1), [])
        elif current is not None and (match := _ENTRY_RE.match(line)):
            current.append(match.group(1))
    return notes


def parse_changes(text: str) -> dict[str, str]:
    """Parse CHANGES.md into {version: markdown body}."""
    changes: dict[str, list[str]] = {}
    current: list[str] | None = None
    for line in text.splitlines():
        if match := _CHANGES_HEADING_RE.match(line):
            if len(changes) >= MAX_VERSIONS:
                break
            current = changes.setdefault(match.group(1), [])
        elif line.startswith("## "):
            current = None
        elif current is not None:
            # Demote headings one level so they nest under the version.
            current.append("#" + line if line.startswith("### ") else line)
    return {version: "\n".join(lines).strip() for version, lines in changes.items()}


def build_release_notes(
    installed: str | None,
    latest: str | None,
    notes: dict[str, list[str]] | None,
    changes: dict[str, str] | None,
    tag: str | None,
) -> str | None:
    """Return markdown notes for all versions newer than installed up to latest."""
    newest = parse_version(latest)
    if newest is None:
        return None
    current = parse_version(installed)

    versions = {
        version
        for version in (*(notes or {}), *(changes or {}))
        if (parsed := parse_version(version)) is not None
        and parsed <= newest
        and (current is None or current >= newest or parsed > current)
    }
    if current is None or current >= newest:
        # Nothing to upgrade (or unknown): show just the latest version.
        versions = {latest} & versions
    ordered = sorted(versions, key=parse_version, reverse=True)

    sections: list[str] = []
    has_changes = False
    for version in ordered:
        parts = [f"## {version}"]
        if changes and changes.get(version):
            has_changes = True
            parts.append(changes[version])
        if notes and notes.get(version):
            parts.append("\n".join(f"- {entry}" for entry in notes[version]))
        sections.append("\n\n".join(parts))

    if tag:
        links = [f"[Full release notes]({RELEASE_NOTES_PAGE_URL.format(tag=tag)})"]
        if has_changes:
            links.append(
                f"[Breaking changes and notices]({CHANGES_PAGE_URL.format(tag=tag)})"
            )
        sections.append(" · ".join(links))
    return "\n\n".join(sections) if sections else None
