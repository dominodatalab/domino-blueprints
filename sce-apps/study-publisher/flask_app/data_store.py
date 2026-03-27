"""Read-only access to the study dataset files plus signature writing."""
from __future__ import annotations

import json
import logging
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

DATASET_ROOT = Path(os.environ.get('STUDY_DATASET_PATH', '/domino/datasets/local/studyapp'))
CODES_FILE = DATASET_ROOT / 'codes.json'
AUTH_FILE = DATASET_ROOT / 'auth.json'
SIGNATURES_DIR = DATASET_ROOT / 'signatures'

# Filename-safe characters only (guards against path traversal in filenames)
_SAFE_FILENAME_RE = re.compile(r'[^A-Za-z0-9_.-]')


def _load_json(path: Path) -> dict:
    try:
        with path.open('r', encoding='utf-8') as fh:
            return json.load(fh)
    except FileNotFoundError:
        logger.error('Dataset file not found: %s', path)
        return {}
    except json.JSONDecodeError as exc:
        logger.error('Invalid JSON in %s: %s', path, exc)
        return {}


def get_all_study_codes() -> dict:
    """Return {studyCode: description} mapping from codes.json."""
    return _load_json(CODES_FILE)


def get_authorized_codes(username: str) -> list[str]:
    """Return the list of study codes the given user is authorised to use."""
    auth = _load_json(AUTH_FILE)
    return auth.get(username, [])


def get_authorized_code_details(username: str) -> list[dict]:
    """Return [{code, description}] for all codes the user is authorised to use."""
    all_codes = get_all_study_codes()
    authorized = get_authorized_codes(username)
    return [
        {'code': code, 'description': all_codes.get(code, '(no description)')}
        for code in authorized
        if code in all_codes
    ]


def record_signature(
    *,
    username: str,
    study_code: str,
    project_name: str,
    project_id: str,
    signature: str,
    remote_addr: str,
    user_agent: str,
    terms_version: str = '1.0',
) -> Path:
    """Persist the user's acceptance of the Terms of Use.

    Returns the path of the written signature file.
    Raises OSError if the file cannot be written.
    """
    SIGNATURES_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).isoformat()
    # Build a filename that is unique and contains no user-controlled path separators
    safe_user = _SAFE_FILENAME_RE.sub('_', username)
    safe_code = _SAFE_FILENAME_RE.sub('_', study_code)
    uid = uuid.uuid4().hex[:8]
    filename = f'{safe_user}_{safe_code}_{uid}.json'

    # Ensure the resolved path stays inside SIGNATURES_DIR (path traversal guard)
    target = (SIGNATURES_DIR / filename).resolve()
    if not str(target).startswith(str(SIGNATURES_DIR.resolve())):
        raise ValueError(f'Unsafe signature path: {target}')

    record = {
        'username': username,
        'study_code': study_code,
        'project_name': project_name,
        'project_id': project_id,
        'signature': signature,
        'timestamp': timestamp,
        'remote_addr': remote_addr,
        'user_agent': user_agent,
        'terms_version': terms_version,
    }

    with target.open('w', encoding='utf-8') as fh:
        json.dump(record, fh, indent=2)

    logger.info('Signature recorded: %s', target)
    return target
