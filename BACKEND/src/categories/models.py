import uuid
from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base

if TYPE_CHECKING:
    from src.providers.models import ProviderService
    from src.requests.models import ServiceRequest


class ServiceCategory(Base):
    __tablename__ = "service_categories"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    description: Mapped[str] = mapped_column(String(1000))

    provider_services: Mapped[list["ProviderService"]] = relationship(back_populates="service_category")
    service_requests: Mapped[list["ServiceRequest"]] = relationship(back_populates="service_category")
