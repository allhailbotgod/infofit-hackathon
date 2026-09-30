import uuid
from functools import wraps

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.auth.dependencies import require_customer
from src.auth.models import User
from src.database import get_db
from src.providers.models import ProviderProfile
from src.requests.enums import ServiceRequestStatus
from src.requests.models import ServiceRequest
from src.reviews.models import Review
from src.reviews.schemas import ReviewCreate, ReviewResponse

router = APIRouter(tags=["reviews"])


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


@router.post("/requests/{request_id}/review", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
@handle_unexpected_errors
def create_review(
    request_id: uuid.UUID,
    review_data: ReviewCreate,
    current_user: User = Depends(require_customer),
    db: Session = Depends(get_db),
) -> Review:
    service_request = db.get(ServiceRequest, request_id)
    if service_request is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service request not found")
    if service_request.customer_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to review this request")
    if service_request.status != ServiceRequestStatus.COMPLETED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only completed requests can be reviewed")
    if db.scalar(select(Review).where(Review.service_request_id == request_id)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This request already has a review")

    review = Review(
        customer_id=current_user.id,
        provider_id=service_request.provider_id,
        service_request_id=service_request.id,
        **review_data.model_dump(),
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return review


@router.get("/providers/{provider_id}/reviews", response_model=list[ReviewResponse])
@handle_unexpected_errors
def list_provider_reviews(provider_id: uuid.UUID, db: Session = Depends(get_db)) -> list[Review]:
    if db.get(ProviderProfile, provider_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Provider not found")
    return list(
        db.scalars(
            select(Review).where(Review.provider_id == provider_id).order_by(Review.created_at.desc())
        )
    )
