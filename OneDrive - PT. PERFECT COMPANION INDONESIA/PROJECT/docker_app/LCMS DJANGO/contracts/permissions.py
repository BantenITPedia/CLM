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
        ParticipantRole.SALES,
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
        ParticipantRole.SALES,
        ParticipantRole.LEGAL,
    },
    ContractPermission.UPLOAD_FINAL_DOCUMENT: {
        ParticipantRole.OWNER,
        ParticipantRole.LEGAL,
    },
    ContractPermission.ADD_COMMENT: {
        ParticipantRole.OWNER,
        ParticipantRole.SALES,
        ParticipantRole.LEGAL,
        ParticipantRole.CUSTOMER,
        ParticipantRole.APPROVER,
    },
    ContractPermission.EDIT_STRUCTURED_DATA: {
        ParticipantRole.OWNER,
        ParticipantRole.SALES,
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
        ParticipantRole.OWNER: {ContractStatus.SUBMITTED},
        ParticipantRole.SALES: {ContractStatus.SUBMITTED},
    },
    ContractStatus.SUBMITTED: {
        ParticipantRole.LEGAL: {ContractStatus.LEGAL_REVIEW, ContractStatus.DRAFT},
    },
    ContractStatus.LEGAL_REVIEW: {
        ParticipantRole.LEGAL: {ContractStatus.APPROVED, ContractStatus.DRAFT},
    },
    ContractStatus.APPROVED: {
        ParticipantRole.LEGAL: {ContractStatus.SIGNED, ContractStatus.TERMINATED},
    },
    ContractStatus.SIGNED: {
        ParticipantRole.LEGAL: {ContractStatus.ACTIVE, ContractStatus.TERMINATED},
    },
    ContractStatus.ACTIVE: {
        ParticipantRole.LEGAL: {ContractStatus.EXPIRING_SOON, ContractStatus.TERMINATED},
    },
    ContractStatus.EXPIRING_SOON: {
        ParticipantRole.LEGAL: {ContractStatus.ACTIVE, ContractStatus.TERMINATED},
    },
    ContractStatus.TERMINATED: {},
}


def get_user_roles(contract, user):
    roles = set()
    if not user or not user.is_authenticated:
        return roles

    if user.is_staff:
        roles.add('STAFF')

    if contract and contract.owner_id == user.id:
        roles.add(ParticipantRole.OWNER)

    if contract:
        participant_roles = contract.participants.filter(
            user=user,
            is_active=True
        ).values_list('role', flat=True)
        roles.update(participant_roles)

    return roles


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

    if user.is_staff:
        return True

    roles = get_user_roles(contract, user)
    if not roles:
        return False

    try:
        permission_key = ContractPermission(permission)
    except ValueError:
        return False

    db_permissions = _get_db_permissions()
    if db_permissions is not None:
        role_map = db_permissions.get(permission_key, {})
        return any(role_map.get(role, False) for role in roles)

    allowed_roles = PERMISSION_ROLE_MAP.get(permission_key, set())
    return any(role in allowed_roles for role in roles)


def can_view_contract(user, contract):
    return has_contract_permission(user, contract, ContractPermission.VIEW_CONTRACT)


def can_edit_contract(user, contract):
    return has_contract_permission(user, contract, ContractPermission.EDIT_CONTRACT)


def can_delete_contract(user, contract):
    if not user or not user.is_authenticated or not contract:
        return False

    if contract.status not in {ContractStatus.DRAFT, ContractStatus.SUBMITTED}:
        return False

    return has_contract_permission(user, contract, ContractPermission.DELETE_CONTRACT)


def can_update_contract_status(user, contract):
    return bool(get_allowed_next_statuses(user, contract))


def can_manage_participants(user, contract):
    return has_contract_permission(user, contract, ContractPermission.MANAGE_PARTICIPANTS)


def can_add_document(user, contract):
    return has_contract_permission(user, contract, ContractPermission.ADD_DOCUMENT)


def can_add_comment(user, contract):
    return has_contract_permission(user, contract, ContractPermission.ADD_COMMENT)


def can_edit_contract_data(user, contract):
    return has_contract_permission(user, contract, ContractPermission.EDIT_STRUCTURED_DATA)


def can_regenerate_draft(user, contract):
    return has_contract_permission(user, contract, ContractPermission.REGENERATE_DRAFT)


def get_allowed_next_statuses(user, contract):
    if not user or not user.is_authenticated or not contract:
        return set()

    if user.is_superuser:
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
