from datetime import datetime
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models.database import MappingVersion


class MappingRegistry:

    def create_version(
        self,
        db: Session,
        source: str,
        mappings: list[dict[str, Any]],
        confidence: float,
        status: str = "candidate",
    ) -> dict[str, Any]:

        latest = db.execute(
            select(MappingVersion)
            .where(MappingVersion.source == source)
            .order_by(MappingVersion.version.desc())
        ).scalars().first()

        next_version = (
            latest.version + 1
            if latest
            else 1
        )

        record = MappingVersion(
            source=source,
            version=next_version,
            mappings=mappings,
            confidence=confidence,
            status=status,
            created_at=datetime.utcnow(),
        )

        db.add(record)
        db.commit()
        db.refresh(record)

        return self._to_dict(record)

    def get_versions(
        self,
        db: Session,
        source: str,
    ) -> list[dict[str, Any]]:

        records = db.execute(
            select(MappingVersion)
            .where(MappingVersion.source == source)
            .order_by(MappingVersion.version.asc())
        ).scalars().all()

        return [
            self._to_dict(record)
            for record in records
        ]

    def get_active_version(
        self,
        db: Session,
        source: str,
    ):

        record = db.execute(
            select(MappingVersion)
            .where(
                MappingVersion.source == source,
                MappingVersion.status == "active",
            )
            .order_by(MappingVersion.version.desc())
        ).scalars().first()

        if record is None:
            return None

        return self._to_dict(record)

    def activate_version(
        self,
        db: Session,
        source: str,
        version_number: int,
    ) -> dict[str, Any]:

        target = db.execute(
            select(MappingVersion)
            .where(
                MappingVersion.source == source,
                MappingVersion.version == version_number,
            )
        ).scalars().first()

        if target is None:
            raise ValueError(
                f"Version {version_number} not found for {source}"
            )

        db.execute(
            update(MappingVersion)
            .where(MappingVersion.source == source)
            .values(status="archived")
        )

        target.status = "active"

        db.commit()
        db.refresh(target)

        return self._to_dict(target)

    @staticmethod
    def _to_dict(record: MappingVersion) -> dict[str, Any]:
        return {
            "source": record.source,
            "version": record.version,
            "mappings": record.mappings,
            "confidence": record.confidence,
            "status": record.status,
            "created_at": record.created_at.isoformat(),
        }


mapping_registry = MappingRegistry()