from app.domain.models.current_user import CurrentUser
from app.schemas.auth import MeResponse, OrganizationResponse, UserResponse


class UserService:
    def get_me(self, current_user: CurrentUser) -> MeResponse:
        return MeResponse(
            user=UserResponse(
                id=current_user.user_id,
                clerk_id=current_user.clerk_id,
                email=current_user.email,
                first_name=current_user.first_name,
                last_name=current_user.last_name,
                full_name=current_user.full_name,
                user_type=current_user.user_type,
                is_root=current_user.is_root,
                organization_id=current_user.organization_id,
                status=current_user.status,
            ),
            organization=OrganizationResponse(
                id=current_user.organization_id,
                name=current_user.organization_name,
                industry=current_user.organization_industry,
                status="active",
            ),
        )
