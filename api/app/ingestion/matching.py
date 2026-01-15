from __future__ import annotations

from datetime import date
from typing import Any, Dict

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import DocumentEdition, DocumentWork, SourceRecord


def match_and_merge_candidate(
    candidate: Dict[str, Any], db: Session | None, provider: str
) -> Dict[str, Any]:
    if not db:
        return candidate

    work_payload = candidate.get("work") or {}
    edition_payload = candidate.get("edition") or {}
    relations = candidate.setdefault("relations", [])

    external_id = candidate.get("external_id")
    existing_work = None
    existing_edition = None

    if external_id:
        source_record = (
            db.query(SourceRecord)
            .filter(
                SourceRecord.provider == provider, SourceRecord.external_id == external_id
            )
            .first()
        )
        if source_record:
            if source_record.work_id:
                existing_work = db.get(DocumentWork, source_record.work_id)
            if source_record.edition_id:
                existing_edition = db.get(DocumentEdition, source_record.edition_id)

    identifier = work_payload.get("identifier")
    if identifier and not existing_work:
        normalized_identifier = _normalize_identifier(identifier)
        existing_work = (
            db.query(DocumentWork)
            .filter(
                func.replace(func.lower(DocumentWork.identifier), " ", "")
                == normalized_identifier
            )
            .first()
        )

    source_url = edition_payload.get("source_canonical_url")
    if source_url and not existing_edition:
        existing_edition = (
            db.query(DocumentEdition)
            .filter(DocumentEdition.source_canonical_url == source_url)
            .first()
        )

    if existing_edition and not existing_work:
        existing_work = existing_edition.work

    if existing_work:
        work_payload["identifier"] = existing_work.identifier
        candidate["work"] = work_payload

    if existing_edition:
        edition_payload["edition_label"] = existing_edition.edition_label
        edition_payload["publication_date"] = existing_edition.publication_date
        candidate["edition"] = edition_payload

    if existing_work and not existing_edition:
        candidate_date = _parse_date(edition_payload.get("publication_date"))
        matching_edition = (
            db.query(DocumentEdition)
            .filter(
                DocumentEdition.work_id == existing_work.id,
                DocumentEdition.edition_label == edition_payload.get("edition_label"),
                DocumentEdition.publication_date == candidate_date,
            )
            .first()
        )
        if not matching_edition:
            related_source = _latest_source_for_work(db, existing_work.id, provider)
            if related_source and related_source.external_id != external_id:
                _append_relation(relations, related_source.external_id)

    return candidate


def _normalize_identifier(value: str) -> str:
    return value.strip().lower().replace(" ", "")


def _parse_date(value: date | str | None) -> date | None:
    if isinstance(value, date):
        return value
    if isinstance(value, str) and value:
        return date.fromisoformat(value)
    return None


def _latest_source_for_work(
    db: Session, work_id: int, provider: str
) -> SourceRecord | None:
    return (
        db.query(SourceRecord)
        .join(DocumentEdition, SourceRecord.edition_id == DocumentEdition.id)
        .filter(
            SourceRecord.provider == provider,
            DocumentEdition.work_id == work_id,
        )
        .order_by(
            DocumentEdition.publication_date.desc().nullslast(),
            SourceRecord.fetched_at.desc(),
        )
        .first()
    )


def _append_relation(relations: list[dict[str, Any]], to_external_id: str) -> None:
    for relation in relations:
        if relation.get("to_external_id") == to_external_id:
            return
    relations.append(
        {
            "to_external_id": to_external_id,
            "type": "related",
            "confidence": 1.0,
            "source": "match_and_merge",
        }
    )
