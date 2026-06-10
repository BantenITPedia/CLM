from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect

from .models import ParticipantRole, ContractPermission, ContractRolePermission, ContractStatus


PERMISSION_ROLE_MAP = {
    ContractPermission.VIEW_CONTRACT: {
        ParticipantRole.OWNER,
        ParticipantRole.SALES,
        ParticipantRole.LEGAL,
        ParticipantRole.CUSTOMER,
        ParticipantRole.APPROVER,
        ParticipantRole.SIGNATORY,
    },
    ContractPermission.EDIT_CONTRACT: {
        ParticipantRole.OWNER,
        ParticipantRole.LEGAL,
    },
    ContractPermission.DELETE_CONTRACT: {
        ParticipantRole.OWNER,
    },
    ContractPermission.UPDATE_STATUS: {
        ParticipantRole.OWNER,
        ParticipantRole.LEGAL,
    },
    ContractPermission.MANAGE_PARTICIPANTS: {
        ParticipantRole.OWNER,
        ParticipantRole.LEGAL,
    },
    ContractPermission.ADD_DOCUMENT: {
        ParticipantRole.OWNER,
        ParticipantRole.LEGAL,
    },
    ContractPermission.UPLOAD_FINAL_DOCUMENT: {
        ParticipantRole.LEGAL,
    },
    ContractPermission.ADD_COMMENT: {
        ParticipantRole.OWNER,
        ParticipantRole.LEGAL,
        ParticipantRole.CUSTOMER,
        ParticipantRole.APPROVER,
    },
    ContractPermission.EDIT_STRUCTURED_DATA: {
        ParticipantRole.OWNER,
        ParticipantRole.LEGAL,
    },
    ContractPermission.REGENERATE_DRAFT: {
        ParticipantRole.LEGAL,
    },
}

PERMISSION_LABELS = {
    ContractPermission.VIEW_CONTRACT: 'View contract',
    ContractPermission.EDIT_CONTRACT: 'Edit contract',
    ContractPermission.DELETE_CONTRACT: 'Delete contract',
    ContractPermission.UPDATE_STATUS: 'Update status',
    ContractPermission.MANAGE_PARTICIPANTS: 'Manage participants',
    ContractPermission.ADD_DOCUMENT: 'Add documents',
    ContractPermission.UPLOAD_FINAL_DOCUMENT: 'Upload final approved document',
    ContractPermission.ADD_COMMENT: 'Add comments',
    ContractPermission.EDIT_STRUCTURED_DATA: 'Edit structured data',
    ContractPermission.REGENERATE_DRAFT: 'Regenerate drafts',
}


WORKFLOW_TRANSITION_MAP = {
    ContractStatus.DRAFT: {
        # User submission should move directly to legal review.
        ParticipantRole.OWNER: {ContractStatus.LEGAL_REVIEW},
    },
    # Legal picks up from submitted → starts review. Data/doc revision requests
    # send contracts back to DRAFT through dedicated revision endpoints, not status form.
    ContractStatus.SUBMITTED: {
        ParticipantRole.LEGAL: {ContractStatus.LEGAL_REVIEW},
    },
    # Legal final decision: approve (all OK) or terminate (permanently rejected).
    ContractStatus.LEGAL_REVIEW: {
        ParticipantRole.LEGAL: {ContractStatus.APPROVED, ContractStatus.TERMINATED},
    },
    # ACTIVE is set automatically when legal uploads the final signed document.
    ContractStatus.APPROVED: {
        ParticipantRole.LEGAL: {ContractStatus.TERMINATED},
    },
    ContractStatus.ACTIVE: {
        ParticipantRole.LEGAL: {ContractStatus.TERMINATED},
    },
    ContractStatus.EXPIRING_SOON: {
        ParticipantRole.LEGAL: {ContractStatus.ACTIVE, ContractStatus.TERMINATED},
    },
    ContractStatus.TERMINATED: {},
}


class GlobalPermission:
    """Centralized global permission codenames for app-level RBAC checks."""

    MANAGE_COMPANY_SETTINGS = 'change_companyprofile'
    VIEW_PERMISSION_MATRIX = 'view_contractrolepermission'


def has_global_permission(user, permission_codename):
    """Return whether user has a global Django permission in contracts app."""
    if not user or not user.is_authenticated:
        return False

    if user.is_superuser:
        return True

    full_permission = permission_codename
    if '.' not in permission_codename:
        full_permission = f'contracts.{permission_codename}'

    return user.has_perm(full_permission)


def require_global_permission(permission_codename, error_message='You do not have permission to access this page.'):
    """Decorator to enforce global app-level permission and redirect safely."""

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if has_global_permission(request.user, permission_codename):
                return view_func(request, *args, **kwargs)

            messages.error(request, error_message)
            return redirect('dashboard')

        return _wrapped_view

    return decorator


def get_user_roles(contract, user):
    roles = set()
    if not user or not user.is_authenticated:
        return roles

    if contract and contract.owner_id == user.id:
        roles.add(ParticipantRole.OWNER)

    if contract:
        participant_roles = contract.participants.filter(
            user=user,
            is_active=True
        ).values_list('role', flat=True)
        roles.update(participant_roles)

    return roles


def is_legal_team_user(user):
    """Legal team has full contract access across the system."""
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return user.groups.filter(name__in=['CLM Legal', 'CLM Admin', 'Legal Team']).exists()


def _get_db_permissions():
    try:
        entries = ContractRolePermission.objects.all()
        if not entries.exists():
            return None
    except Exception:
        return None

    permission_map = {}
    for entry in entries:
        permission_map.setdefault(entry.permission, {})[entry.role] = entry.allowed
    return permission_map


def has_contract_permission(user, contract, permission):
    if not user or not user.is_authenticated or not contract:
        return False

    if is_legal_team_user(user):
        return True

    roles = get_user_roles(contract, user)
    if not roles:
        return False

    try:
        permission_key = ContractPermission(permission)
    except ValueError:
        return False

    # Explicit policy override: standalone sales users are read-only.
    if (
        ParticipantRole.SALES in roles
        and ParticipantRole.OWNER not in roles
        and ParticipantRole.LEGAL not in roles
    ):
        return permission_key == ContractPermission.VIEW_CONTRACT

    db_permissions = _get_db_permissions()
    if db_permissions is not None:
        role_map = db_permissions.get(permission_key, {})
        return any(role_map.get(role, False) for role in roles)

    allowed_roles = PERMISSION_ROLE_MAP.get(permission_key, set())
    return any(role in allowed_roles for role in roles)


def can_view_contract(user, contract):
    return has_contract_permission(user, contract, ContractPermission.VIEW_CONTRACT)


def can_edit_contract(user, contract):
    if not user or not user.is_authenticated or not contract:
        return False

    if is_legal_team_user(user):
        return True

    if not has_contract_permission(user, contract, ContractPermission.EDIT_CONTRACT):
        return False

    # Owners can edit only before final legal approval.
    if contract.owner_id == user.id and contract.status in {
        ContractStatus.APPROVED,
        ContractStatus.ACTIVE,
        ContractStatus.EXPIRING_SOON,
        ContractStatus.TERMINATED,
    }:
        return False

    return True


def can_delete_contract(user, contract):
    if not user or not user.is_authenticated or not contract:
        return False

    # Default policy: delete only while still in early workflow.
    if contract.status in {ContractStatus.DRAFT, ContractStatus.SUBMITTED}:
        return has_contract_permission(user, contract, ContractPermission.DELETE_CONTRACT)

    # Exception policy: only superuser can delete beyond Draft/Submitted.
    if user.is_superuser:
        return has_contract_permission(user, contract, ContractPermission.DELETE_CONTRACT)

    return False


def can_update_contract_status(user, contract):
    return bool(get_allowed_next_statuses(user, contract))


def can_manage_participants(user, contract):
    return has_contract_permission(user, contract, ContractPermission.MANAGE_PARTICIPANTS)


def can_add_document(user, contract):
    if not user or not user.is_authenticated or not contract:
        return False

    if is_legal_team_user(user):
        return True

    if not has_contract_permission(user, contract, ContractPermission.ADD_DOCUMENT):
        return False

    if contract.owner_id == user.id and contract.status in {
        ContractStatus.APPROVED,
        ContractStatus.ACTIVE,
        ContractStatus.EXPIRING_SOON,
        ContractStatus.TERMINATED,
    }:
        return False

    return True


def can_add_comment(user, contract):
    return has_contract_permission(user, contract, ContractPermission.ADD_COMMENT)


def can_edit_contract_data(user, contract):
    if not user or not user.is_authenticated or not contract:
        return False

    if is_legal_team_user(user):
        return True

    if not has_contract_permission(user, contract, ContractPermission.EDIT_STRUCTURED_DATA):
        return False

    if contract.owner_id == user.id and contract.status in {
        ContractStatus.APPROVED,
        ContractStatus.ACTIVE,
        ContractStatus.EXPIRING_SOON,
        ContractStatus.TERMINATED,
    }:
        return False

    return True


def can_regenerate_draft(user, contract):
    return has_contract_permission(user, contract, ContractPermission.REGENERATE_DRAFT)


def get_allowed_next_statuses(user, contract):
    if not user or not user.is_authenticated or not contract:
        return set()

    if is_legal_team_user(user):
        return {choice[0] for choice in ContractStatus.choices if choice[0] != contract.status}

    if not has_contract_permission(user, contract, ContractPermission.UPDATE_STATUS):
        return set()

    current_status = contract.status
    transitions_by_role = WORKFLOW_TRANSITION_MAP.get(current_status, {})
    roles = get_user_roles(contract, user)

    allowed_statuses = set()
    for role in roles:
        allowed_statuses.update(transitions_by_role.get(role, set()))

    return allowed_statuses


def can_transition_to_status(user, contract, next_status):
    if not next_status:
        return False
    return next_status in get_allowed_next_statuses(user, contract)
