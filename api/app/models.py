from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class DisciplineCategory(Base):
    __tablename__ = "discipline_categories"

    id = Column(Integer, primary_key=True)
    code = Column(String(50), nullable=False, unique=True)
    name = Column(String(255), nullable=False)
    version = Column(String(50), nullable=False, default="v1")
    sort_order = Column(Integer, nullable=False, default=0)
    active = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    works = relationship("DocumentWork", back_populates="primary_discipline")


class UserTag(Base):
    __tablename__ = "user_tags"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    normalized_name = Column(String(255), nullable=False, unique=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    works = relationship("WorkTag", back_populates="tag")


class DocumentWork(Base):
    __tablename__ = "document_works"

    id = Column(Integer, primary_key=True)
    authority = Column(String(50), nullable=False)
    identifier = Column(String(255), nullable=False, unique=True)
    title = Column(String(512), nullable=False)
    abstract = Column(Text, nullable=True)
    primary_discipline_id = Column(Integer, ForeignKey("discipline_categories.id"))
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    primary_discipline = relationship("DisciplineCategory", back_populates="works")
    editions = relationship("DocumentEdition", back_populates="work")
    secondary_disciplines = relationship("WorkDiscipline", back_populates="work")
    tags = relationship("WorkTag", back_populates="work")


class WorkDiscipline(Base):
    __tablename__ = "work_disciplines"

    work_id = Column(Integer, ForeignKey("document_works.id"), primary_key=True)
    discipline_id = Column(
        Integer, ForeignKey("discipline_categories.id"), primary_key=True
    )

    work = relationship("DocumentWork", back_populates="secondary_disciplines")
    discipline = relationship("DisciplineCategory")


class WorkTag(Base):
    __tablename__ = "work_tags"

    work_id = Column(Integer, ForeignKey("document_works.id"), primary_key=True)
    tag_id = Column(Integer, ForeignKey("user_tags.id"), primary_key=True)

    work = relationship("DocumentWork", back_populates="tags")
    tag = relationship("UserTag", back_populates="works")


class DocumentEdition(Base):
    __tablename__ = "document_editions"

    id = Column(Integer, primary_key=True)
    work_id = Column(Integer, ForeignKey("document_works.id"), nullable=False)
    edition_label = Column(String(100), nullable=False)
    publication_date = Column(Date, nullable=True)
    status = Column(String(50), nullable=False, default="unknown")
    valid_from = Column(Date, nullable=True)
    valid_to = Column(Date, nullable=True)
    source_canonical_url = Column(String(1024), nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    work = relationship("DocumentWork", back_populates="editions")
    relations_from = relationship(
        "EditionRelation", foreign_keys="EditionRelation.from_edition_id"
    )
    relations_to = relationship(
        "EditionRelation", foreign_keys="EditionRelation.to_edition_id"
    )
    attachments = relationship("LocalAttachment", back_populates="edition")


class EditionRelation(Base):
    __tablename__ = "edition_relations"

    id = Column(Integer, primary_key=True)
    from_edition_id = Column(Integer, ForeignKey("document_editions.id"), nullable=False)
    to_edition_id = Column(Integer, ForeignKey("document_editions.id"), nullable=False)
    type = Column(String(50), nullable=False)
    confidence = Column(Float, nullable=False, default=1.0)
    source = Column(String(100), nullable=True)

    __table_args__ = (
        CheckConstraint("confidence >= 0 AND confidence <= 1", name="ck_confidence"),
    )


class SourceRecord(Base):
    __tablename__ = "source_records"

    id = Column(Integer, primary_key=True)
    provider = Column(String(100), nullable=False)
    external_id = Column(String(255), nullable=False)
    payload_hash = Column(String(128), nullable=False)
    fetched_at = Column(DateTime, nullable=False, server_default=func.now())
    raw_reference = Column(String(1024), nullable=True)
    work_id = Column(Integer, ForeignKey("document_works.id"), nullable=True)
    edition_id = Column(Integer, ForeignKey("document_editions.id"), nullable=True)

    __table_args__ = (
        UniqueConstraint("provider", "external_id", name="uq_source_external"),
    )


class LocalAttachment(Base):
    __tablename__ = "local_attachments"

    id = Column(Integer, primary_key=True)
    edition_id = Column(Integer, ForeignKey("document_editions.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    mime_type = Column(String(100), nullable=False)
    size_bytes = Column(Integer, nullable=False)
    sha256 = Column(String(64), nullable=False)
    storage_path = Column(String(1024), nullable=False)
    uploaded_at = Column(DateTime, nullable=False, server_default=func.now())

    edition = relationship("DocumentEdition", back_populates="attachments")


class NormativeList(Base):
    __tablename__ = "normative_lists"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, default="draft")
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )
    source_filter_json = Column(JSONB, nullable=False, default=dict)
    regeneration_mode = Column(String(50), nullable=False, default="dynamic")
    preserve_overrides = Column(Boolean, nullable=False, default=True)

    items = relationship("NormativeListItem", back_populates="list")


class NormativeListItem(Base):
    __tablename__ = "normative_list_items"

    id = Column(Integer, primary_key=True)
    list_id = Column(Integer, ForeignKey("normative_lists.id"), nullable=False)
    edition_id = Column(Integer, ForeignKey("document_editions.id"), nullable=False)
    included = Column(Boolean, nullable=False, default=True)
    reason = Column(String(50), nullable=False, default="auto")
    note = Column(Text, nullable=True)
    primary_discipline_id_at_time = Column(Integer, nullable=True)
    secondary_discipline_ids_at_time = Column(JSONB, nullable=False, default=list)
    added_at = Column(DateTime, nullable=False, server_default=func.now())

    list = relationship("NormativeList", back_populates="items")
    edition = relationship("DocumentEdition")
