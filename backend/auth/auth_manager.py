import os
import bcrypt
import jwt
import json
import logging
import secrets
from datetime import datetime, timedelta, timezone

logger = logging.getLogger("zeroharm-auth")

ROLES = {
    "admin": ["read", "write", "delete", "manage_users", "trigger_emergency", "configure"],
    "safety_officer": ["read", "write", "trigger_emergency", "approve_permits"],
    "operator": ["read", "write_permits", "trigger_emergency"],
    "viewer": ["read"],
}

_REFRESH_TOKENS: dict[str, dict] = {}


def _load_refresh_tokens():
    path = os.getenv("REFRESH_TOKEN_FILE", "")
    if not path:
        return {}
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save_refresh_tokens(tokens: dict):
    path = os.getenv("REFRESH_TOKEN_FILE", "")
    if not path:
        return
    try:
        with open(path, "w") as f:
            json.dump(tokens, f)
    except OSError:
        pass


class AuthManager:
    def __init__(self, users_file: str = None):
        self.users: dict = {}
        self.users_file = users_file or os.path.join(
            os.path.dirname(__file__), os.pardir, "config", "users.json"
        )
        self.jwt_secret = os.getenv("JWT_SECRET", "zeroharm-default-secret-change-in-production")
        self.jwt_expiry_hours = int(os.getenv("JWT_EXPIRY_HOURS", "24"))
        self.refresh_expiry_days = int(os.getenv("REFRESH_EXPIRY_DAYS", "7"))
        self._check_default_secret()
        self._load_users()

    def _check_default_secret(self):
        if self.jwt_secret == "zeroharm-default-secret-change-in-production":
            logger.warning("*" * 60)
            logger.warning("SECURITY: Using default JWT secret! Set JWT_SECRET in .env")
            logger.warning("*" * 60)

    def _load_users(self):
        try:
            with open(self.users_file) as f:
                data = json.load(f)
                for u in data.get("users", []):
                    pw_hash = u.get("password_hash") or u.get("password", "")
                    if pw_hash and not pw_hash.startswith("$2b$") and not pw_hash.startswith("$2a$"):
                        pw_hash = bcrypt.hashpw(pw_hash.encode(), bcrypt.gensalt()).decode()
                    elif not pw_hash:
                        default_pw = u["username"] + "123"
                        pw_hash = bcrypt.hashpw(default_pw.encode(), bcrypt.gensalt()).decode()
                    self.users[u["username"]] = {
                        "username": u["username"],
                        "password_hash": pw_hash,
                        "role": u["role"],
                        "tenant_id": u["tenant_id"],
                        "name": u.get("name", u["username"]),
                    }
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        if not self.users:
            self._create_default_admin()

    def _create_default_admin(self):
        logger.warning("*" * 60)
        logger.warning("SECURITY: Creating default admin/admin123 account!")
        logger.warning("Create users.json with proper credentials or set up .env")
        logger.warning("*" * 60)
        pw_hash = bcrypt.hashpw(b"admin123", bcrypt.gensalt()).decode()
        self.users["admin"] = {
            "username": "admin",
            "password_hash": pw_hash,
            "role": "admin",
            "tenant_id": "plant_1",
            "name": "System Administrator",
        }

    def list_users(self):
        return [
            {"username": u["username"], "role": u["role"], "tenant_id": u["tenant_id"], "name": u["name"]}
            for u in self.users.values()
        ]

    def create_user(self, username: str, password: str, role: str, tenant_id: str, name: str = None):
        if username in self.users:
            return False
        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        self.users[username] = {
            "username": username,
            "password_hash": password_hash,
            "role": role,
            "tenant_id": tenant_id,
            "name": name or username,
        }
        return True

    def delete_user(self, username: str):
        if username not in self.users:
            return False
        del self.users[username]
        return True

    def update_user_role(self, username: str, role: str):
        if username not in self.users:
            return False
        self.users[username]["role"] = role
        return True

    def authenticate(self, username: str, password: str):
        user = self.users.get(username)
        if not user:
            return None
        if not bcrypt.checkpw(password.encode(), user["password_hash"].encode()):
            return None
        return user

    def change_password(self, username: str, old_password: str, new_password: str):
        user = self.users.get(username)
        if not user:
            return False
        if not bcrypt.checkpw(old_password.encode(), user["password_hash"].encode()):
            return False
        user["password_hash"] = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
        return True

    def reset_password(self, username: str, new_password: str):
        user = self.users.get(username)
        if not user:
            return False
        user["password_hash"] = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
        return True

    def create_token(self, username: str):
        user = self.users.get(username)
        if not user:
            return None
        payload = {
            "sub": username,
            "role": user["role"],
            "tenant_id": user["tenant_id"],
            "exp": datetime.now(timezone.utc) + timedelta(hours=self.jwt_expiry_hours),
        }
        return jwt.encode(payload, self.jwt_secret, algorithm="HS256")

    def create_refresh_token(self, username: str):
        token = secrets.token_urlsafe(48)
        _REFRESH_TOKENS[token] = {
            "username": username,
            "expires": (datetime.now(timezone.utc) + timedelta(days=self.refresh_expiry_days)).isoformat(),
        }
        _save_refresh_tokens(_REFRESH_TOKENS)
        return token

    def verify_refresh_token(self, token: str):
        entry = _REFRESH_TOKENS.get(token)
        if not entry:
            return None
        try:
            expires = datetime.fromisoformat(entry["expires"])
            if expires < datetime.now(timezone.utc):
                del _REFRESH_TOKENS[token]
                return None
        except (ValueError, TypeError):
            return None
        return entry["username"]

    def revoke_refresh_token(self, token: str):
        _REFRESH_TOKENS.pop(token, None)

    def revoke_all_user_tokens(self, username: str):
        to_delete = [t for t, e in _REFRESH_TOKENS.items() if e["username"] == username]
        for t in to_delete:
            del _REFRESH_TOKENS[t]

    def verify_token(self, token: str):
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
            username = payload.get("sub")
            user = self.users.get(username)
            if not user:
                return None
            return user
        except jwt.PyJWTError:
            return None

    def check_permission(self, user: dict, required_role: str = None, resource: str = None):
        if not user:
            return False
        user_role = user.get("role")
        if not user_role:
            return False
        if required_role:
            return user_role == required_role
        if resource:
            return resource in ROLES.get(user_role, [])
        return True
