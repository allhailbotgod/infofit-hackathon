import uuid
from functools import wraps

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from src.auth.dependencies import require_provider
from src.auth.models import User
from src.categories.models import ServiceCategory
from src.database import get_db
from src.providers.enums import VerificationStatus
from src.providers.models import ProviderAvailability, ProviderProfile, ProviderService
from src.providers.schemas import (
    ProviderAvailabilityCreate,
    ProviderAvailabilityResponse,
    ProviderAvailabilityUpdate,
    ProviderProfileResponse,
    ProviderProfileUpdate,
    ProviderPublicResponse,
    ProviderServiceCreate,
    ProviderServicePublicResponse,
    ProviderServiceResponse,
)
from src.reviews.models import Review

router = APIRouter(tags=["providers"])


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


def get_provider_profile(user: User, db: Session) -> ProviderProfile:
    profile = db.scalar(select(ProviderProfile).where(ProviderProfile.user_id == user.id))
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Provider profile not found")
    return profile


def provider_response(profile: ProviderProfile, db: Session) -> ProviderPublicResponse:
    average_rating, review_count = db.execute(
        select(func.avg(Review.rating), func.count(Review.id)).where(Review.provider_id == profile.id)
    ).one()
    services = [
        ProviderServicePublicResponse(
            service_category_id=service.service_category_id,
            name=service.service_category.name,
            description=service.service_category.description,
        )
        for service in profile.services
    ]
    return ProviderPublicResponse(
        id=profile.id,
        name=profile.user.name,
        bio=profile.bio,
        experience_years=profile.experience_years,
        location=profile.location,
        area=profile.area,
        verification_status=profile.verification_status,
        is_available=profile.is_available,
        services=services,
        average_rating=float(average_rating) if average_rating is not None else None,
        review_count=review_count,
    )


@router.get("/providers", response_model=list[ProviderPublicResponse])
@handle_unexpected_errors
def list_providers(
    search: str | None = None,
    service_id: uuid.UUID | None = None,
    location: str | None = None,
    area: str | None = None,
    verification_status: VerificationStatus | None = None,
    is_available: bool | None = None,
    db: Session = Depends(get_db),
) -> list[ProviderPublicResponse]:
    statement = (
        select(ProviderProfile)
        .join(ProviderProfile.user)
        .options(selectinload(ProviderProfile.user), selectinload(ProviderProfile.services).selectinload(ProviderService.service_category))
    )
    if search:
        statement = statement.where(User.name.ilike(f"%{search}%"))
    if service_id:
        statement = statement.join(ProviderProfile.services).where(ProviderService.service_category_id == service_id)
    if location:
        statement = statement.where(ProviderProfile.location.ilike(f"%{location}%"))
    if area:
        statement = statement.where(ProviderProfile.area.ilike(f"%{area}%"))
    if verification_status:
        statement = statement.where(ProviderProfile.verification_status == verification_status)
    if is_available is not None:
        statement = statement.where(ProviderProfile.is_available == is_available)

    profiles = db.scalars(statement).unique().all()
    return [provider_response(profile, db) for profile in profiles]


@router.get("/providers/{provider_id}", response_model=ProviderPublicResponse)
@handle_unexpected_errors
def get_provider(provider_id: uuid.UUID, db: Session = Depends(get_db)) -> ProviderPublicResponse:
    profile = db.scalar(
        select(ProviderProfile)
        .where(ProviderProfile.id == provider_id)
        .options(selectinload(ProviderProfile.user), selectinload(ProviderProfile.services).selectinload(ProviderService.service_category))
    )
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Provider not found")
    return provider_response(profile, db)


@router.get("/provider/profile", response_model=ProviderProfileResponse)
@handle_unexpected_errors
def read_own_profile(
    current_user: User = Depends(require_provider), db: Session = Depends(get_db)
) -> ProviderProfile:
    return get_provider_profile(current_user, db)


@router.patch("/provider/profile", response_model=ProviderProfileResponse)
@handle_unexpected_errors
def update_own_profile(
    profile_data: ProviderProfileUpdate,
    current_user: User = Depends(require_provider),
    db: Session = Depends(get_db),
) -> ProviderProfile:
    profile = get_provider_profile(current_user, db)
    for field, value in profile_data.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)
    db.commit()
    db.refresh(profile)
    return profile


@router.get("/provider/services", response_model=list[ProviderServiceResponse])
@handle_unexpected_errors
def list_own_services(
    current_user: User = Depends(require_provider), db: Session = Depends(get_db)
) -> list[ProviderService]:
    profile = get_provider_profile(current_user, db)
    return list(db.scalars(select(ProviderService).where(ProviderService.provider_id == profile.id)))


@router.post("/provider/services", response_model=ProviderServiceResponse, status_code=status.HTTP_201_CREATED)
@handle_unexpected_errors
def add_provider_service(
    service_data: ProviderServiceCreate,
    current_user: User = Depends(require_provider),
    db: Session = Depends(get_db),
) -> ProviderService:
    profile = get_provider_profile(current_user, db)
    category = db.get(ServiceCategory, service_data.service_category_id)
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    existing_service = db.get(ProviderService, (profile.id, service_data.service_category_id))
    if existing_service:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Service already added")
    service = ProviderService(provider_id=profile.id, service_category_id=service_data.service_category_id)
    db.add(service)
    db.commit()
    db.refresh(service)
    return service


@router.delete("/provider/services/{service_category_id}", status_code=status.HTTP_204_NO_CONTENT)
@handle_unexpected_errors
def remove_provider_service(
    service_category_id: uuid.UUID,
    current_user: User = Depends(require_provider),
    db: Session = Depends(get_db),
) -> Response:
    profile = get_provider_profile(current_user, db)
    service = db.get(ProviderService, (profile.id, service_category_id))
    if service is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Provider service not found")
    db.delete(service)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/provider/availability", response_model=list[ProviderAvailabilityResponse])
@handle_unexpected_errors
def list_own_availability(
    current_user: User = Depends(require_provider), db: Session = Depends(get_db)
) -> list[ProviderAvailability]:
    profile = get_provider_profile(current_user, db)
    return list(db.scalars(select(ProviderAvailability).where(ProviderAvailability.provider_id == profile.id)))


@router.post(
    "/provider/availability", response_model=ProviderAvailabilityResponse, status_code=status.HTTP_201_CREATED
)
@handle_unexpected_errors
def create_availability(
    availability_data: ProviderAvailabilityCreate,
    current_user: User = Depends(require_provider),
    db: Session = Depends(get_db),
) -> ProviderAvailability:
    profile = get_provider_profile(current_user, db)
    availability = ProviderAvailability(provider_id=profile.id, **availability_data.model_dump())
    db.add(availability)
    db.commit()
    db.refresh(availability)
    return availability


@router.patch("/provider/availability/{availability_id}", response_model=ProviderAvailabilityResponse)
@handle_unexpected_errors
def update_availability(
    availability_id: uuid.UUID,
    availability_data: ProviderAvailabilityUpdate,
    current_user: User = Depends(require_provider),
    db: Session = Depends(get_db),
) -> ProviderAvailability:
    profile = get_provider_profile(current_user, db)
    availability = db.get(ProviderAvailability, availability_id)
    if availability is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Availability not found")
    if availability.provider_id != profile.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot modify another provider's availability")
    for field, value in availability_data.model_dump(exclude_unset=True).items():
        setattr(availability, field, value)
    db.commit()
    db.refresh(availability)
    return availability


@router.delete("/provider/availability/{availability_id}", status_code=status.HTTP_204_NO_CONTENT)
@handle_unexpected_errors
def delete_availability(
    availability_id: uuid.UUID,
    current_user: User = Depends(require_provider),
    db: Session = Depends(get_db),
) -> Response:
    profile = get_provider_profile(current_user, db)
    availability = db.get(ProviderAvailability, availability_id)
    if availability is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Availability not found")
    if availability.provider_id != profile.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot modify another provider's availability")
    db.delete(availability)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
