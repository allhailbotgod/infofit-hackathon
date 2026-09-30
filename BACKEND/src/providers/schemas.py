import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from src.providers.enums import VerificationStatus


class ProviderProfileUpdate(BaseModel):
    bio: str | None = Field(default=None, max_length=1000)
    experience_years: int | None = Field(default=None, ge=0)
    location: str | None = Field(default=None, min_length=1, max_length=120)
    area: str | None = Field(default=None, min_length=1, max_length=120)
    is_available: bool | None = None


class ProviderProfileResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    bio: str
    experience_years: int
    location: str
    area: str
    verification_status: VerificationStatus
    is_available: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProviderServiceCreate(BaseModel):
    service_category_id: uuid.UUID


class ProviderServiceResponse(BaseModel):
    provider_id: uuid.UUID
    service_category_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)


class ProviderServicePublicResponse(BaseModel):
    service_category_id: uuid.UUID
    name: str
    description: str


class ProviderAvailabilityCreate(BaseModel):
    day_of_week: str = Field(min_length=1, max_length=20)
    start_time: str = Field(min_length=1, max_length=20)
    end_time: str = Field(min_length=1, max_length=20)


class ProviderAvailabilityUpdate(BaseModel):
    day_of_week: str | None = Field(default=None, min_length=1, max_length=20)
    start_time: str | None = Field(default=None, min_length=1, max_length=20)
    end_time: str | None = Field(default=None, min_length=1, max_length=20)


class ProviderAvailabilityResponse(ProviderAvailabilityCreate):
    id: uuid.UUID
    provider_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)


class ProviderPublicResponse(BaseModel):
    id: uuid.UUID
    name: str
    bio: str
    experience_years: int
    location: str
    area: str
    verification_status: VerificationStatus
    is_available: bool
    services: list[ProviderServicePublicResponse]
    average_rating: float | None
    review_count: int


class VerificationUpdate(BaseModel):
    verification_status: VerificationStatus


class AdminDashboardResponse(BaseModel):
    total_users: int
    total_providers: int
    verified_providers: int
    pending_providers: int
    total_service_requests: int
    completed_service_requests: int
