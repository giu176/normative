from datetime import date, datetime
from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ORMBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class DisciplineCreate(BaseModel):
    code: str
    name: str
    version: str = "v1"
    sort_order: int = 0
    active: bool = True


class DisciplineOut(ORMBase, DisciplineCreate):
    id: int
    created_at: datetime
    updated_at: datetime


class TagCreate(BaseModel):
    name: str


class TagOut(ORMBase):
    id: int
    name: str
    normalized_name: str
    created_at: datetime


class WorkCreate(BaseModel):
    authority: str
    identifier: str
    title: str
    abstract: Optional[str] = None
    primary_discipline_id: Optional[int] = None
    secondary_discipline_ids: List[int] = Field(default_factory=list)
    tag_ids: List[int] = Field(default_factory=list)


class WorkOut(ORMBase):
    id: int
    authority: str
    identifier: str
    title: str
    abstract: Optional[str]
    primary_discipline_id: Optional[int]
    created_at: datetime
    updated_at: datetime


class WorkSummary(ORMBase):
    id: int
    authority: str
    identifier: str
    title: str


class WorkUpdate(BaseModel):
    authority: Optional[str] = None
    identifier: Optional[str] = None
    title: Optional[str] = None
    abstract: Optional[str] = None
    primary_discipline_id: Optional[int] = None
    secondary_discipline_ids: Optional[List[int]] = None
    tag_ids: Optional[List[int]] = None


class EditionCreate(BaseModel):
    work_id: int
    edition_label: str
    publication_date: Optional[date] = None
    status: str = "unknown"
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None
    source_canonical_url: Optional[str] = None


class EditionOut(ORMBase):
    id: int
    work_id: int
    edition_label: str
    publication_date: Optional[date]
    status: str
    valid_from: Optional[date]
    valid_to: Optional[date]
    source_canonical_url: Optional[str]
    created_at: datetime
    updated_at: datetime


class EditionSummary(ORMBase):
    id: int
    edition_label: str
    publication_date: Optional[date]
    status: str
    work: WorkSummary


class EditionUpdate(BaseModel):
    edition_label: Optional[str] = None
    publication_date: Optional[date] = None
    status: Optional[str] = None
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None
    source_canonical_url: Optional[str] = None


class RelationCreate(BaseModel):
    from_edition_id: int
    to_edition_id: int
    type: str
    confidence: float = 1.0
    source: Optional[str] = None


class ListFilters(BaseModel):
    query: Optional[str] = None
    authority: Optional[List[str]] = None
    status: Optional[List[str]] = None
    publication_date_from: Optional[date] = None
    publication_date_to: Optional[date] = None
    updated_from: Optional[datetime] = None
    updated_to: Optional[datetime] = None
    discipline_ids: Optional[List[int]] = None
    tag_ids: Optional[List[int]] = None
    only_latest_in_force: bool = False
    has_attachment: Optional[bool] = None
    has_official_link: Optional[bool] = None
    include_related: bool = False


class ListCreate(BaseModel):
    name: str
    description: Optional[str] = None
    filters: ListFilters = Field(default_factory=ListFilters)
    regeneration_mode: str = "dynamic"
    preserve_overrides: bool = True


class ListUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    regeneration_mode: Optional[str] = None
    preserve_overrides: Optional[bool] = None


class ListOut(ORMBase):
    id: int
    name: str
    description: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime
    source_filter_json: dict[str, Any]
    regeneration_mode: str
    preserve_overrides: bool


class ListItemUpdate(BaseModel):
    note: Optional[str] = None


class ManualAddItem(BaseModel):
    edition_id: int
    note: Optional[str] = None


class ListItemOut(ORMBase):
    id: int
    list_id: int
    edition_id: int
    included: bool
    reason: str
    note: Optional[str]
    primary_discipline_id_at_time: Optional[int]
    secondary_discipline_ids_at_time: List[int]
    added_at: datetime
    edition: EditionSummary


class AttachmentOut(ORMBase):
    id: int
    edition_id: int
    filename: str
    mime_type: str
    size_bytes: int
    sha256: str
    uploaded_at: datetime


class IngestionStatus(ORMBase):
    last_run_at: Optional[datetime] = None
    last_provider: Optional[str] = None
    status: str = "idle"


class IngestionRunOut(ORMBase):
    id: int
    provider: str
    status: str
    started_at: datetime
    finished_at: Optional[datetime]
    error_message: Optional[str]
    records_imported: int
