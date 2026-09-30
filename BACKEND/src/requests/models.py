import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, Enum as SqlEnum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base
from src.requests.enums import ServiceRequestStatus

if TYPE_CHECKING:
    from src.auth.models import User
    from src.categories.models import ServiceCategory
    from src.providers.models import ProviderProfile
    from src.reviews.models import Review


class ServiceRequest(Base):
    __tablename__ = "service_requests"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    customer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    provider_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("provider_profiles.id"))
    service_category_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("service_categories.id"))
    description: Mapped[str] = mapped_column(String(1000))
    requested_date: Mapped[date] = mapped_column(Date)
    requested_time: Mapped[str] = mapped_column(String(20))
    status: Mapped[ServiceRequestStatus] = mapped_column(
        SqlEnum(ServiceRequestStatus, name="service_request_status"), default=ServiceRequestStatus.PENDING
    )
    provider_response: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    customer: Mapped["User"] = relationship(back_populates="service_requests")
    provider: Mapped["ProviderProfile"] = relationship(back_populates="service_requests")
    service_category: Mapped["ServiceCategory"] = relationship(back_populates="service_requests")
    review: Mapped["Review | None"] = relationship(back_populates="service_request")
