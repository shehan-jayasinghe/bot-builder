from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CurrentUser:
    user_id: str
    organization_id: str
    clerk_id: str
    email: str
    first_name: str
    last_name: str
    user_type: str
    is_root: bool
    status: str
    organization_name: str
    organization_industry: str | None

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()

    def to_context(self) -> dict[str, Any]:
        return {
            "user_id": self.user_id,
            "organization_id": self.organization_id,
            "clerk_id": self.clerk_id,
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "full_name": self.full_name,
            "user_type": self.user_type,
            "is_root": self.is_root,
            "status": self.status,
            "organization_name": self.organization_name,
            "organization_industry": self.organization_industry,
        }
