"""Keyboard builders for the HQ bot."""

from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from src.domain.enums import PermissionKey
from src.domain.models import User


def main_menu_keyboard(user: User) -> InlineKeyboardMarkup:
    """Build the main menu keyboard based on user permissions.

    Buttons are shown based on actual permissions —
    this is a UI hint only; backend always re-verifies.
    """
    buttons: list[list[InlineKeyboardButton]] = []

    # Everyone can see their info
    buttons.append(
        [InlineKeyboardButton(text="👤 My Profile", callback_data="profile")]
    )

    if user.has_permission(PermissionKey.USERS_VIEW):
        buttons.append(
            [InlineKeyboardButton(text="👥 Users", callback_data="users_list")]
        )

    if user.has_permission(PermissionKey.STAFF_VIEW):
        buttons.append(
            [InlineKeyboardButton(text="💼 Staff", callback_data="staff_list")]
        )

    if user.has_permission(PermissionKey.ROLES_VIEW):
        buttons.append(
            [
                InlineKeyboardButton(
                    text="🛠 Roles & Permissions",
                    callback_data="roles_view",
                )
            ]
        )

    if user.has_permission(PermissionKey.SYSTEM_AUDIT):
        buttons.append(
            [InlineKeyboardButton(text="📝 Audit Log", callback_data="audit_log")]
        )

    if user.has_permission(PermissionKey.SYSTEM_SETTINGS):
        buttons.append(
            [
                InlineKeyboardButton(
                    text="⚙️ Settings", callback_data="settings"
                )
            ]
        )

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def back_button(callback_data: str = "main_menu") -> InlineKeyboardMarkup:
    """Single back button."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Back", callback_data=callback_data)]
        ]
    )
