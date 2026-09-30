import uuid

from pydantic import BaseModel, ConfigDict, Field


class ServiceCategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str = Field(min_length=1, max_length=1000)


class ServiceCategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, min_length=1, max_length=1000)


class ServiceCategoryResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str

    model_config = ConfigDict(from_attributes=True)
