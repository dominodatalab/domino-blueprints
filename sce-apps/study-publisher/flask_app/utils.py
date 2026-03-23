"""Input validation and sanitisation helpers."""
import re

# Study codes are exactly 6 uppercase alphanumeric characters, e.g. "ABC123"
STUDY_CODE_RE = re.compile(r'^[A-Z0-9]{6}$')

# Project names must start with a study code followed by a hyphen
STUDY_NAME_PREFIX_RE = re.compile(r'^([A-Z0-9]{6})-(.+)$')

# Allowed characters for the user-supplied name suffix (no spaces — Domino requirement)
_SAFE_NAME_CHARS_RE = re.compile(r'[^A-Za-z0-9_-]')


def is_valid_study_code(code: str) -> bool:
    return bool(code and STUDY_CODE_RE.match(str(code)))


def sanitize_name_suffix(raw: str, max_length: int = 80) -> str:
    """Return a Domino-safe project-name suffix.

    - Strips surrounding whitespace
    - Collapses internal whitespace to a single hyphen
    - Removes any remaining characters outside [A-Za-z0-9_-]
    - Truncates to max_length
    - Returns empty string if nothing valid remains
    """
    value = raw.strip()
    value = re.sub(r'\s+', '-', value)
    value = _SAFE_NAME_CHARS_RE.sub('', value)
    # Collapse multiple consecutive hyphens
    value = re.sub(r'-{2,}', '-', value).strip('-')
    return value[:max_length]


def sanitize_text(raw: str, max_length: int = 1000) -> str:
    """Sanitise a free-text field (description, signature).

    Strips leading/trailing whitespace and truncates. HTML rendering is
    handled by Jinja2's auto-escaping, so we don't HTML-encode here.
    """
    return raw.strip()[:max_length]


def extract_study_code(project_name: str):
    """Return the study code embedded in a project name, or None."""
    m = STUDY_NAME_PREFIX_RE.match(project_name or '')
    return m.group(1) if m else None
