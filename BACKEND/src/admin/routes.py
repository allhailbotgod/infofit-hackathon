import uuid
from functools import wraps

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.auth.dependencies import require_admin
from src.database import get_db
from src.providers.enums import VerificationStatus
from src.providers.models import ProviderProfile
from src.providers.schemas import AdminDashboardResponse, ProviderProfileResponse, VerificationUpdate
from src.requests.enums import ServiceRequestStatus
from src.requests.models import ServiceRequest
from src.auth.models import User

router = APIRouter(prefix="/admin", tags=["admin"])


def handle_unexpected_errors(endpoint):
    @wraps(endpoint)
    def wrapper(*args, **kwargs):
        try:
            return endpoint(*args, **kwargs)
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred",
            ) from exc

    return wrapper


@router.get("/providers/pending", response_model=list[ProviderProfileResponse])
@handle_unexpected_errors
def list_pending_providers(
    db: Session = Depends(get_db), _: object = Depends(require_admin)
) -> list[ProviderProfile]:
    return list(
        db.scalars(
            select(ProviderProfile).where(ProviderProfile.verification_status == VerificationStatus.PENDING)
        )
    )


@router.patch("/providers/{provider_id}/verification", response_model=ProviderProfileResponse)
@handle_unexpected_errors
def update_provider_verification(
    provider_id: uuid.UUID,
    verification_data: VerificationUpdate,
    db: Session = Depends(get_db),
    _: object = Depends(require_admin),
) -> ProviderProfile:
    provider = db.get(ProviderProfile, provider_id)
    if provider is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Provider not found")
    provider.verification_status = verification_data.verification_status
    db.commit()
    db.refresh(provider)
    return provider


@router.get("/dashboard", response_model=AdminDashboardResponse)
@handle_unexpected_errors
def get_dashboard(
    db: Session = Depends(get_db), _: object = Depends(require_admin)
) -> AdminDashboardResponse:
    return AdminDashboardResponse(
        total_users=db.scalar(select(func.count(User.id))) or 0,
        total_providers=db.scalar(select(func.count(ProviderProfile.id))) or 0,
        verified_providers=db.scalar(
            select(func.count(ProviderProfile.id)).where(
                ProviderProfile.verification_status == VerificationStatus.VERIFIED
            )
        )
        or 0,
        pending_providers=db.scalar(
            select(func.count(ProviderProfile.id)).where(
                ProviderProfile.verification_status == VerificationStatus.PENDING
            )
        )
        or 0,
        total_service_requests=db.scalar(select(func.count(ServiceRequest.id))) or 0,
        completed_service_requests=db.scalar(
            select(func.count(ServiceRequest.id)).where(
                ServiceRequest.status == ServiceRequestStatus.COMPLETED
            )
        )
        or 0,
    )
