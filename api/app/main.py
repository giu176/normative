from __future__ import annotations

from datetime import datetime
from typing import Dict, List

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app.db import SessionLocal, engine
from app.models import (
    DisciplineCategory,
    DocumentEdition,
    DocumentWork,
    EditionRelation,
    LocalAttachment,
    NormativeList,
    NormativeListItem,
    UserTag,
    WorkDiscipline,
    WorkTag,
)
from app.models import Base
from app.schemas import (
    DisciplineCreate,
    DisciplineOut,
    EditionCreate,
    EditionOut,
    IngestionStatus,
    ListCreate,
    ListFilters,
    ListItemUpdate,
    ListOut,
    ListUpdate,
    ManualAddItem,
    RelationCreate,
    TagCreate,
    TagOut,
    WorkCreate,
    WorkOut,
)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Standarr API")

_ingestion_status = IngestionStatus()


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
    authority: List[str] | None = Query(default=None),
    status: List[str] | None = Query(default=None),
    db: Session = Depends(get_db),
) -> List[DocumentWork]:
    query = db.query(DocumentWork)
    if authority:
        query = query.filter(DocumentWork.authority.in_(authority))
    if status:
        query = query.join(DocumentWork.editions).filter(DocumentEdition.status.in_(status))
    return query.all()


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


@app.get("/api/editions/{edition_id}", response_model=EditionOut)
def get_edition(edition_id: int, db: Session = Depends(get_db)) -> DocumentEdition:
    edition = db.get(DocumentEdition, edition_id)
    if not edition:
        raise HTTPException(status_code=404, detail="Edition not found")
    return edition


@app.post("/api/editions", response_model=EditionOut)
def create_edition(
    payload: EditionCreate, db: Session = Depends(get_db)
) -> DocumentEdition:
    edition = DocumentEdition(**payload.model_dump())
    db.add(edition)
    db.commit()
    db.refresh(edition)
    return edition


@app.post("/api/relations")
def create_relation(
    payload: RelationCreate, db: Session = Depends(get_db)
) -> dict[str, int]:
    relation = EditionRelation(**payload.model_dump())
    db.add(relation)
    db.commit()
    return {"id": relation.id}


def apply_filters(query, filters: ListFilters):
    if filters.authority:
        query = query.filter(DocumentWork.authority.in_(filters.authority))
    if filters.status:
        query = query.filter(DocumentEdition.status.in_(filters.status))
    if filters.publication_date_from:
        query = query.filter(DocumentEdition.publication_date >= filters.publication_date_from)
    if filters.publication_date_to:
        query = query.filter(DocumentEdition.publication_date <= filters.publication_date_to)
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

    existing_items = (
        db.query(NormativeListItem)
        .filter(NormativeListItem.list_id == list_id)
        .all()
    )
    existing_by_edition = {item.edition_id: item for item in existing_items}

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

    if not normative_list.preserve_overrides:
        for item in existing_items:
            if item.reason == "manual_exclude":
                item.included = True
                item.reason = "auto"

    db.commit()
    db.refresh(normative_list)
    return normative_list


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


@app.post("/api/ingestion/run")
def run_ingestion(provider: str = Query(...)) -> dict[str, str]:
    _ingestion_status.last_run_at = datetime.utcnow()
    _ingestion_status.last_provider = provider
    _ingestion_status.status = "queued"
    return {"status": "queued", "provider": provider}


@app.get("/api/ingestion/status", response_model=IngestionStatus)
def ingestion_status() -> IngestionStatus:
    return _ingestion_status
