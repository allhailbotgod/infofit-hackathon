import uuid
from functools import wraps

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.auth.dependencies import require_admin
from src.categories.models import ServiceCategory
from src.categories.schemas import ServiceCategoryCreate, ServiceCategoryResponse, ServiceCategoryUpdate
from src.database import get_db

router = APIRouter(prefix="/categories", tags=["categories"])


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


@router.get("", response_model=list[ServiceCategoryResponse])
@handle_unexpected_errors
def list_categories(db: Session = Depends(get_db)) -> list[ServiceCategory]:
    return list(db.scalars(select(ServiceCategory).order_by(ServiceCategory.name)))


@router.get("/{category_id}", response_model=ServiceCategoryResponse)
@handle_unexpected_errors
def get_category(category_id: uuid.UUID, db: Session = Depends(get_db)) -> ServiceCategory:
    category = db.get(ServiceCategory, category_id)
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return category


@router.post("", response_model=ServiceCategoryResponse, status_code=status.HTTP_201_CREATED)
@handle_unexpected_errors
def create_category(
    category_data: ServiceCategoryCreate,
    db: Session = Depends(get_db),
    _: object = Depends(require_admin),
) -> ServiceCategory:
    category = ServiceCategory(**category_data.model_dump())
    db.add(category)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Category name already exists")
    db.refresh(category)
    return category


@router.patch("/{category_id}", response_model=ServiceCategoryResponse)
@handle_unexpected_errors
def update_category(
    category_id: uuid.UUID,
    category_data: ServiceCategoryUpdate,
    db: Session = Depends(get_db),
    _: object = Depends(require_admin),
) -> ServiceCategory:
    category = db.get(ServiceCategory, category_id)
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    for field, value in category_data.model_dump(exclude_unset=True).items():
        setattr(category, field, value)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Category name already exists")
    db.refresh(category)
    return category


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
@handle_unexpected_errors
def delete_category(
    category_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: object = Depends(require_admin),
) -> Response:
    category = db.get(ServiceCategory, category_id)
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    db.delete(category)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Category cannot be deleted while it is in use",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
