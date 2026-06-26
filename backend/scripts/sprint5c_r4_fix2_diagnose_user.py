#!/usr/bin/env python3
"""Runtime diagnosis for Sprint 5C-R4-Fix-2 — inspect user RBAC state (no secrets)."""

from __future__ import annotations

import asyncio
import json
import sys

from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models import Role, User, UserRole
from app.services.rbac_service import get_effective_permissions


async def diagnose(username: str) -> None:
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.username == username))
        user = result.scalar_one_or_none()
        if not user:
            print(json.dumps({"error": f"user not found: {username}"}))
            return

        roles_result = await db.execute(
            select(Role)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(UserRole.user_id == user.id)
        )
        roles = roles_result.scalars().all()
        perms = await get_effective_permissions(db, user)
        master_data = sorted(p for p in perms if p.startswith("master_data"))
        access_control = sorted(p for p in perms if p.startswith("access_control"))
        users_perms = sorted(p for p in perms if p.startswith("users."))

        print(
            json.dumps(
                {
                    "username": user.username,
                    "legacy_role": user.role,
                    "is_active": user.is_active,
                    "rbac_roles": [
                        {
                            "code": r.code,
                            "display_name": r.display_name,
                            "is_system": r.is_system,
                            "is_active": r.is_active,
                        }
                        for r in roles
                    ],
                    "effective_permission_count": len(perms),
                    "access_control_permissions": access_control,
                    "users_permissions": users_perms,
                    "master_data_permissions": master_data,
                    "has_master_data_leak": bool(master_data),
                },
                indent=2,
            )
        )


if __name__ == "__main__":
    username = sys.argv[1] if len(sys.argv) > 1 else "testuser5"
    asyncio.run(diagnose(username))
