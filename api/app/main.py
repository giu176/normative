from __future__ import annotations

from datetime import date, datetime
import hashlib
import json
from pathlib import Path
from typing import Dict, List, Sequence
from uuid import uuid4

from fastapi import BackgroundTasks, Depends, FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, PlainTextResponse
from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app.db import SessionLocal, engine
from app.models import (
    DisciplineCategory,
    DocumentEdition,
    DocumentWork,
    EditionRelation,
    IngestionRun,
    LocalAttachment,
    NormativeList,
    NormativeListItem,
    SourceRecord,
    UserTag,
    WorkDiscipline,
    WorkTag,
)
from app.models import Base
from app.schemas import (
    AttachmentOut,
    DisciplineCreate,
    DisciplineOut,
    EditionCreate,
    EditionOut,
    EditionUpdate,
    IngestionStatus,
    ListCreate,
    ListFilters,
    ListItemOut,
    ListItemUpdate,
    ListOut,
    ListUpdate,
    ManualAddItem,
    RelationCreate,
    TagCreate,
    TagOut,
    WorkCreate,
    WorkOut,
    WorkUpdate,
)
from app.providers import get_provider

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Standarr API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ATTACHMENTS_DIR = Path("/data/attachments")
ATTACHMENTS_DIR.mkdir(parents=True, exist_ok=True)


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/disciplines", response_model=List[DisciplineOut])
def list_disciplines(db: Session = Depends(get_db)) -> List[DisciplineCategory]:
    return db.query(DisciplineCategory).order_by(DisciplineCategory.sort_order).all()


@app.post("/api/disciplines", response_model=DisciplineOut)
def create_discipline(
    payload: DisciplineCreate, db: Session = Depends(get_db)
) -> DisciplineCategory:
    discipline = DisciplineCategory(**payload.model_dump())
    db.add(discipline)
    db.commit()
    db.refresh(discipline)
    return discipline


@app.get("/api/tags", response_model=List[TagOut])
def list_tags(db: Session = Depends(get_db)) -> List[UserTag]:
    return db.query(UserTag).order_by(UserTag.name).all()


@app.post("/api/tags", response_model=TagOut)
def create_tag(payload: TagCreate, db: Session = Depends(get_db)) -> UserTag:
    normalized = payload.name.strip().lower()
    existing = db.query(UserTag).filter(UserTag.normalized_name == normalized).first()
    if existing:
        return existing
    tag = UserTag(name=payload.name.strip(), normalized_name=normalized)
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return tag


@app.get("/api/works", response_model=List[WorkOut])
def list_works(
    query: str | None = Query(default=None),
    authority: List[str] | None = Query(default=None),
    status: List[str] | None = Query(default=None),
    publication_date_from: date | None = Query(default=None),
    publication_date_to: date | None = Query(default=None),
    updated_from: datetime | None = Query(default=None),
    updated_to: datetime | None = Query(default=None),
    discipline_ids: List[int] | None = Query(default=None),
    tag_ids: List[int] | None = Query(default=None),
    only_latest_in_force: bool = Query(default=False),
    has_attachment: bool | None = Query(default=None),
    has_official_link: bool | None = Query(default=None),
    include_related: bool = Query(default=False),
    db: Session = Depends(get_db),
) -> List[DocumentWork]:
    filters = ListFilters(
        query=query,
        authority=authority,
        status=status,
        publication_date_from=publication_date_from,
        publication_date_to=publication_date_to,
        updated_from=updated_from,
        updated_to=updated_to,
        discipline_ids=discipline_ids,
        tag_ids=tag_ids,
        only_latest_in_force=only_latest_in_force,
        has_attachment=has_attachment,
        has_official_link=has_official_link,
        include_related=include_related,
    )
    editions_query = db.query(DocumentEdition).join(DocumentWork)
    editions_query = apply_filters(editions_query, filters)
    editions = editions_query.all()
    edition_ids = expand_with_related_editions(db, editions, filters.include_related)
    if not edition_ids:
        return []
    return (
        db.query(DocumentWork)
        .join(DocumentEdition)
        .filter(DocumentEdition.id.in_(edition_ids))
        .distinct()
        .all()
    )


@app.get("/api/works/{work_id}", response_model=WorkOut)
def get_work(work_id: int, db: Session = Depends(get_db)) -> DocumentWork:
    work = db.get(DocumentWork, work_id)
    if not work:
        raise HTTPException(status_code=404, detail="Work not found")
    return work


@app.post("/api/works", response_model=WorkOut)
def create_work(payload: WorkCreate, db: Session = Depends(get_db)) -> DocumentWork:
    work = DocumentWork(
        authority=payload.authority,
        identifier=payload.identifier,
        title=payload.title,
        abstract=payload.abstract,
        primary_discipline_id=payload.primary_discipline_id,
    )
    db.add(work)
    db.flush()
    for discipline_id in payload.secondary_discipline_ids:
        db.add(WorkDiscipline(work_id=work.id, discipline_id=discipline_id))
    for tag_id in payload.tag_ids:
        db.add(WorkTag(work_id=work.id, tag_id=tag_id))
    db.commit()
    db.refresh(work)
    return work


@app.patch("/api/works/{work_id}", response_model=WorkOut)
def update_work(
    work_id: int, payload: WorkUpdate, db: Session = Depends(get_db)
) -> DocumentWork:
    work = db.get(DocumentWork, work_id)
    if not work:
        raise HTTPException(status_code=404, detail="Work not found")
    data = payload.model_dump(exclude_unset=True)
    secondary_ids = data.pop("secondary_discipline_ids", None)
    tag_ids = data.pop("tag_ids", None)
    for key, value in data.items():
        setattr(work, key, value)
    if secondary_ids is not None:
        db.query(WorkDiscipline).filter(WorkDiscipline.work_id == work_id).delete()
        for discipline_id in secondary_ids:
            db.add(WorkDiscipline(work_id=work_id, discipline_id=discipline_id))
    if tag_ids is not None:
        db.query(WorkTag).filter(WorkTag.work_id == work_id).delete()
        for tag_id in tag_ids:
            db.add(WorkTag(work_id=work_id, tag_id=tag_id))
    db.commit()
    db.refresh(work)
    return work


@app.delete("/api/works/{work_id}")
def delete_work(work_id: int, db: Session = Depends(get_db)) -> dict[str, str]:
    work = db.get(DocumentWork, work_id)
    if not work:
        raise HTTPException(status_code=404, detail="Work not found")
    edition_ids = [edition.id for edition in work.editions]
    if edition_ids:
        db.query(LocalAttachment).filter(LocalAttachment.edition_id.in_(edition_ids)).delete()
        db.query(EditionRelation).filter(
            or_(
                EditionRelation.from_edition_id.in_(edition_ids),
                EditionRelation.to_edition_id.in_(edition_ids),
            )
        ).delete()
        db.query(NormativeListItem).filter(
            NormativeListItem.edition_id.in_(edition_ids)
        ).delete()
        db.query(DocumentEdition).filter(DocumentEdition.id.in_(edition_ids)).delete()
    db.query(WorkDiscipline).filter(WorkDiscipline.work_id == work_id).delete()
    db.query(WorkTag).filter(WorkTag.work_id == work_id).delete()
    db.delete(work)
    db.commit()
    return {"status": "deleted"}


@app.get("/api/editions/{edition_id}", response_model=EditionOut)
def get_edition(edition_id: int, db: Session = Depends(get_db)) -> DocumentEdition:
    edition = db.get(DocumentEdition, edition_id)
    if not edition:
        raise HTTPException(status_code=404, detail="Edition not found")
    return edition


@app.get("/api/editions", response_model=List[EditionOut])
def list_editions(
    query: str | None = Query(default=None),
    work_id: int | None = Query(default=None),
    authority: List[str] | None = Query(default=None),
    status: List[str] | None = Query(default=None),
    publication_date_from: date | None = Query(default=None),
    publication_date_to: date | None = Query(default=None),
    updated_from: datetime | None = Query(default=None),
    updated_to: datetime | None = Query(default=None),
    discipline_ids: List[int] | None = Query(default=None),
    tag_ids: List[int] | None = Query(default=None),
    only_latest_in_force: bool = Query(default=False),
    has_attachment: bool | None = Query(default=None),
    has_official_link: bool | None = Query(default=None),
    include_related: bool = Query(default=False),
    db: Session = Depends(get_db),
) -> List[DocumentEdition]:
    filters = ListFilters(
        query=query,
        authority=authority,
        status=status,
        publication_date_from=publication_date_from,
        publication_date_to=publication_date_to,
        updated_from=updated_from,
        updated_to=updated_to,
        discipline_ids=discipline_ids,
        tag_ids=tag_ids,
        only_latest_in_force=only_latest_in_force,
        has_attachment=has_attachment,
        has_official_link=has_official_link,
        include_related=include_related,
    )
    query_set = db.query(DocumentEdition).join(DocumentWork)
    if work_id is not None:
        query_set = query_set.filter(DocumentEdition.work_id == work_id)
    query_set = apply_filters(query_set, filters)
    editions = query_set.all()
    edition_ids = expand_with_related_editions(db, editions, filters.include_related)
    if not edition_ids:
        return []
    return (
        db.query(DocumentEdition)
        .filter(DocumentEdition.id.in_(edition_ids))
        .all()
    )


@app.post("/api/editions", response_model=EditionOut)
def create_edition(
    payload: EditionCreate, db: Session = Depends(get_db)
) -> DocumentEdition:
    edition = DocumentEdition(**payload.model_dump())
    db.add(edition)
    db.commit()
    db.refresh(edition)
    return edition


@app.patch("/api/editions/{edition_id}", response_model=EditionOut)
def update_edition(
    edition_id: int, payload: EditionUpdate, db: Session = Depends(get_db)
) -> DocumentEdition:
    edition = db.get(DocumentEdition, edition_id)
    if not edition:
        raise HTTPException(status_code=404, detail="Edition not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(edition, key, value)
    db.commit()
    db.refresh(edition)
    return edition


@app.delete("/api/editions/{edition_id}")
def delete_edition(edition_id: int, db: Session = Depends(get_db)) -> dict[str, str]:
    edition = db.get(DocumentEdition, edition_id)
    if not edition:
        raise HTTPException(status_code=404, detail="Edition not found")
    db.query(LocalAttachment).filter(LocalAttachment.edition_id == edition_id).delete()
    db.query(EditionRelation).filter(
        or_(
            EditionRelation.from_edition_id == edition_id,
            EditionRelation.to_edition_id == edition_id,
        )
    ).delete()
    db.query(NormativeListItem).filter(NormativeListItem.edition_id == edition_id).delete()
    db.delete(edition)
    db.commit()
    return {"status": "deleted"}


@app.post("/api/relations")
def create_relation(
    payload: RelationCreate, db: Session = Depends(get_db)
) -> dict[str, int]:
    relation = EditionRelation(**payload.model_dump())
    db.add(relation)
    db.commit()
    return {"id": relation.id}


def apply_filters(query, filters: ListFilters):
    if filters.query:
        like_term = f"%{filters.query.strip()}%"
        query = query.filter(
            or_(
                DocumentWork.title.ilike(like_term),
                DocumentWork.identifier.ilike(like_term),
                DocumentWork.abstract.ilike(like_term),
            )
        )
    if filters.authority:
        query = query.filter(DocumentWork.authority.in_(filters.authority))
    if filters.status:
        query = query.filter(DocumentEdition.status.in_(filters.status))
    if filters.publication_date_from:
        query = query.filter(DocumentEdition.publication_date >= filters.publication_date_from)
    if filters.publication_date_to:
        query = query.filter(DocumentEdition.publication_date <= filters.publication_date_to)
    if filters.updated_from:
        query = query.filter(DocumentEdition.updated_at >= filters.updated_from)
    if filters.updated_to:
        query = query.filter(DocumentEdition.updated_at <= filters.updated_to)
    if filters.discipline_ids:
        query = query.outerjoin(WorkDiscipline).filter(
            or_(
                DocumentWork.primary_discipline_id.in_(filters.discipline_ids),
                WorkDiscipline.discipline_id.in_(filters.discipline_ids),
            )
        )
    if filters.tag_ids:
        query = query.join(WorkTag).filter(WorkTag.tag_id.in_(filters.tag_ids))
    if filters.has_attachment is True:
        query = query.join(LocalAttachment)
    if filters.has_attachment is False:
        query = query.outerjoin(LocalAttachment).filter(LocalAttachment.id.is_(None))
    if filters.has_official_link is True:
        query = query.filter(DocumentEdition.source_canonical_url.is_not(None))
    if filters.has_official_link is False:
        query = query.filter(DocumentEdition.source_canonical_url.is_(None))
    if filters.only_latest_in_force:
        subq = (
            select(
                DocumentEdition.work_id,
                func.max(DocumentEdition.publication_date).label("max_pub"),
            )
            .where(DocumentEdition.status == "in_force")
            .group_by(DocumentEdition.work_id)
            .subquery()
        )
        query = query.join(
            subq,
            and_(
                DocumentEdition.work_id == subq.c.work_id,
                DocumentEdition.publication_date == subq.c.max_pub,
            ),
        )
    return query


def expand_with_related_editions(
    db: Session, editions: Sequence[DocumentEdition], include_related: bool
) -> List[int]:
    edition_ids = {edition.id for edition in editions}
    if not include_related or not edition_ids:
        return list(edition_ids)
    relations = (
        db.query(EditionRelation)
        .filter(
            or_(
                EditionRelation.from_edition_id.in_(edition_ids),
                EditionRelation.to_edition_id.in_(edition_ids),
            )
        )
        .all()
    )
    for relation in relations:
        edition_ids.add(relation.from_edition_id)
        edition_ids.add(relation.to_edition_id)
    return list(edition_ids)


def build_list_items(
    db: Session, list_id: int, editions: List[DocumentEdition]
) -> None:
    for edition in editions:
        work = edition.work
        secondary_ids = [wd.discipline_id for wd in work.secondary_disciplines]
        item = NormativeListItem(
            list_id=list_id,
            edition_id=edition.id,
            included=True,
            reason="auto",
            primary_discipline_id_at_time=work.primary_discipline_id,
            secondary_discipline_ids_at_time=secondary_ids,
        )
        db.add(item)


@app.post("/api/lists", response_model=ListOut)
def create_list(payload: ListCreate, db: Session = Depends(get_db)) -> NormativeList:
    normative_list = NormativeList(
        name=payload.name,
        description=payload.description,
        source_filter_json=payload.filters.model_dump(),
        regeneration_mode=payload.regeneration_mode,
        preserve_overrides=payload.preserve_overrides,
    )
    db.add(normative_list)
    db.flush()

    query = db.query(DocumentEdition).join(DocumentWork)
    query = apply_filters(query, payload.filters)
    editions = query.all()
    edition_ids = expand_with_related_editions(
        db, editions, payload.filters.include_related
    )
    if edition_ids:
        editions = (
            db.query(DocumentEdition)
            .filter(DocumentEdition.id.in_(edition_ids))
            .all()
        )
    else:
        editions = []
    build_list_items(db, normative_list.id, editions)

    db.commit()
    db.refresh(normative_list)
    return normative_list


@app.get("/api/lists/{list_id}", response_model=ListOut)
def get_list(list_id: int, db: Session = Depends(get_db)) -> NormativeList:
    normative_list = db.get(NormativeList, list_id)
    if not normative_list:
        raise HTTPException(status_code=404, detail="List not found")
    return normative_list


@app.patch("/api/lists/{list_id}", response_model=ListOut)
def update_list(
    list_id: int, payload: ListUpdate, db: Session = Depends(get_db)
) -> NormativeList:
    normative_list = db.get(NormativeList, list_id)
    if not normative_list:
        raise HTTPException(status_code=404, detail="List not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(normative_list, key, value)
    db.commit()
    db.refresh(normative_list)
    return normative_list


@app.post("/api/lists/{list_id}/regenerate", response_model=ListOut)
def regenerate_list(list_id: int, db: Session = Depends(get_db)) -> NormativeList:
    normative_list = db.get(NormativeList, list_id)
    if not normative_list:
        raise HTTPException(status_code=404, detail="List not found")

    filters = ListFilters(**normative_list.source_filter_json)
    query = db.query(DocumentEdition).join(DocumentWork)
    query = apply_filters(query, filters)
    editions = query.all()
    edition_ids = expand_with_related_editions(db, editions, filters.include_related)
    if edition_ids:
        editions = (
            db.query(DocumentEdition)
            .filter(DocumentEdition.id.in_(edition_ids))
            .all()
        )
    else:
        editions = []

    existing_items = (
        db.query(NormativeListItem)
        .filter(NormativeListItem.list_id == list_id)
        .all()
    )
    existing_by_edition = {item.edition_id: item for item in existing_items}
    new_edition_ids = {edition.id for edition in editions}

    for edition in editions:
        if edition.id in existing_by_edition:
            continue
        work = edition.work
        secondary_ids = [wd.discipline_id for wd in work.secondary_disciplines]
        db.add(
            NormativeListItem(
                list_id=list_id,
                edition_id=edition.id,
                included=True,
                reason="auto",
                primary_discipline_id_at_time=work.primary_discipline_id,
                secondary_discipline_ids_at_time=secondary_ids,
            )
        )

    for item in existing_items:
        if item.edition_id not in new_edition_ids and item.reason == "auto":
            db.delete(item)
            continue
        if not normative_list.preserve_overrides and item.reason in {
            "manual_exclude",
            "manual_include",
        }:
            if item.edition_id in new_edition_ids:
                item.included = True
                item.reason = "auto"
            else:
                db.delete(item)

    db.commit()
    db.refresh(normative_list)
    return normative_list


@app.get("/api/lists/{list_id}/items", response_model=List[ListItemOut])
def list_items(list_id: int, db: Session = Depends(get_db)) -> List[NormativeListItem]:
    normative_list = db.get(NormativeList, list_id)
    if not normative_list:
        raise HTTPException(status_code=404, detail="List not found")
    return (
        db.query(NormativeListItem)
        .join(NormativeListItem.edition)
        .join(DocumentEdition.work)
        .filter(NormativeListItem.list_id == list_id)
        .order_by(NormativeListItem.added_at)
        .all()
    )


@app.post("/api/lists/{list_id}/items/{item_id}/include")
def include_item(
    list_id: int, item_id: int, db: Session = Depends(get_db)
) -> dict[str, str]:
    item = (
        db.query(NormativeListItem)
        .filter(
            NormativeListItem.list_id == list_id,
            NormativeListItem.id == item_id,
        )
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="List item not found")
    item.included = True
    item.reason = "manual_include"
    db.commit()
    return {"status": "included"}


@app.post("/api/lists/{list_id}/items/{item_id}/exclude")
def exclude_item(
    list_id: int, item_id: int, db: Session = Depends(get_db)
) -> dict[str, str]:
    item = (
        db.query(NormativeListItem)
        .filter(
            NormativeListItem.list_id == list_id,
            NormativeListItem.id == item_id,
        )
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="List item not found")
    item.included = False
    item.reason = "manual_exclude"
    db.commit()
    return {"status": "excluded"}


@app.post("/api/lists/{list_id}/items/manual-add")
def manual_add_item(
    list_id: int, payload: ManualAddItem, db: Session = Depends(get_db)
) -> dict[str, int]:
    normative_list = db.get(NormativeList, list_id)
    if not normative_list:
        raise HTTPException(status_code=404, detail="List not found")
    edition = db.get(DocumentEdition, payload.edition_id)
    if not edition:
        raise HTTPException(status_code=404, detail="Edition not found")
    work = edition.work
    secondary_ids = [wd.discipline_id for wd in work.secondary_disciplines]
    item = NormativeListItem(
        list_id=list_id,
        edition_id=edition.id,
        included=True,
        reason="manual_include",
        note=payload.note,
        primary_discipline_id_at_time=work.primary_discipline_id,
        secondary_discipline_ids_at_time=secondary_ids,
    )
    db.add(item)
    db.commit()
    return {"id": item.id}


@app.patch("/api/lists/{list_id}/items/{item_id}")
def update_item_note(
    list_id: int,
    item_id: int,
    payload: ListItemUpdate,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    item = (
        db.query(NormativeListItem)
        .filter(
            NormativeListItem.list_id == list_id,
            NormativeListItem.id == item_id,
        )
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="List item not found")
    if payload.note is not None:
        item.note = payload.note
    db.commit()
    return {"status": "updated"}


def format_export_line(item: NormativeListItem, discipline_name: str) -> str:
    edition = item.edition
    work = edition.work
    pub_date = edition.publication_date.isoformat() if edition.publication_date else "n.d."
    status = edition.status
    return (
        f"- {work.identifier} — {work.title} (Ed. {edition.edition_label}, "
        f"Pub. {pub_date}) [{work.authority}] {status}\n"
        + (f"  Note: {item.note}\n" if item.note else "")
    )


def calculate_sha256(payload: bytes) -> str:
    import hashlib

    return hashlib.sha256(payload).hexdigest()


def sanitize_filename(filename: str) -> str:
    sanitized = filename.strip().replace("/", "_").replace("\\", "_")
    return sanitized or f"attachment-{uuid4().hex}"


@app.get("/api/lists/{list_id}/export/txt", response_class=PlainTextResponse)
def export_list_txt(list_id: int, db: Session = Depends(get_db)) -> str:
    normative_list = db.get(NormativeList, list_id)
    if not normative_list:
        raise HTTPException(status_code=404, detail="List not found")

    items = (
        db.query(NormativeListItem)
        .join(NormativeListItem.edition)
        .join(DocumentEdition.work)
        .filter(NormativeListItem.list_id == list_id, NormativeListItem.included.is_(True))
        .all()
    )

    disciplines = {
        d.id: d
        for d in db.query(DisciplineCategory).order_by(DisciplineCategory.sort_order).all()
    }

    sections: Dict[int, Dict[str, List[str]]] = {}
    for item in items:
        primary_id = item.primary_discipline_id_at_time
        if primary_id is None:
            continue
        sections.setdefault(primary_id, {"primary": [], "references": []})
        sections[primary_id]["primary"].append(
            format_export_line(item, disciplines[primary_id].name)
        )
        for secondary_id in item.secondary_discipline_ids_at_time or []:
            if secondary_id == primary_id:
                continue
            sections.setdefault(secondary_id, {"primary": [], "references": []})
            primary_name = disciplines.get(primary_id).name if disciplines.get(primary_id) else "N/D"
            sections[secondary_id]["references"].append(
                f"- {item.edition.work.identifier} — vedi disciplina primaria: {primary_name}\n"
            )

    header = [
        "Standarr – Elenco Normative",
        f"Nome elenco: {normative_list.name}",
        f"Generato: {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
        f"Modalità: {normative_list.regeneration_mode}",
        f"Criteri (snapshot): {normative_list.source_filter_json}",
        "",
    ]

    body: List[str] = []
    for discipline_id, discipline in disciplines.items():
        if discipline_id not in sections:
            continue
        body.append(f"== {discipline.name.upper()} ==")
        body.append("[Norme]")
        body.extend(sections[discipline_id]["primary"] or ["- (nessuna)\n"])
        body.append("[Riferimenti]")
        body.extend(sections[discipline_id]["references"] or ["- (nessuno)\n"])
        body.append("")

    return "\n".join(header + body)


@app.get("/api/editions/{edition_id}/attachments", response_model=List[AttachmentOut])
def list_attachments(
    edition_id: int, db: Session = Depends(get_db)
) -> List[LocalAttachment]:
    edition = db.get(DocumentEdition, edition_id)
    if not edition:
        raise HTTPException(status_code=404, detail="Edition not found")
    return (
        db.query(LocalAttachment)
        .filter(LocalAttachment.edition_id == edition_id)
        .order_by(LocalAttachment.uploaded_at.desc())
        .all()
    )


@app.post("/api/editions/{edition_id}/attachments", response_model=AttachmentOut)
def upload_attachment(
    edition_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> LocalAttachment:
    edition = db.get(DocumentEdition, edition_id)
    if not edition:
        raise HTTPException(status_code=404, detail="Edition not found")
    payload = file.file.read()
    if not payload:
        raise HTTPException(status_code=400, detail="Empty upload")
    digest = calculate_sha256(payload)
    existing = (
        db.query(LocalAttachment)
        .filter(LocalAttachment.sha256 == digest, LocalAttachment.edition_id == edition_id)
        .first()
    )
    if existing:
        return existing
    safe_name = sanitize_filename(file.filename or "attachment.bin")
    stored_name = f"{uuid4().hex}-{safe_name}"
    storage_path = ATTACHMENTS_DIR / stored_name
    storage_path.write_bytes(payload)
    attachment = LocalAttachment(
        edition_id=edition_id,
        filename=safe_name,
        mime_type=file.content_type or "application/octet-stream",
        size_bytes=len(payload),
        sha256=digest,
        storage_path=str(storage_path),
    )
    db.add(attachment)
    db.commit()
    db.refresh(attachment)
    return attachment


@app.get("/api/attachments/{attachment_id}")
def download_attachment(
    attachment_id: int, db: Session = Depends(get_db)
) -> FileResponse:
    attachment = db.get(LocalAttachment, attachment_id)
    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")
    return FileResponse(
        attachment.storage_path,
        media_type=attachment.mime_type,
        filename=attachment.filename,
    )


@app.delete("/api/attachments/{attachment_id}")
def delete_attachment(attachment_id: int, db: Session = Depends(get_db)) -> dict[str, str]:
    attachment = db.get(LocalAttachment, attachment_id)
    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")
    storage_path = Path(attachment.storage_path)
    if storage_path.exists():
        storage_path.unlink()
    db.delete(attachment)
    db.commit()
    return {"status": "deleted"}


def enqueue_ingestion(
    provider: str, background_tasks: BackgroundTasks, db: Session
) -> int:
    try:
        get_provider(provider)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    run = IngestionRun(provider=provider, status="running", started_at=datetime.utcnow())
    db.add(run)
    db.commit()
    db.refresh(run)
    background_tasks.add_task(_run_ingestion_job, provider, run.id)
    return run.id


def _run_ingestion_job(provider: str, run_id: int) -> None:
    db = SessionLocal()
    try:
        provider_module = get_provider(provider)
        run = db.get(IngestionRun, run_id)
        if not run:
            return
        previous_run = (
            db.query(IngestionRun)
            .filter(IngestionRun.id != run_id)
            .order_by(IngestionRun.started_at.desc())
            .first()
        )
        since = previous_run.started_at if previous_run else None

        records = provider_module.fetch_changes(since)
        ingested = 0
        try:
            for record in records:
                normalized = provider_module.normalize(record, db=db)
                candidate = provider_module.match_and_merge(normalized, db=db)
                work_payload = candidate["work"]
                edition_payload = candidate["edition"]
                external_id = candidate["external_id"]

                work = _upsert_work(db, work_payload)
                edition = _upsert_edition(db, work, edition_payload)

                payload_hash = _payload_hash(record)
                raw_reference = edition_payload.get("source_canonical_url")
                _upsert_source_record(
                    db,
                    provider=provider,
                    external_id=external_id,
                    payload_hash=payload_hash,
                    raw_reference=raw_reference,
                    work_id=work.id,
                    edition_id=edition.id,
                )

                for relation in candidate.get("relations", []):
                    to_external_id = relation.get("to_external_id")
                    if not to_external_id:
                        continue
                    target_source = (
                        db.query(SourceRecord)
                        .filter(
                            SourceRecord.provider == provider,
                            SourceRecord.external_id == to_external_id,
                        )
                        .first()
                    )
                    if not target_source or not target_source.edition_id:
                        continue
                    exists = (
                        db.query(EditionRelation)
                        .filter(
                            EditionRelation.from_edition_id == edition.id,
                            EditionRelation.to_edition_id == target_source.edition_id,
                            EditionRelation.type == relation.get("type", "related"),
                        )
                        .first()
                    )
                    if exists:
                        continue
                    db.add(
                        EditionRelation(
                            from_edition_id=edition.id,
                            to_edition_id=target_source.edition_id,
                            type=relation.get("type", "related"),
                            confidence=relation.get("confidence", 1.0),
                            source=relation.get("source"),
                        )
                    )
                ingested += 1
            db.commit()
            run.status = "completed"
            run.finished_at = datetime.utcnow()
            run.error_message = None
            db.add(run)
            db.commit()
        except Exception as exc:
            db.rollback()
            run.status = "failed"
            run.finished_at = datetime.utcnow()
            run.error_message = str(exc)
            db.add(run)
            db.commit()
    finally:
        db.close()


@app.post("/api/ingestion/run")
def run_ingestion(
    background_tasks: BackgroundTasks,
    provider: str = Query(...),
    db: Session = Depends(get_db),
) -> dict[str, str | int]:
    run_id = enqueue_ingestion(provider, background_tasks, db)
    return {"status": "queued", "provider": provider, "run_id": run_id}


@app.get("/api/ingestion/status", response_model=IngestionStatus)
def ingestion_status(db: Session = Depends(get_db)) -> IngestionStatus:
    latest_run = db.query(IngestionRun).order_by(IngestionRun.started_at.desc()).first()
    if not latest_run:
        return IngestionStatus()
    return IngestionStatus(
        last_run_at=latest_run.started_at,
        last_provider=latest_run.provider,
        status=latest_run.status,
    )


def _parse_date(value: date | str | None) -> date | None:
    if isinstance(value, date):
        return value
    if isinstance(value, str) and value:
        return date.fromisoformat(value)
    return None


def _payload_hash(payload: dict) -> str:
    encoded = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _upsert_work(db: Session, payload: dict) -> DocumentWork:
    secondary_ids = payload.get("secondary_discipline_ids")
    tag_ids = payload.get("tag_ids")
    work = (
        db.query(DocumentWork)
        .filter(DocumentWork.identifier == payload["identifier"])
        .first()
    )
    if work:
        work.authority = payload["authority"]
        work.title = payload["title"]
        if payload.get("primary_discipline_id") is not None:
            work.primary_discipline_id = payload.get("primary_discipline_id")
        db.add(work)
        if secondary_ids is not None:
            _sync_work_disciplines(db, work.id, secondary_ids)
        if tag_ids is not None:
            _sync_work_tags(db, work.id, tag_ids)
        return work
    work = DocumentWork(
        authority=payload["authority"],
        identifier=payload["identifier"],
        title=payload["title"],
        primary_discipline_id=payload.get("primary_discipline_id"),
    )
    db.add(work)
    db.flush()
    if secondary_ids is not None:
        _sync_work_disciplines(db, work.id, secondary_ids)
    if tag_ids is not None:
        _sync_work_tags(db, work.id, tag_ids)
    return work


def _sync_work_disciplines(
    db: Session, work_id: int, discipline_ids: Sequence[int]
) -> None:
    db.query(WorkDiscipline).filter(WorkDiscipline.work_id == work_id).delete()
    for discipline_id in discipline_ids:
        db.add(WorkDiscipline(work_id=work_id, discipline_id=discipline_id))


def _sync_work_tags(db: Session, work_id: int, tag_ids: Sequence[int]) -> None:
    db.query(WorkTag).filter(WorkTag.work_id == work_id).delete()
    for tag_id in tag_ids:
        db.add(WorkTag(work_id=work_id, tag_id=tag_id))


def _upsert_edition(db: Session, work: DocumentWork, payload: dict) -> DocumentEdition:
    publication_date = _parse_date(payload.get("publication_date"))
    edition = (
        db.query(DocumentEdition)
        .filter(
            DocumentEdition.work_id == work.id,
            DocumentEdition.edition_label == payload["edition_label"],
            DocumentEdition.publication_date == publication_date,
        )
        .first()
    )
    if edition:
        edition.status = payload.get("status", edition.status)
        edition.source_canonical_url = payload.get(
            "source_canonical_url", edition.source_canonical_url
        )
        db.add(edition)
        return edition
    edition = DocumentEdition(
        work_id=work.id,
        edition_label=payload["edition_label"],
        publication_date=publication_date,
        status=payload.get("status", "unknown"),
        source_canonical_url=payload.get("source_canonical_url"),
    )
    db.add(edition)
    db.flush()
    return edition


def _upsert_source_record(
    db: Session,
    provider: str,
    external_id: str,
    payload_hash: str,
    raw_reference: str | None,
    work_id: int | None,
    edition_id: int | None,
) -> SourceRecord:
    record = (
        db.query(SourceRecord)
        .filter(SourceRecord.provider == provider, SourceRecord.external_id == external_id)
        .first()
    )
    if record:
        record.payload_hash = payload_hash
        record.raw_reference = raw_reference
        record.work_id = work_id
        record.edition_id = edition_id
        db.add(record)
        return record
    record = SourceRecord(
        provider=provider,
        external_id=external_id,
        payload_hash=payload_hash,
        raw_reference=raw_reference,
        work_id=work_id,
        edition_id=edition_id,
    )
    db.add(record)
    return record
