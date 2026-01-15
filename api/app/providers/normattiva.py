from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List


PROVIDER_NAME = "normattiva"


def fetch_changes(since: datetime | None) -> List[Dict[str, Any]]:
    return [
        {
            "external_id": "normattiva:urn:nir:stato:legge:1990-08-07;241",
            "title": "Nuove norme in materia di procedimento amministrativo",
            "publication_date": "1990-08-07",
            "status": "in_force",
            "source_url": "https://www.normattiva.it/urn:nir:stato:legge:1990-08-07;241",
            "authority": "IT",
            "identifier": "urn:nir:stato:legge:1990-08-07;241",
            "primary_discipline_id": None,
        }
    ]


def get_details(external_id: str) -> Dict[str, Any]:
    return {
        "external_id": external_id,
        "title": "Nuove norme in materia di procedimento amministrativo",
        "publication_date": "1990-08-07",
        "status": "in_force",
        "source_url": "https://www.normattiva.it/urn:nir:stato:legge:1990-08-07;241",
        "authority": "IT",
        "identifier": "urn:nir:stato:legge:1990-08-07;241",
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
