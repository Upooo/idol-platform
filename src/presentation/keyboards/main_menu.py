"""Keyboard builders for the HQ bot."""

from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from src.domain.enums import PermissionKey
from src.domain.models import User


def main_menu_keyboard(user: User) -> InlineKeyboardMarkup:
    """Build main menu based on user permissions."""
    buttons: list[list[InlineKeyboardButton]] = []

    # Everyone
    buttons.append(
        [InlineKeyboardButton(text="👤 Profile", callback_data="profile")]
    )

    if user.has_permission(PermissionKey.STAFF_VIEW):
        buttons.append(
            [InlineKeyboardButton(text="👥 Team", callback_data="staff_list")]
        )

    if user.has_permission(PermissionKey.ROLES_ASSIGN):
        buttons.append(
            [InlineKeyboardButton(text="🔑 Roles", callback_data="roles_manage")]
        )

    if user.has_permission(PermissionKey.SYSTEM_AUDIT):
        buttons.append(
            [InlineKeyboardButton(text="📋 Audit", callback_data="audit_log")]
        )

    if user.has_permission(PermissionKey.SYSTEM_SETTINGS):
        buttons.append(
            [InlineKeyboardButton(text="⚙️ Settings", callback_data="settings")]
        )

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def back_button(callback_data: str = "main_menu") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="← Back", callback_data=callback_data)]
        ]
    )
