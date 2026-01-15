from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from app.ingestion.mapping import apply_mapping
from app.ingestion.matching import match_and_merge_candidate


PROVIDER_NAME = "iso"


def fetch_changes(since: datetime | None) -> List[Dict[str, Any]]:
    return [
        {
            "external_id": "iso:9001:2015",
            "title": "Quality management systems — Requirements",
            "publication_date": "2015-09-15",
            "status": "in_force",
            "source_url": "https://www.iso.org/standard/62085.html",
            "authority": "ISO",
            "identifier": "ISO 9001:2015",
            "primary_discipline_id": None,
            "categories": ["quality management"],
            "keywords": ["QMS", "quality"],
        }
    ]


def get_details(external_id: str) -> Dict[str, Any]:
    return {
        "external_id": external_id,
        "title": "Quality management systems — Requirements",
        "publication_date": "2015-09-15",
        "status": "in_force",
        "source_url": "https://www.iso.org/standard/62085.html",
        "authority": "ISO",
        "identifier": "ISO 9001:2015",
        "primary_discipline_id": None,
        "categories": ["quality management"],
        "keywords": ["QMS", "quality"],
    }


def normalize(record: Dict[str, Any], db: Session | None = None) -> Dict[str, Any]:
    normalized = {
        "external_id": record["external_id"],
        "work": {
            "authority": record["authority"],
            "identifier": record["identifier"],
            "title": record["title"],
            "primary_discipline_id": record.get("primary_discipline_id"),
        },
        "edition": {
            "edition_label": "original",
            "publication_date": record.get("publication_date"),
            "status": record.get("status", "unknown"),
            "source_canonical_url": record.get("source_url"),
        },
        "relations": [],
        "categories": record.get("categories", []),
        "keywords": record.get("keywords", []),
    }
    return apply_mapping(normalized, db=db)


def match_and_merge(
    candidate: Dict[str, Any], db: Session | None = None
) -> Dict[str, Any]:
    return match_and_merge_candidate(candidate, db=db, provider=PROVIDER_NAME)
