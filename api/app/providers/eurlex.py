from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List


PROVIDER_NAME = "eurlex"


def fetch_changes(since: datetime | None) -> List[Dict[str, Any]]:
    return [
        {
            "external_id": "eurlex:32016R0679",
            "title": "General Data Protection Regulation",
            "publication_date": "2016-04-27",
            "status": "in_force",
            "source_url": "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32016R0679",
            "authority": "EU",
            "identifier": "CELEX:32016R0679",
            "primary_discipline_id": None,
        }
    ]


def get_details(external_id: str) -> Dict[str, Any]:
    return {
        "external_id": external_id,
        "title": "General Data Protection Regulation",
        "publication_date": "2016-04-27",
        "status": "in_force",
        "source_url": "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32016R0679",
        "authority": "EU",
        "identifier": "CELEX:32016R0679",
        "primary_discipline_id": None,
    }


def normalize(record: Dict[str, Any]) -> Dict[str, Any]:
    return {
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
    }


def match_and_merge(candidate: Dict[str, Any]) -> Dict[str, Any]:
    return candidate
