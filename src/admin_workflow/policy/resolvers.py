"""Policy resolvers — field ownership and role lookup.

FC-1: exactly one accountable owner per completion task. An unmapped field
resolves to the Intake Coordinator, never to "unassigned" — an unassigned task is
a task nobody is accountable for.
"""

from __future__ import annotations

from ..domain.models import Role
from .bundle import PolicyBundle


def owner_for_field(field_name: str, bundle: PolicyBundle) -> Role:
    mapping = bundle.field_owner_map
    family = mapping.get("field_families", {}).get(field_name)
    if family:
        role_id = mapping.get("mappings", {}).get(family)
        if role_id:
            return Role(role_id)
    return Role(mapping["default_owner"])


def queue_approver(queue_value: str) -> Role:
    return Role(f"{queue_value.lower()}_approver")
