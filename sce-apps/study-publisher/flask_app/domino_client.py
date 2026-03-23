"""Domino Public API client for Study Publisher.

All calls use either a JWT Bearer token (Enhanced/Extended Identity) or a
DominoApiKey (service-account API key from the DOMINO_USER_API_KEY env var).
The JWT is preferred because it scopes calls to the current user's permissions.
"""
from __future__ import annotations

import logging
import os
import re
from typing import Optional

import requests

logger = logging.getLogger(__name__)

_DOMINO_API_HOST = os.environ.get(
    'DOMINO_API_HOST', 'http://nucleus-frontend.domino-platform'
).rstrip('/')
_SERVICE_API_KEY = os.environ.get('DOMINO_USER_API_KEY', '')

# Matches study-code prefixed project names, e.g. "ABC123-MyTrial"
_STUDY_PREFIX_RE = re.compile(r'^([A-Z0-9]{6})-')

_REQUEST_TIMEOUT = 15  # seconds


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _auth_headers(jwt_token: str | None = None) -> dict:
    """Return auth headers, preferring JWT over the service-account API key."""
    if jwt_token:
        return {'Authorization': f'Bearer {jwt_token}', 'Content-Type': 'application/json'}
    if _SERVICE_API_KEY:
        return {'X-Domino-Api-Key': _SERVICE_API_KEY, 'Content-Type': 'application/json'}
    raise RuntimeError(
        'No Domino credentials available. Set DOMINO_USER_API_KEY or enable '
        'Enhanced Identity so the app receives an Authorization header.'
    )


def _get_paginated(path: str, list_key: str, jwt_token: str | None = None) -> list:
    """Fetch all pages of a paginated Domino list endpoint."""
    results = []
    offset, limit = 0, 100
    while True:
        resp = requests.get(
            f'{_DOMINO_API_HOST}{path}',
            headers=_auth_headers(jwt_token),
            params={'offset': offset, 'limit': limit},
            timeout=_REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        batch = resp.json().get(list_key, [])
        results.extend(batch)
        if len(batch) < limit:
            break
        offset += limit
    return results


# ---------------------------------------------------------------------------
# User resolution
# ---------------------------------------------------------------------------

def get_self(jwt_token: str | None = None) -> dict:
    """Return the current user's profile from GET /v4/users/self.

    Response contains at least: userName, id (plus other profile fields).
    Raises requests.HTTPError on non-2xx responses.
    """
    resp = requests.get(
        f'{_DOMINO_API_HOST}/v4/users/self',
        headers=_auth_headers(jwt_token),
        timeout=_REQUEST_TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json()


# ---------------------------------------------------------------------------
# Project queries
# ---------------------------------------------------------------------------

def get_user_study_projects(
    username: str,
    user_id: str | None,
    valid_codes: set[str],
    jwt_token: str | None = None,
) -> list[dict]:
    """Return study projects visible to the caller where the user is owner or collaborator.

    A project is a study project when its name begins with a recognised study code.
    `valid_codes` is the set of codes from codes.json (source of truth).
    """
    all_projects = _get_paginated('/api/projects/beta/projects', 'projects', jwt_token)

    result = []
    for p in all_projects:
        # Ownership check
        is_owner = p.get('ownerUsername') == username
        # Collaboration check — collaborators only expose {id, role}
        is_collaborator = (
            user_id is not None
            and any(c.get('id') == user_id for c in p.get('collaborators', []))
        )
        if not (is_owner or is_collaborator):
            continue

        m = _STUDY_PREFIX_RE.match(p.get('name', ''))
        if m and m.group(1) in valid_codes:
            result.append({**p, 'study_code': m.group(1)})

    return result


def get_all_study_codes_in_use(
    valid_codes: set[str],
    jwt_token: str | None = None,
) -> set[str]:
    """Return the set of study codes that already have at least one project."""
    all_projects = _get_paginated('/api/projects/beta/projects', 'projects', jwt_token)
    in_use = set()
    for p in all_projects:
        m = _STUDY_PREFIX_RE.match(p.get('name', ''))
        if m and m.group(1) in valid_codes:
            in_use.add(m.group(1))
    return in_use


# ---------------------------------------------------------------------------
# Project creation
# ---------------------------------------------------------------------------

def create_project(
    name: str,
    description: str,
    owner_id: str | None = None,
    visibility: str = 'private',
    jwt_token: str | None = None,
) -> dict:
    """Create a new Domino project and return the response JSON."""
    payload: dict = {
        'name': name,
        'description': description,
        'visibility': visibility,
    }
    if owner_id:
        payload['ownerId'] = owner_id

    resp = requests.post(
        f'{_DOMINO_API_HOST}/api/projects/beta/projects',
        headers=_auth_headers(jwt_token),
        json=payload,
        timeout=_REQUEST_TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json()


def add_project_tag(project_id: str, tag_name: str, jwt_token: str | None = None) -> bool:
    """Attach a tag to a project via POST /v4/projects/{projectId}/tags.

    Payload: {"tagNames": ["<tag>"]}

    Failures are logged as warnings rather than raised so that they do not
    block project creation — the study code is already encoded in the name.
    """
    url = f'{_DOMINO_API_HOST}/v4/projects/{project_id}/tags'
    try:
        resp = requests.post(
            url,
            headers=_auth_headers(jwt_token),
            json={'tagNames': [tag_name]},
            timeout=_REQUEST_TIMEOUT,
        )
        if resp.status_code == 404:
            logger.warning(
                'Project tag endpoint not found (v4 unavailable); '
                'tag "%s" not applied to project %s.',
                tag_name, project_id,
            )
            return False
        resp.raise_for_status()
        return True
    except requests.RequestException as exc:
        logger.warning('Failed to tag project %s with "%s": %s', project_id, tag_name, exc)
        return False
