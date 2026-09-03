"""Backward-compatible wrapper for the canonical YouTube OAuth token store."""

from database.oauth_tokens import delete_token, get_token, save_token

__all__ = ["save_token", "get_token", "delete_token"]
