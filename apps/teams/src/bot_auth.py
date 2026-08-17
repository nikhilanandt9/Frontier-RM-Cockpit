from __future__ import annotations

import json
import os
import ssl
import time
from urllib import parse, request

import jwt


OPENID_CONFIGURATION = "https://login.botframework.com/v1/.well-known/openidconfiguration"
BOT_CONNECTOR_ISSUER = "https://api.botframework.com"
TRUSTED_SERVICE_SUFFIXES = (
    ".botframework.com",
    ".trafficmanager.net",
    ".teams.microsoft.com",
)

_OPENID_CACHE: tuple[dict, float] | None = None
_JWKS_CACHE: tuple[dict, float] | None = None
_CONNECTOR_TOKEN_CACHE: tuple[str, float] | None = None


def _json_get(url: str, headers: dict[str, str] | None = None) -> dict:
    http_request = request.Request(url, headers=headers or {})
    with request.urlopen(http_request, timeout=10, context=ssl.create_default_context()) as response:
        return json.loads(response.read().decode("utf-8"))


def _openid_documents() -> tuple[dict, dict]:
    global _OPENID_CACHE, _JWKS_CACHE
    now = time.time()
    if _OPENID_CACHE is None or _OPENID_CACHE[1] < now:
        configuration = _json_get(OPENID_CONFIGURATION)
        _OPENID_CACHE = (configuration, now + 3600)
    else:
        configuration = _OPENID_CACHE[0]
    if _JWKS_CACHE is None or _JWKS_CACHE[1] < now:
        key_set = _json_get(configuration["jwks_uri"])
        _JWKS_CACHE = (key_set, now + 3600)
    else:
        key_set = _JWKS_CACHE[0]
    return configuration, key_set


def validate_bot_token(authorization: str, service_url: str) -> dict:
    bot_id = os.environ.get("BOT_ID", "").strip()
    if not bot_id:
        raise ValueError("BOT_ID is not configured")
    if not authorization.startswith("Bearer "):
        raise ValueError("Bearer authorization is required")
    encoded_token = authorization[7:].strip()
    header = jwt.get_unverified_header(encoded_token)
    _, key_set = _openid_documents()
    matching_key = next((key for key in key_set.get("keys", []) if key.get("kid") == header.get("kid")), None)
    if matching_key is None:
        raise ValueError("Token signing key is not trusted")
    signing_key = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(matching_key))
    claims = jwt.decode(
        encoded_token,
        signing_key,
        algorithms=["RS256"],
        audience=bot_id,
        issuer=BOT_CONNECTOR_ISSUER,
        options={"require": ["exp", "iss", "aud"]},
    )
    claimed_service_url = claims.get("serviceurl")
    if claimed_service_url and claimed_service_url.rstrip("/") != service_url.rstrip("/"):
        raise ValueError("Activity service URL does not match the token")
    return claims


def is_trusted_service_url(service_url: str, playground: bool) -> bool:
    parsed = parse.urlparse(service_url)
    hostname = (parsed.hostname or "").casefold()
    if playground:
        return parsed.scheme == "http" and hostname in {"127.0.0.1", "localhost", "::1"}
    return parsed.scheme == "https" and any(hostname.endswith(suffix) for suffix in TRUSTED_SERVICE_SUFFIXES)


def connector_token() -> str:
    global _CONNECTOR_TOKEN_CACHE
    if _CONNECTOR_TOKEN_CACHE and _CONNECTOR_TOKEN_CACHE[1] > time.time() + 120:
        return _CONNECTOR_TOKEN_CACHE[0]
    identity_endpoint = os.environ.get("IDENTITY_ENDPOINT")
    identity_header = os.environ.get("IDENTITY_HEADER")
    client_id = os.environ.get("AZURE_CLIENT_ID")
    if not identity_endpoint or not identity_header or not client_id:
        raise RuntimeError("Managed identity configuration is unavailable")
    separator = "&" if "?" in identity_endpoint else "?"
    token_url = (
        f"{identity_endpoint}{separator}resource={parse.quote('https://api.botframework.com')}"
        f"&api-version=2019-08-01&client_id={parse.quote(client_id)}"
    )
    payload = _json_get(token_url, {"X-IDENTITY-HEADER": identity_header, "Metadata": "true"})
    token = payload["access_token"]
    expiry = float(payload.get("expires_on", time.time() + 300))
    _CONNECTOR_TOKEN_CACHE = (token, expiry)
    return token
