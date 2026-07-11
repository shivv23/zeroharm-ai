import os
import bcrypt
import jwt
import json
import logging
from datetime import datetime, timedelta, timezone

logger = logging.getLogger("zeroharm-auth")

ROLES = {
    "admin": ["read", "write", "delete", "manage_users", "trigger_emergency", "configure"],
    "safety_officer": ["read", "write", "trigger_emergency", "approve_permits"],
    "operator": ["read", "write_permits", "trigger_emergency"],
    "viewer": ["read"],
}


class AuthManager:
    def __init__(self, users_file: str = None):
        self.users: dict = {}
        self.users_file = users_file or os.path.join(
            os.path.dirname(__file__), os.pardir, "config", "users.json"
        )
        self.jwt_secret = os.getenv("JWT_SECRET", "zeroharm-default-secret-change-in-production")
        self.jwt_expiry_hours = int(os.getenv("JWT_EXPIRY_HOURS", "24"))
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
                    pw_hash = u.get("password_hash") or u.get("password")
                    if pw_hash and not pw_hash.startswith("$2b$") and not pw_hash.startswith("$2a$"):
                        pw_hash = bcrypt.hashpw(pw_hash.encode(), bcrypt.gensalt()).decode()
                    self.users[u["username"]] = {
                        "username": u["username"],
                        "password_hash": pw_hash or "",
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

    def authenticate(self, username: str, password: str):
        user = self.users.get(username)
        if not user:
            return None
        if not bcrypt.checkpw(password.encode(), user["password_hash"].encode()):
            return None
        return user

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
