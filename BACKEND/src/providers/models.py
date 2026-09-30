import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum as SqlEnum, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base
from src.providers.enums import VerificationStatus

if TYPE_CHECKING:
    from src.auth.models import User
    from src.categories.models import ServiceCategory
    from src.requests.models import ServiceRequest
    from src.reviews.models import Review


class ProviderProfile(Base):
    __tablename__ = "provider_profiles"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), unique=True)
    bio: Mapped[str] = mapped_column(String(1000))
    experience_years: Mapped[int] = mapped_column(Integer)
    location: Mapped[str] = mapped_column(String(120))
    area: Mapped[str] = mapped_column(String(120))
    verification_status: Mapped[VerificationStatus] = mapped_column(
        SqlEnum(VerificationStatus, name="verification_status"), default=VerificationStatus.PENDING
    )
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="provider_profile")
    services: Mapped[list["ProviderService"]] = relationship(back_populates="provider", cascade="all, delete-orphan")
    availability: Mapped[list["ProviderAvailability"]] = relationship(
        back_populates="provider", cascade="all, delete-orphan"
    )
    service_requests: Mapped[list["ServiceRequest"]] = relationship(back_populates="provider")
    reviews: Mapped[list["Review"]] = relationship(back_populates="provider")


class ProviderService(Base):
    __tablename__ = "provider_services"

    provider_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("provider_profiles.id"), primary_key=True)
    service_category_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("service_categories.id"), primary_key=True
    )

    provider: Mapped[ProviderProfile] = relationship(back_populates="services")
    service_category: Mapped["ServiceCategory"] = relationship(back_populates="provider_services")


class ProviderAvailability(Base):
    __tablename__ = "provider_availability"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    provider_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("provider_profiles.id"))
    day_of_week: Mapped[str] = mapped_column(String(20))
    start_time: Mapped[str] = mapped_column(String(20))
    end_time: Mapped[str] = mapped_column(String(20))

    provider: Mapped[ProviderProfile] = relationship(back_populates="availability")
