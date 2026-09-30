import uuid
from functools import wraps

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.auth.dependencies import get_current_user, require_customer
from src.auth.enums import UserRole
from src.auth.models import User
from src.categories.models import ServiceCategory
from src.database import get_db
from src.providers.models import ProviderProfile, ProviderService
from src.requests.enums import ServiceRequestStatus
from src.requests.models import ServiceRequest
from src.requests.schemas import ServiceRequestCreate, ServiceRequestResponse, ServiceRequestUpdateStatus

router = APIRouter(prefix="/requests", tags=["service requests"])


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


def current_provider_profile(user: User, db: Session) -> ProviderProfile:
    profile = db.scalar(select(ProviderProfile).where(ProviderProfile.user_id == user.id))
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Provider profile not found")
    return profile


def can_view_request(service_request: ServiceRequest, user: User, db: Session) -> bool:
    if user.role == UserRole.ADMIN:
        return True
    if user.role == UserRole.CUSTOMER:
        return service_request.customer_id == user.id
    profile = current_provider_profile(user, db)
    return service_request.provider_id == profile.id


@router.post("", response_model=ServiceRequestResponse, status_code=status.HTTP_201_CREATED)
@handle_unexpected_errors
def create_service_request(
    request_data: ServiceRequestCreate,
    current_user: User = Depends(require_customer),
    db: Session = Depends(get_db),
) -> ServiceRequest:
    provider = db.get(ProviderProfile, request_data.provider_id)
    if provider is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Provider not found")
    if db.get(ServiceCategory, request_data.service_category_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    provider_service = db.get(ProviderService, (provider.id, request_data.service_category_id))
    if provider_service is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Provider does not offer this service")

    service_request = ServiceRequest(customer_id=current_user.id, **request_data.model_dump())
    db.add(service_request)
    db.commit()
    db.refresh(service_request)
    return service_request


@router.get("", response_model=list[ServiceRequestResponse])
@handle_unexpected_errors
def list_service_requests(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[ServiceRequest]:
    statement = select(ServiceRequest).order_by(ServiceRequest.created_at.desc())
    if current_user.role == UserRole.CUSTOMER:
        statement = statement.where(ServiceRequest.customer_id == current_user.id)
    elif current_user.role == UserRole.PROVIDER:
        profile = current_provider_profile(current_user, db)
        statement = statement.where(ServiceRequest.provider_id == profile.id)
    return list(db.scalars(statement))


@router.get("/{request_id}", response_model=ServiceRequestResponse)
@handle_unexpected_errors
def get_service_request(
    request_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ServiceRequest:
    service_request = db.get(ServiceRequest, request_id)
    if service_request is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service request not found")
    if not can_view_request(service_request, current_user, db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to view this request")
    return service_request


@router.patch("/{request_id}/status", response_model=ServiceRequestResponse)
@handle_unexpected_errors
def update_request_status(
    request_id: uuid.UUID,
    status_data: ServiceRequestUpdateStatus,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ServiceRequest:
    service_request = db.get(ServiceRequest, request_id)
    if service_request is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service request not found")

    if current_user.role == UserRole.CUSTOMER:
        if service_request.customer_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to update this request")
        if status_data.status != ServiceRequestStatus.CANCELLED or service_request.status not in {
            ServiceRequestStatus.PENDING,
            ServiceRequestStatus.ACCEPTED,
        }:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid request status transition")
    elif current_user.role == UserRole.PROVIDER:
        profile = current_provider_profile(current_user, db)
        if service_request.provider_id != profile.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to update this request")
        provider_transitions = {
            ServiceRequestStatus.PENDING: {ServiceRequestStatus.ACCEPTED, ServiceRequestStatus.REJECTED},
            ServiceRequestStatus.ACCEPTED: {ServiceRequestStatus.COMPLETED},
        }
        if status_data.status not in provider_transitions.get(service_request.status, set()):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid request status transition")

    service_request.status = status_data.status
    if current_user.role == UserRole.PROVIDER and status_data.provider_response is not None:
        service_request.provider_response = status_data.provider_response
    db.commit()
    db.refresh(service_request)
    return service_request
