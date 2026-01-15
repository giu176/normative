from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from sqlalchemy.orm import Session

from app.models import DisciplineCategory, UserTag


@dataclass(frozen=True)
class DisciplineRule:
    code: str
    name: str
    keywords: tuple[str, ...]


DISCIPLINE_RULES: tuple[DisciplineRule, ...] = (
    DisciplineRule(
        code="PRIV",
        name="Privacy e protezione dati",
        keywords=("privacy", "data protection", "gdpr", "personal data"),
    ),
    DisciplineRule(
        code="QUAL",
        name="Gestione della qualita",
        keywords=("quality", "quality management", "qms"),
    ),
    DisciplineRule(
        code="ADM",
        name="Procedimento amministrativo",
        keywords=("procedimento amministrativo", "public administration", "administrative"),
    ),
)

TAG_RULES: dict[str, tuple[str, ...]] = {
    "gdpr": ("gdpr", "general data protection regulation"),
    "quality-management": ("quality management", "qms"),
    "procedimento-amministrativo": ("procedimento amministrativo",),
}


def apply_mapping(normalized: dict, db: Session | None = None) -> dict:
    work = normalized.get("work")
    if not work:
        return normalized

    terms = _collect_terms(normalized)
    discipline_codes = _match_disciplines(terms)
    tag_names = _match_tags(terms)

    primary_id = work.get("primary_discipline_id")
    secondary_ids: list[int] | None = work.get("secondary_discipline_ids")
    tag_ids: list[int] | None = work.get("tag_ids")

    if db:
        mapped_primary_id, mapped_secondary_ids = _resolve_discipline_ids(
            db, discipline_codes
        )
        mapped_tag_ids = _resolve_tag_ids(db, tag_names)

        if primary_id is None:
            primary_id = mapped_primary_id
        if secondary_ids is None:
            secondary_ids = mapped_secondary_ids
        else:
            secondary_ids = _merge_ids(secondary_ids, mapped_secondary_ids)
        if tag_ids is None:
            tag_ids = mapped_tag_ids
        else:
            tag_ids = _merge_ids(tag_ids, mapped_tag_ids)

    if primary_id is not None:
        work["primary_discipline_id"] = primary_id
    if secondary_ids is not None:
        if primary_id is not None:
            secondary_ids = [value for value in secondary_ids if value != primary_id]
        work["secondary_discipline_ids"] = secondary_ids
    if tag_ids is not None:
        work["tag_ids"] = tag_ids

    return normalized


def _collect_terms(normalized: dict) -> list[str]:
    candidates: list[str] = []
    for key in ("categories", "keywords"):
        for value in normalized.get(key) or []:
            candidates.append(str(value))
    work = normalized.get("work") or {}
    title = work.get("title")
    if title:
        candidates.append(str(title))
    return [item.strip().lower() for item in candidates if str(item).strip()]


def _match_disciplines(terms: Iterable[str]) -> list[str]:
    matches: list[str] = []
    for rule in DISCIPLINE_RULES:
        if _has_keyword(terms, rule.keywords):
            matches.append(rule.code)
    return matches


def _match_tags(terms: Iterable[str]) -> list[str]:
    matches: list[str] = []
    for name, keywords in TAG_RULES.items():
        if _has_keyword(terms, keywords):
            matches.append(name)
    return matches


def _has_keyword(terms: Iterable[str], keywords: Iterable[str]) -> bool:
    for term in terms:
        for keyword in keywords:
            if keyword in term:
                return True
    return False


def _resolve_discipline_ids(
    db: Session, codes: list[str]
) -> tuple[int | None, list[int]]:
    if not codes:
        return None, []
    existing = (
        db.query(DisciplineCategory)
        .filter(DisciplineCategory.code.in_(codes))
        .all()
    )
    by_code = {discipline.code: discipline for discipline in existing}
    for rule in DISCIPLINE_RULES:
        if rule.code not in codes or rule.code in by_code:
            continue
        discipline = DisciplineCategory(
            code=rule.code,
            name=rule.name,
            version="v1",
            sort_order=0,
            active=True,
        )
        db.add(discipline)
        db.flush()
        by_code[rule.code] = discipline

    ordered_ids = [by_code[code].id for code in codes if code in by_code]
    primary_id = ordered_ids[0] if ordered_ids else None
    secondary_ids = ordered_ids[1:] if len(ordered_ids) > 1 else []
    return primary_id, secondary_ids


def _resolve_tag_ids(db: Session, names: list[str]) -> list[int]:
    if not names:
        return []
    normalized_map = {_normalize_tag(name): name for name in names}
    existing = (
        db.query(UserTag)
        .filter(UserTag.normalized_name.in_(normalized_map))
        .all()
    )
    by_normalized = {tag.normalized_name: tag for tag in existing}
    for normalized, original in normalized_map.items():
        if normalized in by_normalized:
            continue
        tag = UserTag(name=original, normalized_name=normalized)
        db.add(tag)
        db.flush()
        by_normalized[normalized] = tag
    return [by_normalized[key].id for key in normalized_map]


def _normalize_tag(value: str) -> str:
    return value.strip().lower()


def _merge_ids(existing: list[int], incoming: list[int]) -> list[int]:
    merged: list[int] = []
    for value in existing + incoming:
        if value not in merged:
            merged.append(value)
    return merged
