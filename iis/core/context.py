from contextvars import ContextVar
from typing import Optional

# Context variable to store the current user's authentication token
auth_token_ctx: ContextVar[Optional[str]] = ContextVar("auth_token", default=None)

# Context variable to store the current authentication flow preference
auth_flow_ctx: ContextVar[str] = ContextVar("auth_flow", default="CLIENT_CREDENTIALS")

# Context variable to store the current user's email/ID
auth_user_ctx: ContextVar[Optional[str]] = ContextVar("auth_user", default=None)
