"""Study Publisher route handlers."""
from __future__ import annotations

import logging
import secrets

from flask import (
    Blueprint,
    abort,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from .data_store import (
    get_all_study_codes,
    get_authorized_code_details,
    record_signature,
)
from .domino_client import (
    add_project_tag,
    create_project,
    get_all_study_codes_in_use,
    get_self,
    get_user_study_projects,
)
from .utils import (
    is_valid_study_code,
    sanitize_name_suffix,
    sanitize_text,
)

logger = logging.getLogger(__name__)
main = Blueprint('main', __name__)

TERMS_VERSION = '1.0'


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_identity() -> tuple[str, str | None, str | None]:
    """Return (username, user_id, jwt_token) for the current request.

    The JWT is extracted from the Authorization: Bearer header and used to
    call GET /v4/users/self, which is the authoritative source of the caller's
    userName and id. Aborts 401 if the call fails or returns no userName.
    """
    auth_header = request.headers.get('Authorization', '')
    jwt_token = auth_header[7:].strip() if auth_header.startswith('Bearer ') else None

    try:
        profile = get_self(jwt_token)
    except Exception as exc:  # noqa: BLE001
        logger.exception('GET /v4/users/self failed')
        abort(401, description=f'Could not resolve caller identity: {exc}')

    username = profile.get('userName', '').strip()
    user_id = profile.get('id', '').strip() or None

    if not username:
        abort(401, description='GET /v4/users/self returned no userName.')

    return username, user_id, jwt_token


def _csrf_token() -> str:
    """Return (and create if needed) a CSRF token stored in the session."""
    if '_csrf_token' not in session:
        session['_csrf_token'] = secrets.token_hex(32)
    return session['_csrf_token']


def _validate_csrf(form_token: str) -> None:
    """Abort 400 if the submitted CSRF token doesn't match the session token."""
    expected = session.get('_csrf_token')
    if not expected or not secrets.compare_digest(expected, form_token or ''):
        abort(400, description='Invalid or missing CSRF token.')


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@main.route('/')
def index():
    username, user_id, jwt_token = _get_identity()

    all_codes = get_all_study_codes()
    valid_codes = set(all_codes.keys())

    try:
        projects = get_user_study_projects(username, user_id, valid_codes, jwt_token)
    except Exception as exc:  # noqa: BLE001
        logger.exception('Failed to fetch projects for %s', username)
        return render_template(
            'index.html',
            username=username,
            projects=[],
            all_codes=all_codes,
            error=f'Could not load projects: {exc}',
            csrf_token=_csrf_token(),
        )

    # Annotate each project with its description from codes.json
    for p in projects:
        p['study_description'] = all_codes.get(p['study_code'], '')

    return render_template(
        'index.html',
        username=username,
        projects=projects,
        all_codes=all_codes,
        error=None,
        csrf_token=_csrf_token(),
    )


@main.route('/create', methods=['GET'])
def create_get():
    username, _user_id, jwt_token = _get_identity()

    all_codes = get_all_study_codes()
    valid_codes = set(all_codes.keys())
    authorized = get_authorized_code_details(username)

    if not authorized:
        return render_template(
            'create.html',
            username=username,
            authorized_codes=[],
            error='You are not authorised to create projects for any study code.',
            csrf_token=_csrf_token(),
        )

    try:
        in_use = get_all_study_codes_in_use(valid_codes, jwt_token)
    except Exception as exc:  # noqa: BLE001
        logger.exception('Failed to fetch existing study codes')
        in_use = set()

    # Only offer codes that haven't been used yet
    available = [c for c in authorized if c['code'] not in in_use]

    return render_template(
        'create.html',
        username=username,
        authorized_codes=available,
        error=None,
        csrf_token=_csrf_token(),
    )


@main.route('/create', methods=['POST'])
def create_post():
    username, _user_id, jwt_token = _get_identity()
    _validate_csrf(request.form.get('csrf_token', ''))

    # --- Validate study_code ---
    raw_code = request.form.get('study_code', '').strip().upper()
    if not is_valid_study_code(raw_code):
        return _create_error(username, 'Invalid study code format.', jwt_token)

    authorized_codes = [c['code'] for c in get_authorized_code_details(username)]
    if raw_code not in authorized_codes:
        return _create_error(username, 'You are not authorised to use that study code.', jwt_token)

    # --- Validate name suffix ---
    raw_suffix = request.form.get('name_suffix', '')
    name_suffix = sanitize_name_suffix(raw_suffix)
    if not name_suffix:
        return _create_error(username, 'Project name must contain valid characters (letters, digits, hyphens, underscores).', jwt_token)

    # --- Validate description ---
    raw_desc = request.form.get('description', '')
    description = sanitize_text(raw_desc, max_length=1000)
    if len(description) < 10:
        return _create_error(username, 'Description must be at least 10 characters.', jwt_token)

    # --- Check code not already in use ---
    all_codes = get_all_study_codes()
    valid_codes = set(all_codes.keys())
    try:
        in_use = get_all_study_codes_in_use(valid_codes, jwt_token)
    except Exception as exc:  # noqa: BLE001
        logger.exception('Could not verify study code availability')
        return _create_error(username, f'Could not verify study code availability: {exc}', jwt_token)

    if raw_code in in_use:
        return _create_error(
            username,
            f'Study code {raw_code} already has a project. '
            'Each study code may only be used once.',
            jwt_token,
        )

    # --- Compose full project name ---
    full_name = f'{raw_code}-{name_suffix}'

    # Store pending project data in session for the terms step
    session['pending_project'] = {
        'study_code': raw_code,
        'name': full_name,
        'description': description,
    }

    return redirect(url_for('main.terms_get'))


@main.route('/terms', methods=['GET'])
def terms_get():
    username, _user_id, _ = _get_identity()
    pending = session.get('pending_project')
    if not pending:
        return redirect(url_for('main.create_get'))

    return render_template(
        'terms.html',
        username=username,
        project_name=pending['name'],
        study_code=pending['study_code'],
        description=pending['description'],
        terms_version=TERMS_VERSION,
        csrf_token=_csrf_token(),
        error=None,
    )


@main.route('/terms', methods=['POST'])
def terms_post():
    username, user_id, jwt_token = _get_identity()
    _validate_csrf(request.form.get('csrf_token', ''))

    pending = session.get('pending_project')
    if not pending:
        abort(400, description='No pending project found. Please start again.')

    # --- Validate signature ---
    raw_sig = request.form.get('signature', '')
    signature = sanitize_text(raw_sig, max_length=200)
    if not signature:
        return render_template(
            'terms.html',
            username=username,
            project_name=pending['name'],
            study_code=pending['study_code'],
            description=pending['description'],
            terms_version=TERMS_VERSION,
            csrf_token=_csrf_token(),
            error='You must enter your digital signature to proceed.',
        )

    # --- Confirm checkbox ---
    if request.form.get('accept_terms') != 'yes':
        return render_template(
            'terms.html',
            username=username,
            project_name=pending['name'],
            study_code=pending['study_code'],
            description=pending['description'],
            terms_version=TERMS_VERSION,
            csrf_token=_csrf_token(),
            error='You must accept the Terms of Use to create a project.',
        )

    study_code = pending['study_code']
    project_name = pending['name']
    description = pending['description']

    # --- Final re-check: code must still be unused ---
    all_codes = get_all_study_codes()
    valid_codes = set(all_codes.keys())
    try:
        in_use = get_all_study_codes_in_use(valid_codes, jwt_token)
    except Exception as exc:  # noqa: BLE001
        logger.exception('Pre-creation code check failed')
        return _terms_error(username, pending, f'Could not verify study code: {exc}')

    if study_code in in_use:
        session.pop('pending_project', None)
        return _terms_error(
            username, pending,
            f'Study code {study_code} was taken by another project while you were reviewing the terms. Please start again.',
        )

    # --- Create the project ---
    try:
        project = create_project(
            name=project_name,
            description=description,
            owner_id=user_id,
            visibility='private',
            jwt_token=jwt_token,
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception('Project creation failed for %s / %s', username, project_name)
        return _terms_error(username, pending, f'Project creation failed: {exc}')

    project_id = project.get('id', '')

    # --- Tag the project (best-effort) ---
    tag_name = f'studyCode:{study_code}'
    add_project_tag(project_id, tag_name, jwt_token)

    # --- Record digital signature ---
    try:
        sig_path = record_signature(
            username=username,
            study_code=study_code,
            project_name=project_name,
            project_id=project_id,
            signature=signature,
            remote_addr=request.remote_addr or '',
            user_agent=request.user_agent.string or '',
            terms_version=TERMS_VERSION,
        )
        logger.info('Signature saved to %s', sig_path)
    except Exception as exc:  # noqa: BLE001
        # Signature failure is critical — log and surface the error without
        # leaving an un-signed project creation in a silent state.
        logger.exception('Signature write failed for %s / %s', username, project_name)
        return _terms_error(
            username, pending,
            f'Project was created (id={project_id}) but the signature could not be recorded: {exc}. '
            'Please contact your administrator.',
        )

    # --- Clean up session ---
    session.pop('pending_project', None)

    return redirect(url_for('main.success', project_id=project_id, project_name=project_name))


@main.route('/success')
def success():
    username, _user_id, _ = _get_identity()
    project_id = request.args.get('project_id', '')
    project_name = request.args.get('project_name', '')
    return render_template(
        'success.html',
        username=username,
        project_id=project_id,
        project_name=project_name,
    )


# ---------------------------------------------------------------------------
# Error-rendering helpers
# ---------------------------------------------------------------------------

def _create_error(username: str, message: str, jwt_token: str | None):
    all_codes = get_all_study_codes()
    valid_codes = set(all_codes.keys())
    authorized = get_authorized_code_details(username)
    try:
        in_use = get_all_study_codes_in_use(valid_codes, jwt_token)
    except Exception:  # noqa: BLE001
        in_use = set()
    available = [c for c in authorized if c['code'] not in in_use]
    return render_template(
        'create.html',
        username=username,
        authorized_codes=available,
        error=message,
        csrf_token=_csrf_token(),
    ), 400


def _terms_error(username: str, pending: dict, message: str):
    return render_template(
        'terms.html',
        username=username,
        project_name=pending['name'],
        study_code=pending['study_code'],
        description=pending['description'],
        terms_version=TERMS_VERSION,
        csrf_token=_csrf_token(),
        error=message,
    ), 400
