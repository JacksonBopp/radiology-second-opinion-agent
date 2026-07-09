import os
from dataclasses import dataclass

from fastapi import HTTPException, Request, Security
from fastapi.security import APIKeyHeader

# API_KEYS format: "name1:key1,name2:key2" so each caller (radiologist,
# UI service account, etc.) is individually identifiable in the audit
# log rather than sharing one anonymous credential.
_DEV_DEFAULT_KEYS = "dev:dev-local-key"

_api_key_header = APIKeyHeader(name="X-API-Key")


@dataclass
class AuthenticatedUser:
    name: str


def _load_valid_keys() -> dict[str, str]:
    raw = os.environ.get("API_KEYS", _DEV_DEFAULT_KEYS)
    keys: dict[str, str] = {}
    for pair in raw.split(","):
        pair = pair.strip()
        if not pair:
            continue
        name, _, key = pair.partition(":")
        if name and key:
            keys[key] = name
    return keys


def get_current_user(
    request: Request, api_key: str = Security(_api_key_header)
) -> AuthenticatedUser:
    valid_keys = _load_valid_keys()
    name = valid_keys.get(api_key)
    if name is None:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    # Recorded so AuditLogMiddleware can attribute the request to a
    # named actor instead of just an IP address.
    request.state.actor = name
    return AuthenticatedUser(name=name)
